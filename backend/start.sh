#!/bin/bash
# Railway start script for Naver Place Optimizer Backend

echo "Starting Naver Place Optimizer Backend..."
echo "Python version: $(python --version)"
echo "Port: $PORT"

# Start uvicorn server
exec python -m uvicorn main_v2:app --host 0.0.0.0 --port ${PORT:-8000}
