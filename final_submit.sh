#!/usr/bin/env bash
# final_submit.sh — 최종 저장(체크포인트/제출) 한 번에: 검증 → 백업 → 커밋 → 푸시. (서버 /root/app 에서 실행)
#   사용:  bash final_submit.sh                # 기본: 서버 main.py 를 그대로 제출본으로 확정
#          bash final_submit.sh "메시지"       # 커밋 메시지 지정
#          REPO=/root/other/repo bash final_submit.sh   # 레포가 /root/app 이 아닐 때
#   안전장치: (1) py_compile 실패면 중단 (2) 서버 응답 확인 실패면 중단 (3) .env·백업·로그·venv 는 절대 커밋 안 함
#            (4) 마감(2026-09-06 23:59 KST) 30분 전 이후엔 FORCE=1 없이는 푸시하지 않음 — 마감 후 커밋/푸시는 실격.
set -u
APP=/root/app
REPO="${REPO:-$APP}"
MSG="${1:-final: pension RAG chatbot v13.26 (calc path fixed, product facts, 429 fallback, citation consistency)}"
cd "$APP" || { echo "[중단] $APP 없음"; exit 1; }

echo "== 1) 코드 검증"
python3 -m py_compile main.py || { echo "[중단] main.py 문법 오류"; exit 2; }
MD5=$(md5sum main.py | cut -d' ' -f1); echo "main.py md5: $MD5"
VER=$(grep -o "v13\.[0-9]*" main.py | sort -t. -k2 -n | tail -1); echo "코드에 보이는 최신 버전 표식: ${VER:-?}"

echo "== 2) 서버 응답 확인 (uvicorn 살아있는지)"
if ! pgrep -f "uvicorn main:app" >/dev/null; then
  echo "uvicorn 없음 → 기동"; source venv/bin/activate 2>/dev/null
  nohup uvicorn main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &
  sleep 15
fi
RESP=$(curl -s --max-time 120 "http://127.0.0.1:8000/answer?question_id=FINAL&question=IRP%EB%9E%80%20%EB%AC%B4%EC%97%87%EC%9D%B8%EA%B0%80%EC%9A%94")
echo "$RESP" | grep -q '"answer"' || { echo "[중단] 서버 응답 없음/비정상: $RESP"; exit 3; }
echo "응답 OK: $(echo "$RESP" | head -c 160)..."

echo "== 3) 최종본 백업"
TS=$(date +%Y%m%d_%H%M%S)
cp main.py "main_final_${VER:-vfinal}_${TS}.py"; echo "백업: main_final_${VER:-vfinal}_${TS}.py"

echo "== 4) 마감 확인 (KST)"
NOW=$(TZ=Asia/Seoul date +%s); DEAD=$(TZ=Asia/Seoul date -d "2026-09-06 23:29:00" +%s)
if [ "$NOW" -gt "$DEAD" ] && [ "${FORCE:-0}" != "1" ]; then
  echo "[중단] 마감 30분 전을 지났습니다(KST $(TZ=Asia/Seoul date '+%m-%d %H:%M')). 정말 푸시하려면 FORCE=1 bash final_submit.sh"; exit 4
fi

echo "== 5) git 커밋·푸시  (레포: $REPO)"
cd "$REPO" || { echo "[중단] 레포 경로 없음: $REPO"; exit 5; }
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "[중단] $REPO 는 git 레포가 아님. REPO=/경로 로 지정"; exit 5; }
# 레포가 /root/app 과 다르면 main.py 를 레포로 복사
if [ "$REPO" != "$APP" ]; then cp "$APP/main.py" "$REPO/main.py"; echo "main.py → $REPO/main.py 복사"; fi
# 절대 올리면 안 되는 것들
for pat in ".env" "venv/" "*.bak_*" "main.py.bak_*" "*_out.txt" "server.log" "error.log" "__pycache__/" "nohup.out"; do
  grep -qxF "$pat" .gitignore 2>/dev/null || echo "$pat" >> .gitignore
done
git rm -r --cached --quiet .env venv "*.bak_*" server.log error.log __pycache__ 2>/dev/null || true
git add -A
git reset -q -- .env 2>/dev/null || true
echo "-- 커밋될 파일:"; git diff --cached --name-only | head -40
if git diff --cached --name-only | grep -qx ".env"; then echo "[중단] .env 가 스테이징됨"; exit 6; fi
if git diff --cached --quiet; then echo "변경 없음 — 이미 커밋된 상태"; else
  git -c user.name="${GIT_USER:-$(git config user.name || echo submitter)}" -c user.email="${GIT_EMAIL:-$(git config user.email || echo submitter@example.com)}" \
      commit -q -m "$MSG" || { echo "[중단] 커밋 실패"; exit 7; }
  echo "커밋: $(git log -1 --format='%h %s')"
fi
BR=$(git rev-parse --abbrev-ref HEAD)
git push origin "$BR" || { echo "[중단] 푸시 실패 — 원격/인증 확인: git remote -v"; exit 8; }
echo "== 완료: origin/$BR 에 푸시됨 ($(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M KST')), main.py md5=$MD5"
git log -1 --format='%H %ci %s'
