#!/usr/bin/env bash
# اجرای ALEMS — Backend (پورت 8000) + Frontend dev server (پورت 5173)
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== ALEMS — اجرای برنامه =="

# Backend
(cd backend && .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000) &
BACK_PID=$!
echo "→ API:      http://localhost:8000  (اسناد: /api/docs)"

# Frontend
(cd frontend && npm run dev) &
FRONT_PID=$!
echo "→ وب‌اپ:    http://localhost:5173"

trap 'kill $BACK_PID $FRONT_PID 2>/dev/null' EXIT
echo ""
echo "برای توقف Ctrl+C را بزن."
wait
