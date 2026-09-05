# -*- coding: utf-8 -*-
"""
test_notecheck.py — 문서 단위 오표기(doc41·doc26)를 챗봇이 런타임에
                    올바르게 처리하는지 실증.

확인:
  ① 해당 문서를 검색해 오는지([참고 문서]/context)
  ② 오표기 교정이 발동하는지(think_trace에 '단위 오표기')
  ③ 답변에 '계산값'이 들어가고, 잘못된 표기가 남았다면 '원문엔 X로 적혀
     있으나' 식의 고지와 함께인지(고지 없이 틀린 값만 나오면 실패)
"""
import re
import time
import auto_probe as ap

# (질문, 잘못된표기, 계산값표기, 근거문서)
CASES = [
    ("연금저축이랑 IRP 합쳐서 연 900만원 납입하면 세액공제로 얼마 돌려받아?",
     "148만 5천만원", ["148만 5천원", "1,485,000", "148만5천원"], "doc41"),
    ("총급여 5천만원 직장인이 연금저축·IRP로 900만원 넣으면 절세액이 얼마야?",
     "148만 5천만원", ["148만 5천원", "1,485,000", "148만5천원"], "doc41"),
    ("연금저축 세액공제로 실제 환급받는 금액을 예시로 알려줘",
     "148만 5천만원", ["148만 5천원", "1,485,000"], "doc41"),
    ("연금저축 납입액의 세액공제 절세 효과 예시를 금액으로 알려줘",
     "26만 4천만원", ["26만 4천원", "264,000", "7만 9,200", "79,200"], "doc26"),
]
DISCLOSE = ("원문", "적혀 있으나", "적혀있으나", "표기", "기재")

for i, (q, wrong, rights, doc) in enumerate(CASES):
    if i:
        time.sleep(3)
    a, tr, c = ap.ask(f"NOTE{i:02d}", q)
    retrieved = (doc in (c or "")) or (doc in a) or (doc in (tr or ""))
    note_fired = "단위 오표기" in (tr or "")
    has_wrong = wrong in a
    has_disclose = any(k in a for k in DISCLOSE)
    has_right = any(r in a for r in rights)

    if not retrieved and not note_fired:
        verdict = "△ 이 질문으론 해당 문서 미검색(검증 안 됨)"
    elif has_wrong and not has_disclose:
        verdict = "❌ 오표기가 고지 없이 그대로 노출"
    elif has_right or (note_fired and has_disclose):
        verdict = "✅ 계산값+고지로 정상 처리"
    else:
        verdict = "△ 애매(수동 확인 필요)"

    print("=" * 66)
    print(f"[{doc}] {q}")
    print(f"  문서 검색됨: {'✅' if retrieved else '❌'}"
          f"  | 오표기 교정 발동(trace): {'✅' if note_fired else '없음'}")
    print(f"  계산값 포함: {'✅' if has_right else '❌'}"
          f"  | 잘못된표기 노출: {'있음' if has_wrong else '없음'}"
          f"  | 원문 고지: {'✅' if has_disclose else '없음'}")
    print(f"  판정: {verdict}")
    # 관련 문장 발췌
    for ln in a.splitlines():
        if any(r in ln for r in rights) or wrong in ln or any(k in ln for k in DISCLOSE):
            print(f"    ▷ {ln.strip()[:140]}")
    print()
