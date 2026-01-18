# -*- coding: utf-8 -*-
"""
配置管理模块
处理 JSON 配置文件的读写和默认值管理
"""

import json
from pathlib import Path
from typing import Any, Optional


class Config:
    """配置管理类"""

    # 默认配置
    DEFAULT_CONFIG = {
        'download_path': str(Path.home() / 'Documents' / 'Squirrel'),
        'default_video_quality': 'best',  # best, 2160, 1440, 1080, 720
        'default_audio_format': 'mp3',    # mp3, m4a, flac
        'max_concurrent_downloads': 3,
        'launch_at_startup': False,
        'desktop_notifications': True,
        'dark_mode': False,
    }

    def __init__(self, config_path: Optional[Path] = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径，默认为用户目录下的 .grabfrom/config.json
        """
        if config_path is None:
            config_dir = Path.home() / '.grabfrom'
            config_dir.mkdir(parents=True, exist_ok=True)
            self.config_path = config_dir / 'config.json'
        else:
            self.config_path = Path(config_path)

        self._config = self._load_config()

    def _load_config(self) -> dict:
        """加载配置文件，不存在则使用默认配置"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                # 合并默认配置，确保新增配置项有默认值
                config = {**self.DEFAULT_CONFIG, **loaded}
                return config
            except (json.JSONDecodeError, IOError):
                return self.DEFAULT_CONFIG.copy()
        return self.DEFAULT_CONFIG.copy()

    def save(self) -> bool:
        """保存配置到文件"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            return True
        except IOError:
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        self._config[key] = value

    def get_all(self) -> dict:
        """获取所有配置"""
        return self._config.copy()

    def update(self, settings: dict) -> None:
        """批量更新配置"""
        self._config.update(settings)

    @property
    def download_path(self) -> Path:
        """获取下载路径"""
        path = Path(self._config.get('download_path', self.DEFAULT_CONFIG['download_path']))
        path.mkdir(parents=True, exist_ok=True)
        return path


# 全局配置实例
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """获取全局配置实例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
