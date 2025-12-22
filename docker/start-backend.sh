#!/bin/bash
set -e

echo "🚀 Starting RECEIVER backend (port 8000)"
python -u /app/backend/api.py &

echo "🚀 Starting SENDER backend (port 8001)"
python -u /app/backend/client/sender_api.py &

# Keep container alive
wait
