# Squirrel 产品需求文档 (PRD)

## 1. 产品概述

**Squirrel** 是一个简洁高效的跨平台视频下载工具，支持从 YouTube、X.com 和 Bilibili 下载视频到本地。

### 1.1 目标用户
- 需要下载在线视频供离线观看的用户
- 希望保存社交媒体视频的用户
- 需要提取视频音频的用户

### 1.2 支持平台
- **桌面系统**: macOS 10.14+, Windows 10/11
- **视频来源**: YouTube, X.com (Twitter), Bilibili

| 网站 | URL 示例 | 支持状态 |
|------|---------|---------|
| YouTube | `https://www.youtube.com/watch?v=xxxxx` | ✅ |
| YouTube 短链接 | `https://youtu.be/xxxxx` | ✅ |
| X.com | `https://x.com/user/status/xxxxx` | ✅ |
| Bilibili | `https://www.bilibili.com/video/BVxxxxx/` | ✅ |
| Twitter | `https://twitter.com/user/status/xxxxx` | ✅ |

---

## 2. 功能特性

### 2.1 核心功能
- ✅ 支持 YouTube 视频下载（包括 youtube.com 和 youtu.be 短链接）
- ✅ 支持 X.com（Twitter）视频下载
- ✅ 支持 Bilibili 视频下载
- ✅ 跨平台支持（macOS 和 Windows）
- ✅ 简洁的 4 界面设计，操作流程清晰直观

### 2.2 解析与下载选项
- 📹 **智能解析选项**
  - 最高质量视频（自动选择最佳质量）
  - 所有质量视频（展示所有可用分辨率）
- 🎬 **灵活的合并选项**
  - 自动合并音视频（完整视频文件）
  - 视频 Only（仅下载视频流）
  - 音频 Only（提取音频为 MP3）
- 📝 **视频预览功能**（缩略图、标题、时长）

### 2.3 下载管理
- 📊 **Download Dashboard 下载仪表盘**
  - 实时下载进度和速度显示
  - 多任务并发下载（最多 3 个同时进行）
  - 任务状态跟踪（等待中、下载中、已完成、失败）
- ⏯️ **完整的任务控制**
  - 暂停/恢复/取消/重试单个任务
  - 全部暂停/全部开始批量操作
  - 清除已完成任务
- 🗂️ **下载记录（History）**
  - 自动记录每次下载任务（含完成/失败/取消）
  - 记录内容：URL、标题、平台、格式/清晰度、文件大小、保存路径、开始/结束时间、状态、错误原因、是否提取音频
  - 支持按时间/状态/平台/关键字筛选、搜索与排序
  - 支持快速操作：打开文件夹、复制链接、重新下载（跳转到详情界面）、删除单条、清空历史
  - 技术实现：SQLite 本地数据库（默认位置 `~/.grabfrom/history.db`）
- 📁 **智能路径管理**
  - 默认保存路径：`~/Documents/Squirrel/`
  - 自定义保存文件夹
  - 记忆上次选择的路径
- 💾 **断点续传支持**
  - 应用退出后保留未完成任务，下次启动可继续

### 2.4 用户体验
- 🎨 现代化的 4 界面设计
- 🚀 流畅的界面切换体验
- 📂 下载完成后直接打开文件夹

---

## 3. 界面设计

### 3.1 界面交互流程

```
┌─────────────┐
│  Launch UI  │ 输入 URL
└──────┬──────┘
       │ 点击"下载"
       ↓
┌─────────────────┐
│ Video Details   │ 选择解析/合并选项
│      UI         │ 查看视频预览
└──────┬──────────┘
       │ 点击结果的"下载"
       ↓
┌─────────────────┐
│   Download      │ 监控下载进度
│   Dashboard     │ 管理任务队列 ←───────┐
└──────┬──────────┘                     │
       │                                │
       │ 点击 ⚙️                         │
       ↓                                │
┌─────────────────┐                     │
│  Settings UI    │ 查看关于/检查更新    │
└─────────────────┘                     │
       │                                │
       └────────────────────────────────┘
         返回 Dashboard
```

### 3.2 界面详细设计

#### 3.2.1 Launch UI（启动界面）

**设计稿**: [/design/ui/grabfrom_launch_ui/](/design/ui/grabfrom_launch_ui/)

- **功能**: URL 输入入口
- **组件**:
  - 应用 Logo 和标语
  - URL 输入框（支持粘贴）
  - "下载"按钮
  - 兼容平台图标展示
  - 存储使用情况显示
  - 检查更新按钮
