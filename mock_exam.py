# 실전 모의고사: 문서 속 실제 질문(FAQ)을 추출해 챗봇에 던지고 결과를 파일로 저장
# 사용법: 서버 켠 상태에서 → python3 mock_exam.py
import json, re, requests

BASE = "http://localhost:8000/answer"
MAX_Q = 30  # 모의고사 문항 수

KEYWORDS = ["연금", "IRP", "퇴직", "세액", "공제", "수령", "납입", "인출",
            "디폴트", "TDF", "펀드", "ETF", "상품", "과세", "해지"]

# 1) 문서에서 물음표로 끝나는 문장(질문) 추출
chunks = json.load(open("chunks.json", encoding="utf-8"))
pat = re.compile(r"[가-힣A-Za-z0-9 ,·()%~'\"]+\?")
cand = {}
for c in chunks:
    for m in pat.findall(c["text"]):
        q = re.sub(r"^[①-⑳0-9.\s/|]+", "", m).strip()  # 앞 번호표 제거
        if not (10 <= len(q) <= 60):
            continue
        if not any(k in q for k in KEYWORDS):
            continue
        key = q.replace(" ", "")
        if key not in cand:
            cand[key] = q

questions = list(cand.values())
print(f"문서에서 추출한 질문 후보: {len(questions)}개")
# 골고루 뽑기: 전체에서 균등 간격으로 MAX_Q개
step = max(1, len(questions) // MAX_Q)
picked = questions[::step][:MAX_Q]
print(f"모의고사 문항: {len(picked)}개 (문항당 수십 초, 총 10~20분 예상)\n")

# 2) 실행 + 결과 저장
stats = {"유형": {}, "수정됨": 0, "확인불가": 0, "오류": 0}
lines = []
for i, q in enumerate(picked, 1):
    try:
        r = requests.get(BASE, params={"question_id": str(i), "question": q}, timeout=300)
        d = r.json()
        trace = d.get("think_trace", "")
        ans = d.get("answer", "")
        m = re.search(r"유형 분류: '([^']+)'", trace)
        qtype = m.group(1) if m else ("무관" if "무관" in trace else "?")
        stats["유형"][qtype] = stats["유형"].get(qtype, 0) + 1
        if "수정됨" in trace:
            stats["수정됨"] += 1
        if "확인할 수 없" in ans:
            stats["확인불가"] += 1
        flag = " [검증수정]" if "수정됨" in trace else ""
        print(f"  {i:2d}/{len(picked)} [{qtype}]{flag} {q}")
    except Exception as e:
        trace, ans, qtype = f"오류: {e}", "", "오류"
        stats["오류"] += 1
        print(f"  {i:2d}/{len(picked)} [오류] {q}")
    lines.append(f"{'='*70}\n[{i}] ({qtype}) {q}\n[trace] {trace}\n[answer]\n{ans}\n")

open("mock_exam_result.txt", "w", encoding="utf-8").write("\n".join(lines))

# 3) 요약
print("\n===== 모의고사 요약 =====")
print("유형 분포:", stats["유형"])
print(f"검증기 수정 발생: {stats['수정됨']}건 / '확인 불가' 답변: {stats['확인불가']}건 / 호출 오류: {stats['오류']}건")
print("\n전체 답변은 mock_exam_result.txt 에 저장됨")
print("확인 방법: less mock_exam_result.txt  (위아래 화살표로 넘기고 q로 종료)")
