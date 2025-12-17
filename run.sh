#!/bin/bash
LOG_DIR="logs"

echo "启动服务并记录日志..."
nohup python3 manage.py runserver 0.0.0.0:8000 > ${LOG_DIR}/console.log 2>&1 &
echo $! > ${LOG_DIR}/django.pid
echo "服务已启动，PID: $(cat ${LOG_DIR}/django.pid)"

