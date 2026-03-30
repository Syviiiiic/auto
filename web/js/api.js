const API_BASE = '/api';

function authHeadersJson() {
    const h = { 'Content-Type': 'application/json' };
    const t = Auth.getToken();
    if (t) {
        h['Authorization'] = `Bearer ${t}`;
    }
    return h;
}

function authHeadersOnly() {
    const h = {};
    const t = Auth.getToken();
    if (t) {
        h['Authorization'] = `Bearer ${t}`;
    }
    return h;
}

function detailMessage(data) {
    if (typeof data.detail === 'string') {
        return data.detail;
    }
    if (Array.isArray(data.detail)) {
        return data.detail.map((d) => d.msg || JSON.stringify(d)).join('; ');
    }
    return 'Ошибка запроса';
}

const api = {
    auth: {
        async register(email, password, first_name, last_name) {
            const response = await fetch(`${API_BASE}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email,
                    password,
                    first_name: first_name || null,
                    last_name: last_name || null,
                }),
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok) {
                throw new Error(detailMessage(data));
            }
            if (data.access_token) {
                Auth.setToken(data.access_token);
            }
            return data;
        },

        async login(email, password) {
            const response = await fetch(`${API_BASE}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password }),
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok) {
                throw new Error(typeof data.detail === 'string' ? data.detail : 'Неверный email или пароль');
            }
            if (data.access_token) {
                Auth.setToken(data.access_token);
            }
            return data;
        },

        async me() {
            const response = await fetch(`${API_BASE}/auth/me`, {
                headers: authHeadersJson(),
            });
            if (response.status === 401) {
                return null;
            }
            const data = await response.json().catch(() => null);
            if (!response.ok) {
                return null;
            }
            return data;
        },

        logout() {
            Auth.clearToken();
        },
    },

    uploads: {
        async uploadImage(file) {
            const fd = new FormData();
            fd.append('file', file);
            const response = await fetch(`${API_BASE}/uploads/image`, {
                method: 'POST',
                headers: authHeadersOnly(),
                body: fd,
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok) {
                throw new Error(typeof data.detail === 'string' ? data.detail : 'Не удалось загрузить файл');
            }
            return data.url;
        },
    },

    ads: {
        async getAll(params = {}) {
            const query = new URLSearchParams(params).toString();
            const response = await fetch(`${API_BASE}/ads?${query}`);
            return response.json();
        },

        async getById(id) {
            const response = await fetch(`${API_BASE}/ads/${id}`);
            return response.json();
        },

        async getMy() {
            const response = await fetch(`${API_BASE}/ads/me`, {
                headers: authHeadersJson(),
            });
            if (response.status === 401) {
                throw new Error('UNAUTHORIZED');
            }
            return response.json();
        },

        async create(adData) {
            const response = await fetch(`${API_BASE}/ads`, {
                method: 'POST',
                headers: authHeadersJson(),
                body: JSON.stringify(adData),
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok) {
                throw new Error(typeof data.detail === 'string' ? data.detail : 'Не удалось создать объявление');
            }
            return data;
        },

        async update(id, adData) {
            const response = await fetch(`${API_BASE}/ads/${id}`, {
                method: 'PUT',
                headers: authHeadersJson(),
                body: JSON.stringify(adData),
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok) {
                throw new Error(typeof data.detail === 'string' ? data.detail : 'Ошибка обновления');
            }
            return data;
        },

        async delete(id) {
            const response = await fetch(`${API_BASE}/ads/${id}`, {
                method: 'DELETE',
                headers: authHeadersJson(),
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok) {
                throw new Error(typeof data.detail === 'string' ? data.detail : 'Ошибка удаления');
            }
            return data;
        },
    },

    favorites: {
        async getAll() {
            const response = await fetch(`${API_BASE}/favorites`, {
                headers: authHeadersJson(),
            });
            if (response.status === 401) {
                throw new Error('UNAUTHORIZED');
            }
            return response.json();
        },

        async add(adId) {
            const response = await fetch(`${API_BASE}/favorites`, {
                method: 'POST',
                headers: authHeadersJson(),
                body: JSON.stringify({ ad_id: adId }),
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok) {
                throw new Error(typeof data.detail === 'string' ? data.detail : 'Ошибка');
            }
            return data;
        },

        async remove(adId) {
            const response = await fetch(`${API_BASE}/favorites/${adId}`, {
                method: 'DELETE',
                headers: authHeadersJson(),
            });
            if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                throw new Error(typeof data.detail === 'string' ? data.detail : 'Ошибка');
            }
            return response.json();
        },
    },

    search: {
        async suggestions(query) {
            const response = await fetch(`${API_BASE}/search/suggestions?query=${encodeURIComponent(query)}`);
            return response.json();
        },

        async getFilters() {
            const response = await fetch(`${API_BASE}/search/filters`);
            return response.json();
        },
    },

    user: {
        async update(payload) {
            const response = await fetch(`${API_BASE}/user`, {
                method: 'PUT',
                headers: authHeadersJson(),
                body: JSON.stringify(payload),
            });
            const resData = await response.json().catch(() => ({}));
            if (!response.ok) {
                throw new Error(detailMessage(resData));
            }
            return resData;
        },

        async getStats() {
            const response = await fetch(`${API_BASE}/user/stats`, {
                headers: authHeadersJson(),
            });
            if (response.status === 401) {
                throw new Error('UNAUTHORIZED');
            }
            return response.json();
        },
    },
};

function formatPrice(price) {
    return new Intl.NumberFormat('ru-RU').format(price) + ' ₽';
}

function formatMileage(mileage) {
    return new Intl.NumberFormat('ru-RU').format(mileage) + ' км';
}

function formatDate(date) {
    return new Date(date).toLocaleDateString('ru-RU');
}
