/**
 * router.js - 前端路由
 * 简单的单页应用路由实现
 */

const Router = {
    // 当前路由
    currentRoute: 'home',

    // 路由历史
    history: [],

    // 路由配置
    routes: {
        'home': {
            title: 'Home',
            view: 'view-home'
        },
        'video-details': {
            title: 'Video Details',
            view: 'view-video-details'
        },
        'downloads': {
            title: 'Downloads',
            view: 'view-downloads'
        },
        'settings': {
            title: 'Settings',
            view: 'view-settings'
        }
    },

    // 路由变化回调
    _onRouteChange: null,

    // 初始化路由
    init(onRouteChange) {
        this._onRouteChange = onRouteChange;

        // 初始显示首页
        this.navigate('home');
    },

    // 导航到指定路由
    navigate(route, params = {}) {
        if (!this.routes[route]) {
            console.error(`Route not found: ${route}`);
            return;
        }

        // 保存历史
        if (this.currentRoute !== route) {
            this.history.push(this.currentRoute);
        }

        this.currentRoute = route;

        // 隐藏所有视图
        document.querySelectorAll('[data-view]').forEach(view => {
            view.classList.add('hidden');
        });

        // 显示目标视图
        const viewElement = document.querySelector(`[data-view="${this.routes[route].view}"]`);
        if (viewElement) {
            viewElement.classList.remove('hidden');
        }

        // 更新导航高亮
        this._updateNavHighlight(route);

        // 触发回调
        if (this._onRouteChange) {
            this._onRouteChange(route, params);
        }
    },

    // 返回上一页
    back() {
        if (this.history.length > 0) {
            const previousRoute = this.history.pop();
            this.navigate(previousRoute);
        }
    },

    // 更新导航高亮
    _updateNavHighlight(route) {
        // 移除所有高亮
        document.querySelectorAll('[data-nav]').forEach(nav => {
            nav.classList.remove('bg-primary/10', 'text-primary');
            nav.classList.add('text-gray-600', 'hover:bg-gray-100', 'dark:text-gray-400', 'dark:hover:bg-gray-800');

            // 移除图标填充
            const icon = nav.querySelector('.material-symbols-outlined');
            if (icon) {
                icon.style.fontVariationSettings = "'FILL' 0";
            }
        });

        // 添加当前路由高亮
        const currentNav = document.querySelector(`[data-nav="${route}"]`);
        if (currentNav) {
            currentNav.classList.remove('text-gray-600', 'hover:bg-gray-100', 'dark:text-gray-400', 'dark:hover:bg-gray-800');
            currentNav.classList.add('bg-primary/10', 'text-primary');

            // 添加图标填充
            const icon = currentNav.querySelector('.material-symbols-outlined');
            if (icon) {
                icon.style.fontVariationSettings = "'FILL' 1";
            }
        }
    },

    // 获取当前路由
    getCurrentRoute() {
        return this.currentRoute;
    }
};

// 导出 Router
window.Router = Router;
