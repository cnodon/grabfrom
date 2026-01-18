# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Squirrel - 跨平台视频下载工具，支持 YouTube 和 X.com 视频下载。

## 运行命令

```bash
# 安装依赖
pip install -r requirements.txt

# 运行应用
python main.py

# 打包 macOS 应用
python build_macos.py

# 打包 Windows 应用
python build_windows.py
```

## 文档索引

| 文档 | 说明 |
|------|------|
| [prd.md](./prd.md) | 产品需求文档 - 功能特性、界面设计、使用流程、路线图 |
| [tech_arch.md](./tech_arch.md) | 技术架构文档 - 技术栈、项目结构、模块设计、API |
| [README.md](./README.md) | 用户文档 - 安装说明、快速开始 |

## 设计稿

| 界面 | 路径 |
|------|------|
| Launch UI | [/design/ui/grabfrom_launch_ui/](/design/ui/grabfrom_launch_ui/) |
| Video Details UI | [/design/ui/video_details_ui/](/design/ui/video_details_ui/) |
| Download Dashboard UI | [/design/ui/download_dashboard_ui/](/design/ui/download_dashboard_ui/) |
| Settings UI | [/design/ui/settings_ui/](/design/ui/settings_ui/) |

## 技术栈速览

- **后端**: Python 3.9+ / pywebview / yt-dlp
- **前端**: HTML5 / Tailwind CSS / JavaScript
- **打包**: PyInstaller

详见 [tech_arch.md](./tech_arch.md)

## 开发约定

- 使用中文注释
- 使用 pathlib 处理文件路径
- 支持断点续传
- 提供清晰的错误提示
