#!/bin/bash
# Production startup script for Railway
# This script:
# 1. Runs smart database migrations
# 2. Starts the FastAPI application

set -e  # Exit on any error

echo "=========================================="
echo "Starting Moreach Backend"
echo "=========================================="

# Run smart migrations
echo "Running database migrations..."
python scripts/migrate.py

# Start the application
echo "Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
