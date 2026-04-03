.PHONY: dev dev-worker down down-clean infra infra-down build test test-back test-front test-e2e lint lint-back lint-front migrate migration logs clean ps setup

COMPOSE_BASE  = docker compose -f infra/docker/docker-compose.yml
COMPOSE_DEV   = $(COMPOSE_BASE) -f infra/docker/docker-compose.dev.yml

# ============================
# Desarrollo
# ============================

## Levantar TODO (infra + backend + frontend, sin Celery)
dev:
	$(COMPOSE_DEV) up --build

## Levantar TODO + Celery worker
dev-worker:
	$(COMPOSE_DEV) --profile worker up --build

## Solo infraestructura (postgres, redis, minio) — para desarrollar fuera de Docker
infra:
	$(COMPOSE_DEV) up postgres redis minio -d

## Detener infraestructura
infra-down:
	$(COMPOSE_DEV) down

## Detener y eliminar contenedores
down:
	$(COMPOSE_DEV) down

## Detener y eliminar contenedores + volúmenes (¡destructivo!)
down-clean:
	$(COMPOSE_DEV) down -v

## Reconstruir imágenes sin cache
build:
	$(COMPOSE_BASE) build --no-cache

## Ver logs de todos los servicios
logs:
	$(COMPOSE_DEV) logs -f

## Ver estado de servicios
ps:
	$(COMPOSE_DEV) ps

# ============================
# Setup inicial
# ============================

## Configuración inicial del entorno de desarrollo
setup:
	@test -f .env || (cp .env.example .env && echo "✓ .env creado")
	@test -f backend/.env || (cp backend/.env.example backend/.env && echo "✓ backend/.env creado")
	@test -f frontend/.env.local || (cp frontend/.env.local.example frontend/.env.local && echo "✓ frontend/.env.local creado")
	@echo "✓ Setup completo. Ejecuta: make infra  o  make dev"

# ============================
# Testing
# ============================

test: test-back test-front

test-back:
	cd backend && python -m pytest tests/ -v

test-front:
	cd frontend && npm test

test-e2e:
	cd frontend && npm run test:e2e

# ============================
# Linting
# ============================

lint: lint-back lint-front

lint-back:
	cd backend && python -m ruff check .

lint-front:
	cd frontend && npm run lint

# ============================
# Base de datos
# ============================

migrate:
	cd backend && python -m alembic -c app/infrastructure/database/migrations/alembic.ini upgrade head

migration:
	@read -p "Nombre de la migración: " name; \
	cd backend && python -m alembic -c app/infrastructure/database/migrations/alembic.ini revision --autogenerate -m "$$name"

# ============================
# Limpieza
# ============================

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .next -exec rm -rf {} + 2>/dev/null || true
