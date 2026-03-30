# 🚗 Auto Ads

Веб-площадка для размещения и поиска объявлений о продаже автомобилей (FastAPI + PostgreSQL + статический фронт в `web/`).

## Возможности

- Каталог с фильтрами и поиском
- Регистрация и вход (JWT)
- До 10 фото на объявление
- Избранное и статистика по объявлениям

## Технологии

- Python 3.11, FastAPI
- PostgreSQL 15, Redis
- Docker / Docker Compose
- Nginx раздаёт `web/`, API и `/media/` проксируются

## Быстрый старт

Требования: Docker и Docker Compose, от ~2 GB RAM.

1. Скопируйте `.env.example` в `.env`, задайте `JWT_SECRET` и пароли БД.
2. Примените миграции Alembic (при необходимости внутри контейнера API).
3. Запуск: `docker compose up --build -d` или `./scripts/start.sh`.

Сервисы: `api`, `web` (nginx + статика из `./web`), `postgres`, `redis`.
