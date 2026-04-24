-- ─────────────────────────────────────────────────────────────────────────────
--  AIU — PostgreSQL Initialization
--  Runs once on first container start.
-- ─────────────────────────────────────────────────────────────────────────────

-- Enable pgvector extension (required for memory embeddings)
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable pg_trgm for full-text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Enable uuid-ossp for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create read-only user for analytics/reporting (least privilege)
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'aiu_readonly') THEN
    CREATE ROLE aiu_readonly LOGIN PASSWORD 'readonly_password';
    GRANT CONNECT ON DATABASE aiu_db TO aiu_readonly;
    GRANT USAGE ON SCHEMA public TO aiu_readonly;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO aiu_readonly;
  END IF;
END
$$;
