# Squirrel

一个简洁高效的跨平台视频下载工具，支持从 YouTube、X.com 和 Bilibili 下载视频到本地。

## ✨ 功能亮点

- 📹 支持 YouTube、X.com (Twitter) 和 Bilibili 视频下载
- 🎬 智能解析 - 自动选择最高质量或手动选择
- 🔀 灵活输出 - 视频+音频 / 仅视频 / 仅音频
- 📊 下载管理 - 多任务并发、暂停恢复、断点续传
- 🎨 现代界面 - 4 界面设计，操作流畅
- 🔊 下载完成后自动保存音频（用于字幕/后处理，需 ffmpeg）
- 🗂️ 下载记录（SQLite 存储，支持筛选与重试）

> 📖 **详细功能说明**: [prd.md](./prd.md)

---

## 📦 安装

### 方式一：下载安装包（推荐）

从 [Releases](https://github.com/yourusername/squirrel/releases) 页面下载：
- **macOS**: `Squirrel-macOS.dmg`
- **Windows**: `Squirrel-Windows.exe`

### 方式二：从源码运行

```bash
# 克隆仓库
git clone https://github.com/yourusername/squirrel.git
cd squirrel

# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 更新 yt-dlp（建议遇到 403 或格式错误时执行）
pip install -U yt-dlp

# 运行应用
python main.py
```

### 系统要求

| 平台 | 最低要求 |
|------|---------|
| Python | 3.9+ |
| macOS | 10.14+ (Mojave) |
| Windows | Windows 10/11 |

---

## 🚀 快速开始

```
1. 启动应用，粘贴视频 URL
2. 选择质量和输出格式
3. 点击下载，等待完成
4. 打开文件夹查看视频
```

> 📖 **详细使用说明**: [prd.md - 使用流程](./prd.md#4-使用流程)

---

## 🖼️ 界面预览

| 界面 | 说明 | 设计稿 |
|------|------|--------|
| Launch UI | URL 输入入口 | [查看](/design/ui/grabfrom_launch_ui/) |
| Video Details UI | 视频预览和选项 | [查看](/design/ui/video_details_ui/) |
| Download Dashboard | 下载管理中心 | [查看](/design/ui/download_dashboard_ui/) |
| Settings UI | 应用设置 | [查看](/design/ui/settings_ui/) |

---

## 📚 文档

| 文档 | 内容 |
|------|------|
| [prd.md](./prd.md) | 产品需求 - 功能、界面、流程、路线图 |
| [tech_arch.md](./tech_arch.md) | 技术架构 - 技术栈、项目结构、API |
| [CLAUDE.md](./CLAUDE.md) | 开发指南 - 运行命令、开发约定 |

---

## 🛠️ 技术栈

| 组件 | 技术 |
|------|------|
| 后端 | Python 3.9+ / pywebview / yt-dlp |
| 前端 | HTML5 / Tailwind CSS / JavaScript |
| 打包 | PyInstaller |
| 数据存储 | SQLite（下载记录） |

> 📖 **详细架构说明**: [tech_arch.md](./tech_arch.md)

---

## ⚙️ 额外配置

### 自动保存音频

默认会在下载完成后生成单独的音频文件，便于后续字幕/转写处理（依赖 ffmpeg）。

配置项位于 `src/config.py`：
- `save_audio_on_complete`: 是否保存音频（默认 `True`）
- `audio_extract_format`: 音频格式（`m4a`/`mp3`/`flac`，默认 `m4a`）

### 文案与字符串管理

- 后端字符串：`src/strings.py`
- 前端字符串：`ui/js/strings.js`

---

## 🗂️ 下载记录

- 记录内容：URL、标题、平台、格式/清晰度、文件大小、保存路径、开始/结束时间、状态（完成/失败/取消）、错误原因、是否提取音频
- 历史列表：按时间/状态/平台/关键字筛选，支持搜索与排序
- 快捷操作：打开文件夹、复制链接、重新下载（跳转到详情界面）、删除单条、清空历史
- 技术方案：SQLite 本地数据库存储（`~/.grabfrom/history.db`）

---

## 🖼️ 图标与品牌

- GUI 界面 logo：替换 `assets/app_icon.png`
- 系统应用图标：
  - macOS：使用 `.icns` 并在打包时指定
  - Windows：使用 `.ico` 并在打包时指定

### 生成图标与打包

```bash
# 从 assets/app_icon.png 生成 .icns / .ico
python scripts/generate_icons.py
# 或
sh scripts/make_icons.sh

# 使用 PyInstaller spec 打包
pyinstaller scripts/squirrel.spec
```

---

## 📋 支持的网站

| 网站 | URL 示例 |
|------|---------|
| YouTube | `https://www.youtube.com/watch?v=xxxxx` |
| YouTube 短链接 | `https://youtu.be/xxxxx` |
| X.com | `https://x.com/user/status/xxxxx` |
| Bilibili | `https://www.bilibili.com/video/BVxxxxxx/` |
| Twitter | `https://twitter.com/user/status/xxxxx` |

---

## 🗺️ 路线图

- ✅ v1.0.0 - 核心功能（YouTube/X.com/Bilibili 下载）
- 🚧 v1.1.0 - 增强功能（完整设置、批量导入、下载记录）
- 📅 v1.2.0 - 扩展功能（播放列表、更多网站）
- 📅 v2.0.0 - 高级功能（视频预览、字幕下载）

> 📖 **完整路线图**: [prd.md - 产品路线图](./prd.md#7-产品路线图)

---

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**免责声明**: 本工具仅供个人学习和研究使用，请尊重视频版权。
