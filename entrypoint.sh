#!/bin/sh
set -e

echo "[CampusRide] Running container startup sequence..."

# Seed database with campus locations, fares, and demo users if database file does not exist
if [ ! -f /app/campushustle.db ]; then
    echo "[CampusRide] Database missing. Executing seed script..."
    python seed.py
fi

PORT="${PORT:-8080}"
echo "[CampusRide] Starting Gunicorn server with WebSocket support on port ${PORT}..."

exec gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 --bind "0.0.0.0:${PORT}" "run:app"
