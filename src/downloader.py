# -*- coding: utf-8 -*-
"""
下载管理器模块
实现下载任务管理、队列控制、进度追踪
"""

import uuid
import threading
import time
import shutil
import subprocess
import json
from pathlib import Path
from typing import Optional, Callable, Dict
from dataclasses import dataclass, field
from enum import Enum

import yt_dlp

from src.config import get_config
from src.strings import Messages
from src.utils import sanitize_filename, get_unique_filepath, format_size, format_speed, format_eta
from src.history import get_history_store


class TaskStatus(Enum):
    """任务状态"""
    PENDING = 'pending'        # 等待中
    DOWNLOADING = 'downloading'  # 下载中
    PAUSED = 'paused'          # 已暂停
    COMPLETED = 'completed'    # 已完成
    FAILED = 'failed'          # 失败
    CANCELLED = 'cancelled'    # 已取消


@dataclass
class DownloadProgress:
    """下载进度信息"""
    downloaded_bytes: int = 0
    total_bytes: int = 0
    speed: float = 0.0
    eta: Optional[int] = None
    percent: float = 0.0
    filename: str = ""

    def to_dict(self) -> dict:
        return {
            'downloaded_bytes': self.downloaded_bytes,
            'total_bytes': self.total_bytes,
            'downloaded_str': format_size(self.downloaded_bytes),
            'total_str': format_size(self.total_bytes),
            'speed': self.speed,
            'speed_str': format_speed(self.speed),
            'eta': self.eta,
            'eta_str': format_eta(self.eta),
            'percent': self.percent,
            'filename': self.filename,
        }


@dataclass
class DownloadTask:
    """下载任务"""
    task_id: str
    url: str
    title: str
    thumbnail: str = ""
    platform: str = ""
    format_id: str = "best"
    quality_label: str = ""
    resolution: str = ""
    output_format: str = "mp4"  # mp4, webm, mp3, m4a
    include_audio: bool = True
    has_audio: bool = True
    has_video: bool = True
    format_ext: str = ""
    history_id: Optional[int] = None
    audio_path: Optional[Path] = None
    output_path: Optional[Path] = None
    status: TaskStatus = TaskStatus.PENDING
    stage: str = "pending"
    progress: DownloadProgress = field(default_factory=DownloadProgress)
    error_message: str = ""
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            'task_id': self.task_id,
            'history_id': self.history_id,
            'url': self.url,
            'title': self.title,
            'thumbnail': self.thumbnail,
            'platform': self.platform,
            'format_id': self.format_id,
            'quality_label': self.quality_label,
            'resolution': self.resolution,
            'output_format': self.output_format,
            'include_audio': self.include_audio,
            'has_audio': self.has_audio,
            'has_video': self.has_video,
            'format_ext': self.format_ext,
            'audio_path': str(self.audio_path) if self.audio_path else None,
            'output_path': str(self.output_path) if self.output_path else None,
            'status': self.status.value,
            'stage': self.stage,
            'progress': self.progress.to_dict(),
            'error_message': self.error_message,
            'created_at': self.created_at,
            'completed_at': self.completed_at,
        }


