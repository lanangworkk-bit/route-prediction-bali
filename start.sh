#!/usr/bin/env bash
# Jalankan aplikasi sekali klik/baris: ./start.sh
# Env opsional: PORT (default 9000), HOST, RELOAD=1 untuk auto-reload saat dev.
set -euo pipefail
cd "$(dirname "$0")"

PORT="${PORT:-9000}"
HOST="${HOST:-0.0.0.0}"

if [ ! -f .env ] && [ -f .env.example ]; then
    cp .env.example .env
    echo "==> .env dibuat dari .env.example (isi API key bila ada)"
fi

if [ ! -d venv ]; then
    echo "==> Membuat virtualenv & menginstal dependensi (sekali saja)..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --quiet --upgrade pip
    pip install --quiet -r requirements.txt
else
    source venv/bin/activate
fi

echo "==> Menjalankan server di http://$HOST:$PORT"
if [ "${RELOAD:-0}" = "1" ]; then
    exec uvicorn app.main:app --host "$HOST" --port "$PORT" --reload "$@"
fi
exec uvicorn app.main:app --host "$HOST" --port "$PORT" "$@"