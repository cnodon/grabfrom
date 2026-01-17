# -*- coding: utf-8 -*-
"""
JavaScript Bridge API 模块
为 pywebview 提供前后端通信接口
"""

import webview
from pathlib import Path
from typing import Optional

from src.config import get_config
from src.parser import get_parser
from src.downloader import get_download_manager
from src.utils import open_folder as util_open_folder


class GrabFromAPI:
    """
    pywebview JavaScript API 类
    所有公开方法都可以从前端 JavaScript 调用
    """

    def __init__(self):
        """初始化 API"""
        self._window: Optional[webview.Window] = None
        self._config = get_config()
        self._parser = get_parser()
        self._downloader = get_download_manager()

        # 设置下载进度回调
        self._downloader.set_progress_callback(self._on_progress_update)

    def set_window(self, window: webview.Window):
        """设置 webview 窗口引用"""
        self._window = window

    def _on_progress_update(self, task_data: dict):
        """下载进度更新回调"""
        if self._window:
            # 通过 evaluate_js 推送进度到前端
            js_code = f"window.onDownloadProgress && window.onDownloadProgress({task_data})"
            try:
                self._window.evaluate_js(js_code)
            except Exception:
                pass  # 忽略窗口已关闭的情况

    # ==================== URL 解析 ====================

    def parse_url(self, url: str) -> dict:
        """
        解析视频 URL

        Args:
            url: 视频 URL

        Returns:
            视频信息字典，包含标题、缩略图、格式列表等
            出错时返回 {'error': '错误信息'}
        """
        if not url or not url.strip():
            return {'error': '请输入有效的 URL'}

        return self._parser.extract_info(url.strip())

    def validate_url(self, url: str) -> dict:
        """
        验证 URL 是否有效

        Args:
            url: 要验证的 URL

        Returns:
            {'valid': bool, 'platform': str}
        """
        if not url or not url.strip():
            return {'valid': False, 'platform': 'unknown'}

        is_valid = self._parser.validate_url(url.strip())
        platform, _ = self._parser.identify_platform(url.strip())

        return {
            'valid': is_valid,
            'platform': platform.value if is_valid else 'unknown'
        }

    # ==================== 下载管理 ====================

    def start_download(
        self,
        url: str,
        format_id: str,
        output_format: str,
        title: str,
        thumbnail: str = ""
    ) -> dict:
        """
        开始下载任务

        Args:
            url: 视频 URL
            format_id: 格式 ID
            output_format: 输出格式 (mp4, webm, mp3, m4a)
            title: 视频标题
            thumbnail: 缩略图 URL

        Returns:
            {'success': bool, 'task_id': str} 或 {'error': str}
        """
        try:
            task_id = self._downloader.create_task(
                url=url,
                format_id=format_id,
                output_format=output_format,
                title=title,
                thumbnail=thumbnail,
            )
            return {'success': True, 'task_id': task_id}
        except Exception as e:
            return {'error': str(e)}

    def pause_download(self, task_id: str) -> dict:
        """
        暂停下载任务

        Args:
            task_id: 任务 ID

        Returns:
            {'success': bool}
        """
        success = self._downloader.pause_task(task_id)
        return {'success': success}

    def resume_download(self, task_id: str) -> dict:
        """
        恢复下载任务

        Args:
            task_id: 任务 ID

        Returns:
            {'success': bool}
        """
        success = self._downloader.resume_task(task_id)
        return {'success': success}

    def cancel_download(self, task_id: str) -> dict:
        """
        取消下载任务

        Args:
            task_id: 任务 ID

        Returns:
            {'success': bool}
        """
        success = self._downloader.cancel_task(task_id)
        return {'success': success}

    def remove_task(self, task_id: str) -> dict:
        """
        移除已完成/取消/失败的任务

        Args:
            task_id: 任务 ID

        Returns:
            {'success': bool}
        """
        success = self._downloader.remove_task(task_id)
        return {'success': success}

    def get_task(self, task_id: str) -> dict:
        """
        获取任务信息

        Args:
            task_id: 任务 ID

        Returns:
            任务信息字典或 {'error': str}
        """
        task = self._downloader.get_task(task_id)
        if task:
            return task
        return {'error': '任务不存在'}

    def get_all_tasks(self) -> list:
        """
        获取所有下载任务

        Returns:
            任务列表
        """
        return self._downloader.get_all_tasks()

    def clear_completed(self) -> dict:
        """
        清除所有已完成的任务

        Returns:
            {'count': int} 已清除的任务数
        """
        count = self._downloader.clear_completed()
        return {'count': count}

    # ==================== 设置管理 ====================

    def get_settings(self) -> dict:
        """
        获取应用设置

        Returns:
            设置字典
        """
        return self._config.get_all()

    def save_settings(self, settings: dict) -> dict:
        """
        保存应用设置

        Args:
            settings: 设置字典

        Returns:
            {'success': bool}
        """
        try:
            self._config.update(settings)
            success = self._config.save()
            return {'success': success}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_setting(self, key: str) -> dict:
        """
        获取单个设置项

        Args:
            key: 设置键名

        Returns:
            {'value': any}
        """
        value = self._config.get(key)
        return {'value': value}

    def set_setting(self, key: str, value) -> dict:
        """
        设置单个设置项

        Args:
            key: 设置键名
            value: 设置值

        Returns:
            {'success': bool}
        """
        try:
            self._config.set(key, value)
            success = self._config.save()
            return {'success': success}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ==================== 文件系统操作 ====================

    def select_folder(self) -> dict:
        """
        打开文件夹选择对话框

        Returns:
            {'path': str} 选择的路径，或 {'cancelled': True}
        """
        if not self._window:
            return {'error': '窗口未初始化'}

        result = self._window.create_file_dialog(
            webview.FOLDER_DIALOG,
            directory=str(self._config.download_path)
        )

        if result and len(result) > 0:
            return {'path': result[0]}
        return {'cancelled': True}

    def open_folder(self, path: str = None) -> dict:
        """
        在系统文件管理器中打开文件夹

        Args:
            path: 文件夹路径，默认为下载目录

        Returns:
            {'success': bool}
        """
        if path is None:
            path = str(self._config.download_path)

        folder_path = Path(path)
        if not folder_path.exists():
            return {'success': False, 'error': '文件夹不存在'}

        success = util_open_folder(folder_path)
        return {'success': success}

    def open_file_location(self, filepath: str) -> dict:
        """
        在系统文件管理器中显示文件

        Args:
            filepath: 文件路径

        Returns:
            {'success': bool}
        """
        file_path = Path(filepath)
        if not file_path.exists():
            return {'success': False, 'error': '文件不存在'}

        # 打开文件所在目录
        success = util_open_folder(file_path.parent)
        return {'success': success}

    # ==================== 应用信息 ====================

    def get_app_info(self) -> dict:
        """
        获取应用信息

        Returns:
            应用信息字典
        """
        from src import __version__
        return {
            'name': 'GrabFrom',
            'version': __version__,
            'download_path': str(self._config.download_path),
        }
