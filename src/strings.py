# -*- coding: utf-8 -*-
"""
用户可见字符串常量
"""


class Messages:
    INVALID_URL = '请输入有效的 URL'
    UNSUPPORTED_URL = '不支持的 URL 格式，请输入 YouTube 或 X.com 链接'
    VIDEO_UNAVAILABLE = '视频不可用或已被删除'
    PRIVATE_VIDEO = '这是一个私密视频，无法访问'
    LOGIN_REQUIRED = '此视频需要登录才能观看，请在浏览器中登录 X.com 后重试'
    INFO_FETCH_FAILED = '获取视频信息失败: {error}'
    PARSE_ERROR = '解析出错: {error}'

    WINDOW_NOT_READY = '窗口未初始化'
    FOLDER_NOT_FOUND = '文件夹不存在'
    FILE_NOT_FOUND = '文件不存在'
    FILE_NOT_FOUND_OPENED = '文件不存在，已打开下载目录'
    TASK_NOT_FOUND = '任务不存在'

    DOWNLOAD_CANCELLED = '用户取消下载'
    DOWNLOAD_FAILED = '下载失败: {error}'

    FFMPEG_AUDIO_REQUIRED = '需要安装 ffmpeg 才能提取音频'
    FFMPEG_MERGE_REQUIRED = '需要安装 ffmpeg 才能合并音视频'