- **交互流程**:
  - 用户粘贴视频 URL
  - 点击下载按钮后自动进入 Video Details UI

#### 3.2.2 Video Details UI（视频详情界面）

**设计稿**: [/design/ui/video_details_ui/](/design/ui/video_details_ui/)

- **功能**: 视频预览和解析配置
- **组件**:
  - 视频预览区域
    - 缩略图（带时长标签）
    - 视频来源标识（SOURCE: YOUTUBE）
    - 标题、频道名称、订阅数
    - 播放量、点赞数、分享按钮
  - 解析选项（Quality Profile，单选）:
    - Max Quality（最高质量）
    - All Available（所有质量）
  - 合并选项（Output Format，单选）:
    - Video+Audio（自动合并音视频）
    - Video Only（仅视频）
    - Audio（仅音频）
  - 解析结果列表（Available Streams）
    - 每项显示：分辨率标签、格式、编码信息、文件大小、下载按钮
  - 智能提示区域（Squirrel Engine 提示）
  - 已选择汇总（Total Selected）和"Download All"按钮
- **交互流程**:
  - 自动解析 URL 并显示视频信息
  - 用户选择解析选项和合并选项
  - 点击具体结果的"下载"按钮后进入 Download Dashboard UI

#### 3.2.3 Download Dashboard UI（下载仪表盘）

**设计稿**: [/design/ui/download_dashboard_ui/](/design/ui/download_dashboard_ui/)

- **功能**: 下载任务管理中心
- **组件**:
  - 顶部统计（Active / Finished 数量）
  - 搜索框和"Paste URL"快捷按钮
  - 任务过滤标签（All Tasks / Downloading / Paused / Completed / History）
  - 任务列表
    - 缩略图、文件名
    - 下载速度、剩余时间、已下载/总大小
    - 进度条
    - 状态标签（DOWNLOADING / PAUSED / COMPLETED）
    - 任务阶段标签（下载视频 / 下载音频 / 组装）
    - 操作按钮（暂停/播放、取消）
    - "Show in Folder"链接
  - 历史记录列表
    - 历史状态（完成/失败/取消）、完成时间、文件大小、保存路径
    - 操作：打开文件夹/复制链接/重新下载（跳转到详情界面）/删除记录/清空历史
  - 底部控制区
    - 总下载速度显示
    - 保存路径显示和"Change"按钮
    - "Pause All"和"Clear Finished"按钮
- **交互流程**:
  - 实时显示下载进度
  - 支持多任务并发下载
  - 完成后可直接打开文件所在文件夹

#### 3.2.4 Settings UI（设置界面）

**设计稿**: [/design/ui/settings_ui/](/design/ui/settings_ui/)

- **功能**: 应用配置和信息
- **组件**:
  - 侧边导航（General / Connection / About）
  - Download Location 设置
    - 默认保存路径输入框
    - "Change..."按钮
  - Quality Preferences 设置
    - Default Video Quality 下拉选择
    - Preferred Audio Format 下拉选择
  - App Behavior 设置
    - Launch at Startup（开关）
    - Desktop Notifications（开关）
    - Dark Mode（开关）
  - 版本状态显示和"Check for Updates"按钮

---

## 4. 使用流程

### 4.1 完整使用流程

#### 步骤 1：Launch UI（启动界面）
1. **启动应用**：双击打开 Squirrel
2. **输入 URL**：在输入框中粘贴视频链接
3. **点击"下载"按钮**：自动进入 Video Details UI

#### 步骤 2：Video Details UI（视频详情界面）
1. **查看视频预览**：自动显示视频缩略图、标题和时长
2. **选择解析选项**（单选）
   - 🔘 **Max Quality**：自动选择最佳分辨率（推荐）
   - 🔘 **All Available**：展示所有可用的分辨率选项
3. **选择合并选项**（单选）
   - 🔘 **Video+Audio**：下载完整视频文件（推荐）
   - 🔘 **Video Only**：仅下载视频流（无音频）
   - 🔘 **Audio**：仅提取音频
4. **查看解析结果**：列表显示所有可用的视频流
5. **点击"下载"按钮**：选择目标流，进入 Download Dashboard UI

#### 步骤 3：Download Dashboard UI（下载仪表盘）
1. **监控下载进度**：实时查看下载速度、进度条
2. **管理下载任务**：暂停、恢复、取消、重试
3. **批量操作**：全部暂停、清除已完成
4. **查看下载记录**：筛选历史任务、再次下载或清理记录
5. **管理保存路径**：可更改路径，应用会记忆选择
6. **打开文件夹**：下载完成后可直接打开文件所在位置

