#!/usr/bin/env bash
set -euo pipefail

echo "=== Configuración de entorno de desarrollo ==="

# Root .env (Docker Compose)
if [ ! -f .env ]; then
  cp .env.example .env
  echo "✓ .env creado"
else
  echo "· .env ya existe"
fi

# Backend
if [ ! -f backend/.env ]; then
  cp backend/.env.example backend/.env
  echo "✓ backend/.env creado"
else
  echo "· backend/.env ya existe"
fi

# Frontend
if [ ! -f frontend/.env.local ]; then
  cp frontend/.env.local.example frontend/.env.local
  echo "✓ frontend/.env.local creado"
else
  echo "· frontend/.env.local ya existe"
fi

echo ""
echo "=== Entorno listo ==="
echo ""
echo "Opciones:"
echo "  make infra    → Solo infra (postgres, redis, minio) para dev local"
echo "  make dev      → Todo (infra + backend + frontend)"
echo "  make dev-worker → Todo + Celery worker"
