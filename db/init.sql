-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Roles for RLS
DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'epi_app') THEN
    CREATE ROLE epi_app LOGIN PASSWORD 'epi_app_password';
  END IF;
END $$;

GRANT CONNECT ON DATABASE epi TO epi_app;

-- RLS helper: set current agency_id via session variable
-- Usage: SET LOCAL app.current_agency_id = 'uuid-here';
CREATE OR REPLACE FUNCTION current_agency_id() RETURNS UUID AS $$
  SELECT COALESCE(
    NULLIF(current_setting('app.current_agency_id', TRUE), '')::UUID,
    '00000000-0000-0000-0000-000000000000'::UUID
  );
$$ LANGUAGE SQL STABLE;
