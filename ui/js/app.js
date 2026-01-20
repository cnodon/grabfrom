/* app.js - SPA logic for Squirrel */

let STRINGS = window.STRINGS || {};

const App = {
  state: {
    currentUrl: "",
    videoInfo: null,
    formats: [],
    qualityMode: "max",
    outputMode: "video+audio",
    selectedFormatIds: new Set(),
    tasks: new Map(),
    filter: "downloading",
    search: "",
    history: [],
    historyFilters: {
      status: "all",
      platform: "all",
      keyword: "",
      sort: "newest",
    },
    settings: {},
    appInfo: {},
  },
  elements: {},
  historyRefreshAt: 0,
  historyRefreshInFlight: false,

  init() {
    this.injectSidebars();
    this.cacheElements();
    this.bindEvents();
    window.onDownloadProgress = (task) => this.onDownloadProgress(task);
    Router.init((route) => this.onRouteChange(route));
    API.init().then(() => this.bootstrap());
  },

  cacheElements() {
    const get = (id) => document.getElementById(id);
    this.elements = {
      homeUrlInput: get("home-url-input"),
      homeDownloadBtn: get("home-download-btn"),
      homeError: get("home-error"),
      homeDownloadCounts: document.querySelectorAll(".home-download-count"),
      appVersionNodes: document.querySelectorAll(".app-version"),
      detailsRefresh: get("details-refresh"),
      detailsCopyUrl: get("details-copy-url"),
      detailsThumbnail: get("details-thumbnail"),
      detailsDuration: get("details-duration"),
      detailsSource: get("details-source"),
      detailsTitle: get("details-title"),
      detailsChannel: get("details-channel"),
      detailsMeta: get("details-meta"),
      detailsViews: get("details-views"),
      detailsLikes: get("details-likes"),
      qualityProfile: get("quality-profile"),
      outputFormat: get("output-format"),
      streamsList: get("streams-list"),
      downloadAllBtn: get("download-all-btn"),
      selectionSummary: get("selection-summary"),
      detailsDiskSpace: get("details-disk-space"),
      tasksList: get("tasks-list"),
      tasksSearch: get("tasks-search"),
      statActive: get("stat-active"),
      statPaused: get("stat-paused"),
      historyControls: get("history-controls"),
      historySearch: get("history-search"),
      historyStatus: get("history-status"),
      historyPlatform: get("history-platform"),
      historySort: get("history-sort"),
      dashboardPasteUrl: get("dashboard-paste-url"),
      dashboardSavePath: get("dashboard-save-path"),
      dashboardChangePath: get("dashboard-change-path"),
      pauseAllBtn: get("pause-all-btn"),
      clearFinishedBtn: get("clear-finished-btn"),
      clearHistoryBtn: get("clear-history-btn"),
      totalSpeed: get("total-speed"),
      speedBar: get("speed-bar"),
      settingsDownloadPath: get("settings-download-path"),
      settingsChangePath: get("settings-change-path"),
      settingsVideoQuality: get("settings-video-quality"),
      settingsAudioFormat: get("settings-audio-format"),
      toggleStartup: get("toggle-startup"),
      toggleNotifications: get("toggle-notifications"),
      toggleDarkMode: get("toggle-dark-mode"),
      settingsVersion: get("settings-version"),
      aboutVersion: get("about-version"),
      toastContainer: get("toast-container"),
      launchAnalysis: get("launch-analysis"),
      settingsLanguage: get("settings-language"),
    };
  },

  injectSidebars() {
    const template = document.getElementById("sidebar-template");
    if (!template) return;
    document.querySelectorAll("[data-sidebar]").forEach((slot) => {
      const clone = template.content.firstElementChild.cloneNode(true);
      slot.replaceWith(clone);
    });
  },

  setLanguage(language) {
    const fallback = (window.I18N && window.I18N["zh-Hans"]) || {};
    const next = (window.I18N && window.I18N[language]) || fallback;
    window.STRINGS = next;
    STRINGS = next;
    this.applyI18n();
    this.updateVersionLabels();
    if (this.state.videoInfo) {
      this.populateDetails(this.state.videoInfo);
    }
    if (this.state.filter === "history") {
      this.renderHistoryList();
    }
    this.refreshDiskInfo();
  },

  getString(path) {
    if (!path) return "";
    return path.split(".").reduce((acc, key) => acc?.[key], STRINGS);
  },

  formatString(template, values = {}) {
    if (!template) return "";
    return Object.keys(values).reduce(
      (text, key) => text.replaceAll(`{${key}}`, values[key]),
      template
    );
  },

  applyI18n() {
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const value = this.getString(el.dataset.i18n);
      if (value !== undefined && value !== null) {
        el.textContent = value;
      }
    });

    document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
      const value = this.getString(el.dataset.i18nPlaceholder);
      if (value !== undefined && value !== null) {
        el.setAttribute("placeholder", value);
      }
    });

    document.querySelectorAll("[data-i18n-title]").forEach((el) => {
      const value = this.getString(el.dataset.i18nTitle);
      if (value !== undefined && value !== null) {
        el.setAttribute("title", value);
      }
    });
  },

  bindEvents() {
    document.querySelectorAll("[data-route]").forEach((link) => {
      link.addEventListener("click", (event) => {
        event.preventDefault();
        const route = event.currentTarget.dataset.route;
        Router.navigate(route);
      });
    });

    document.querySelectorAll('[data-action="route-back"]').forEach((btn) => {
      btn.addEventListener("click", () => Router.back());
    });

    this.elements.homeDownloadBtn.addEventListener("click", () =>
      this.handleParseUrl()
    );
    this.elements.homeUrlInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        this.handleParseUrl();
      }
    });

    this.elements.detailsRefresh.addEventListener("click", () => {
      if (this.state.currentUrl) {
        this.parseUrl(this.state.currentUrl);
      }
    });
    this.elements.detailsCopyUrl.addEventListener("click", () => {
      if (this.state.currentUrl) {
        navigator.clipboard.writeText(this.state.currentUrl).catch(() => null);
        this.showToast(
          STRINGS.info?.linkCopiedTitle || "Link copied",
          STRINGS.info?.linkCopiedBody || "Copy completed"
        );
      }
    });

    this.elements.qualityProfile.addEventListener("click", (event) => {
      const button = event.target.closest("[data-quality]");
      if (!button) return;
      this.state.qualityMode = button.dataset.quality;
      this.updateToggleGroup(this.elements.qualityProfile, button);
      this.syncSelectionForMode();
      this.renderStreams();
    });

    this.elements.outputFormat.addEventListener("click", (event) => {
      const button = event.target.closest("[data-output]");
      if (!button) return;
      this.state.outputMode = button.dataset.output;
      this.updateToggleGroup(this.elements.outputFormat, button);
      if (
        this.state.outputMode === "audio" &&
        this.state.appInfo.ffmpeg_available === false
      ) {
        this.showToast(
          STRINGS.errors?.ffmpegRequiredTitle || "FFmpeg required",
          STRINGS.errors?.ffmpegRequiredBody ||
            "Audio extraction needs ffmpeg. Install it to continue.",
          true
        );
      }
      this.syncSelectionForMode();
      this.renderStreams();
    });

    this.elements.streamsList.addEventListener("click", (event) => {
      const downloadButton = event.target.closest("[data-action='download']");
      if (downloadButton) {
        const formatId = downloadButton.dataset.formatId;
        this.startDownload(formatId);
        return;
      }

      const row = event.target.closest("[data-format-id]");
      if (!row) return;
      this.toggleFormatSelection(row.dataset.formatId);
    });

    if (this.elements.downloadAllBtn) {
      this.elements.downloadAllBtn.addEventListener("click", () =>
        this.downloadSelected()
      );
    }

    document.querySelectorAll("[data-filter]").forEach((button) => {
      button.addEventListener("click", (event) => {
        document.querySelectorAll("[data-filter]").forEach((btn) => {
          btn.classList.remove("bg-primary", "text-white");
          btn.classList.add(
            "bg-white",
            "dark:bg-gray-800",
            "border",
            "border-gray-200",
            "dark:border-gray-700",
            "text-gray-600",
            "dark:text-gray-300"
          );
        });
        event.currentTarget.classList.add("bg-primary", "text-white");
        event.currentTarget.classList.remove(
          "bg-white",
          "dark:bg-gray-800",
          "border",
          "border-gray-200",
          "dark:border-gray-700",
          "text-gray-600",
          "dark:text-gray-300"
        );
        this.state.filter = event.currentTarget.dataset.filter;
        this.renderTasks();
      });
    });

    if (this.elements.tasksSearch) {
      this.elements.tasksSearch.addEventListener("input", (event) => {
        this.state.search = event.target.value.trim().toLowerCase();
        this.renderTasks();
      });
    }

    if (this.elements.historySearch) {
      this.elements.historySearch.addEventListener("input", (event) => {
        this.state.historyFilters.keyword = event.target.value.trim();
        this.refreshHistory();
      });
    }
    if (this.elements.historyStatus) {
      this.elements.historyStatus.addEventListener("change", (event) => {
        this.state.historyFilters.status = event.target.value;
        this.refreshHistory();
      });
    }
    if (this.elements.historyPlatform) {
      this.elements.historyPlatform.addEventListener("change", (event) => {
        this.state.historyFilters.platform = event.target.value;
        this.refreshHistory();
      });
    }
    if (this.elements.historySort) {
      this.elements.historySort.addEventListener("change", (event) => {
        this.state.historyFilters.sort = event.target.value;
        this.refreshHistory();
      });
    }

    if (this.elements.dashboardPasteUrl) {
      this.elements.dashboardPasteUrl.addEventListener("click", async () => {
        const text = await navigator.clipboard.readText().catch(() => "");
        if (text) {
          this.elements.homeUrlInput.value = text;
          Router.navigate("home");
          this.elements.homeUrlInput.focus();
        }
      });
    }

    if (this.elements.dashboardChangePath) {
      this.elements.dashboardChangePath.addEventListener("click", () =>
        this.pickDownloadPath()
      );
    }
    this.elements.settingsChangePath.addEventListener("click", () =>
      this.pickDownloadPath()
    );

    this.elements.pauseAllBtn.addEventListener("click", () =>
      this.pauseAll()
    );
    this.elements.clearFinishedBtn.addEventListener("click", () =>
      this.clearFinished()
    );
    if (this.elements.clearHistoryBtn) {
      this.elements.clearHistoryBtn.addEventListener("click", () =>
        this.clearHistory()
      );
    }

    this.elements.tasksList.addEventListener("click", (event) => {
      const historyAction = event.target.closest("[data-history-action]");
      if (historyAction) {
        const recordId = historyAction.dataset.historyId;
        const action = historyAction.dataset.historyAction;
        this.handleHistoryAction(recordId, action);
        return;
      }

      const action = event.target.closest("[data-task-action]");
      if (action) {
        const taskId = action.dataset.taskId;
        const taskAction = action.dataset.taskAction;
        this.handleTaskAction(taskId, taskAction);
        return;
      }

      const row = event.target.closest("[data-task-url]");
      if (!row) return;
      const taskUrl = row.dataset.taskUrl;
      if (taskUrl) {
        this.parseUrl(taskUrl);
      }
    });

    this.elements.settingsVideoQuality.addEventListener("change", () =>
      this.saveSettings()
    );
    this.elements.settingsAudioFormat.addEventListener("change", () =>
      this.saveSettings()
    );
    if (this.elements.settingsLanguage) {
      this.elements.settingsLanguage.addEventListener("change", () =>
        this.saveSettings()
      );
    }
    this.elements.toggleStartup.addEventListener("change", () =>
      this.saveSettings()
    );
    this.elements.toggleNotifications.addEventListener("change", () =>
      this.saveSettings()
    );
    this.elements.toggleDarkMode.addEventListener("change", () =>
      this.saveSettings()
    );
  },

  async bootstrap() {
    await this.loadAppInfo();
    await this.loadSettings();
    await this.loadTasks();
    this.renderTasks();
    this.syncDownloadCount();
  },

  onRouteChange(route) {
    if (route === "downloads") {
      this.renderTasks();
    }
  },

  async loadAppInfo() {
    const info = await API.getAppInfo();
    this.state.appInfo = info || {};
    this.updateVersionLabels();
    if (info?.download_path) {
      this.updateDownloadPath(info.download_path);
    }
    if (info && info.ffmpeg_available === false) {
      this.showToast(
        STRINGS.errors?.ffmpegMissingTitle || "FFmpeg missing",
        STRINGS.errors?.ffmpegMissingBody ||
          "Install ffmpeg to merge audio/video or extract audio.",
        true
      );
    }
  },

  updateVersionLabels() {
    const version = this.state.appInfo?.version;
    if (!version) return;
    if (this.elements.appVersionNodes) {
      this.elements.appVersionNodes.forEach((node) => {
        node.textContent = `v${version}`;
      });
    }
    if (this.elements.settingsVersion) {
      const template =
        STRINGS.ui?.settings?.statusUpToDate || "Up to date (v{version})";
      this.elements.settingsVersion.textContent = this.formatString(template, {
        version,
      });
    }
    if (this.elements.aboutVersion) {
      const template =
        STRINGS.ui?.settings?.aboutVersion || "Version {version}";
      this.elements.aboutVersion.textContent = this.formatString(template, {
        version,
      });
    }
  },

  async loadSettings() {
    const settings = await API.getSettings();
    this.state.settings = settings || {};
    this.applySettingsToUI();
    await this.refreshDiskInfo();
  },

  applySettingsToUI() {
    const settings = this.state.settings;
    if (settings.download_path) {
      this.updateDownloadPath(settings.download_path);
    }
    if (settings.default_video_quality) {
      this.elements.settingsVideoQuality.value =
        settings.default_video_quality;
    }
    if (settings.default_audio_format) {
      this.elements.settingsAudioFormat.value = settings.default_audio_format;
    }
    if (this.elements.settingsLanguage && settings.language) {
      this.elements.settingsLanguage.value = settings.language;
    }
    this.elements.toggleStartup.checked = !!settings.launch_at_startup;
    this.elements.toggleNotifications.checked =
      settings.desktop_notifications !== false;
    this.elements.toggleDarkMode.checked = !!settings.dark_mode;
    this.applyDarkMode(!!settings.dark_mode);
    this.setLanguage(settings.language || "zh-Hans");
  },

  async saveSettings() {
    const payload = {
      download_path: this.elements.settingsDownloadPath.value,
      default_video_quality: this.elements.settingsVideoQuality.value,
      default_audio_format: this.elements.settingsAudioFormat.value,
      language: this.elements.settingsLanguage
        ? this.elements.settingsLanguage.value
        : "zh-Hans",
      launch_at_startup: this.elements.toggleStartup.checked,
      desktop_notifications: this.elements.toggleNotifications.checked,
      dark_mode: this.elements.toggleDarkMode.checked,
    };
    await API.saveSettings(payload);
    this.state.settings = { ...this.state.settings, ...payload };
    this.applyDarkMode(!!payload.dark_mode);
    this.setLanguage(payload.language);
  },

  applyDarkMode(enabled) {
    document.documentElement.classList.toggle("dark", enabled);
  },

  async pickDownloadPath() {
    const result = await API.selectFolder();
    if (result?.path) {
      this.updateDownloadPath(result.path);
      await API.saveSettings({ download_path: result.path });
      this.state.settings.download_path = result.path;
    }
  },

  updateDownloadPath(path) {
    this.elements.settingsDownloadPath.value = path;
    if (this.elements.dashboardSavePath) {
      this.elements.dashboardSavePath.textContent = path;
    }
    this.refreshDiskInfo();
  },

  async loadTasks() {
    const tasks = await API.getAllTasks();
    this.state.tasks.clear();
    (tasks || []).forEach((task) => {
      this.state.tasks.set(task.task_id, task);
    });
  },

  syncDownloadCount() {
    const count = Array.from(this.state.tasks.values()).filter(
      (task) => task.status !== "completed"
    ).length;
    if (this.elements.homeDownloadCounts) {
      this.elements.homeDownloadCounts.forEach((node) => {
        node.textContent = count;
      });
    }
  },

  async handleParseUrl() {
    const url = this.elements.homeUrlInput.value.trim();
    if (!url) {
      this.showHomeError(STRINGS.errors?.emptyUrl || "Please enter a URL.");
      return;
    }
    this.showHomeError("");
    this.setLaunchLoading(true);
    await this.parseUrl(url);
  },

  async parseUrl(url) {
    this.elements.homeDownloadBtn.disabled = true;
    this.elements.homeDownloadBtn.classList.add("opacity-70");
    const result = await API.parseUrl(url);
    this.elements.homeDownloadBtn.disabled = false;
    this.elements.homeDownloadBtn.classList.remove("opacity-70");
    this.setLaunchLoading(false);

    if (result?.error) {
      this.showHomeError(result.error);
      return;
    }

    this.state.currentUrl = url;
    this.state.videoInfo = result;
    this.state.formats = result.formats || [];
    this.state.selectedFormatIds = new Set();
    this.state.qualityMode = "max";
    this.state.outputMode = "video+audio";
    this.updateToggleGroup(
      this.elements.qualityProfile,
      this.elements.qualityProfile.querySelector("[data-quality='max']")
    );
    this.updateToggleGroup(
      this.elements.outputFormat,
      this.elements.outputFormat.querySelector("[data-output='video+audio']")
    );
    this.populateDetails(result);
    this.syncSelectionForMode();
    this.renderStreams();
    Router.navigate("video-details");
  },

  setLaunchLoading(isLoading) {
    if (!this.elements.launchAnalysis) return;
    if (isLoading) {
      this.elements.launchAnalysis.classList.remove("hidden");
    } else {
      this.elements.launchAnalysis.classList.add("hidden");
    }
  },

  populateDetails(info) {
    if (!info) return;
    this.elements.detailsTitle.textContent = info.title || "--";
    this.elements.detailsDuration.textContent = info.duration_str || "0:00";
    const sourcePrefix =
      STRINGS.ui?.details?.sourcePrefix || "Source:";
    this.elements.detailsSource.textContent = `${sourcePrefix} ${
      info.platform || "--"
    }`;
    this.elements.detailsChannel.textContent = info.channel || "--";
    const uploadedPrefix =
      STRINGS.ui?.details?.uploadedPrefix || "Uploaded";
    this.elements.detailsMeta.textContent = info.upload_date
      ? `${uploadedPrefix} ${info.upload_date}`
      : "--";
    this.elements.detailsViews.textContent = this.formatNumber(
      info.view_count || 0
    );
    this.elements.detailsLikes.textContent = this.formatNumber(
      info.like_count || 0
    );
    if (info.thumbnail) {
      this.elements.detailsThumbnail.style.backgroundImage = `url('${info.thumbnail}')`;
    }
  },

  renderStreams() {
    const formats = this.getVisibleFormats();
    if (!formats.length) {
      const emptyText =
        STRINGS.labels?.noStreams || "No streams available for this mode.";
      this.elements.streamsList.innerHTML = `<div class="px-6 py-8 text-center text-sm text-gray-500">${this.escapeHtml(
        emptyText
      )}</div>`;
      this.updateSelectionSummary();
      return;
    }

    const rows = formats
      .map((format) => this.renderStreamRow(format))
      .join("");
    this.elements.streamsList.innerHTML = rows;
    this.updateSelectionSummary();
  },

  async refreshDiskInfo() {
    if (!this.elements.detailsDiskSpace) return;
    const result = await API.getDiskInfo();
    if (!result || !result.total_bytes) {
      return;
    }
    const template =
      STRINGS.ui?.details?.diskSpace || "Disk Free: {free} / {total}";
    this.elements.detailsDiskSpace.textContent = this.formatString(template, {
      free: this.formatBytes(result.free_bytes || 0),
      total: this.formatBytes(result.total_bytes || 0),
    });
  },

  renderStreamRow(format) {
    const selected = this.state.selectedFormatIds.has(format.format_id);
    const sizeLabel = format.filesize_str || "--";
    const ext = format.ext ? format.ext.toUpperCase() : "FILE";
    const title = format.has_video ? `${ext} Video` : `${ext} Audio`;
    const subtitle = format.has_video
      ? `${format.resolution} ${format.vcodec || ""}`.trim()
      : `${format.quality_label}`;
    const badgeClass = format.has_video
      ? "bg-primary text-white"
      : "bg-amber-100 text-amber-700";
    const badgeText = format.has_video ? format.quality_label : "HQ";
    const selectedClass = selected ? "bg-primary/5" : "";

    return `
      <div class="flex items-center px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 group transition-colors ${selectedClass}" data-format-id="${this.escapeHtml(
      format.format_id
    )}">
        <div class="flex-1 flex items-center gap-6">
          <span class="w-12 text-xs font-bold ${badgeClass} px-2 py-0.5 rounded text-center">${this.escapeHtml(
      badgeText
    )}</span>
          <div class="flex flex-col">
            <span class="text-sm font-semibold">${this.escapeHtml(title)}</span>
            <span class="text-[10px] text-gray-400 uppercase">${this.escapeHtml(
      subtitle || "--"
    )}</span>
          </div>
        </div>
        <div class="flex items-center gap-8">
          <span class="text-xs font-medium text-gray-500">${this.escapeHtml(
            sizeLabel
          )}</span>
          <button class="w-8 h-8 flex items-center justify-center rounded-full bg-gray-100 group-hover:bg-primary group-hover:text-white transition-all text-gray-400" data-action="download" data-format-id="${this.escapeHtml(
            format.format_id
          )}">
            <span class="material-symbols-outlined text-xl">download</span>
          </button>
        </div>
      </div>
    `;
  },

  getVisibleFormats() {
    const formats = this.state.formats || [];
    const mode = this.state.outputMode;
    let filtered = formats;

    if (mode === "audio") {
      filtered = formats.filter((f) => !f.has_video && f.has_audio);
    } else if (mode === "video-only") {
      filtered = formats.filter((f) => f.has_video);
    } else {
      filtered = formats.filter((f) => f.has_video);
      if (this.state.appInfo.ffmpeg_available === false) {
        filtered = filtered.filter((f) => f.has_audio && f.has_video);
      }
    }

    if (this.state.qualityMode === "max") {
      const best = this.pickBestFormat(filtered);
      return best ? [best] : filtered.slice(0, 1);
    }

    return filtered;
  },

  pickBestFormat(formats) {
    if (!formats.length) return null;
    const hasVideo = formats.some((format) => format.has_video);
    if (!hasVideo) {
      return formats.reduce((best, format) => {
        const bestSize = best.filesize || 0;
        const currentSize = format.filesize || 0;
        return currentSize > bestSize ? format : best;
      }, formats[0]);
    }

    const preferred = this.state.settings.default_video_quality;
    const match = formats.find((format) => {
      if (!preferred || preferred === "best") return false;
      return format.quality_label === `${preferred}p`;
    });
    if (match) return match;

    return formats.reduce((best, format) => {
      const bestHeight = this.extractHeight(best.quality_label);
      const currentHeight = this.extractHeight(format.quality_label);
      return currentHeight > bestHeight ? format : best;
    }, formats[0]);
  },

  syncSelectionForMode() {
    this.state.selectedFormatIds.clear();
    if (this.state.qualityMode === "max") {
      const best = this.pickBestFormat(this.getVisibleFormats());
      if (best) {
        this.state.selectedFormatIds.add(best.format_id);
      }
    }
    this.updateSelectionSummary();
  },

  toggleFormatSelection(formatId) {
    if (this.state.qualityMode === "max") return;
    if (this.state.selectedFormatIds.has(formatId)) {
      this.state.selectedFormatIds.delete(formatId);
    } else {
      this.state.selectedFormatIds.add(formatId);
    }
    this.renderStreams();
  },

  updateSelectionSummary() {
    const selected = Array.from(this.state.selectedFormatIds);
    const formats = this.state.formats || [];
    const selectedFormats = formats.filter((format) =>
      selected.includes(format.format_id)
    );
    const totalSize = selectedFormats.reduce(
      (sum, format) => sum + (format.filesize || 0),
      0
    );
    const template =
      STRINGS.ui?.details?.selectionSummary || "{count} Stream - {size}";
    this.elements.selectionSummary.textContent = this.formatString(template, {
      count: selectedFormats.length,
      size: this.formatBytes(totalSize),
    });
    if (this.elements.downloadAllBtn) {
      this.elements.downloadAllBtn.disabled = selectedFormats.length === 0;
    }
  },

  async downloadSelected() {
    const selected = Array.from(this.state.selectedFormatIds);
    for (const formatId of selected) {
      await this.startDownload(formatId, false);
    }
    Router.navigate("downloads");
  },

  async startDownload(formatId, navigate = true) {
    const info = this.state.videoInfo;
    if (!info) return;
    const format = this.state.formats.find((f) => f.format_id === formatId);
    if (!format) return;

    const outputFormat = this.resolveOutputFormat(format);
    const includeAudio = this.state.outputMode === "video+audio";
    const response = await API.startDownload(
      info.url,
      formatId,
      outputFormat,
      info.title,
      info.thumbnail || "",
      info.platform || "",
      format.quality_label || "",
      format.resolution || "",
      includeAudio,
      !!format.has_audio,
      !!format.has_video,
      format.ext || ""
    );

    if (response?.error) {
      this.showToast(
        STRINGS.errors?.downloadFailed || "Download failed",
        response.error,
        true
      );
      return;
    }

    if (response?.task_id) {
      const task = await API.getTask(response.task_id);
      if (task && !task.error) {
        this.state.tasks.set(task.task_id, task);
        this.renderTasks();
        this.syncDownloadCount();
        this.showToast(
          STRINGS.info?.downloadStartedTitle || "Download started",
          info.title
        );
        if (navigate) Router.navigate("downloads");
      }
    }
  },

  resolveOutputFormat(format) {
    if (this.state.outputMode === "audio") {
      return this.state.settings.default_audio_format || "mp3";
    }
    if (this.state.outputMode === "video-only") {
      return ["mp4", "webm"].includes(format.ext) ? format.ext : "mp4";
    }
    return "mp4";
  },

  async onDownloadProgress(task) {
    if (!task?.task_id) return;
    this.state.tasks.set(task.task_id, task);
    this.renderTasks();
    this.syncDownloadCount();
    if (task.status === "completed") {
      this.showToast(
        STRINGS.info?.downloadCompletedTitle || "Download completed",
        task.title
      );
    }
  },

  renderTasks() {
    this.updateStats([]);
    if (this.state.filter === "history") {
      this.toggleHistoryControls(true);
      this.refreshHistory();
      return;
    }
    this.toggleHistoryControls(false);
    const tasks = this.getFilteredTasks();
    if (!tasks.length) {
      const emptyTasks =
        STRINGS.labels?.noTasks || "No tasks available.";
      this.elements.tasksList.innerHTML = `<div class="bg-white dark:bg-[#25282c] p-6 rounded-xl border border-gray-100 dark:border-gray-700/50 text-center text-sm text-gray-500">${this.escapeHtml(
        emptyTasks
      )}</div>`;
    } else {
      this.elements.tasksList.innerHTML = tasks
        .map((task) => this.renderTaskRow(task))
        .join("");
    }
    this.updateStats(tasks);
  },

  getFilteredTasks() {
    const all = Array.from(this.state.tasks.values());
    let filtered = all;
    if (this.state.filter === "downloading") {
      filtered = filtered.filter((task) =>
        ["downloading", "pending", "paused"].includes(task.status)
      );
    } else if (this.state.filter === "completed") {
      filtered = filtered.filter((task) => task.status === "completed");
    }
    if (this.state.search) {
      filtered = filtered.filter((task) =>
        task.title.toLowerCase().includes(this.state.search)
      );
    }
    return filtered.sort((a, b) => b.created_at - a.created_at);
  },

  toggleHistoryControls(show) {
    if (this.elements.historyControls) {
      this.elements.historyControls.classList.toggle("hidden", !show);
    }
    if (this.elements.pauseAllBtn) {
      this.elements.pauseAllBtn.classList.toggle("hidden", show);
    }
    if (this.elements.clearFinishedBtn) {
      this.elements.clearFinishedBtn.classList.toggle("hidden", show);
    }
    if (this.elements.clearHistoryBtn) {
      this.elements.clearHistoryBtn.classList.toggle("hidden", !show);
    }
  },

  async refreshHistory(force = false) {
    if (this.historyRefreshInFlight) return;
    const now = Date.now();
    if (!force && now - this.historyRefreshAt < 600) return;
    if (this.state.filter !== "history") return;
    this.historyRefreshInFlight = true;
    this.historyRefreshAt = now;
    try {
      const filters = this.state.historyFilters || {};
      const records = await API.getHistory({
        status: filters.status || "all",
        platform: filters.platform || "all",
        keyword: filters.keyword || "",
        sort: filters.sort || "newest",
      });
      if (this.state.filter !== "history") {
        return;
      }
      this.state.history = records || [];
      this.renderHistoryList();
    } finally {
      this.historyRefreshInFlight = false;
    }
  },

  renderHistoryList() {
    const records = this.state.history || [];
    if (!records.length) {
      const emptyText =
        STRINGS.ui?.dashboard?.history?.empty || "No history records.";
      this.elements.tasksList.innerHTML = `<div class="bg-white dark:bg-[#25282c] p-6 rounded-xl border border-gray-100 dark:border-gray-700/50 text-center text-sm text-gray-500">${this.escapeHtml(
        emptyText
      )}</div>`;
      return;
    }
    this.elements.tasksList.innerHTML = records
      .map((record) => this.renderHistoryRow(record))
      .join("");
  },

  renderHistoryRow(record) {
    const status = record.status || "completed";
    const statusBadge = this.getStatusBadge(status);
    const sizeLabel = record.filesize_bytes
      ? this.formatBytes(record.filesize_bytes)
      : "--";
    const finishedAt = record.finished_at || record.started_at;
    const timeLabel = finishedAt ? this.formatDateTime(finishedAt) : "--";
    const qualityLabel =
      record.quality_label ||
      record.resolution ||
      (record.output_format ? record.output_format.toUpperCase() : "--");
    const platformLabel = this.getPlatformLabel(record.platform);
    const strings = STRINGS.ui?.dashboard?.history || {};
    const audioLabel = record.audio_extracted
      ? strings.audioYes || "Yes"
      : strings.audioNo || "No";

    return `
      <div class="history-row group relative bg-white dark:bg-[#25282c] p-4 rounded-xl border border-gray-100 dark:border-gray-700/50 shadow-sm hover:shadow-md transition-all" data-history-id="${this.escapeHtml(
        record.id
      )}">
        <div class="flex items-start gap-4">
          <div class="relative size-14 shrink-0 bg-gray-100 dark:bg-gray-800 rounded-lg overflow-hidden flex items-center justify-center">
            <span class="material-symbols-outlined text-primary text-2xl">history</span>
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between mb-1">
              <h3 class="text-sm font-bold truncate text-[#121617] dark:text-white pr-4">${this.escapeHtml(
                record.title || "Untitled"
              )}</h3>
              ${statusBadge}
            </div>
            <div class="flex flex-wrap items-center gap-3 text-[11px] text-[#658086] mb-2">
              <span>${this.escapeHtml(platformLabel)}</span>
              <span>•</span>
              <span>${this.escapeHtml(qualityLabel)}</span>
              <span>•</span>
              <span>${this.escapeHtml(
                (strings.labelSize || "Size") + ": " + sizeLabel
              )}</span>
              <span>•</span>
              <span>${this.escapeHtml(
                (strings.labelAudio || "Audio extracted") + ": " + audioLabel
              )}</span>
            </div>
            <div class="text-[11px] text-[#8A9AA0] flex items-center gap-2">
              <span class="material-symbols-outlined text-[14px]">event</span>
              <span>${this.escapeHtml(
                (strings.labelFinished || "Finished") + ": " + timeLabel
              )}</span>
            </div>
            ${
              record.error_message
                ? `<p class="text-[11px] text-red-500 mt-2">${this.escapeHtml(
                    record.error_message
                  )}</p>`
                : ""
            }
          </div>
          <div class="hover-actions opacity-0 flex items-center gap-2 transition-opacity ml-2">
            <button class="size-9 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 flex items-center justify-center hover:bg-gray-200 transition-colors" data-history-action="open-folder" data-history-id="${this.escapeHtml(
              record.id
            )}" title="${this.escapeHtml(
      strings.actionOpen || "Open folder"
    )}">
              <span class="material-symbols-outlined text-xl">folder_open</span>
            </button>
            <button class="size-9 rounded-full bg-primary text-white flex items-center justify-center hover:bg-primary/90 transition-colors shadow-lg shadow-primary/30" data-history-action="play" data-history-id="${this.escapeHtml(
              record.id
            )}" title="${this.escapeHtml(
      strings.actionPlay || "Play"
    )}">
              <span class="material-symbols-outlined text-xl">play_arrow</span>
            </button>
            <button class="size-9 rounded-full bg-gray-100 dark:bg-gray-700 text-red-500 flex items-center justify-center hover:bg-red-50 transition-colors" data-history-action="delete" data-history-id="${this.escapeHtml(
              record.id
            )}" title="${this.escapeHtml(
      strings.actionDelete || "Delete record"
    )}">
              <span class="material-symbols-outlined text-xl">delete</span>
            </button>
          </div>
        </div>
      </div>
    `;
  },

  async handleHistoryAction(recordId, action) {
    const record = (this.state.history || []).find(
      (item) => String(item.id) === String(recordId)
    );
    if (!record) return;

    if (action === "open-folder") {
      if (record.save_path) {
        const result = await API.openFileLocation(record.save_path);
        if (result?.warning) {
          this.showToast(
            STRINGS.info?.openedFolderTitle || "Opened folder",
            result.warning
          );
        } else if (result?.success === false) {
          this.showToast(
            STRINGS.errors?.openFailed || "Open failed",
            result.error ||
              STRINGS.errors?.openFailedGeneric ||
              "Unable to open",
            true
          );
        }
      } else {
        this.showToast(
          STRINGS.errors?.openFailed || "Open failed",
          STRINGS.errors?.openFailedMissingPath || "File path missing",
          true
        );
      }
      return;
    }

    if (action === "play") {
      if (record.save_path) {
        const result = await API.openFile(record.save_path);
        if (result?.warning) {
          this.showToast(
            STRINGS.info?.openedFolderTitle || "Opened folder",
            result.warning
          );
        } else if (result?.success === false) {
          this.showToast(
            STRINGS.errors?.openFailed || "Open failed",
            result.error ||
              STRINGS.errors?.openFailedGeneric ||
              "Unable to open",
            true
          );
        }
      } else {
        this.showToast(
          STRINGS.errors?.openFailed || "Open failed",
          STRINGS.errors?.openFailedMissingPath || "File path missing",
          true
        );
      }
      return;
    }

    if (action === "delete") {
      await API.deleteHistory(record.id);
      this.refreshHistory(true);
    }
  },

  async clearHistory() {
    await API.clearHistory();
    this.refreshHistory(true);
  },

  renderTaskRow(task) {
    const status = task.status || "pending";
    const isDownloading = status === "downloading";
    const isPaused = status === "paused";
    const isCompleted = status === "completed";
    const isFailed = status === "failed";
    const progress = task.progress || {};
    const percent = Math.min(progress.percent || 0, 100);
    const speedLabel = progress.speed_str || "0 KB/s";
    const etaLabel = progress.eta_str || "--";
    const sizeLabel =
      progress.total_str && progress.downloaded_str
        ? `${progress.downloaded_str} / ${progress.total_str}`
        : "--";
    const completedSize = progress.total_str || progress.downloaded_str || "--";
    const completedTime = task.completed_at
      ? this.formatDateTime(task.completed_at)
      : "--";
    const platformLabel = this.getPlatformLabel(task.platform);
    const completedTemplate =
      STRINGS.ui?.dashboard?.completedMeta ||
      "Size {size} · Finished {time} · Source {source}";
    const completedMeta = this.formatString(completedTemplate, {
      size: completedSize,
      time: completedTime,
      source: platformLabel,
    });
    const statusBadge = this.getStatusBadge(status);
    const actionButtons = this.getTaskActions(task, status);
    const stageLabel = this.getStageLabel(task);

    return `
      <div class="task-row group relative bg-white dark:bg-[#25282c] p-4 rounded-xl border border-gray-100 dark:border-gray-700/50 shadow-sm hover:shadow-md transition-all" data-task-url="${this.escapeHtml(
        task.url
      )}">
        <div class="flex items-center gap-4">
          <div class="relative size-16 shrink-0 bg-gray-100 dark:bg-gray-800 rounded-lg overflow-hidden flex items-center justify-center">
            ${
              task.thumbnail
                ? `<div class="absolute inset-0 bg-cover bg-center opacity-60" style="background-image:url(${encodeURI(
                    task.thumbnail
                  )})"></div>`
                : ""
            }
            <span class="material-symbols-outlined text-primary text-3xl z-10">${
              isCompleted ? "check_circle" : isPaused ? "pause_circle" : "play_circle"
            }</span>
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between mb-1">
              <h3 class="text-sm font-bold truncate text-[#121617] dark:text-white pr-4">${this.escapeHtml(
                task.title || "Untitled"
              )}</h3>
              ${statusBadge}
            </div>
            ${
              isCompleted
                ? `<div class="flex items-center gap-4 mb-1">
                    <span class="text-[11px] text-[#658086]">${this.escapeHtml(
                      completedMeta
                    )}</span>
                    ${
                      task.output_path
                        ? `<button class="text-[11px] text-primary hover:underline flex items-center gap-1" data-task-action="open-folder" data-task-id="${task.task_id}">
                            Show in Folder <span class="material-symbols-outlined text-xs">open_in_new</span>
                          </button>`
                        : ""
                    }
                  </div>`
                : `<div class="flex items-center gap-4 mb-3">
                    <span class="text-[11px] text-[#658086] flex items-center gap-1"><span class="material-symbols-outlined text-[14px]">developer_board</span> ${stageLabel}</span>
                    <span class="text-[11px] text-[#658086] flex items-center gap-1"><span class="material-symbols-outlined text-[14px]">speed</span> ${speedLabel}</span>
                    ${
                      isDownloading
                        ? `<span class="text-[11px] text-[#658086] flex items-center gap-1"><span class="material-symbols-outlined text-[14px]">timer</span> ${etaLabel}</span>`
                        : ""
                    }
                    <span class="text-[11px] text-[#658086] flex items-center gap-1"><span class="material-symbols-outlined text-[14px]">data_usage</span> ${sizeLabel}</span>
                  </div>
                  <div class="w-full bg-gray-100 dark:bg-gray-800 h-1.5 rounded-full overflow-hidden">
                    <div class="bg-primary h-full" style="width: ${percent}%; transition: width 1s linear;"></div>
                  </div>`
            }
            ${
              isFailed && task.error_message
                ? `<p class="text-[11px] text-red-500 mt-2">${this.escapeHtml(
                    task.error_message
                  )}</p>`
                : ""
            }
          </div>
          <div class="hover-actions opacity-0 flex items-center gap-2 transition-opacity ml-4">
            ${actionButtons}
          </div>
        </div>
      </div>
    `;
  },

  getStatusBadge(status) {
    if (status === "downloading") {
      return `<span class="shrink-0 px-2 py-0.5 rounded bg-primary/10 text-primary text-[10px] font-bold uppercase tracking-tight">${this.escapeHtml(
        STRINGS.labels?.statusDownloading || "Downloading"
      )}</span>`;
    }
    if (status === "paused") {
      return `<span class="shrink-0 px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-500 text-[10px] font-bold uppercase tracking-tight">${this.escapeHtml(
        STRINGS.labels?.statusPaused || "Paused"
      )}</span>`;
    }
    if (status === "completed") {
      return `<span class="shrink-0 px-2 py-0.5 rounded bg-green-500/10 text-green-600 dark:text-green-400 text-[10px] font-bold uppercase tracking-tight">${this.escapeHtml(
        STRINGS.labels?.statusCompleted || "Completed"
      )}</span>`;
    }
    if (status === "failed") {
      return `<span class="shrink-0 px-2 py-0.5 rounded bg-red-500/10 text-red-600 text-[10px] font-bold uppercase tracking-tight">${this.escapeHtml(
        STRINGS.labels?.statusFailed || "Failed"
      )}</span>`;
    }
    if (status === "cancelled") {
      return `<span class="shrink-0 px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-500 text-[10px] font-bold uppercase tracking-tight">${this.escapeHtml(
        STRINGS.labels?.statusCancelled || "Cancelled"
      )}</span>`;
    }
    return `<span class="shrink-0 px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-500 text-[10px] font-bold uppercase tracking-tight">${this.escapeHtml(
      STRINGS.labels?.statusPending || "Pending"
    )}</span>`;
  },

  getStageLabel(task) {
    const stage = task.stage || task.status || "pending";
    const labels = STRINGS.labels || {};
    const stageMap = {
      downloading_video: labels.stageDownloadingVideo || "Downloading video",
      downloading_audio: labels.stageDownloadingAudio || "Downloading audio",
      downloading: labels.stageDownloading || "Downloading",
      merging: labels.stageMerging || "Assembling",
      extracting_audio: labels.stageExtractingAudio || "Extracting audio",
      processing: labels.stageProcessing || "Processing",
      paused: labels.stagePaused || "Paused",
      completed: labels.stageCompleted || "Completed",
      failed: labels.stageFailed || "Failed",
      cancelled: labels.stageCancelled || "Cancelled",
      pending: labels.stagePending || "Pending",
    };
    return stageMap[stage] || stageMap.downloading;
  },

  getPlatformLabel(platform) {
    const value = String(platform || "").toLowerCase();
    if (value.includes("youtube")) return "YouTube";
    if (["x", "x.com", "twitter"].includes(value)) return "X.com";
    if (value.includes("bilibili") || value === "bili" || value === "b") {
      return "Bilibili";
    }
    return platform || "--";
  },

  getTaskActions(task, status) {
    if (status === "downloading") {
      return `
        <button class="size-9 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 flex items-center justify-center hover:bg-gray-200 transition-colors" data-task-action="pause" data-task-id="${task.task_id}">
          <span class="material-symbols-outlined text-xl">pause</span>
        </button>
        <button class="size-9 rounded-full bg-gray-100 dark:bg-gray-700 text-red-500 flex items-center justify-center hover:bg-red-50 transition-colors" data-task-action="cancel" data-task-id="${task.task_id}">
          <span class="material-symbols-outlined text-xl">close</span>
        </button>
      `;
    }
    if (status === "paused") {
      return `
        <button class="size-9 rounded-full bg-primary text-white flex items-center justify-center hover:bg-primary/90 transition-colors shadow-lg shadow-primary/30" data-task-action="resume" data-task-id="${task.task_id}">
          <span class="material-symbols-outlined text-xl">play_arrow</span>
        </button>
        <button class="size-9 rounded-full bg-gray-100 dark:bg-gray-700 text-red-500 flex items-center justify-center hover:bg-red-50 transition-colors" data-task-action="cancel" data-task-id="${task.task_id}">
          <span class="material-symbols-outlined text-xl">close</span>
        </button>
      `;
    }
    if (status === "completed") {
      return `
        <button class="size-9 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 flex items-center justify-center hover:bg-gray-200 transition-colors" data-task-action="open-folder" data-task-id="${task.task_id}">
          <span class="material-symbols-outlined text-xl">folder_open</span>
        </button>
        <button class="size-9 rounded-full bg-gray-100 dark:bg-gray-700 text-red-500 flex items-center justify-center hover:bg-red-50 transition-colors" data-task-action="remove" data-task-id="${task.task_id}">
          <span class="material-symbols-outlined text-xl">delete</span>
        </button>
      `;
    }
    if (status === "failed" || status === "cancelled") {
      return `
        <button class="size-9 rounded-full bg-gray-100 dark:bg-gray-700 text-red-500 flex items-center justify-center hover:bg-red-50 transition-colors" data-task-action="remove" data-task-id="${task.task_id}">
          <span class="material-symbols-outlined text-xl">delete</span>
        </button>
      `;
    }
    return "";
  },

  updateStats(filteredTasks) {
    const allTasks = Array.from(this.state.tasks.values());
    const activeCount = allTasks.filter((task) =>
      ["downloading", "pending"].includes(task.status)
    ).length;
    const pausedCount = allTasks.filter(
      (task) => task.status === "paused"
    ).length;
    const strings = STRINGS.ui?.dashboard || {};
    const activeText = (strings.activeCount || "{count} Active").replace(
      "{count}",
      activeCount
    );
    const pausedText = (strings.pausedCount || "{count} Pause").replace(
      "{count}",
      pausedCount
    );
    this.elements.statActive.textContent = activeText;
    if (this.elements.statPaused) {
      this.elements.statPaused.textContent = pausedText;
    }

    const totalSpeed = allTasks.reduce(
      (sum, task) => sum + (task.progress?.speed || 0),
      0
    );
    this.elements.totalSpeed.textContent = this.formatBytes(totalSpeed) + "/s";
    if (this.elements.speedBar) {
      const speedRatio = Math.min(totalSpeed / (10 * 1024 * 1024), 1);
      this.elements.speedBar.style.width = `${Math.max(speedRatio * 100, 10)}%`;
    }
  },

  async handleTaskAction(taskId, action) {
    if (!taskId) return;
    if (action === "pause") {
      await API.pauseDownload(taskId);
    } else if (action === "resume") {
      await API.resumeDownload(taskId);
    } else if (action === "cancel") {
      await API.cancelDownload(taskId);
    } else if (action === "remove") {
      await API.removeTask(taskId);
    } else if (action === "open-folder") {
      const task = this.state.tasks.get(taskId);
      if (task?.output_path) {
        const result = await API.openFileLocation(task.output_path);
        if (result?.warning) {
          this.showToast(
            STRINGS.info?.openedFolderTitle || "Opened folder",
            result.warning
          );
        } else if (result?.success === false) {
          this.showToast(
            STRINGS.errors?.openFailed || "Open failed",
            result.error ||
              STRINGS.errors?.openFailedGeneric ||
              "Unable to open",
            true
          );
        }
      } else {
        this.showToast(
          STRINGS.errors?.openFailed || "Open failed",
          STRINGS.errors?.openFailedMissingPath || "File path missing",
          true
        );
      }
    }
    await this.loadTasks();
    this.renderTasks();
    this.syncDownloadCount();
  },

  async pauseAll() {
    const tasks = Array.from(this.state.tasks.values());
    for (const task of tasks) {
      if (task.status === "downloading") {
        await API.pauseDownload(task.task_id);
      }
    }
    await this.loadTasks();
    this.renderTasks();
  },

  async clearFinished() {
    await API.clearCompleted();
    await this.loadTasks();
    this.renderTasks();
    this.syncDownloadCount();
  },

  showHomeError(message) {
    if (!message) {
      this.elements.homeError.classList.add("hidden");
      this.elements.homeError.textContent = "";
      return;
    }
    this.elements.homeError.textContent = message;
    this.elements.homeError.classList.remove("hidden");
  },

  showToast(title, message, isError = false) {
    const toast = document.createElement("div");
    toast.className =
      "bg-white dark:bg-[#25282c] border border-gray-100 dark:border-gray-800 rounded-xl mac-shadow p-4 flex items-start gap-4";
    toast.innerHTML = `
      <div class="size-10 ${
        isError ? "bg-red-100 text-red-600" : "bg-green-100 text-green-600"
      } rounded-full flex items-center justify-center">
        <span class="material-symbols-outlined">${
          isError ? "error" : "check_circle"
        }</span>
      </div>
      <div class="flex flex-col pr-4">
        <p class="text-xs font-bold text-[#121617] dark:text-white">${this.escapeHtml(
          title
        )}</p>
        <p class="text-[10px] text-[#658086]">${this.escapeHtml(
          message || ""
        )}</p>
      </div>
      <button class="text-gray-400 hover:text-gray-600">
        <span class="material-symbols-outlined text-sm">close</span>
      </button>
    `;
    const closeBtn = toast.querySelector("button");
    closeBtn.addEventListener("click", () => toast.remove());
    this.elements.toastContainer.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
  },

  updateToggleGroup(container, activeButton) {
    if (!container || !activeButton) return;
    container.querySelectorAll("button").forEach((button) => {
      button.classList.remove(
        "bg-white",
        "dark:bg-gray-700",
        "shadow-sm",
        "text-gray-900",
        "dark:text-white"
      );
      button.classList.add("text-gray-500", "dark:text-gray-400");
    });
    activeButton.classList.add(
      "bg-white",
      "dark:bg-gray-700",
      "shadow-sm",
      "text-gray-900",
      "dark:text-white"
    );
    activeButton.classList.remove("text-gray-500", "dark:text-gray-400");
  },

  extractHeight(label) {
    const match = String(label || "").match(/(\d+)/);
    return match ? parseInt(match[1], 10) : 0;
  },

  formatBytes(bytes) {
    if (!bytes || bytes <= 0) return "0 B";
    const units = ["B", "KB", "MB", "GB", "TB"];
    let size = bytes;
    let unitIndex = 0;
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex += 1;
    }
    return `${size.toFixed(size >= 100 ? 0 : 1)} ${units[unitIndex]}`;
  },

  formatNumber(value) {
    return new Intl.NumberFormat().format(value);
  },

  formatDateTime(timestamp) {
    const date = new Date(timestamp * 1000);
    return new Intl.DateTimeFormat(undefined, {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    }).format(date);
  },

  escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  },
};

document.addEventListener("DOMContentLoaded", () => App.init());
