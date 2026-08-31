import time, statistics, requests

Q = [
 ("간단-제도",  "IRP가 뭐야?"),
 ("간단-세제",  "연금저축 세액공제 한도가 얼마야?"),
 ("계산기",     "연봉 6천만원에 연금저축 400만원, IRP에 300만원 넣으면 세액공제 얼마야?"),
 ("되묻기",     "좋은 연금 상품 하나 추천해 주세요."),
 ("비교표",     "솔로몬 국공채 단기·중장기·장기, 뭐가 달라요? 안정적인 걸 원해요."),
 ("복합질문",   "IRP는 누가 가입할 수 있고, 세액공제 한도는 얼마야? 그리고 중도인출 조건도 알려줘"),
 ("보수표",     "미래에셋 장기성장포커스 증권자투자신탁 1호 종류A의 총보수는 얼마이고, 어떤 항목들로 구성되어 있나요?"),
 ("최상급",     "수수료가 가장 적은 연금 상품 하나만 딱 골라주세요"),
 ("무관",       "BTS 콘서트 티켓 예매 방법"),
 ("문서밖",     "국민연금 보험료율이 몇 퍼센트야?"),
]

rows = []
for tag, q in Q:
    t0 = time.time()
    try:
        d = requests.get("http://localhost:8000/answer",
                         params={"question_id": tag, "question": q}, timeout=300).json()
        el = time.time() - t0
        tr = d.get("think_trace", "")
        calls = tr.count("HCX-005") + (0 if "무관" in tr else 1)
        rows.append((tag, el, len(d.get("answer", ""))))
        print(f"{tag:<10s} {el:6.1f}초   답변 {len(d.get('answer','')):4d}자", flush=True)
    except Exception as e:
        print(f"{tag:<10s} 실패: {e}", flush=True)

ts = [r[1] for r in rows]
print("\n" + "=" * 56)
print(f"측정 {len(ts)}건")
print(f"  최소 {min(ts):.1f}초 / 중앙값 {statistics.median(ts):.1f}초 / 최대 {max(ts):.1f}초")
print(f"  평균 {statistics.mean(ts):.1f}초")
over = [(t, s) for s, t, _ in [(r[0], r[1], r[2]) for r in rows] if t > 20]
print("\n20초 초과:", [f"{s}({t:.0f}초)" for t, s in over] or "없음")
print("30초 초과:", [f"{s}({t:.0f}초)" for t, s in over if t > 30] or "없음")
