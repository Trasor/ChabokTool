#!/bin/bash
# Stop all Celery workers

echo "🛑 Stopping all workers..."
pkill -9 -f celery

sleep 2

COUNT=$(ps aux | grep celery | grep -v grep | wc -l)

if [ $COUNT -eq 0 ]; then
    echo "✅ All workers stopped!"
else
    echo "⚠️ Warning: $COUNT workers still running"
fi