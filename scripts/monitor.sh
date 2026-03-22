#!/bin/bash

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Мониторинг ресурсов${NC}"
echo -e "${BLUE}========================================${NC}"

# Общая статистика Docker
echo -e "\n${GREEN}📊 Docker контейнеры:${NC}"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

# PostgreSQL статистика
echo -e "\n${GREEN}🐘 PostgreSQL:${NC}"
docker exec auto_ads_postgres psql -U autobot -d auto_ads -c "
SELECT 
    datname,
    numbackends,
    xact_commit,
    xact_rollback,
    blks_read,
    blks_hit,
    temp_files,
    temp_bytes
FROM pg_stat_database WHERE datname = 'auto_ads';
"

# Размер базы данных
echo -e "\n${GREEN}💾 Размер БД:${NC}"
docker exec auto_ads_postgres psql -U autobot -d auto_ads -c "
SELECT 
    pg_database_size('auto_ads')/1024/1024 AS size_mb,
    pg_total_relation_size('ads')/1024/1024 AS ads_table_mb,
    pg_indexes_size('ads')/1024/1024 AS ads_indexes_mb;
"

# Количество объявлений
echo -e "\n${GREEN}📋 Статистика объявлений:${NC}"
docker exec auto_ads_postgres psql -U autobot -d auto_ads -c "
SELECT 
    COUNT(*) as total_ads,
    COUNT(*) FILTER (WHERE is_active = true) as active_ads,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as ads_today,
    SUM(views_count) as total_views
FROM ads;
"

# Дисковое пространство
echo -e "\n${GREEN}💿 Дисковое пространство:${NC}"
df -h / | awk 'NR==1 || NR==2'

# Логи ошибок за последний час
echo -e "\n${GREEN}⚠️  Ошибки за последний час:${NC}"
docker logs auto_ads_bot --since 1h 2>&1 | grep -i error | wc -l
docker logs auto_ads_api --since 1h 2>&1 | grep -i error | wc -l
