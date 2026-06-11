#!/bin/bash

cd "$(dirname "$0")"

LOG_FILE="/home/console.log"
STATS_INTERVAL=600  # 统计刷新间隔（秒），默认 1 小时
ORDER_EXPIRE_INTERVAL=300  # 订单超时关单扫描间隔（秒），默认 5 分钟
RUN_DIR=".run"
RUNSERVER_PID_FILE="$RUN_DIR/runserver.pid"
STATS_PID_FILE="$RUN_DIR/stats_loop.pid"
ORDER_EXPIRE_PID_FILE="$RUN_DIR/order_expire.pid"

mkdir -p "$RUN_DIR"

stop_pid() {
    local pid_file="$1"
    local name="$2"
    if [ ! -f "$pid_file" ]; then
        return
    fi
    local pid
    pid=$(cat "$pid_file" 2>/dev/null)
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        echo "停止旧 ${name} (PID ${pid})..." | tee -a "$LOG_FILE"
        kill "$pid" 2>/dev/null
        sleep 1
        if kill -0 "$pid" 2>/dev/null; then
            kill -9 "$pid" 2>/dev/null
        fi
    fi
    rm -f "$pid_file"
}

stop_existing_processes() {
    echo "检查并停止旧进程..." | tee -a "$LOG_FILE"
    stop_pid "$RUNSERVER_PID_FILE" "runserver"
    stop_pid "$STATS_PID_FILE" "统计刷新任务"
    stop_pid "$ORDER_EXPIRE_PID_FILE" "订单超时关单任务"

    # 兜底：按命令特征结束遗留进程
    pkill -f "manage.py runserver 0.0.0.0:8000" 2>/dev/null || true

    # 兜底：释放 8000 端口
    if command -v lsof >/dev/null 2>&1; then
        local port_pids
        port_pids=$(lsof -ti:8000 2>/dev/null || true)
        if [ -n "$port_pids" ]; then
            echo "释放 8000 端口..." | tee -a "$LOG_FILE"
            kill $port_pids 2>/dev/null || true
            sleep 1
            kill -9 $port_pids 2>/dev/null || true
        fi
    fi
}

stop_existing_processes

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
echo $! > "$STATS_PID_FILE"

# 后台定时关闭超时未支付订单
(
    while true; do
        sleep "$ORDER_EXPIRE_INTERVAL"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] 扫描超时订单..." >> "$LOG_FILE"
        python3 manage.py expire_pending_orders >> "$LOG_FILE" 2>&1
    done
) &
echo $! > "$RUN_DIR/order_expire.pid"

echo "启动服务并记录日志..." | tee -a "$LOG_FILE"
nohup python3 manage.py runserver 0.0.0.0:8000 >> "$LOG_FILE" 2>&1 &
echo $! > "$RUNSERVER_PID_FILE"

echo "服务已重启。runserver PID: $(cat "$RUNSERVER_PID_FILE"), 统计任务 PID: $(cat "$STATS_PID_FILE")" | tee -a "$LOG_FILE"
