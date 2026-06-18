.PHONY: help dev up down build test lint clean reset logs shell

help:
	@echo 'VAPT Platform - Makefile'
	@echo ''
	@echo 'Usage:'
	@echo '  make dev          Start development environment'
	@echo '  make up           Start all services (detached)'
	@echo '  make down         Stop all services'
	@echo '  make build        Build all containers'
	@echo '  make prod         Start production environment'
	@echo '  make test         Run all tests'
	@echo '  make lint         Run linters'
	@echo '  make clean        Clean build artifacts'
	@echo '  make reset        Reset Docker environment (volumes wiped)'
	@echo '  make logs         Follow logs'
	@echo '  make shell        Open bash in backend container'
	@echo '  make migrate      Run Alembic migrations'
	@echo '  make seed         Seed database with sample data'

# Development
dev:
	docker compose -f docker-compose.yml -f docker-compose.override.yml up --build

up:
	docker compose -f docker-compose.yml -f docker-compose.override.yml up -d --build

down:
	docker compose -f docker-compose.yml -f docker-compose.override.yml down

build:
	docker compose -f docker-compose.yml build

# Production
prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

prod-down:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# Testing
test:
	docker compose -f docker-compose.yml -f docker-compose.override.yml exec backend pytest -v --cov=app --cov-report=term-missing

test-frontend:
	docker compose -f docker-compose.yml -f docker-compose.override.yml exec frontend npm run test

test-e2e:
	docker compose -f docker-compose.yml -f docker-compose.override.yml exec frontend npm run cypress:run

# Linting
lint:
	docker compose -f docker-compose.yml -f docker-compose.override.yml exec backend ruff check .
	docker compose -f docker-compose.yml -f docker-compose.override.yml exec backend mypy app
	docker compose -f docker-compose.yml -f docker-compose.override.yml exec frontend npm run lint

lint-frontend:
	docker compose -f docker-compose.yml -f docker-compose.override.yml exec frontend npm run lint

lint-backend:
	docker compose -f docker-compose.yml -f docker-compose.override.yml exec backend ruff check .

# Cleanup
clean:
	rm -rf frontend/dist
	rm -rf frontend/.vite
	rm -rf backend/dist
	rm -rf backend/*.egg-info
	rm -rf .pytest_cache
	rm -rf **/__pycache__
	find . -type f -name "*.pyc" -delete

reset:
	docker compose -f docker-compose.yml -f docker-compose.override.yml down -v
	docker compose -f docker-compose.yml -f docker-compose.override.yml build
	docker compose -f docker-compose.yml -f docker-compose.override.yml up -d

# Utilities
logs:
	docker compose -f docker-compose.yml -f docker-compose.override.yml logs -f

shell:
	docker compose -f docker-compose.yml -f docker-compose.override.yml exec backend /bin/bash

shell-frontend:
	docker compose -f docker-compose.yml -f docker-compose.override.yml exec frontend /bin/sh

shell-worker:
	docker compose -f docker-compose.yml -f docker-compose.override.yml exec celery_worker /bin/bash

# Database
migrate:
	docker compose -f docker-compose.yml -f docker-compose.override.yml exec backend alembic upgrade head

migrate-auto:
	docker compose -f docker-compose.yml -f docker-compose.override.yml exec backend alembic revision --autogenerate -m "$(message)"

seed:
	docker compose -f docker-compose.yml -f docker-compose.override.yml exec backend python scripts/seed.py

# Monitoring
grafana:
	@echo 'Grafana: http://localhost:3001 (admin:admin)'

prometheus:
	@echo 'Prometheus: http://localhost:9090'

kibana:
	@echo 'Kibana: http://localhost:5601'

# Flask Webhooks
flask-logs:
	docker compose -f docker-compose.yml -f docker-compose.override.yml logs -f flask_webhooks

flask-shell:
	docker compose -f docker-compose.yml -f docker-compose.override.yml exec flask_webhooks /bin/bash
