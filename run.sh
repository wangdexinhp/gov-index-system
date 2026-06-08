#!/bin/bash

cd "$(dirname "$0")"

LOG_FILE="/home/console.log"
STATS_INTERVAL=600  # 统计刷新间隔（秒），默认 1 小时

echo "重建覆盖统计..." | tee -a "$LOG_FILE"
python3 manage.py rebuild_coverage_stats >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    echo "覆盖统计重建失败，继续启动服务..." | tee -a "$LOG_FILE"
fi

# 后台定时刷新统计（随 run.sh 启动，无需单独配置 cron）
(
    while true; do
        sleep "$STATS_INTERVAL"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] 定时重建覆盖统计..." >> "$LOG_FILE"
        python3 manage.py rebuild_coverage_stats >> "$LOG_FILE" 2>&1
    done
) &

echo "启动服务并记录日志..." | tee -a "$LOG_FILE"
nohup python3 manage.py runserver 0.0.0.0:8000 >> "$LOG_FILE" 2>&1 &
