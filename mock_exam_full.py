# 확장 모의고사: 문서 속 질문 전체를 시험 (중간 저장 → 끊겨도 재실행하면 이어서 진행)
# 사용법: 서버 켠 상태에서 → python3 mock_exam_full.py   (총 2~4시간, 켜두고 다른 일 하면 됨)
import json, re, os, requests

BASE = "http://localhost:8000/answer"
STATE = "mock_full_state.json"   # 진행 상황 저장 파일

KEYWORDS = ["연금", "IRP", "퇴직", "세액", "공제", "수령", "납입", "인출",
            "디폴트", "TDF", "펀드", "ETF", "상품", "과세", "해지"]

# 1) 문서에서 질문 추출 (mock_exam.py와 동일한 규칙 → 항상 같은 순서)
chunks = json.load(open("chunks.json", encoding="utf-8"))
pat = re.compile(r"[가-힣A-Za-z0-9 ,·()%~'\"]+\?")
cand = {}
for c in chunks:
    for m in pat.findall(c["text"]):
        q = re.sub(r"^[①-⑳0-9.\s/|]+", "", m).strip()
        if not (10 <= len(q) <= 60):
            continue
        if not any(k in q for k in KEYWORDS):
            continue
        key = q.replace(" ", "")
        if key not in cand:
            cand[key] = q
questions = list(cand.values())
total = len(questions)

# 2) 이전 진행 상황 불러오기 (이어하기)
done = {}
if os.path.exists(STATE):
    try:
        done = json.load(open(STATE, encoding="utf-8"))
    except Exception:
        done = {}
print(f"전체 문항: {total}개 / 완료: {len(done)}개 / 남은 문항: {total - len(done)}개\n")

# 3) 실행 (문항마다 즉시 저장)
for i, q in enumerate(questions, 1):
    if q in done:
        continue
    try:
        r = requests.get(BASE, params={"question_id": str(i), "question": q}, timeout=300)
        d = r.json()
        trace = d.get("think_trace", "")
        ans = d.get("answer", "")
        m = re.search(r"유형 분류: '([^']+)'", trace)
        qtype = m.group(1) if m else ("무관" if "무관" in trace else "?")
        rec = {"n": i, "type": qtype, "trace": trace, "answer": ans}
        flag = ""
        if qtype == "무관":
            flag += " [무관!]"
        if "수정됨" in trace:
            flag += " [검증수정]"
        if "확인할 수 없" in ans:
            flag += " [확인불가]"
        print(f"  {i:3d}/{total} [{qtype}]{flag} {q[:44]}")
    except Exception as e:
        rec = {"n": i, "type": "오류", "trace": f"오류: {e}", "answer": ""}
        print(f"  {i:3d}/{total} [오류] {q[:44]}")
    done[q] = rec
    json.dump(done, open(STATE, "w", encoding="utf-8"), ensure_ascii=False)

# 4) 전체 요약 + 이상 신호 목록
types, offtopic, fixed, unknown, errors = {}, [], [], [], []
for q, rec in done.items():
    t = rec["type"]
    types[t] = types.get(t, 0) + 1
    if t == "무관":
        offtopic.append(q)
    if t == "오류":
        errors.append(q)
    if "수정됨" in rec.get("trace", ""):
        fixed.append(q)
    if "확인할 수 없" in rec.get("answer", ""):
        unknown.append(q)

print("\n" + "=" * 60)
print("===== 확장 모의고사 최종 요약 =====")
print(f"완료: {len(done)}/{total}")
print("유형 분포:", types)

def show(title, items):
    print(f"\n[{title}] {len(items)}건")
    for q in items:
        print("  -", q)

show("무관 판정 (문서 질문인데 걸러짐 → 오판 의심)", offtopic)
show("검증기 수정 발생 (환각 시도 흔적)", fixed)
show("'확인 불가' 답변 (검색 실패 의심)", unknown)
show("호출 오류", errors)

# 전체 답변 파일로 저장
lines = []
for q, rec in sorted(done.items(), key=lambda x: x[1]["n"]):
    lines.append(f"{'='*70}\n[{rec['n']}] ({rec['type']}) {q}\n[trace] {rec['trace']}\n[answer]\n{rec['answer']}\n")
open("mock_full_result.txt", "w", encoding="utf-8").write("\n".join(lines))
print("\n전체 답변: mock_full_result.txt / 진행 상태: mock_full_state.json")
print("보기: less mock_full_result.txt  (q로 종료)")
