# -*- coding: utf-8 -*-
"""test_doc26.py — 퇴직소득세 오표기(doc26 '26만 4천만원'→'26만 4천원') 정조준 검증."""
import time
import auto_probe as ap

CASES = [
    "30년 근무하고 퇴직수당 1억원이면 퇴직소득세가 얼마야?",
    "퇴직수당 1억원(2002년 이후 기여분) 받으면 퇴직소득세 얼마고, 연금계좌로 받으면 얼마나 절세돼?",
    "퇴직소득세를 연금계좌에서 10년 이상 수령하면 30% 절세된다는데 예시로 금액 알려줘",
]
WRONG = "26만 4천만원"
RIGHTS = ["26만 4천원", "264,000", "26만4천원", "7만 9,200", "79,200"]
DISCLOSE = ("원문", "적혀 있으나", "적혀있으나", "표기", "기재")

for i, q in enumerate(CASES):
    if i:
        time.sleep(3)
    a, tr, c = ap.ask(f"D26_{i}", q)
    retrieved = ("doc26" in (c or "")) or ("doc26" in (tr or ""))
    note_fired = "단위 오표기" in (tr or "")
    has_wrong = WRONG in a
    has_disclose = any(k in a for k in DISCLOSE)
    has_right = any(r in a for r in RIGHTS)

    if not retrieved and not note_fired:
        verdict = "△ 이 질문으론 doc26 미검색"
    elif has_wrong and not has_disclose:
        verdict = "❌ 오표기가 고지 없이 그대로 노출"
    elif has_right or (note_fired and has_disclose):
        verdict = "✅ 계산값+고지로 정상 처리"
    else:
        verdict = "△ 애매(수동 확인)"

    print("=" * 66)
    print(f"{q}")
    print(f"  doc26 검색: {'✅' if retrieved else '❌'}"
          f"  | 오표기 교정(trace): {'✅' if note_fired else '없음'}")
    print(f"  계산값: {'✅' if has_right else '❌'}"
          f"  | 잘못된표기 노출: {'있음' if has_wrong else '없음'}"
          f"  | 원문 고지: {'✅' if has_disclose else '없음'}")
    print(f"  판정: {verdict}")
    for ln in a.splitlines():
        if any(r in ln for r in RIGHTS) or WRONG in ln or any(k in ln for k in DISCLOSE):
            print(f"    ▷ {ln.strip()[:150]}")
    print()
