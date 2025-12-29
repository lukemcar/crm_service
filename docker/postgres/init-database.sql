-- init-database.sql
-- Create the main database
CREATE DATABASE crm_service;

-- Connect to the new database
\c crm_service;

-- ==============================================
-- Create users
-- ==============================================

-- API user (FastAPI service)
CREATE USER crm_service_app WITH PASSWORD '2cHfTngNdjFIX78JUz2Z91iDpQKGJPWo';

-- Admin user (Liquibase + DB migrations)
CREATE USER crm_service_admin WITH PASSWORD '9F6c8LuEZThSa5mwjDiDWRf4KYlurOeN';

-- Worker user (Celery or async background jobs)
CREATE USER crm_service_worker WITH PASSWORD '1M5o4SwYViW0VgknMR43l0bcNEy2tNC8';

-- ==============================================
-- Create schema
-- ==============================================
-- Schema must exist BEFORE Liquibase runs
CREATE SCHEMA IF NOT EXISTS dyno_crm AUTHORIZATION crm_service_admin;

-- ==============================================
-- Privileges
-- ==============================================

-- Admin user gets full control over schema and migration tables
GRANT ALL PRIVILEGES ON DATABASE crm_service TO crm_service_admin;
GRANT ALL PRIVILEGES ON SCHEMA dyno_crm TO crm_service_admin;

-- API has full read/write privileges on application schema
GRANT USAGE, CREATE ON SCHEMA dyno_crm TO crm_service_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA dyno_crm
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO crm_service_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA dyno_crm
  GRANT USAGE ON SEQUENCES TO crm_service_app;

-- Worker has controlled access — read and write, but NOT create/drop
GRANT USAGE ON SCHEMA dyno_crm TO crm_service_worker;
ALTER DEFAULT PRIVILEGES IN SCHEMA dyno_crm
  GRANT SELECT, INSERT, UPDATE ON TABLES TO crm_service_worker;
ALTER DEFAULT PRIVILEGES IN SCHEMA dyno_crm
  GRANT USAGE ON SEQUENCES TO crm_service_worker;

-- =========
