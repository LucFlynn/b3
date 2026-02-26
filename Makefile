.PHONY: up down build test test-e2e validate logs pixel-build seed

up:
	cp -n .env.example .env 2>/dev/null || true
	docker compose up -d --build

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

test:
	docker compose exec backend python -m pytest tests/ -v

test-e2e:
	cd frontend && npx playwright test

validate:
	bash scripts/validate_dod.sh

pixel-build:
	cd pixel && npm run build

seed:
	docker compose exec -T postgres psql -U epi -d epi < db/seed.sql

migrate:
	docker compose exec backend alembic upgrade head

migrate-new:
	docker compose exec backend alembic revision --autogenerate -m "$(msg)"

format:
	docker compose exec backend ruff format app/ tests/
	docker compose exec backend ruff check --fix app/ tests/
