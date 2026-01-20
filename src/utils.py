# -*- coding: utf-8 -*-
"""
工具函数模块
提供格式化、路径处理等通用功能
"""

import re
import platform
import subprocess
from pathlib import Path
from typing import Optional


def format_size(bytes_size: int) -> str:
    """
    格式化文件大小

    Args:
        bytes_size: 字节数

    Returns:
        格式化后的字符串，如 "1.5 GB"
    """
    if bytes_size < 0:
        return "0 B"

    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = float(bytes_size)

    for unit in units:
        if size < 1024:
            if unit == 'B':
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024

    return f"{size:.1f} PB"


def format_duration(seconds: int) -> str:
    """
    格式化时长

    Args:
        seconds: 秒数

    Returns:
        格式化后的字符串，如 "10:24" 或 "1:30:45"
    """
    if seconds is None:
        return "0:00"

    seconds = int(seconds)

    if seconds < 0:
        return "0:00"

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def format_speed(bytes_per_second: float) -> str:
    """
    格式化下载速度

    Args:
        bytes_per_second: 每秒字节数

    Returns:
        格式化后的字符串，如 "5.2 MB/s"
    """
    return f"{format_size(int(bytes_per_second))}/s"


def format_eta(seconds: Optional[int]) -> str:
    """
    格式化剩余时间

    Args:
        seconds: 剩余秒数

    Returns:
        格式化后的字符串，如 "2 mins remaining"
    """
    if seconds is None:
        return "计算中..."

    seconds = int(seconds)
    if seconds < 0:
        return "计算中..."

    if seconds < 60:
        return f"{seconds} 秒"

    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} 分钟"

    hours = minutes // 60
    remaining_mins = minutes % 60
    if remaining_mins > 0:
        return f"{hours} 小时 {remaining_mins} 分钟"
    return f"{hours} 小时"


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除非法字符

    Args:
        filename: 原始文件名

    Returns:
        清理后的安全文件名
    """
    # 移除/替换非法字符
    illegal_chars = r'[<>:"/\\|?*\x00-\x1f]'
    sanitized = re.sub(illegal_chars, '_', filename)

    # 移除首尾空格和点
    sanitized = sanitized.strip(' .')

    # 限制长度
    max_length = 200
    if len(sanitized) > max_length:
        # 保留扩展名
        name, ext = split_filename(sanitized)
        name = name[:max_length - len(ext) - 1]
        sanitized = f"{name}.{ext}" if ext else name

    return sanitized or 'untitled'


def split_filename(filename: str) -> tuple:
    """
    分离文件名和扩展名

    Args:
        filename: 完整文件名

    Returns:
        (文件名, 扩展名) 元组
    """
    path = Path(filename)
    return path.stem, path.suffix.lstrip('.')


def get_unique_filepath(directory: Path, filename: str) -> Path:
    """
    获取唯一的文件路径，避免覆盖已存在的文件

    Args:
        directory: 目标目录
        filename: 文件名

    Returns:
        唯一的文件路径
    """
    filepath = directory / filename

    if not filepath.exists():
        return filepath

    name, ext = split_filename(filename)
    counter = 1

    while True:
        new_filename = f"{name} ({counter}).{ext}" if ext else f"{name} ({counter})"
        new_filepath = directory / new_filename
        if not new_filepath.exists():
            return new_filepath
        counter += 1


def open_folder(path: Path) -> bool:
    """
    在系统文件管理器中打开文件夹

    Args:
        path: 文件夹路径

    Returns:
        是否成功打开
    """
    try:
        system = platform.system()

        if system == 'Darwin':  # macOS
            subprocess.run(['open', str(path)], check=True)
        elif system == 'Windows':
            subprocess.run(['explorer', str(path)], check=True)
        else:  # Linux
            subprocess.run(['xdg-open', str(path)], check=True)

        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def open_file(path: Path) -> bool:
    """
    使用系统默认程序打开文件

    Args:
        path: 文件路径

    Returns:
        是否成功打开
    """
    try:
        system = platform.system()

        if system == 'Darwin':  # macOS
            subprocess.run(['open', str(path)], check=True)
        elif system == 'Windows':
            subprocess.run(['cmd', '/c', 'start', '', str(path)], check=True)
        else:  # Linux
            subprocess.run(['xdg-open', str(path)], check=True)

        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False
