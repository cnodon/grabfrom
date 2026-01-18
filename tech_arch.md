# Squirrel 技术架构文档

## 1. 技术栈概览

### 1.1 核心技术

| 组件 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 后端语言 | Python | 3.9+ | 视频解析、下载逻辑 |
| GUI 框架 | pywebview | 5.0+ | 跨平台桌面窗口，渲染 Web UI |
| 下载引擎 | yt-dlp | latest | 视频解析与下载 |
| 打包工具 | PyInstaller | 6.0+ | 生成独立可执行文件 |

### 1.2 前端技术

| 组件 | 技术 | 说明 |
|------|------|------|
| 样式框架 | Tailwind CSS | 现代化原子 CSS |
| 图标库 | Material Symbols | Google 图标 |
| 字体 | Manrope | 现代无衬线字体 |
| 交互 | Vanilla JavaScript (ES6+) | 前端路由与 API 调用 |

### 1.3 系统要求

| 平台 | 最低要求 |
|------|---------|
| Python | 3.9 或更高版本 |
| macOS | 10.14+ (Mojave 及以上) |
| Windows | Windows 10/11 |

---

## 2. 技术栈选型理由

### 2.1 为什么使用 pywebview 而非 Tkinter？

设计稿采用现代化的 Web 技术（Tailwind CSS）构建，具有以下特点：
- 侧边栏导航 + 主内容区布局
- 圆角卡片、阴影、渐变等现代视觉效果
- Toggle 开关、自定义下拉框等复杂组件
- 视频缩略图和进度条动画
- 响应式设计和暗黑模式支持

### 2.2 Tkinter 的限制

- 原生组件样式过时，难以实现现代化设计
- 自定义样式能力有限（无 CSS 支持）
- 缺少圆角、阴影、动画等现代 UI 特性
- 实现复杂布局和组件需要大量自定义代码

### 2.3 pywebview 的优势

- ✅ 直接复用 HTML/CSS 设计稿，无需重写 UI
- ✅ 完整的 CSS 样式支持，轻松实现现代化设计
- ✅ 通过 JavaScript Bridge 实现前后端通信
- ✅ 跨平台支持（macOS/Windows/Linux）
- ✅ 打包体积适中（约 30-50MB）

---

## 3. 架构特点

- **前后端分离**：Python 后端 + HTML/CSS/JS 前端
- **JavaScript Bridge**：pywebview 提供前后端通信桥梁
- **SPA 架构**：单页面应用，4 个视图动态切换
- **异步下载**：多任务并发，不阻塞 UI

---

## 4. 项目结构

```
grabfrom/
├── main.py                 # 应用入口
├── requirements.txt        # Python 依赖
├── build_macos.py         # macOS 打包脚本
├── build_windows.py       # Windows 打包脚本
│
├── src/                    # Python 后端源码
│   ├── __init__.py
│   ├── api.py             # pywebview JavaScript Bridge API
│   ├── downloader.py      # yt-dlp 下载逻辑封装
│   ├── parser.py          # URL 解析和视频信息获取
│   ├── config.py          # 配置管理
│   └── utils.py           # 工具函数
│
├── ui/                     # 前端资源
│   ├── index.html         # 主 HTML 文件（SPA 入口）
│   ├── css/
│   │   └── styles.css     # Tailwind 编译后的样式
│   ├── js/
│   │   ├── app.js         # 主应用逻辑
│   │   ├── router.js      # 前端路由
│   │   └── api.js         # 与 Python 后端通信
│   └── assets/            # 图片、图标等静态资源
│
├── design/                 # 设计稿（参考）
│   └── ui/
│       ├── grabfrom_launch_ui/
│       ├── video_details_ui/
│       ├── download_dashboard_ui/
│       └── settings_ui/
│
├── config/                 # 用户配置文件目录
│   └── settings.json
│
└── docs/                   # 文档
    ├── prd.md             # 产品需求文档
    └── tech_arch.md       # 技术架构文档（本文档）
```

---

## 5. 核心功能模块

### 5.1 视频解析模块 (`src/parser.py`)

| 组件 | 功能 |
|------|------|
| URL 解析器 | 识别和验证视频 URL（YouTube、X.com） |
| 元数据抓取器 | 获取视频标题、缩略图、时长等信息 |
| 流解析器 | 解析可用的视频流（分辨率、格式、编码） |

### 5.2 下载引擎模块 (`src/downloader.py`)

| 组件 | 功能 |
|------|------|
| 下载管理器 | 管理下载队列和并发任务 |
| 文件合并器 | 合并视频和音频流 |
| 进度追踪器 | 实时监控下载进度和速度 |
| 断点续传 | 支持下载中断后继续 |

### 5.3 GUI 交互模块 (`ui/js/`)

| 组件 | 功能 |
|------|------|
| 界面路由 | 管理 4 个界面之间的切换 |
| 状态管理 | 维护应用全局状态（下载任务、用户设置） |
| 事件处理 | 处理用户交互事件 |

### 5.4 存储管理模块 (`src/config.py`)

| 组件 | 功能 |
|------|------|
| 路径管理器 | 管理文件保存路径和路径记忆 |
| 配置管理器 | 保存和读取用户配置（JSON 格式） |
| 历史记录 | 记录下载历史 |

---

## 6. 前后端通信

pywebview 提供 JavaScript Bridge 实现前后端通信：

