-- PostgreSQL initialization script
-- This script is run when the PostgreSQL container starts for the first time

-- Create additional databases if needed
CREATE DATABASE fastapi_enterprise_test;

-- Create extensions that might be useful
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create a read-only user for reporting (optional)
CREATE USER fastapi_readonly WITH PASSWORD 'readonly_password';
GRANT CONNECT ON DATABASE fastapi_enterprise TO fastapi_readonly;
GRANT USAGE ON SCHEMA public TO fastapi_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO fastapi_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO fastapi_readonly;

-- Set up logging (optional)
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 1000; -- Log queries taking more than 1 second

-- Create indexes for common queries (these would typically be in migrations)
-- Example indexes - these should actually be created via Alembic migrations
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users(email);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_username ON users(username);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_created_at ON users(created_at);

SELECT 'PostgreSQL initialization completed' as status;
