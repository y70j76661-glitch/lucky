# -*- coding: utf-8 -*-
"""test_calc_fails.py — calc100 실패 7건(검색실패4+오답3) 재검증(빠른 반복용)."""
import re, time
import auto_probe as ap

Q = [
    ("G02","집중투자한도는 언제 폐지됐어?", [["2023","23.07","23년"]], "2023.07.03"),
    ("G03","집중투자한도 폐지 전 DB의 한도는 몇 %였어?", [["10%"]], "DB 10%"),
    ("G04","집중투자한도 폐지 전 DC/IRP의 한도는 몇 %였어?", [["30%"]], "DC/IRP 30%"),
    ("G08","과학기술인공제회 개인부담금은 연간 임금총액의 최소 몇 %야?", [["4.5"]], "4.5%"),
    ("C12","세후로 받은 퇴직금을 IRP나 연금저축으로 옮기려면 며칠 안에 입금해야 해?", [["60일"]], "60일"),
    ("C10","임원퇴직소득 한도를 초과한 금액은 근로소득으로 몇 % 누진과세돼?", [["6.6"],["49.5"]], "6.6~49.5%"),
    ("D04","구 개인연금저축(2000년 이전 개설)을 연금외수령하면 세율은?", [["15.4"],["이자소득세"]], "이자소득세 15.4%"),
]

def _n(s): return s.replace(",","").replace(" ","").replace("*","")
def has(a,v): return _n(v) in _n(a)

ok=0
for qid, q, need, memo in Q:
    time.sleep(2)
    a, tr, c = ap.ask(qid, q)
    passed = all(any(has(a or "", v) for v in grp) for grp in need)
    ok += passed
    print("="*60)
    print(f"[{qid}] {'✅' if passed else '❌'} 기대:{memo}   {q}")
    # 정답 청크가 실제로 붙었는지(MUST_CHUNK 발동 확인)
    pulled = "필수 근거 보강" in (tr or "")
    print(f"  MUST_CHUNK 보강: {'✅' if pulled else '없음'}")
    print(f"  답변: {(a or '')[:160]}")
print("\n" + "#"*60)
print(f"통과: {ok}/{len(Q)}")
