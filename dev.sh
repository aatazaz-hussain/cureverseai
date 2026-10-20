#!/usr/bin/env bash

set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "=============================================="
echo "        CUREVERSEAI DEVELOPMENT SERVER"
echo "=============================================="
echo ""
echo "Frontend   → http://localhost:3000"
echo "Backend    → http://localhost:8000"
echo "AI Engine  → http://localhost:8001"
echo ""
echo "Press Ctrl+C to stop all services."
echo ""

cleanup() {
    echo ""
    echo "Stopping CureVerseAI services..."
    kill 0
}

trap cleanup SIGINT SIGTERM EXIT

# Frontend
(
    cd "$ROOT/frontend"
    echo "[FRONTEND] Starting Next.js..."
    npm run dev
) &

# Backend
(
    cd "$ROOT/backend"
    source .venv/bin/activate
    echo "[BACKEND] Starting FastAPI on :8000..."
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
) &

# AI Engine
(
    cd "$ROOT/ai-engine"
    source .venv/bin/activate

    # Load AI Engine environment variables
    if [ -f ".env" ]; then
        set -a
        source .env
        set +a
    else
        echo "[AI ENGINE] ERROR: ai-engine/.env not found."
        exit 1
    fi

    echo "[AI ENGINE] Starting FastAPI on :8001..."
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
) &

wait
