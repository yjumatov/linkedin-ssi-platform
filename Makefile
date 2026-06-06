.PHONY: up down dev logs test seed migrate shell-backend shell-db

# ── Production ─────────────────────────────────────────────────────────────────
up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

restart:
	docker compose restart backend scheduler

# ── Development ────────────────────────────────────────────────────────────────
dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up

# ── Testing ────────────────────────────────────────────────────────────────────
test:
	cd backend && pytest tests/ -v

test-cov:
	cd backend && pytest tests/ -v --cov=app --cov-report=html
	@echo "Coverage report: backend/htmlcov/index.html"

# ── Database ───────────────────────────────────────────────────────────────────
migrate:
	docker compose exec backend alembic upgrade head

migrate-local:
	cd backend && alembic upgrade head

seed:
	docker compose exec backend python /scripts/seed_mock_data.py

# ── Scraping ───────────────────────────────────────────────────────────────────
scrape:
	curl -X POST http://localhost:8000/scrape/run | python3 -m json.tool

# ── AI ─────────────────────────────────────────────────────────────────────────
recs:
	curl -X POST http://localhost:8000/recommendations/generate | python3 -m json.tool

# ── Utils ──────────────────────────────────────────────────────────────────────
shell-backend:
	docker compose exec backend bash

shell-db:
	docker compose exec postgres psql -U ssi -d ssi_db

health:
	curl -s http://localhost:8000/health | python3 -m json.tool

keygen:
	@echo "SECRET_KEY=$$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
	@echo "ENCRYPTION_KEY=$$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
