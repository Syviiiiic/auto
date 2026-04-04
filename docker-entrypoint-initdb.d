-- Создаём пользователя auto (если не существует)
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'auto') THEN
      CREATE USER auto WITH PASSWORD '14811481a';
   END IF;
END
$$;

-- Создаём базу данных avto (если не существует)
SELECT 'CREATE DATABASE avto'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'avto')\gexec

-- Подключаемся к базе avto
\c avto

-- Даём права пользователю auto
GRANT ALL PRIVILEGES ON DATABASE avto TO auto;
GRANT ALL ON SCHEMA public TO auto;
ALTER SCHEMA public OWNER TO auto;

-- Создаём необходимые расширения (если нужны)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
