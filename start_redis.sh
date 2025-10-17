#!/bin/bash

LOG_FILE="/home/dncboti1/ChabokTool/logs/redis.log"

# چک کردن اگه Redis در حال اجرا نیست
if ! pgrep -f "redis-server" > /dev/null; then
    echo "[$(date)] Starting Redis Server..." >> $LOG_FILE
    redis-server --daemonize yes --logfile $LOG_FILE
    
    if [ $? -eq 0 ]; then
        echo "[$(date)] Redis Server started successfully." >> $LOG_FILE
    else
        echo "[$(date)] Failed to start Redis Server." >> $LOG_FILE
    fi
else
    echo "[$(date)] Redis Server is already running." >> $LOG_FILE
fi