### 6.1 Python 后端 API (`src/api.py`)

```python
class Api:
    def parse_url(self, url: str) -> dict:
        """解析视频 URL，返回视频信息"""
        # 调用 yt-dlp 解析视频信息
        return {
            "title": "Video Title",
            "thumbnail": "https://...",
            "duration": "10:24",
            "channel": "Channel Name",
            "formats": [
                {"format_id": "137", "resolution": "1080p", "ext": "mp4", "filesize": 125600000},
                {"format_id": "136", "resolution": "720p", "ext": "mp4", "filesize": 78200000},
            ]
        }

    def start_download(self, video_id: str, format_id: str, save_path: str) -> str:
        """启动下载任务，返回任务 ID"""
        return task_id

    def pause_download(self, task_id: str) -> bool:
        """暂停下载任务"""
        return True

    def resume_download(self, task_id: str) -> bool:
        """恢复下载任务"""
        return True

    def cancel_download(self, task_id: str) -> bool:
        """取消下载任务"""
        return True

    def get_download_progress(self, task_id: str) -> dict:
        """获取下载进度"""
        return {
            "progress": 65.5,
            "speed": "5.2 MB/s",
            "eta": "2 mins remaining",
            "downloaded": "842 MB",
            "total": "1.2 GB"
        }

    def get_settings(self) -> dict:
        """获取用户设置"""
        return settings

    def save_settings(self, settings: dict) -> bool:
        """保存用户设置"""
        return True
```

### 6.2 JavaScript 前端调用 (`ui/js/api.js`)

```javascript
// 封装 Python API 调用
const api = {
    async parseUrl(url) {
        return await window.pywebview.api.parse_url(url);
    },

    async startDownload(videoId, formatId, savePath) {
        return await window.pywebview.api.start_download(videoId, formatId, savePath);
    },

    async pauseDownload(taskId) {
        return await window.pywebview.api.pause_download(taskId);
    },

    async resumeDownload(taskId) {
        return await window.pywebview.api.resume_download(taskId);
    },

    async cancelDownload(taskId) {
        return await window.pywebview.api.cancel_download(taskId);
    },

    async getDownloadProgress(taskId) {
        return await window.pywebview.api.get_download_progress(taskId);
    },

    async getSettings() {
        return await window.pywebview.api.get_settings();
    },

    async saveSettings(settings) {
        return await window.pywebview.api.save_settings(settings);
    }
};
```

---

## 7. 数据流图

```
┌─────────────────────────────────────────────────────────────────┐
│                        Squirrel Application                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐    JavaScript    ┌──────────────────┐     │
│  │                  │      Bridge      │                  │     │
│  │   UI Layer       │ ◄──────────────► │   Python Backend │     │
│  │   (HTML/CSS/JS)  │                  │   (pywebview)    │     │
│  │                  │                  │                  │     │
│  └────────┬─────────┘                  └────────┬─────────┘     │
│           │                                      │               │
│           │ User Events                          │ API Calls     │
│           ▼                                      ▼               │
│  ┌──────────────────┐                  ┌──────────────────┐     │
│  │   router.js      │                  │   downloader.py  │     │
│  │   (View Switch)  │                  │   (yt-dlp)       │     │
│  └──────────────────┘                  └────────┬─────────┘     │
│                                                  │               │
│                                                  ▼               │
│                                        ┌──────────────────┐     │
│                                        │   config.py      │     │
│                                        │   (Settings)     │     │
│                                        └────────┬─────────┘     │
│                                                  │               │
│                                                  ▼               │
│                                        ┌──────────────────┐     │
│                                        │   File System    │     │
│                                        │   (Downloads)    │     │
│                                        └──────────────────┘     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. 依赖清单

### 8.1 Python 依赖 (`requirements.txt`)

```
# GUI 框架 - 跨平台桌面应用
pywebview>=5.0

# 视频下载引擎
yt-dlp>=2024.1.0

# 打包工具
pyinstaller>=6.0

# macOS 专用依赖（pywebview 后端）
pyobjc-core>=10.0; sys_platform == 'darwin'
pyobjc-framework-Cocoa>=10.0; sys_platform == 'darwin'
pyobjc-framework-WebKit>=10.0; sys_platform == 'darwin'
```

### 8.2 前端依赖

- Tailwind CSS (via CDN 或本地编译)
- Material Symbols (via Google Fonts CDN)
- Manrope 字体 (via Google Fonts CDN)

---

## 9. 开发约定

### 9.1 代码规范

- 使用中文注释
- Python 代码遵循 PEP 8 规范
- JavaScript 代码使用 ES6+ 语法
- 使用 pathlib 处理文件路径以确保跨平台兼容性

### 9.2 功能要求

- 视频下载功能应支持断点续传
- 提供清晰的错误提示和下载状态反馈
- 异步操作不应阻塞 UI

### 9.3 错误处理

- 网络错误：显示重试选项
- URL 无效：提示支持的 URL 格式
- 存储空间不足：提示用户清理或更换路径

---

## 10. 构建与打包

### 10.1 开发环境

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 运行应用
python main.py
```

### 10.2 打包命令

```bash
# 打包 macOS 应用
python build_macos.py

# 打包 Windows 应用
python build_windows.py
```

### 10.3 输出产物

- **macOS**: `Squirrel-macOS.dmg` (~40MB)
- **Windows**: `Squirrel-Windows.exe` (~35MB)
