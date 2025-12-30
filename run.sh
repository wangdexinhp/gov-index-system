#!/bin/bash
# python3 manage.py runserver 0.0.0.0:9000
echo "启动服务并记录日志..."
nohup python3 manage.py runserver 0.0.0.0:8000 > /home/console.log 2>&1 &

