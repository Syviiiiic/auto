let photos = [];
let user = null;

function showMsg(title, text) {
    window.alert(title ? `${title}\n\n${text}` : text);
}

document.addEventListener('DOMContentLoaded', async () => {
    if (!Auth.isLoggedIn()) {
        window.location.replace('auth.html?next=' + encodeURIComponent('add-ad.html'));
        return;
    }
    await initUser();
    setupPhotoUpload();
    setupFormSubmit();
});

async function initUser() {
    try {
        user = await api.auth.me();
        if (!user) {
            window.location.replace('auth.html?next=' + encodeURIComponent('add-ad.html'));
        }
    } catch (error) {
        console.error('Auth error:', error);
        window.location.replace('auth.html?next=' + encodeURIComponent('add-ad.html'));
    }
}

function setupPhotoUpload() {
    const uploadDiv = document.getElementById('photoUpload');
    const photoInput = document.getElementById('photoInput');

    uploadDiv.addEventListener('click', () => {
        photoInput.click();
    });

    photoInput.addEventListener('change', async (e) => {
        const files = Array.from(e.target.files);

        for (const file of files) {
            if (photos.length >= 10) {
                showMsg('Лимит фото', 'Максимум 10 фотографий');
                break;
            }

            if (file.size > 10 * 1024 * 1024) {
                showMsg('Ошибка', 'Файл слишком большой (макс. 10 МБ)');
                continue;
            }

            const reader = new FileReader();
            reader.onload = (event) => {
                photos.push({
                    file: file,
                    preview: event.target.result,
                });
                renderPhotoPreview();
            };
            reader.readAsDataURL(file);
        }

        photoInput.value = '';
    });
}

function renderPhotoPreview() {
    const photoPreview = document.getElementById('photoPreview');

    if (photos.length === 0) {
        photoPreview.innerHTML = '';
        return;
    }

    let html = '';
    photos.forEach((photo, index) => {
        html += `
            <div style="position: relative; display: inline-block;">
                <img src="${photo.preview}" alt="Фото ${index + 1}">
                <div class="remove-photo" onclick="removePhoto(${index})">×</div>
            </div>
        `;
    });

    photoPreview.innerHTML = html;
}

function removePhoto(index) {
    photos.splice(index, 1);
    renderPhotoPreview();
}

async function uploadPhotoToServer(file) {
    return api.uploads.uploadImage(file);
}

async function setupFormSubmit() {
    const form = document.getElementById('adForm');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (!user) {
            showMsg('Ошибка', 'Войдите в аккаунт');
            return;
        }

        if (photos.length === 0) {
            showMsg('Ошибка', 'Добавьте хотя бы одну фотографию');
            return;
        }

        const formData = {
            brand: document.getElementById('brand').value.trim(),
            model: document.getElementById('model').value.trim(),
            year: parseInt(document.getElementById('year').value, 10),
            price: parseInt(document.getElementById('price').value, 10),
            mileage: parseInt(document.getElementById('mileage').value, 10) || 0,
            engine_type: document.getElementById('engineType').value,
            engine_capacity: parseFloat(document.getElementById('engineCapacity').value) || 0,
            transmission: document.getElementById('transmission').value,
            drive: document.getElementById('drive').value,
            color: document.getElementById('color').value.trim(),
            description: document.getElementById('description').value.trim(),
            photos: [],
        };

        if (!formData.brand || !formData.model || !formData.year || !formData.price) {
            showMsg('Ошибка', 'Заполните все обязательные поля');
            return;
        }

        if (formData.year < 1900 || formData.year > 2030) {
            showMsg('Ошибка', 'Введите корректный год');
            return;
        }

        if (formData.price < 1000) {
            showMsg('Ошибка', 'Минимальная цена — 1000 ₽');
            return;
        }

        try {
            for (const photo of photos) {
                const photoUrl = await uploadPhotoToServer(photo.file);
                formData.photos.push(photoUrl);
            }

            const result = await api.ads.create(formData);

            if (result.id) {
                if (window.confirm('Объявление опубликовано. Открыть карточку?')) {
                    window.location.href = `ad.html?id=${result.id}`;
                } else {
                    window.location.href = 'index.html';
                }
            } else {
                throw new Error('Failed to create ad');
            }
        } catch (error) {
            console.error('Error creating ad:', error);
            showMsg('Ошибка', error.message || 'Не удалось опубликовать объявление.');
        }
    });
}

window.removePhoto = removePhoto;
