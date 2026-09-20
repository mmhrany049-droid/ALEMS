#!/usr/bin/env bash
# ALEMS 2.0 — one-time dev setup (doc 03 §3.3)
# Backend: Python 3.11+, venv, alembic. Frontend: node 18+, npm.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> Backend setup"
cd "$ROOT/backend"
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt
# schema ONLY via Alembic (doc 05)
.venv/bin/alembic upgrade head
cd "$ROOT"

echo "==> Frontend setup"
cd "$ROOT/frontend"
npm install --no-audit --no-fund
cd "$ROOT"

echo "==> Done. Run with: ./scripts/run.sh"
