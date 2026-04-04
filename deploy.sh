#!/bin/bash

set -e  # Остановить скрипт при любой ошибке

echo "=== Начинаем развертывание ==="

cd /opt/avtoads-service/auto

# Останавливаем и удаляем всё
echo "1. Очищаем старые контейнеры и тома..."
docker compose down -v 2>/dev/null || true

# Удаляем старые образы (опционально)
echo "2. Пересобираем образы..."
docker compose build --no-cache

# Запускаем контейнеры
echo "3. Запускаем контейнеры..."
docker compose up -d

# Ждём инициализации PostgreSQL
echo "4. Ждём инициализации базы данных (30 секунд)..."
sleep 30

# Проверяем, что пользователь и база создались
echo "5. Проверяем настройки базы данных..."
docker exec auto_ads_postgres psql -U postgres -c "\du" | grep auto || echo "Пользователь auto не найден, но init-скрипт должен был его создать"

# Проверяем логи
echo "6. Проверяем логи API..."
docker-compose logs api --tail 20

echo ""
echo "=== Развертывание завершено ==="
echo "Проверьте сайт: http://avtoads.duckdns.org"
echo "Для просмотра логов: docker-compose logs -f"
