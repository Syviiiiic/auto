let user = null;
let myAds = [];

document.addEventListener('DOMContentLoaded', async () => {
    if (!Auth.isLoggedIn()) {
        window.location.replace('auth.html?next=' + encodeURIComponent('my-ads.html'));
        return;
    }
    await initUser();
    await loadMyAds();
    setupEventListeners();
});

async function initUser() {
    try {
        user = await api.auth.me();
        if (!user) {
            window.location.replace('auth.html?next=' + encodeURIComponent('my-ads.html'));
        }
    } catch (error) {
        console.error('Auth error:', error);
        window.location.replace('auth.html?next=' + encodeURIComponent('my-ads.html'));
    }
}

async function loadMyAds() {
    const listContainer = document.getElementById('myAdsList');
    listContainer.innerHTML = '<div class="loading">Загрузка...</div>';

    try {
        myAds = await api.ads.getMy();
        renderMyAds();
    } catch (error) {
        console.error('Error loading ads:', error);
        listContainer.innerHTML = '<div class="error">❌ Ошибка загрузки</div>';
    }
}

function renderMyAds() {
    const listContainer = document.getElementById('myAdsList');

    if (!myAds || myAds.length === 0) {
        listContainer.innerHTML = `
            <div class="no-ads">
                😕 У вас нет объявлений<br>
                <button class="create-btn" onclick="location.href='add-ad.html'">
                    ➕ Создать объявление
                </button>
            </div>
        `;
        return;
    }

    let html = '';
    myAds.forEach((ad) => {
        const price = formatPrice(ad.price);
        const statusClass = ad.is_active ? 'status-active' : 'status-inactive';
        const statusText = ad.is_active ? 'Активно' : 'Скрыто';
        const photo = ad.photos && ad.photos.length > 0 ? ad.photos[0] : 'assets/no-image.jpg';

        html += `
            <div class="my-ad-card" data-id="${ad.id}">
                <div class="my-ad-content">
                    <img src="${photo}" class="my-ad-image" alt="${ad.brand} ${ad.model}">
                    <div class="my-ad-info">
                        <div class="my-ad-title">${escapeHtml(ad.brand)} ${escapeHtml(ad.model)}</div>
                        <div class="my-ad-price">${price}</div>
                        <div class="my-ad-year">${ad.year} · ${formatMileage(ad.mileage)}</div>
                        <div class="my-ad-status ${statusClass}">${statusText}</div>
                    </div>
                </div>
                <div class="my-ad-actions">
                    <button class="edit-btn" data-id="${ad.id}">✏️ Редактировать</button>
                    <button class="delete-btn" data-id="${ad.id}">🗑 Удалить</button>
                </div>
            </div>
        `;
    });

    listContainer.innerHTML = html;

    document.querySelectorAll('.edit-btn').forEach((btn) => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            window.alert('Редактирование в следующей версии. Пока удалите и создайте заново.');
        });
    });

    document.querySelectorAll('.delete-btn').forEach((btn) => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const adId = parseInt(btn.dataset.id, 10);
            if (!window.confirm('Удалить это объявление?')) {
                return;
            }
            await deleteAd(adId);
        });
    });
}

async function deleteAd(adId) {
    try {
        await api.ads.delete(adId);
        window.alert('Объявление удалено');
        await loadMyAds();
    } catch (error) {
        console.error('Error deleting ad:', error);
        window.alert(error.message || 'Не удалось удалить объявление');
    }
}

function setupEventListeners() {
    document.getElementById('addBtn').addEventListener('click', () => {
        window.location.href = 'add-ad.html';
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

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
