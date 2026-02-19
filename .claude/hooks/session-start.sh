#!/bin/bash
set -euo pipefail

# Only run in Claude Code on the web (remote environment)
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

BACKEND_DIR="$CLAUDE_PROJECT_DIR/backend"
FRONTEND_DIR="$CLAUDE_PROJECT_DIR/frontend"
DATA_DIR="$CLAUDE_PROJECT_DIR/data"

# Enable tunnel so port 8000 is accessible from the browser
echo 'export TUNNEL_ENABLED=true' >> "$CLAUDE_ENV_FILE"
echo 'export TUNNEL_PORTS=8000' >> "$CLAUDE_ENV_FILE"

# ── Backend: install Python dependencies ──────────────────────────────────────
cd "$BACKEND_DIR"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -q

# ── Database: seed if first run ───────────────────────────────────────────────
mkdir -p "$DATA_DIR"
if [ ! -f "$DATA_DIR/ups_pricing.db" ]; then
  echo "Seeding database..."
  python seed.py
fi

# ── Frontend: install Node dependencies ───────────────────────────────────────
cd "$FRONTEND_DIR"
npm install --silent

# ── Start backend server (serves API + built React frontend) ──────────────────
cd "$BACKEND_DIR"
source venv/bin/activate

# Kill any stale server from a previous session
pkill -f "uvicorn app.main:app" 2>/dev/null || true
sleep 1

nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 \
  > /tmp/ups-backend.log 2>&1 &
echo $! > /tmp/ups-backend.pid

# Wait briefly and confirm it's up
sleep 3
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
  echo "✓ Backend running on port 8000 (PID: $(cat /tmp/ups-backend.pid))"
else
  echo "⚠ Backend may still be starting — check /tmp/ups-backend.log"
fi
