#!/bin/bash

# مسیر پروژه
PROJECT_DIR="/home/dncboti1/ChabokTool"
VENV_PATH="/home/dncboti1/virtualenv/ChabokTool/3.11/bin/activate"
LOG_FILE="$PROJECT_DIR/logs/celery_worker.log"
ERROR_LOG="$PROJECT_DIR/logs/celery_worker_error.log"

# رفتن به فولدر پروژه
cd $PROJECT_DIR

# فعال کردن virtualenv
source $VENV_PATH

# چک کردن اگه worker در حال اجرا نیست
if ! pgrep -f "celery.*WowDash worker" > /dev/null; then
    echo "[$(date)] Starting Celery Worker..." >> $LOG_FILE
    celery -A WowDash worker \
        --loglevel=info \
        --concurrency=8 \
        --logfile=$LOG_FILE \
        --pidfile=/tmp/celery_chaboktool.pid \
        --detach
    
    if [ $? -eq 0 ]; then
        echo "[$(date)] Celery Worker started successfully." >> $LOG_FILE
    else
        echo "[$(date)] Failed to start Celery Worker." >> $ERROR_LOG
    fi
else
    echo "[$(date)] Celery Worker is already running." >> $LOG_FILE
fi