#### 步骤 4：Settings UI（设置界面）
1. **查看关于信息**：应用版本号
2. **检查更新**：点击"Check for Updates"按钮
3. **配置偏好设置**：下载路径、默认质量、应用行为

### 4.2 快速使用示例

**场景：下载一个 YouTube 1080p 视频**
```
1. Launch UI：粘贴 URL → 点击"下载"
2. Video Details UI：
   - 选择"Max Quality"
   - 选择"Video+Audio"
   - 点击 1080p 选项的"下载"按钮
3. Download Dashboard UI：等待下载完成
4. 完成！点击"Show in Folder"查看视频
```

**场景：仅下载音频**
```
1. Launch UI：粘贴 URL → 点击"下载"
2. Video Details UI：
   - 选择"Max Quality"
   - 选择"Audio"
   - 点击"下载"按钮
3. Download Dashboard UI：等待下载完成
4. 完成！获得音频文件
```

---

## 5. 默认配置

| 配置项 | 默认值 |
|--------|--------|
| 默认保存目录 | `~/Documents/Squirrel/` |
| 默认解析模式 | 最高质量视频 |
| 默认合并模式 | 自动合并音视频 |
| 最大并发下载数 | 3 |
| 开机启动 | 关闭 |
| 桌面通知 | 开启 |
| 暗黑模式 | 关闭 |
| 下载记录保留 | 90 天或 1000 条（先到先删） |
| 下载记录开关 | 开启 |

---

## 6. 常见问题

**Q: 如何在界面之间切换？**
A: 界面切换是自动的：Launch UI → Video Details UI → Download Dashboard UI。从任何界面都可以通过侧边栏进入 Settings UI。

**Q: 可以同时下载多个视频吗？**
A: 是的，在 Video Details UI 中添加多个下载任务，它们会在 Download Dashboard 中排队，最多同时进行 3 个下载。

**Q: "Max Quality"和"All Available"有什么区别？**
A: "Max Quality"会自动选择最佳分辨率（如 4K/1080p），解析速度更快。"All Available"会展示所有可用选项，让您手动选择。

**Q: "Video+Audio"是什么意思？**
A: YouTube 等平台会将高质量视频和音频分开存储。选择"Video+Audio"会下载并合并它们为完整视频文件。

**Q: 下载速度很慢怎么办？**
A: 可以尝试在 Settings UI 中配置代理服务器，或者选择较低的视频质量。

**Q: 提示"无法下载"错误？**
A: 请检查：1) URL 是否正确；2) 视频是否为私密或受地域限制；3) 网络连接是否正常。

**Q: 下载的视频保存在哪里？**
A: 默认保存在 `~/Documents/Squirrel/` 目录。在 Settings UI 或 Download Dashboard UI 中可自定义保存位置。

**Q: 支持断点续传吗？**
A: 是的，如果下载中断，可以在 Download Dashboard UI 中点击"恢复"按钮继续下载。

**Q: 下载记录在哪里查看？**
A: 在 Download Dashboard 的 History 过滤标签中查看，支持搜索、重新下载和清理记录。

---

## 7. 产品路线图

### v1.0.0 核心功能（当前版本）
- [x] 4 界面设计架构
- [x] YouTube、X.com 和 Bilibili 支持
- [x] 智能解析选项（最高质量/所有质量）
- [x] 灵活合并选项（音视频合并/视频 Only/音频 Only）
- [x] Download Dashboard 下载管理
- [x] 多任务并发下载
- [x] 断点续传支持
- [x] 路径记忆功能

### v1.1.0 增强功能
- [ ] Settings UI 完整功能实现
  - [ ] 默认保存路径配置
  - [ ] 默认解析和合并选项配置
  - [ ] 代理服务器设置
- [ ] 下载完成系统通知
- [ ] 批量 URL 导入（粘贴多个链接）
- [ ] 下载记录（可筛选/导出/清理）

### v1.2.0 扩展功能
- [ ] 支持 YouTube 播放列表下载
- [ ] 支持更多视频网站（Bilibili, Vimeo 等）
- [ ] 下载队列优先级调整
- [ ] 深色模式主题切换
- [ ] 自定义文件命名规则

### v2.0.0 高级功能
- [ ] 视频预览播放功能
- [ ] 字幕自动下载
- [ ] 视频转码选项
- [ ] 多语言界面支持

---

## 8. 法律声明

**免责声明**: 本工具仅供个人学习和研究使用，请尊重视频版权，不要用于商业用途或侵犯他人权益。
