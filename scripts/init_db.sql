-- Initial DB setup (runs once on first container start)
-- Alembic migrations handle the schema; this just ensures extensions are enabled.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
