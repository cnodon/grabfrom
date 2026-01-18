# Squirrel

一个简洁高效的跨平台视频下载工具，支持从 YouTube 和 X.com 下载视频到本地。

## ✨ 功能亮点

- 📹 支持 YouTube 和 X.com (Twitter) 视频下载
- 🎬 智能解析 - 自动选择最高质量或手动选择
- 🔀 灵活输出 - 视频+音频 / 仅视频 / 仅音频
- 📊 下载管理 - 多任务并发、暂停恢复、断点续传
- 🎨 现代界面 - 4 界面设计，操作流畅

> 📖 **详细功能说明**: [prd.md](./prd.md)

---

## 📦 安装

### 方式一：下载安装包（推荐）

从 [Releases](https://github.com/yourusername/grabfrom/releases) 页面下载：
- **macOS**: `Squirrel-macOS.dmg`
- **Windows**: `Squirrel-Windows.exe`

### 方式二：从源码运行

```bash
# 克隆仓库
git clone https://github.com/yourusername/grabfrom.git
cd grabfrom

# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

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

> 📖 **详细架构说明**: [tech_arch.md](./tech_arch.md)

---

## 📋 支持的网站

| 网站 | URL 示例 |
|------|---------|
| YouTube | `https://www.youtube.com/watch?v=xxxxx` |
| YouTube 短链接 | `https://youtu.be/xxxxx` |
| X.com | `https://x.com/user/status/xxxxx` |
| Twitter | `https://twitter.com/user/status/xxxxx` |

---

## 🗺️ 路线图

- ✅ v1.0.0 - 核心功能（YouTube/X.com 下载）
- 🚧 v1.1.0 - 增强功能（完整设置、批量导入）
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
