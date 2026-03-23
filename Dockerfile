FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем bot/ в /app
COPY bot/ .

# Копируем database/ в /app/database/
COPY database/ ./database/

# Копируем api/ в /app/api/ (там вероятно services/)
COPY api/ ./api/

# Создаем __init__.py во всех папках
RUN touch __init__.py 2>/dev/null || true
RUN touch database/__init__.py api/__init__.py 2>/dev/null || true
RUN find api -type d -exec touch {}/__init__.py \; 2>/dev/null || true

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

CMD ["python", "main.py"]
