let user = null;
let stats = null;

document.addEventListener('DOMContentLoaded', async () => {
    if (!Auth.isLoggedIn()) {
        window.location.replace('auth.html?next=' + encodeURIComponent('profile.html'));
        return;
    }
    await initUser();
    await loadStats();
    renderProfile();
    setupEventListeners();
});

async function initUser() {
    try {
        user = await api.auth.me();
        if (!user) {
            window.location.replace('auth.html?next=' + encodeURIComponent('profile.html'));
        }
    } catch (error) {
        console.error('Auth error:', error);
        window.location.replace('auth.html?next=' + encodeURIComponent('profile.html'));
    }
}

async function loadStats() {
    try {
        stats = await api.user.getStats();
    } catch (error) {
        console.error('Error loading stats:', error);
        stats = { total_ads: 0, active_ads: 0, total_views: 0 };
    }
}

function renderProfile() {
    const container = document.getElementById('profileContainer');

    if (!user) {
        container.innerHTML = '<div class="error">Ошибка загрузки профиля</div>';
        return;
    }

    const initials = user.first_name ? user.first_name.charAt(0).toUpperCase() : (user.email ? user.email.charAt(0).toUpperCase() : 'U');
    const displayName =
        [user.first_name, user.last_name].filter(Boolean).join(' ').trim() || user.email || 'Пользователь';

    const html = `
        <div class="profile-header">
            <div class="profile-avatar">${initials}</div>
            <div class="profile-name">${escapeHtml(displayName)}</div>
            <div class="profile-username">${escapeHtml(user.email || '')}</div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">${stats.total_ads || 0}</div>
                <div class="stat-label">Объявлений</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${stats.active_ads || 0}</div>
                <div class="stat-label">Активных</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${stats.total_views || 0}</div>
                <div class="stat-label">Просмотров</div>
            </div>
        </div>
        
        <div class="profile-menu">
            <div class="menu-item" data-action="my_ads">
                <span>📋 Мои объявления</span>
                <span>→</span>
            </div>
            <div class="menu-item" data-action="favorites">
                <span>❤️ Избранное</span>
                <span>→</span>
            </div>
            <div class="menu-item" data-action="help">
                <span>❓ Помощь</span>
                <span>→</span>
            </div>
            <div class="menu-item" data-action="logout">
                <span>🚪 Выйти</span>
                <span>→</span>
            </div>
        </div>
    `;

    container.innerHTML = html;
}

function setupEventListeners() {
    const settingsBtn = document.getElementById('settingsBtn');
    if (settingsBtn) {
        settingsBtn.addEventListener('click', () => {
            window.alert('Раздел настроек будет добавлен позже.');
        });
    }

    document.querySelectorAll('.menu-item').forEach((item) => {
        item.addEventListener('click', () => {
            const action = item.dataset.action;
            handleAction(action);
        });
    });

    document.querySelectorAll('.nav-btn').forEach((btn) => {
        btn.addEventListener('click', () => {
            const pages = {
                catalog: 'index.html',
                add: 'add-ad.html',
                favorites: 'favorites.html',
                profile: 'profile.html',
            };
            const pageUrl = pages[btn.dataset.page];
            if (pageUrl) {
                if (btn.dataset.page === 'add' && !Auth.isLoggedIn()) {
                    window.location.href = 'auth.html?next=' + encodeURIComponent('add-ad.html');
                    return;
                }
                window.location.href = pageUrl;
            }
        });
    });
}

function handleAction(action) {
    switch (action) {
        case 'my_ads':
            window.location.href = 'my-ads.html';
            break;
        case 'favorites':
            window.location.href = 'favorites.html';
            break;
        case 'help':
            window.location.href = 'help.html';
            break;
        case 'logout':
            api.auth.logout();
            window.location.href = 'index.html';
            break;
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
