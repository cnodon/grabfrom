# -*- coding: utf-8 -*-
"""
URL 解析模块
实现 URL 验证、平台识别、yt-dlp 元数据提取
"""

import re
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum

import yt_dlp

from src.utils import format_size, format_duration


class Platform(Enum):
    """支持的平台"""
    YOUTUBE = 'youtube'
    TWITTER = 'twitter'  # X.com
    UNKNOWN = 'unknown'


@dataclass
class VideoFormat:
    """视频格式信息"""
    format_id: str
    ext: str
    resolution: str  # 如 "1920x1080" 或 "audio only"
    quality_label: str  # 如 "1080p", "720p", "HQ Audio"
    filesize: Optional[int] = None
    filesize_str: str = ""
    vcodec: str = ""
    acodec: str = ""
    fps: Optional[int] = None
    tbr: Optional[float] = None  # 总比特率
    has_video: bool = True
    has_audio: bool = True

    def __post_init__(self):
        if self.filesize:
            self.filesize_str = format_size(self.filesize)


@dataclass
class VideoInfo:
    """视频信息"""
    url: str
    platform: Platform
    video_id: str
    title: str
    description: str = ""
    thumbnail: str = ""
    duration: int = 0
    duration_str: str = ""
    channel: str = ""
    channel_url: str = ""
    view_count: int = 0
    like_count: int = 0
    upload_date: str = ""
    formats: list = field(default_factory=list)

    def __post_init__(self):
        if self.duration:
            self.duration_str = format_duration(self.duration)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'url': self.url,
            'platform': self.platform.value,
            'video_id': self.video_id,
            'title': self.title,
            'description': self.description,
            'thumbnail': self.thumbnail,
            'duration': self.duration,
            'duration_str': self.duration_str,
            'channel': self.channel,
            'channel_url': self.channel_url,
            'view_count': self.view_count,
            'like_count': self.like_count,
            'upload_date': self.upload_date,
            'formats': [
                {
                    'format_id': f.format_id,
                    'ext': f.ext,
                    'resolution': f.resolution,
                    'quality_label': f.quality_label,
                    'filesize': f.filesize,
                    'filesize_str': f.filesize_str,
                    'vcodec': f.vcodec,
                    'acodec': f.acodec,
                    'fps': f.fps,
                    'has_video': f.has_video,
                    'has_audio': f.has_audio,
                }
                for f in self.formats
            ]
        }


class URLParser:
    """URL 解析器"""

    # YouTube URL 正则
    YOUTUBE_PATTERNS = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?youtu\.be/([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
    ]

    # X.com (Twitter) URL 正则
    TWITTER_PATTERNS = [
        r'(?:https?://)?(?:www\.)?(?:twitter\.com|x\.com)/\w+/status/(\d+)',
    ]

    def __init__(self):
        """初始化解析器"""
        self._ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }

    def identify_platform(self, url: str) -> tuple:
        """
        识别 URL 对应的平台

        Args:
            url: 视频 URL

        Returns:
            (Platform, video_id) 元组
        """
        # 检查 YouTube
        for pattern in self.YOUTUBE_PATTERNS:
            match = re.search(pattern, url)
            if match:
                return Platform.YOUTUBE, match.group(1)

        # 检查 Twitter/X
        for pattern in self.TWITTER_PATTERNS:
            match = re.search(pattern, url)
            if match:
                return Platform.TWITTER, match.group(1)

        return Platform.UNKNOWN, None

    def validate_url(self, url: str) -> bool:
        """
        验证 URL 是否有效

        Args:
            url: 要验证的 URL

        Returns:
            是否有效
        """
        platform, video_id = self.identify_platform(url)
        return platform != Platform.UNKNOWN and video_id is not None

    def _parse_formats(self, formats_data: list) -> list:
        """解析格式列表"""
        formats = []
        seen_labels = set()

        for fmt in formats_data:
            format_id = fmt.get('format_id', '')
            ext = fmt.get('ext', '')
            vcodec = fmt.get('vcodec', 'none')
            acodec = fmt.get('acodec', 'none')

            has_video = vcodec != 'none' and vcodec is not None
            has_audio = acodec != 'none' and acodec is not None

            # 获取分辨率
            height = fmt.get('height')
            width = fmt.get('width')

            if has_video and height:
                resolution = f"{width}x{height}" if width else f"?x{height}"
                quality_label = f"{height}p"
            elif has_audio and not has_video:
                resolution = "audio only"
                abr = fmt.get('abr', 0)
                quality_label = f"HQ" if abr and abr >= 128 else "Audio"
            else:
                continue  # 跳过无效格式

            # 避免重复的质量标签
            label_key = f"{quality_label}_{ext}_{has_video}_{has_audio}"
            if label_key in seen_labels:
                continue
            seen_labels.add(label_key)

            filesize = fmt.get('filesize') or fmt.get('filesize_approx')

            video_format = VideoFormat(
                format_id=format_id,
                ext=ext,
                resolution=resolution,
                quality_label=quality_label,
                filesize=filesize,
                vcodec=vcodec if has_video else "",
                acodec=acodec if has_audio else "",
                fps=fmt.get('fps'),
                tbr=fmt.get('tbr'),
                has_video=has_video,
                has_audio=has_audio,
            )
            formats.append(video_format)

        # 按分辨率排序（高到低），音频格式放最后
        def sort_key(f):
            if not f.has_video:
                return (0, 0)
            try:
                height = int(f.resolution.split('x')[1]) if 'x' in f.resolution else 0
                return (1, height)
            except (ValueError, IndexError):
                return (0, 0)

        formats.sort(key=sort_key, reverse=True)
        return formats

    def extract_info(self, url: str) -> dict:
        """
        提取视频信息

        Args:
            url: 视频 URL

        Returns:
            包含视频信息的字典，出错时返回 {'error': '错误信息'}
        """
        platform, video_id = self.identify_platform(url)

        if platform == Platform.UNKNOWN:
            return {'error': '不支持的 URL 格式，请输入 YouTube 或 X.com 链接'}

        try:
            with yt_dlp.YoutubeDL(self._ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                if info is None:
                    return {'error': '无法获取视频信息'}

                # 解析格式
                formats = self._parse_formats(info.get('formats', []))

                video_info = VideoInfo(
                    url=url,
                    platform=platform,
                    video_id=video_id,
                    title=info.get('title', '未知标题'),
                    description=info.get('description', ''),
                    thumbnail=info.get('thumbnail', ''),
                    duration=info.get('duration', 0),
                    channel=info.get('uploader', info.get('channel', '')),
                    channel_url=info.get('uploader_url', info.get('channel_url', '')),
                    view_count=info.get('view_count', 0),
                    like_count=info.get('like_count', 0),
                    upload_date=info.get('upload_date', ''),
                    formats=formats,
                )

                return video_info.to_dict()

        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            if 'Video unavailable' in error_msg:
                return {'error': '视频不可用或已被删除'}
            elif 'Private video' in error_msg:
                return {'error': '这是一个私密视频，无法访问'}
            elif 'Sign in' in error_msg:
                return {'error': '此视频需要登录才能观看'}
            else:
                return {'error': f'获取视频信息失败: {error_msg}'}
        except Exception as e:
            return {'error': f'解析出错: {str(e)}'}


# 全局解析器实例
_parser_instance: Optional[URLParser] = None


def get_parser() -> URLParser:
    """获取全局解析器实例"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = URLParser()
    return _parser_instance
