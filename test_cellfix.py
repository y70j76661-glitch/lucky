# -*- coding: utf-8 -*-
# test_cellfix.py — v9.99o 검증: 비교표 칸 오배치 교정.
#   C13/C14/M17(유형 비교)은 상품분류·판매클래스 칸에 위험/성향이 안 들어가야,
#   C01(상품 비교)은 정상 표가 그대로 유지돼야(회귀 없음).
import re, time
import auto_probe as ap

Q = [
    ("C13", "안정형이랑 공격형 디폴트옵션 포트폴리오를 비교하면?"),
    ("C14", "원리금보장상품이랑 실적배당상품을 표로 비교해줘."),
    ("M17", "원리금보장상품이랑 실적배당상품 뭐가 다르고, 각각 예금자보호는 되는지, 디폴트옵션엔 뭐가 들어가요?"),
    ("C01", "솔로몬 단기국공채랑 솔로몬 장기국공채 펀드를 비교해줘."),
]
# 상품분류/판매클래스 행에서 위험·성향 표현이 있으면 오배치(❌)
BAD_CLS = re.compile(r"상품\s*분류[^\n|]*\|[^\n]*(?:등급|위험)")
BAD_SALE = re.compile(r"판매\s*클래스[^\n|]*\|[^\n]*(?:투자자에게 적합|성향|추구하는)")
for i, (qid, q) in enumerate(Q):
    if i:
        time.sleep(3)
    a, t, c = ap.ask(qid, q)
    bad1 = bool(BAD_CLS.search(a))
    bad2 = bool(BAD_SALE.search(a))
    print("=" * 60)
    print(f"[{qid}] {q}")
    print(f"  상품분류칸 오배치: {'있음 ❌' if bad1 else '없음 ✅'}"
          f" / 판매클래스칸 오배치: {'있음 ❌' if bad2 else '없음 ✅'}")
    # 표 부분만 발췌 출력
    rows = [ln for ln in a.splitlines() if ln.strip().startswith("|")]
    print("\n".join(rows[:10]) if rows else a[:300])
    print()
