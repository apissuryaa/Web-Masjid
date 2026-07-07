#!/usr/bin/env bash
# =======================================================
# build.sh — Dijalankan otomatis oleh Render setiap deploy
# =======================================================
set -o errexit  # hentikan jika ada error

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "📁 Collecting static files..."
python manage.py collectstatic --no-input

echo "🗄️  Running database migrations..."
python manage.py migrate

echo "✅ Build completed successfully!"
