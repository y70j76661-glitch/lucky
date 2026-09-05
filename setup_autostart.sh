#!/usr/bin/env bash
# setup_autostart.sh — 서버 재부팅 시 uvicorn 자동 기동(systemd) + 지금 즉시 그 방식으로 재시작. /root/app 에서 실행.
set -e
cd /root/app
cat > /etc/systemd/system/pension-rag.service <<'EOF'
[Unit]
Description=Pension RAG chatbot (uvicorn main:app)
After=network.target

[Service]
Type=simple
WorkingDirectory=/root/app
EnvironmentFile=-/root/app/.env
ExecStart=/root/app/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
StandardOutput=append:/root/app/server.log
StandardError=append:/root/app/server.log

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable pension-rag.service
pkill -f "uvicorn main:app" || true
sleep 2
systemctl restart pension-rag.service
for i in $(seq 1 60); do
  curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8000/answer?question_id=ping&question=ping" | grep -q 200 && echo "READY (systemd)" && break
  sleep 3
done
systemctl --no-pager --lines=3 status pension-rag.service | head -8
echo "이후 재시작은: systemctl restart pension-rag.service"