class DownloadManager:
    """下载管理器"""

    def __init__(self, max_concurrent: int = 3):
        """
        初始化下载管理器

        Args:
            max_concurrent: 最大并发下载数
        """
        self._tasks: Dict[str, DownloadTask] = {}
        self._threads: Dict[str, threading.Thread] = {}
        self._pause_events: Dict[str, threading.Event] = {}
        self._cancel_flags: Dict[str, bool] = {}
        self._semaphore = threading.Semaphore(max_concurrent)
        self._lock = threading.Lock()
        self._progress_callback: Optional[Callable] = None
        self._history = get_history_store()

    def _register_task(self, task: DownloadTask) -> None:
        """注册任务到管理器内部"""
        with self._lock:
            self._tasks[task.task_id] = task
            pause_event = self._pause_events.get(task.task_id)
            if not pause_event:
                pause_event = threading.Event()
                self._pause_events[task.task_id] = pause_event
            if task.status == TaskStatus.PAUSED:
                pause_event.clear()
            else:
                pause_event.set()
            self._cancel_flags.setdefault(task.task_id, False)

    def set_progress_callback(self, callback: Callable):
        """设置进度回调函数"""
        self._progress_callback = callback

    def _notify_progress(self, task_id: str):
        """通知进度更新"""
        if self._progress_callback and task_id in self._tasks:
            task = self._tasks[task_id]
            self._progress_callback(task.to_dict())

    def _resolve_output_path(self, task: DownloadTask, download_path: Path, filename: str) -> Path:
        """恢复或生成输出路径"""
        if task.output_path:
            candidate = Path(task.output_path)
            part_candidate = candidate.with_name(candidate.name + ".part")
            if candidate.exists() or part_candidate.exists():
                return candidate
            if candidate.parent.exists():
                return candidate
        return get_unique_filepath(download_path, filename)

    def _determine_stage_from_info(self, info_dict: dict) -> str:
        """根据下载信息判断阶段"""
        vcodec = info_dict.get('vcodec')
        acodec = info_dict.get('acodec')
        if vcodec == 'none' and acodec != 'none':
            return 'downloading_audio'
        if acodec == 'none' and vcodec != 'none':
            return 'downloading_video'
        return 'downloading'

    def _needs_merge(self, task: DownloadTask, ffmpeg_available: bool) -> bool:
        if not ffmpeg_available:
            return False
        return task.include_audio and task.has_video and not task.has_audio

    def _needs_extract(self, task: DownloadTask) -> bool:
        return task.output_format in ['mp3', 'm4a', 'flac']

    def _calculate_overall_percent(
        self,
        task: DownloadTask,
        downloaded_bytes: int,
        total_bytes: int,
        stage: str,
        ffmpeg_available: bool,
    ) -> float:
        if total_bytes <= 0:
            return task.progress.percent

        download_percent = min(max(downloaded_bytes / total_bytes * 100, 0), 100)
        needs_merge = self._needs_merge(task, ffmpeg_available)
        needs_extract = self._needs_extract(task)

        if needs_extract:
            if stage.startswith('downloading'):
                return min(download_percent * 0.9, 90.0)
            if stage in ('extracting_audio', 'processing'):
                return 95.0
            return download_percent

        if needs_merge:
            if stage == 'downloading_video':
                return min(download_percent * 0.45, 45.0)
            if stage == 'downloading_audio':
                return 45.0 + min(download_percent * 0.45, 45.0)
            if stage == 'merging':
                return 95.0
            return min(download_percent, 95.0)

        return download_percent

    def _serialize_task(self, task: DownloadTask) -> dict:
        """序列化任务用于持久化"""
        data = task.to_dict()
        if task.status in (TaskStatus.DOWNLOADING, TaskStatus.PENDING):
            data['status'] = TaskStatus.PAUSED.value
            data['stage'] = 'paused'
        return data

    def _restore_task(self, data: dict) -> Optional[DownloadTask]:
        """从持久化数据恢复任务"""
        if not isinstance(data, dict):
            return None

        status_value = data.get('status', TaskStatus.PENDING.value)
        try:
            status = TaskStatus(status_value)
        except ValueError:
            status = TaskStatus.PAUSED

        if status in (TaskStatus.DOWNLOADING, TaskStatus.PENDING):
            status = TaskStatus.PAUSED

        progress_data = data.get('progress', {}) or {}
        progress = DownloadProgress(
            downloaded_bytes=int(progress_data.get('downloaded_bytes', 0) or 0),
            total_bytes=int(progress_data.get('total_bytes', 0) or 0),
            speed=float(progress_data.get('speed', 0) or 0),
            eta=progress_data.get('eta'),
            percent=float(progress_data.get('percent', 0) or 0),
            filename=progress_data.get('filename', '') or '',
        )

        created_at_value = data.get('created_at')
        try:
            created_at = (
                float(created_at_value)
                if created_at_value is not None
                else time.time()
            )
        except (TypeError, ValueError):
            created_at = time.time()

        task_id_value = data.get('task_id')
        task_id = str(task_id_value) if task_id_value else str(uuid.uuid4())[:8]

        task = DownloadTask(
            task_id=task_id,
            history_id=data.get('history_id'),
            url=data.get('url', ''),
            title=data.get('title', ''),
            thumbnail=data.get('thumbnail', ''),
            platform=data.get('platform', ''),
            format_id=data.get('format_id', 'best'),
            quality_label=data.get('quality_label', ''),
            resolution=data.get('resolution', ''),
            output_format=data.get('output_format', 'mp4'),
            include_audio=bool(data.get('include_audio', True)),
            has_audio=bool(data.get('has_audio', True)),
            has_video=bool(data.get('has_video', True)),
            format_ext=data.get('format_ext', ''),
            audio_path=Path(data['audio_path']) if data.get('audio_path') else None,
            output_path=Path(data['output_path']) if data.get('output_path') else None,
            status=status,
            stage=data.get('stage', status.value),
            progress=progress,
            error_message=data.get('error_message', ''),
            created_at=created_at,
            completed_at=data.get('completed_at'),
        )

        return task

    def save_state(self) -> None:
        """保存任务状态到磁盘"""
        config = get_config()
        state_path = config.tasks_path
        with self._lock:
            payload = [self._serialize_task(task) for task in self._tasks.values()]
        try:
            state_path.parent.mkdir(parents=True, exist_ok=True)
            with open(state_path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
        except OSError:
            pass

    def load_state(self) -> None:
        """从磁盘恢复任务状态"""
        config = get_config()
        state_path = config.tasks_path
        if not state_path.exists():
            return
        try:
            with open(state_path, 'r', encoding='utf-8') as f:
                payload = json.load(f)
        except (OSError, json.JSONDecodeError):
            return

        if not isinstance(payload, list):
            return

        for item in payload:
            task = self._restore_task(item)
            if not task:
                continue
            if not task.url:
                continue
            self._register_task(task)

    def create_task(
        self,
        url: str,
        format_id: str,
        output_format: str,
        title: str,
        thumbnail: str = "",
        platform: str = "",
        quality_label: str = "",
        resolution: str = "",
        include_audio: bool = True,
        has_audio: bool = True,
        has_video: bool = True,
        format_ext: str = "",
        history_id: Optional[int] = None,
    ) -> str:
        """
        创建下载任务

        Args:
            url: 视频 URL
            format_id: 格式 ID
            output_format: 输出格式
            title: 视频标题
            thumbnail: 缩略图 URL

        Returns:
            任务 ID
        """
        task_id = str(uuid.uuid4())[:8]

        task = DownloadTask(
            task_id=task_id,
            history_id=history_id,
            url=url,
            title=title,
            thumbnail=thumbnail,
            platform=platform,
            format_id=format_id,
            quality_label=quality_label,
            resolution=resolution,
            output_format=output_format,
            include_audio=include_audio,
            has_audio=has_audio,
            has_video=has_video,
            format_ext=format_ext,
            stage=TaskStatus.PENDING.value,
        )

        self._register_task(task)
        self._history.record_start(task)

        # 启动下载线程
        thread = threading.Thread(
            target=self._download_worker,
            args=(task_id,),
            daemon=True
        )
        self._threads[task_id] = thread
        thread.start()

        return task_id

    def _download_worker(self, task_id: str):
        """下载工作线程"""
        # 等待获取信号量
        self._semaphore.acquire()

        try:
            task = self._tasks.get(task_id)
            if not task:
                return

            # 检查是否已取消
            if self._cancel_flags.get(task_id, False):
                task.status = TaskStatus.CANCELLED
                self._notify_progress(task_id)
                self._history.record_finish(task)
                return

            task.status = TaskStatus.DOWNLOADING
            task.stage = TaskStatus.DOWNLOADING.value
            self._notify_progress(task_id)

            config = get_config()
            download_path = config.download_path

            # 构建安全的文件名
            safe_title = sanitize_filename(task.title)
            filename = f"{safe_title}.{task.output_format}"
            output_file = self._resolve_output_path(task, download_path, filename)
            task.output_path = output_file

            # 没有 ffmpeg 时，避免输出扩展名与实际格式不一致
            ffmpeg_available = shutil.which('ffmpeg') is not None
            if (
                not ffmpeg_available
                and task.include_audio
                and task.has_audio
                and task.has_video
                and task.format_ext
                and task.format_ext != task.output_format
            ):
                filename = f"{safe_title}.{task.format_ext}"
                output_file = get_unique_filepath(download_path, filename)
                task.output_format = task.format_ext
                task.output_path = output_file

            def attempt_download(opts: dict) -> None:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([task.url])

            # 构建 yt-dlp 选项
            ydl_opts = self._build_ydl_opts(task_id, task, output_file)

            try:
                attempt_download(ydl_opts)

                # 检查是否被取消
                if self._cancel_flags.get(task_id, False):
                    task.status = TaskStatus.CANCELLED
                    # 清理部分下载的文件
                    if output_file.exists():
                        output_file.unlink()
                else:
                    task.status = TaskStatus.COMPLETED
                    task.stage = TaskStatus.COMPLETED.value
                    task.completed_at = time.time()
                    task.progress.percent = 100.0
                    self._extract_audio(task)
                    self._cleanup_temp_files(task)
                    self._history.record_finish(task)

            except yt_dlp.utils.DownloadError as e:
                error_msg = str(e)
                retried = False
                if self._is_format_unavailable(error_msg):
                    retried = self._retry_with_fallback_format(
                        task_id,
                        task,
                        output_file,
                        ffmpeg_available,
                        attempt_download,
                    )
                elif self._is_http_403(error_msg):
                    retried = self._retry_with_cookies(
                        task_id,
                        task,
                        output_file,
                        attempt_download,
                    )

                if retried:
                    if self._cancel_flags.get(task_id, False):
                        task.status = TaskStatus.CANCELLED
                    else:
                        task.status = TaskStatus.COMPLETED
                        task.stage = TaskStatus.COMPLETED.value
                        task.completed_at = time.time()
                        task.progress.percent = 100.0
                    self._history.record_finish(task)
                    return

                if self._cancel_flags.get(task_id, False):
                    task.status = TaskStatus.CANCELLED
                    task.stage = TaskStatus.CANCELLED.value
                    task.error_message = ""
                else:
                    task.status = TaskStatus.FAILED
                    task.stage = TaskStatus.FAILED.value
                    task.error_message = error_msg
                self._history.record_finish(task)
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.stage = TaskStatus.FAILED.value
                task.error_message = Messages.DOWNLOAD_FAILED.format(error=str(e))
                self._history.record_finish(task)

            self._notify_progress(task_id)

        finally:
            self._semaphore.release()

    def _cleanup_temp_files(self, task: DownloadTask) -> None:
        """清理临时下载文件"""
        if not task.output_path:
            return

        output_path = Path(task.output_path)
        if not output_path.parent.exists():
            return

        prefix = output_path.stem
        for entry in output_path.parent.iterdir():
            if not entry.is_file():
                continue
            name = entry.name
            if name in (f"{prefix}.part", f"{prefix}.ytdl"):
                try:
                    entry.unlink()
                except OSError:
                    pass
                continue
            if name.startswith(f"{prefix}.") and (name.endswith(".part") or name.endswith(".ytdl")):
                try:
                    entry.unlink()
                except OSError:
                    pass

    @staticmethod
    def _is_format_unavailable(error_msg: str) -> bool:
        return "requested format is not available" in error_msg.lower()

    @staticmethod
    def _is_http_403(error_msg: str) -> bool:
        return "http error 403" in error_msg.lower() or "403" in error_msg

    def _retry_with_fallback_format(
        self,
        task_id: str,
        task: DownloadTask,
        output_file: Path,
        ffmpeg_available: bool,
        attempt_download: Callable[[dict], None],
    ) -> bool:
        """格式不可用时的降级重试"""
        if task.output_format in ['mp3', 'm4a', 'flac']:
            return False

        original_format_id = task.format_id
        original_has_audio = task.has_audio
        original_has_video = task.has_video

        if task.include_audio:
            if ffmpeg_available:
                task.format_id = ''
                task.has_audio = False
                task.has_video = True
            else:
                task.format_id = 'best'
                task.has_audio = True
                task.has_video = True
        else:
            task.format_id = ''

        try:
            fallback_opts = self._build_ydl_opts(task_id, task, output_file)
            attempt_download(fallback_opts)
            return True
        except Exception:
            task.format_id = original_format_id
            task.has_audio = original_has_audio
            task.has_video = original_has_video
            return False

    def _retry_with_cookies(
        self,
        task_id: str,
        task: DownloadTask,
        output_file: Path,
        attempt_download: Callable[[dict], None],
    ) -> bool:
        """403 时尝试使用浏览器 cookies 重试"""
        for browser in ['chrome', 'edge', 'brave', 'firefox', 'safari']:
            try:
                opts = self._build_ydl_opts(
                    task_id,
                    task,
                    output_file,
                    cookies_from_browser=browser,
                )
                attempt_download(opts)
                return True
            except Exception:
                continue
        return False

    def _extract_audio(self, task: DownloadTask) -> None:
        """为视频额外保存音频文件"""
        config = get_config()
        if not config.get('save_audio_on_complete', True):
            return

        if not task.output_path or not task.output_path.exists():
            return

        if not task.has_video:
            return

        ffmpeg_path = shutil.which('ffmpeg')
        if not ffmpeg_path:
            return

        output_format = config.get('audio_extract_format', 'm4a')
        if output_format not in ['m4a', 'mp3', 'flac']:
            output_format = 'm4a'

        base = task.output_path.with_suffix('')
        audio_path = task.output_path.with_name(f"{base.name}.audio.{output_format}")

        codec_args = {
            'm4a': ['-acodec', 'aac', '-b:a', '192k'],
            'mp3': ['-acodec', 'libmp3lame', '-b:a', '192k'],
            'flac': ['-acodec', 'flac'],
        }[output_format]

        command = [
            ffmpeg_path,
            '-y',
            '-i',
            str(task.output_path),
            '-vn',
            *codec_args,
            str(audio_path),
        ]

        try:
            task.stage = 'extracting_audio'
            task.progress.percent = max(task.progress.percent, 95.0)
            self._notify_progress(task.task_id)
            subprocess.run(
                command,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            task.audio_path = audio_path
            task.stage = TaskStatus.COMPLETED.value
            task.progress.percent = 100.0
            self._notify_progress(task.task_id)
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

    def _build_ydl_opts(
        self,
        task_id: str,
        task: DownloadTask,
        output_file: Path,
        cookies_from_browser: Optional[str] = None,
    ) -> dict:
        """构建 yt-dlp 选项"""

        def progress_hook(d):
            """进度回调钩子"""
            # 检查暂停
            pause_event = self._pause_events.get(task_id)
            if pause_event:
                pause_event.wait()  # 如果暂停则阻塞

            # 检查取消
            if self._cancel_flags.get(task_id, False):
                raise yt_dlp.utils.DownloadError(Messages.DOWNLOAD_CANCELLED)

            if d['status'] == 'downloading':
                task.progress.downloaded_bytes = d.get('downloaded_bytes', 0)
                task.progress.total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                task.progress.speed = d.get('speed', 0) or 0
                task.progress.eta = d.get('eta')
                task.progress.filename = d.get('filename', '')
                if task.progress.filename:
                    task.output_path = Path(task.progress.filename)

                info_dict = d.get('info_dict') or {}
                stage = self._determine_stage_from_info(info_dict)
                task.stage = stage
                task.progress.percent = self._calculate_overall_percent(
                    task,
                    task.progress.downloaded_bytes,
                    task.progress.total_bytes,
                    stage,
                    ffmpeg_available,
                )

                self._notify_progress(task_id)

            elif d['status'] == 'finished':
                if self._needs_merge(task, ffmpeg_available) or self._needs_extract(task):
                    task.stage = 'processing'
                    task.progress.percent = max(task.progress.percent, 95.0)
                else:
                    task.progress.percent = 100.0
                if d.get('filename'):
                    task.output_path = Path(d.get('filename'))
                self._notify_progress(task_id)

        # 基础选项
        opts = {
            'outtmpl': str(output_file.with_suffix('.%(ext)s')),
            'progress_hooks': [progress_hook],
            'postprocessor_hooks': [],
            'quiet': True,
            'no_warnings': True,
            'retries': 5,
            'fragment_retries': 5,
            'socket_timeout': 20,
            'continuedl': True,
            'http_headers': {
                'User-Agent': (
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/120.0.0.0 Safari/537.36'
                ),
                'Accept-Language': 'en-US,en;q=0.9',
            },
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                }
            },
        }
        if cookies_from_browser:
            opts['cookiesfrombrowser'] = cookies_from_browser

        ffmpeg_available = shutil.which('ffmpeg') is not None

        def postprocessor_hook(d):
            status = d.get('status')
            if status not in ['started', 'processing', 'finished']:
                return

            pp_name = d.get('postprocessor', '') or ''
            if 'ExtractAudio' in pp_name or 'AudioExtract' in pp_name:
                task.stage = 'extracting_audio'
            elif 'Merger' in pp_name or 'VideoConvertor' in pp_name:
                task.stage = 'merging'
            else:
                task.stage = 'processing'

            if status in ['started', 'processing']:
                task.progress.percent = max(task.progress.percent, 95.0)
            elif status == 'finished':
                task.progress.percent = 100.0
                if task.status != TaskStatus.CANCELLED:
                    task.stage = TaskStatus.COMPLETED.value
            self._notify_progress(task_id)

        opts['postprocessor_hooks'] = [postprocessor_hook]

        # 根据输出格式设置
        if task.output_format in ['mp3', 'm4a', 'flac']:
            if not ffmpeg_available:
                raise Exception(Messages.FFMPEG_AUDIO_REQUIRED)

            opts['format'] = 'bestaudio/best'
            opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': task.output_format,
                'preferredquality': '320' if task.output_format == 'mp3' else None,
            }]
            return opts

        # 视频格式
        if task.include_audio:
            if task.has_audio and task.has_video:
                opts['format'] = task.format_id or 'best'
            else:
                if not ffmpeg_available:
                    raise Exception(Messages.FFMPEG_MERGE_REQUIRED)
                if task.format_id and task.format_id != 'best':
                    opts['format'] = f"{task.format_id}+bestaudio/best"
                else:
                    opts['format'] = 'bestvideo+bestaudio/best'

            if ffmpeg_available and task.output_format in ['mp4', 'webm']:
                opts['merge_output_format'] = task.output_format
                if task.output_format == 'mp4':
                    opts['postprocessors'] = [{
                        'key': 'FFmpegVideoConvertor',
                        'preferedformat': 'mp4',
                    }]
        else:
            if task.format_id and task.format_id != 'best':
                opts['format'] = task.format_id
            else:
                opts['format'] = 'bestvideo/best'

        return opts

    def pause_task(self, task_id: str) -> bool:
        """暂停任务"""
        if task_id not in self._tasks:
            return False

        task = self._tasks[task_id]
        if task.status != TaskStatus.DOWNLOADING:
            return False

        # 清除暂停事件，让下载线程阻塞
        pause_event = self._pause_events.get(task_id)
        if pause_event:
            pause_event.clear()
            task.status = TaskStatus.PAUSED
            task.stage = TaskStatus.PAUSED.value
            self._notify_progress(task_id)
            return True

        return False

    def resume_task(self, task_id: str) -> bool:
        """恢复任务"""
        if task_id not in self._tasks:
            return False

        task = self._tasks[task_id]
        if task.status != TaskStatus.PAUSED:
            return False

        # 设置暂停事件，让下载线程继续
        pause_event = self._pause_events.get(task_id)
        if not pause_event:
            pause_event = threading.Event()
            self._pause_events[task_id] = pause_event
        pause_event.set()
        task.status = TaskStatus.DOWNLOADING
        task.stage = TaskStatus.DOWNLOADING.value
        task.error_message = ""
        self._cancel_flags[task_id] = False
        self._history.record_start(task)
        self._notify_progress(task_id)

        thread = self._threads.get(task_id)
        if not thread or not thread.is_alive():
            thread = threading.Thread(
                target=self._download_worker,
                args=(task_id,),
                daemon=True
            )
            self._threads[task_id] = thread
            thread.start()

        return True

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if task_id not in self._tasks:
            return False

        task = self._tasks[task_id]
        if task.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
            return False

        # 设置取消标志
        self._cancel_flags[task_id] = True

        # 如果任务已暂停，恢复它以便能退出
        pause_event = self._pause_events.get(task_id)
        if pause_event:
            pause_event.set()

        task.status = TaskStatus.CANCELLED
        task.stage = TaskStatus.CANCELLED.value
        self._notify_progress(task_id)
        self._history.record_finish(task)
        return True

    def get_task(self, task_id: str) -> Optional[dict]:
        """获取任务信息"""
        task = self._tasks.get(task_id)
        return task.to_dict() if task else None

    def get_all_tasks(self) -> list:
        """获取所有任务"""
        with self._lock:
            return [task.to_dict() for task in self._tasks.values()]

    def remove_task(self, task_id: str) -> bool:
        """移除任务（仅限已完成/已取消/失败的任务）"""
        if task_id not in self._tasks:
            return False

        task = self._tasks[task_id]
        if task.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.FAILED]:
            return False

        for target in [task.output_path, task.audio_path]:
            if not target:
                continue
            try:
                path = Path(target)
                if path.exists():
                    path.unlink()
            except OSError:
                pass

        self._cleanup_temp_files(task)

        with self._lock:
            del self._tasks[task_id]
            self._pause_events.pop(task_id, None)
            self._cancel_flags.pop(task_id, None)
            self._threads.pop(task_id, None)

        return True

    def clear_completed(self) -> int:
        """清除所有已完成的任务"""
        count = 0
        task_ids = list(self._tasks.keys())

        for task_id in task_ids:
            task = self._tasks.get(task_id)
            if task and task.status == TaskStatus.COMPLETED:
                self.remove_task(task_id)
                count += 1

        return count


# 全局下载管理器实例
_manager_instance: Optional[DownloadManager] = None


def get_download_manager() -> DownloadManager:
    """获取全局下载管理器实例"""
    global _manager_instance
    if _manager_instance is None:
        config = get_config()
        max_concurrent = config.get('max_concurrent_downloads', 3)
        _manager_instance = DownloadManager(max_concurrent=max_concurrent)
        _manager_instance.load_state()
    return _manager_instance
