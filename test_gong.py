# -*- coding: utf-8 -*-
# test_gong.py — v9.99l 검증: 과기공(과학기술인공제회) 누출 최종 방어.
#   질문에 과기공 맥락이 없으면 답변에 '과학기술인공제회/과기공/공제회'가
#   한 번도 안 나와야 한다. R17은 예전에 실제로 누출된 질문.
#   P10은 '저축성 보험' 오답이 없어야(연금저축=계좌).
import re
import time
import auto_probe as ap

Q = [
    ("R17", "30대인데 뭐 추천해요?"),
    ("P05", "퇴직연금 펀드는 일반 펀드보다 수수료가 싼가요?"),
    ("P10", "IRP랑 연금저축은 뭐가 달라요?"),
]
LEAK = re.compile(r"과학기술인|과기공|공제회|발전\s*장려금|출연연")
INS = re.compile(r"저축성\s*보험|연금저축은?\s*보험")
for i, (qid, q) in enumerate(Q):
    if i:
        time.sleep(3)
    a, t, c = ap.ask(qid, q)
    leak = bool(LEAK.search(a))
    ins = bool(INS.search(a))
    print("=" * 60)
    print(f"[{qid}] {q}")
    print(f"  과기공 누출: {'있음 ❌' if leak else '없음 ✅'}"
          + (f" / 보험오답: {'있음 ❌' if ins else '없음 ✅'}" if qid == "P10" else ""))
    print(a[:450])
    print()
