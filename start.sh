#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "=========================================================="
echo " Starting FinMatch AI - Credit Card & Loan Recommender"
echo "=========================================================="

# 1. Setup Python Virtual Environment
if [ -d ".venv" ]; then
  source .venv/bin/activate
else
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r backend/requirements.txt
fi

# 2. Add Node to PATH if downloaded locally
if [ -d ".tools/node/bin" ]; then
  export PATH="$DIR/.tools/node/bin:$PATH"
fi

# 3. Trap to gracefully kill background processes on Ctrl+C
cleanup() {
  echo ""
  echo "Stopping FinMatch AI processes..."
  kill $(jobs -p) 2>/dev/null || true
  exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# 4. Start Backend API
echo "Starting FastAPI Backend on http://localhost:8000 ..."
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to be ready
echo "Waiting for backend..."
sleep 2

# 5. Start Frontend Dev Server
echo "Starting Vite Frontend on http://localhost:5173 ..."
cd frontend
npm run dev -- --host 0.0.0.0 --port 5173 &
FRONTEND_PID=$!

echo ""
echo "=========================================================="
echo " FinMatch AI is running!"
echo " Web UI:     http://localhost:5173"
echo " API Docs:   http://localhost:8000/docs"
echo " Health:     http://localhost:8000/api/v1/health"
echo " Press Ctrl+C to stop both servers"
echo "=========================================================="
echo ""

wait
