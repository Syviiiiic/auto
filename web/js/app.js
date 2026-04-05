// Render car card with new design
function renderCarCard(ad) {
    const photos = ad.photos && ad.photos.length > 0 ? ad.photos : ['assets/no-image.jpg'];
    const firstPhoto = photos[0];
    
    return `
        <article class="car-card" onclick="window.location.href='/ad.html?id=${ad.id}'">
            <div style="position: relative;">
                <img src="${firstPhoto}" alt="${ad.brand} ${ad.model}" class="car-image">
                <span class="car-badge">2024</span>
                <button class="car-favorite" onclick="event.stopPropagation(); toggleFavorite(${ad.id})">
                    ♡
                </button>
            </div>
            <div class="car-info">
                <h3 class="car-title">${ad.brand} ${ad.model}</h3>
                <div class="car-price">${ad.price.toLocaleString('ru-RU')} ₽</div>
                <div class="car-details">
                    <span class="car-detail">📅 ${ad.year}</span>
                    <span class="car-detail">⛽ ${ad.engine_type}</span>
                    <span class="car-detail">⚙️ ${ad.transmission}</span>
                    <span class="car-detail">🚗 ${ad.mileage.toLocaleString('ru-RU')} км</span>
                </div>
                <div class="car-footer">
                    <span class="car-date">Сегодня</span>
                    <span class="car-views">👁 ${ad.views_count || 0}</span>
                </div>
            </div>
        </article>
    `;
}

// Load ads with new rendering
async function loadAds() {
    const container = document.getElementById('ads-container');
    
    try {
        const ads = await api.get('/ads/');
        
        if (!ads.items || ads.items.length === 0) {
            container.innerHTML = `
                <div class="empty-state" style="grid-column: 1/-1;">
                    <div class="empty-state-icon">🚗</div>
                    <h3>Пока нет объявлений</h3>
                    <p>Будьте первым! <a href="/add-ad.html">Разместите объявление</a></p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = ads.items.map(renderCarCard).join('');
    } catch (error) {
        console.error('Error loading ads:', error);
        container.innerHTML = `
            <div class="empty-state" style="grid-column: 1/-1;">
                <div class="empty-state-icon">⚠️</div>
                <h3>Ошибка загрузки</h3>
                <p>Попробуйте обновить страницу</p>
            </div>
        `;
    }
}

// Search function
async function searchAds() {
    const brand = document.getElementById('search-brand').value;
    const model = document.getElementById('search-model').value;
    const priceMin = document.getElementById('price-min').value;
    const priceMax = document.getElementById('price-max').value;
    const yearMin = document.getElementById('year-min').value;
    const yearMax = document.getElementById('year-max').value;
    
    const params = new URLSearchParams();
    if (brand) params.append('brand', brand);
    if (model) params.append('model', model);
    if (priceMin) params.append('price_min', priceMin);
    if (priceMax) params.append('price_max', priceMax);
    if (yearMin) params.append('year_min', yearMin);
    if (yearMax) params.append('year_max', yearMax);
    
    const container = document.getElementById('ads-container');
    container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
    
    try {
        const ads = await api.get(`/ads/?${params.toString()}`);
        container.innerHTML = ads.items.map(renderCarCard).join('');
    } catch (error) {
        console.error('Search error:', error);
    }
}

// Toggle favorite
async function toggleFavorite(adId) {
    // Implementation here
    console.log('Toggle favorite:', adId);
}

// Load on page load
document.addEventListener('DOMContentLoaded', loadAds);
