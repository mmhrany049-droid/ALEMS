#!/usr/bin/env bash
# راه‌اندازی محیط توسعه ALEMS — Backend (venv + deps + migration) و Frontend (npm)
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== ALEMS — راه‌اندازی محیط توسعه =="

# ---------- Backend ----------
echo "→ ساخت venv و نصب وابستگی‌های Backend..."
python3 -m venv backend/.venv
backend/.venv/bin/pip install --quiet --upgrade pip
backend/.venv/bin/pip install --quiet -e "backend[dev]"

echo "→ اجرای مهاجرت‌های دیتابیس..."
(cd backend && .venv/bin/alembic upgrade head)

echo "→ دانلود فونت وزیرمتن (در صورت نبود)..."
mkdir -p backend/app/assets/fonts frontend/public/fonts
for w in Regular Medium SemiBold Bold; do
  if [ ! -f "backend/app/assets/fonts/Vazirmatn-$w.ttf" ]; then
    curl -sL --max-time 60 -o "backend/app/assets/fonts/Vazirmatn-$w.ttf" \
      "https://registry.npmjs.org/vazirmatn/-/vazirmatn-33.0.3.tgz" > /dev/null 2>&1 || true
  fi
done

# ---------- Frontend ----------
echo "→ نصب وابستگی‌های Frontend..."
(cd frontend && npm install --no-audit --no-fund)

echo ""
echo "✅ محیط آماده است. اجرای برنامه:  bash scripts/run.sh"
