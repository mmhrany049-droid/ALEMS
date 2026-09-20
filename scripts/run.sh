#!/usr/bin/env bash
# ALEMS 2.0 — run (doc 03 §3.2, doc 02 NFR-4)
#   Backend  → http://127.0.0.1:8010   (default host 127.0.0.1, port 8010 — NOT 8000)
#   Frontend → http://localhost:5173   (Vite proxy → http://127.0.0.1:8010)
# Override with env: HOST=0.0.0.0 PORT=8010 FRONTEND_PORT=5173 ./scripts/run.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8010}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

# migrate schema if needed (SQLite by default) — schema ONLY via Alembic (doc 05)
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

echo "==> Backend on http://${HOST}:${PORT}"
(cd "$ROOT/backend" && .venv/bin/uvicorn app.main:app --host "$HOST" --port "$PORT") &
BACK_PID=$!

echo "==> Frontend on http://localhost:${FRONTEND_PORT} (proxy → http://127.0.0.1:${PORT})"
(cd "$ROOT/frontend" && npm run dev -- --host 0.0.0.0 --port "$FRONTEND_PORT") &
FRONT_PID=$!

echo
echo "  UI:      http://localhost:${FRONTEND_PORT}"
echo "  API:     http://127.0.0.1:${PORT}/health"
echo "  Swagger: http://127.0.0.1:${PORT}/docs"
echo
wait
