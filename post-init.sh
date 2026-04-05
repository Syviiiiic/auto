#!/bin/bash
sleep 10
docker exec auto_ads_postgres psql -U postgres -c "CREATE USER IF NOT EXISTS auto WITH PASSWORD '14811481a';"
docker exec auto_ads_postgres psql -U postgres -c "CREATE DATABASE IF NOT EXISTS avto OWNER auto;"
docker exec auto_ads_postgres psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE avto TO auto;"
docker exec auto_ads_postgres psql -U auto -d avto -c "GRANT ALL ON SCHEMA public TO auto;"
