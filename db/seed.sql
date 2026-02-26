-- Seed data: 2 agencies, 3 sites, sample data
-- This is populated after Alembic migrations run

-- Agency 1: Acme Digital
INSERT INTO agencies (id, name, slug, created_at)
VALUES (
  'a1000000-0000-0000-0000-000000000001',
  'Acme Digital',
  'acme-digital',
  NOW()
) ON CONFLICT (id) DO NOTHING;

-- Agency 2: Beta Marketing
INSERT INTO agencies (id, name, slug, created_at)
VALUES (
  'a2000000-0000-0000-0000-000000000002',
  'Beta Marketing',
  'beta-marketing',
  NOW()
) ON CONFLICT (id) DO NOTHING;

-- Users
INSERT INTO users (id, agency_id, email, hashed_password, role, created_at)
VALUES (
  'u1000000-0000-0000-0000-000000000001',
  'a1000000-0000-0000-0000-000000000001',
  'admin@acme.com',
  -- password: "password123"
  '$2b$12$LJ3m4ys4Gz4Iy0S5EP8tBOkGjE4F7.kX6U8Xq0kB5a1DK.XyLJKi2',
  'admin',
  NOW()
),
(
  'u2000000-0000-0000-0000-000000000002',
  'a2000000-0000-0000-0000-000000000002',
  'admin@beta.com',
  '$2b$12$LJ3m4ys4Gz4Iy0S5EP8tBOkGjE4F7.kX6U8Xq0kB5a1DK.XyLJKi2',
  'admin',
  NOW()
)
ON CONFLICT (id) DO NOTHING;

-- Sites
INSERT INTO sites (id, agency_id, domain, name, pixel_id, created_at)
VALUES
(
  's1000000-0000-0000-0000-000000000001',
  'a1000000-0000-0000-0000-000000000001',
  'www.acme-shop.com',
  'Acme Shop',
  'px_acme_001',
  NOW()
),
(
  's2000000-0000-0000-0000-000000000002',
  'a1000000-0000-0000-0000-000000000001',
  'landing.acme-digital.com',
  'Acme Landing Pages',
  'px_acme_002',
  NOW()
),
(
  's3000000-0000-0000-0000-000000000003',
  'a2000000-0000-0000-0000-000000000002',
  'www.beta-marketing.com',
  'Beta Marketing Site',
  'px_beta_001',
  NOW()
)
ON CONFLICT (id) DO NOTHING;
