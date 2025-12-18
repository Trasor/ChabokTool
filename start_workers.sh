#!/bin/bash
# Auto-Start Multiple Workers for ChabokTool

cd /home/dncboti1/ChabokTool
source /home/dncboti1/virtualenv/ChabokTool/3.11/bin/activate

# Kill old workers
echo "🛑 Stopping old workers..."
pkill -9 -f celery
sleep 2

# Create logs directory
mkdir -p logs

# تعداد Workers (برای 8GB RAM: 8 Worker)
NUM_WORKERS=8

echo "🚀 Starting $NUM_WORKERS workers..."

for i in $(seq 1 $NUM_WORKERS); do
    nohup celery -A WowDash worker \
        -Q chaboktool_queue \
        --loglevel=info \
        --concurrency=4 \
        -n worker$i@%h \
        --logfile=logs/worker_$i.log \
        > /dev/null 2>&1 &
    
    echo "✅ Started worker$i"
    sleep 1
done

echo ""
echo "✅ All workers started!"
echo "📊 Total capacity: $(($NUM_WORKERS * 4)) parallel tasks"
echo ""
echo "Check logs:"
echo "  tail -f logs/worker_1.log"
echo ""
echo "Check workers:"
echo "  ps aux | grep celery | grep -v grep | wc -l"