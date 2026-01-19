/**
 * api.js - Python API 调用封装
 * 封装 pywebview 的 js_api 调用
 */

// 等待 pywebview API 就绪
function waitForPywebview() {
    return new Promise((resolve) => {
        if (window.pywebview && window.pywebview.api) {
            resolve(window.pywebview.api);
        } else {
            window.addEventListener('pywebviewready', () => {
                resolve(window.pywebview.api);
            });
        }
    });
}

// API 封装对象
const API = {
    _api: null,
    _ready: false,

    // 初始化 API
    async init() {
        this._api = await waitForPywebview();
        this._ready = true;
        console.log('API initialized');
        return this;
    },

    // 检查 API 是否就绪
    isReady() {
        return this._ready && this._api !== null;
    },

    // ==================== URL 解析 ====================

    // 解析视频 URL
    async parseUrl(url) {
        if (!this._api) await this.init();
        return await this._api.parse_url(url);
    },

    // 验证 URL
    async validateUrl(url) {
        if (!this._api) await this.init();
        return await this._api.validate_url(url);
    },

    // ==================== 下载管理 ====================

    // 开始下载
    async startDownload(
        url,
        formatId,
        outputFormat,
        title,
        thumbnail = '',
        includeAudio = true,
        hasAudio = true,
        hasVideo = true,
        formatExt = ''
    ) {
        if (!this._api) await this.init();
        return await this._api.start_download(
            url,
            formatId,
            outputFormat,
            title,
            thumbnail,
            includeAudio,
            hasAudio,
            hasVideo,
            formatExt
        );
    },

    // 暂停下载
    async pauseDownload(taskId) {
        if (!this._api) await this.init();
        return await this._api.pause_download(taskId);
    },

    // 恢复下载
    async resumeDownload(taskId) {
        if (!this._api) await this.init();
        return await this._api.resume_download(taskId);
    },

    // 取消下载
    async cancelDownload(taskId) {
        if (!this._api) await this.init();
        return await this._api.cancel_download(taskId);
    },

    // 移除任务
    async removeTask(taskId) {
        if (!this._api) await this.init();
        return await this._api.remove_task(taskId);
    },

    // 获取单个任务
    async getTask(taskId) {
        if (!this._api) await this.init();
        return await this._api.get_task(taskId);
    },

    // 获取所有任务
    async getAllTasks() {
        if (!this._api) await this.init();
        return await this._api.get_all_tasks();
    },

    // 清除已完成任务
    async clearCompleted() {
        if (!this._api) await this.init();
        return await this._api.clear_completed();
    },

    // ==================== 设置管理 ====================

    // 获取所有设置
    async getSettings() {
        if (!this._api) await this.init();
        return await this._api.get_settings();
    },

    // 保存设置
    async saveSettings(settings) {
        if (!this._api) await this.init();
        return await this._api.save_settings(settings);
    },

    // 获取单个设置
    async getSetting(key) {
        if (!this._api) await this.init();
        return await this._api.get_setting(key);
    },

    // 设置单个设置
    async setSetting(key, value) {
        if (!this._api) await this.init();
        return await this._api.set_setting(key, value);
    },

    // ==================== 文件系统 ====================

    // 选择文件夹
    async selectFolder() {
        if (!this._api) await this.init();
        return await this._api.select_folder();
    },

    // 打开文件夹
    async openFolder(path = null) {
        if (!this._api) await this.init();
        return await this._api.open_folder(path);
    },

    // 打开文件所在位置
    async openFileLocation(filepath) {
        if (!this._api) await this.init();
        return await this._api.open_file_location(filepath);
    },

    // 获取磁盘信息
    async getDiskInfo() {
        if (!this._api) await this.init();
        return await this._api.get_disk_info();
    },

    // ==================== 应用信息 ====================

    // 获取应用信息
    async getAppInfo() {
        if (!this._api) await this.init();
        return await this._api.get_app_info();
    }
};

// 导出 API
window.API = API;
