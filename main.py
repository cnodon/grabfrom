# -*- coding: utf-8 -*-
"""
Squirrel - 跨平台视频下载工具
应用入口，初始化 pywebview 窗口
"""

import sys
import webview
from pathlib import Path

from src.api import SquirrelAPI
from src.config import get_config


def get_ui_path() -> Path:
    """获取 UI 文件路径"""
    # 开发环境
    ui_path = Path(__file__).parent / 'ui' / 'index.html'

    # 打包环境
    if hasattr(sys, '_MEIPASS'):
        ui_path = Path(sys._MEIPASS) / 'ui' / 'index.html'

    return ui_path


def get_icon_path() -> Path:
    """获取应用图标路径"""
    icon_path = Path(__file__).parent / 'assets' / 'app_icon.png'

    if hasattr(sys, '_MEIPASS'):
        icon_path = Path(sys._MEIPASS) / 'assets' / 'app_icon.png'

    return icon_path


def main():
    """应用主入口"""
    config = get_config()
    api = SquirrelAPI()

    # 获取 UI 路径
    ui_path = get_ui_path()
    icon_path = get_icon_path()

    if not ui_path.exists():
        print(f"错误: 找不到 UI 文件: {ui_path}")
        sys.exit(1)

    # 创建窗口
    window_args = {
        'title': 'Squirrel',
        'url': str(ui_path),
        'js_api': api,
        'width': 1200,
        'height': 800,
        'min_size': (900, 600),
        'background_color': '#fafafa',
    }
    if icon_path.exists():
        window_args['icon'] = str(icon_path)

    try:
        window = webview.create_window(**window_args)
    except TypeError as exc:
        if 'icon' in str(exc):
            window_args.pop('icon', None)
            window = webview.create_window(**window_args)
        else:
            raise

    # 保存窗口引用到 API，用于推送进度更新
    api.set_window(window)

    # 启动应用
    webview.start(debug=False)


if __name__ == '__main__':
    main()
