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
from pathlib import Path
from typing import Optional, Callable, Dict
from dataclasses import dataclass, field
from enum import Enum

import yt_dlp

from src.config import get_config
from src.strings import Messages
from src.utils import sanitize_filename, get_unique_filepath, format_size, format_speed, format_eta


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
    format_id: str = "best"
    output_format: str = "mp4"  # mp4, webm, mp3, m4a
    include_audio: bool = True
    has_audio: bool = True
    has_video: bool = True
    format_ext: str = ""
    audio_path: Optional[Path] = None
    output_path: Optional[Path] = None
    status: TaskStatus = TaskStatus.PENDING
    progress: DownloadProgress = field(default_factory=DownloadProgress)
    error_message: str = ""
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            'task_id': self.task_id,
            'url': self.url,
            'title': self.title,
            'thumbnail': self.thumbnail,
            'format_id': self.format_id,
            'output_format': self.output_format,
            'include_audio': self.include_audio,
            'has_audio': self.has_audio,
            'has_video': self.has_video,
            'format_ext': self.format_ext,
            'audio_path': str(self.audio_path) if self.audio_path else None,
            'output_path': str(self.output_path) if self.output_path else None,
            'status': self.status.value,
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

    def set_progress_callback(self, callback: Callable):
        """设置进度回调函数"""
        self._progress_callback = callback

    def _notify_progress(self, task_id: str):
        """通知进度更新"""
        if self._progress_callback and task_id in self._tasks:
            task = self._tasks[task_id]
            self._progress_callback(task.to_dict())

    def create_task(
        self,
        url: str,
        format_id: str,
        output_format: str,
        title: str,
        thumbnail: str = "",
        include_audio: bool = True,
        has_audio: bool = True,
        has_video: bool = True,
        format_ext: str = ""
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
            url=url,
            title=title,
            thumbnail=thumbnail,
            format_id=format_id,
            output_format=output_format,
            include_audio=include_audio,
            has_audio=has_audio,
            has_video=has_video,
            format_ext=format_ext,
        )

        with self._lock:
            self._tasks[task_id] = task
            self._pause_events[task_id] = threading.Event()
            self._pause_events[task_id].set()  # 初始状态为非暂停
            self._cancel_flags[task_id] = False

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
                return

            task.status = TaskStatus.DOWNLOADING
            self._notify_progress(task_id)

            config = get_config()
            download_path = config.download_path

            # 构建安全的文件名
            safe_title = sanitize_filename(task.title)
            filename = f"{safe_title}.{task.output_format}"
            output_file = get_unique_filepath(download_path, filename)

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

            # 构建 yt-dlp 选项
            ydl_opts = self._build_ydl_opts(task_id, task, output_file)

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([task.url])

                # 检查是否被取消
                if self._cancel_flags.get(task_id, False):
                    task.status = TaskStatus.CANCELLED
                    # 清理部分下载的文件
                    if output_file.exists():
                        output_file.unlink()
                else:
                    task.status = TaskStatus.COMPLETED
                    task.completed_at = time.time()
                    task.progress.percent = 100.0
                    self._extract_audio(task)
                    self._cleanup_temp_files(task)

            except yt_dlp.utils.DownloadError as e:
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error_message = Messages.DOWNLOAD_FAILED.format(error=str(e))

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
            subprocess.run(
                command,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            task.audio_path = audio_path
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

    def _build_ydl_opts(self, task_id: str, task: DownloadTask, output_file: Path) -> dict:
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

                if task.progress.total_bytes > 0:
                    task.progress.percent = (
                        task.progress.downloaded_bytes / task.progress.total_bytes * 100
                    )

                self._notify_progress(task_id)

            elif d['status'] == 'finished':
                task.progress.percent = 100.0
                if d.get('filename'):
                    task.output_path = Path(d.get('filename'))
                self._notify_progress(task_id)

        # 基础选项
        opts = {
            'outtmpl': str(output_file.with_suffix('.%(ext)s')),
            'progress_hooks': [progress_hook],
            'quiet': True,
            'no_warnings': True,
            'retries': 5,
            'fragment_retries': 5,
            'socket_timeout': 20,
        }

        ffmpeg_available = shutil.which('ffmpeg') is not None

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
        if pause_event:
            pause_event.set()
            task.status = TaskStatus.DOWNLOADING
            self._notify_progress(task_id)
            return True

        return False

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
        self._notify_progress(task_id)
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
    return _manager_instance
