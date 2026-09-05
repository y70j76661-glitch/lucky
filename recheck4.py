# -*- coding: utf-8 -*-
# recheck4.py — 잔존 4개 항목의 원래 질문을 probe.jsonl에서 찾아
#   '지금 서버'(새 문서 데이터 + 현재 main.py)에 다시 물어보고 재판정한다.
#
#   4개 그룹:
#     ① P0697            — 반사적 거절 잔존 1건
#     ② P0325 / P0579    — 수수료 숫자 검증 미완 2건
#     ③ 추측 표현         — "~것으로 보입니다 / 통상적으로 ~" 류 (기록에서 자동 탐색)
#     ④ 모순 변형         — "확인할 수 없습니다. 따라서 통상적으로는..." 류 (자동 탐색)
#
#   비용 통제: 총 12문항 상한 (약 180원). 실행 위치: /root/app
import json, os, re, sys, time, requests

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "probe.jsonl")
BASE = "http://localhost:8000/answer"

# ---- 판정 패턴 ----
REFUSE = re.compile(r"(죄송|답변드리기 어렵|도와드리기 어렵|확인할 수 없|자료에 없|찾을 수 없)")
SPECUL = re.compile(r"(것으로 보입니다|것으로 추정|것으로 예상|로 보여집니다|"
                    r"통상적으로|일반적으로는|아마도|추측)")
CONTRA = re.compile(r"(확인할 수 없습니다|자료에 없습니다|찾을 수 없습니다)"
                    r"[^.\n]{0,40}[.\n]\s*[^\n]{0,20}"
                    r"(따라서|다만|하지만|그러나|일반적으로|통상적으로)")

rows = {}
with open(SRC, encoding="utf-8") as f:
    for ln in f:
        try:
            r = json.loads(ln)
            rows[r["id"]] = r
        except Exception:
            pass
print(f"probe.jsonl {len(rows)}건 로드")

# ---- 대상 선정 ----
picks = []          # (그룹, 레코드)
seen = set()

def add(group, r):
    if r and r["id"] not in seen:
        picks.append((group, r))
        seen.add(r["id"])

# ① ②: id로 직접
for pid, g in [("P0697", "①거절"), ("P0325", "②수수료"), ("P0579", "②수수료")]:
    r = rows.get(pid)
    if r is None:
        print(f"  ! {pid}가 probe.jsonl에 없음 — 건너뜀")
    add(g, r)

# ③ 추측 표현 (최대 6건) / ④ 모순 변형 (최대 3건): 저장된 옛 답변에서 탐색
sp = [r for r in rows.values() if SPECUL.search(r.get("answer", ""))]
ct = [r for r in rows.values() if CONTRA.search(r.get("answer", ""))]
print(f"기록상 추측 표현 {len(sp)}건 / 모순 변형 {len(ct)}건 발견")
for r in sp[:6]:
    add("③추측", r)
for r in ct[:3]:
    add("④모순", r)

picks = picks[:12]
print(f"재질문 대상 {len(picks)}건 (상한 12)\n")

# ---- 재질문 + 재판정 ----
results = {"①거절": [0, 0], "②수수료": [0, 0], "③추측": [0, 0], "④모순": [0, 0]}
for i, (g, r) in enumerate(picks, 1):
    q = r.get("q", "")
    try:
        resp = requests.get(BASE, params={"question_id": f"RC{i:02d}", "question": q},
                            timeout=90)
        ans = resp.json().get("answer", "")
    except Exception as e:
        print(f"[{r['id']}] 서버 오류: {e}")
        continue

    if g == "①거절":
        bad = bool(REFUSE.search(ans[:120]))       # 서두가 여전히 거절인가
        verdict = "여전히 거절" if bad else "회복됨"
    elif g == "②수수료":
        bad = None                                  # 숫자 대조는 사람이 본다
        verdict = "숫자 원문 대조 필요 ↓"
    elif g == "③추측":
        m = SPECUL.search(ans)
        bad = bool(m)
        verdict = f"추측 표현 잔존({m.group(0)})" if bad else "사라짐"
    else:
        m = CONTRA.search(ans)
        bad = bool(m)
        verdict = "모순 변형 잔존" if bad else "사라짐"

    if bad is not None:
        results[g][0 if not bad else 1] += 1
    print(f"===== [{r['id']}] {g} — {verdict} =====")
    print(f"Q: {q}")
    if r.get("src"):
        print(f"근거 문서(당시): {r['src']}")
    print("옛 답변: " + re.sub(r"\s+", " ", r.get("answer", ""))[:200])
    print("새 답변: " + re.sub(r"\s+", " ", ans)[:500])
    print()
    time.sleep(1.0)

print("===== 요약 =====")
for g, (good, bad) in results.items():
    if good or bad:
        print(f"  {g}: 해결 {good} / 잔존 {bad}")
print("  ②수수료는 새 답변의 숫자를 근거 문서와 눈으로 대조해 주세요.")
