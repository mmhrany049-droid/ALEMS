#!/usr/bin/env bash
# ALEMS 2.0 — run (doc 03 §3.2, doc 02 NFR-4)
#   Backend  → http://localhost:8010  (default port 8010)
#   Frontend → http://localhost:5173  (Vite proxy → http://127.0.0.1:8010)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_PORT="${ALEMS_BACKEND_PORT:-8010}"
FRONTEND_PORT="${ALEMS_FRONTEND_PORT:-5173}"

# migrate schema if needed (SQLite by default)
cd "$ROOT/backend"
if [ -x .venv/bin/alembic ]; then
  .venv/bin/alembic upgrade head
else
  echo "Backend venv missing — run ./scripts/setup-dev.sh first" >&2
  exit 1
fi
cd "$ROOT"

cleanup() {
  [[ -n "${BACK_PID:-}" ]] && kill "$BACK_PID" 2>/dev/null || true
  [[ -n "${FRONT_PID:-}" ]] && kill "$FRONT_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "==> Backend on :$BACKEND_PORT"
(cd "$ROOT/backend" && .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port "$BACKEND_PORT") &
BACK_PID=$!

echo "==> Frontend on :$FRONTEND_PORT (proxy → 127.0.0.1:$BACKEND_PORT)"
(cd "$ROOT/frontend" && npm run dev -- --host 0.0.0.0 --port "$FRONTEND_PORT") &
FRONT_PID=$!

echo
echo "  UI:      http://localhost:$FRONTEND_PORT"
echo "  API:     http://localhost:$BACKEND_PORT/health"
echo "  Swagger: http://localhost:$BACKEND_PORT/docs"
echo
wait
