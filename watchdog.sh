#!/bin/bash
# 5분마다 실행: 8000 포트가 죽어 있으면 서버 자동 재시작
cd /root/app
if ! ss -tln | grep -q ':8000 '; then
    echo "$(date) 서버 다운 감지 -> 자동 재시작" >> /root/app/watchdog.log
    nohup /root/app/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 >> /root/app/server.log 2>&1 &
fi
