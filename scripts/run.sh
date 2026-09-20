#!/usr/bin/env bash
# ============================================================
# ALEMS — اجرای کامل برنامه با یک دستور
#   bash scripts/run.sh
# خودکار: ساخت venv، نصب وابستگی‌ها، اجرای migration،
#         نصب پکیج‌های Frontend، سپس اجرای Backend + Frontend
# ============================================================
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== ALEMS — راه‌اندازی و اجرا =="

# ---------- Backend ----------
if [ ! -x backend/.venv/bin/python ]; then
  echo "→ ساخت virtualenv و نصب وابستگی‌های Backend..."
  python3 -m venv backend/.venv
  backend/.venv/bin/pip install --quiet --upgrade pip
  backend/.venv/bin/pip install --quiet -e "backend[dev]"
fi

echo "→ به‌روزرسانی پایگاه داده (Alembic)..."
(cd backend && .venv/bin/alembic upgrade head)

# ---------- Frontend ----------
if [ ! -d frontend/node_modules ]; then
  echo "→ نصب وابستگی‌های Frontend (npm install)..."
  (cd frontend && npm install --no-audit --no-fund)
fi

# ---------- اجرا ----------
cleanup() { kill ${BACK_PID:-} ${FRONT_PID:-} 2>/dev/null || true; }
trap cleanup EXIT INT TERM

(cd backend && .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8010) &
BACK_PID=$!
echo "✅ API:   http://localhost:8010   (سلامت: /health · اسناد: /api/docs)"

(cd frontend && npm run dev) &
FRONT_PID=$!
echo "✅ وب‌اپ: http://localhost:5173"

echo ""
echo "برای توقف Ctrl+C را بزن."
wait
