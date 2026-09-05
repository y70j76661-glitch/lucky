#!/bin/bash
# watchdog.sh — 챗봇 서버 감시장치. cron이 1분마다 실행한다.
#   ① uvicorn이 죽어 있으면 다시 띄운다 (서버 재부팅 후 첫 1분 안에도 뜬다)
#   ② 프로세스는 있는데 3분 연속 응답이 없으면(멈춤) 죽이고 다시 띄운다
#      (기동 직후 인덱스 로딩 ~20초 동안을 오인해 죽이지 않도록 3분 유예)
#   유지보수로 잠시 꺼두고 싶으면: touch /root/app/.watchdog_off
#   다시 켜려면:                  rm /root/app/.watchdog_off
cd /root/app || exit 1

[ -f /root/app/.watchdog_off ] && exit 0

STRIKES=/root/app/.watchdog_strikes

if pgrep -f "uvicorn main:app" > /dev/null; then
    if curl -s -m 5 http://localhost:8000/openapi.json > /dev/null; then
        rm -f "$STRIKES"
        exit 0                                  # 정상
    fi
    n=$(( $(cat "$STRIKES" 2>/dev/null || echo 0) + 1 ))
    echo "$n" > "$STRIKES"
    if [ "$n" -lt 3 ]; then
        exit 0                                  # 켜지는 중일 수 있다 — 아직 참는다
    fi
    echo "[$(date '+%F %T')] 3분 연속 무응답 — 프로세스 재기동" >> /root/app/watchdog.log
    pkill -f "uvicorn main:app"
    sleep 2
fi

rm -f "$STRIKES"
echo "[$(date '+%F %T')] uvicorn 시작" >> /root/app/watchdog.log
nohup /root/app/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 \
    >> /root/app/server.log 2>&1 &
