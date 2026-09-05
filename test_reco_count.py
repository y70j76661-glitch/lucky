# -*- coding: utf-8 -*-
# test_reco_count.py — v9.99p4: ①잘림(끝맺음) 해결 ②서두 개수공지 작동.
#   Q1: 5개 요청 — 마지막 항목이 잘리지 않고 끝맺는지.
#   Q2: 10개 요청 — 문서 근거가 부족하니 '서두에 개수 공지'가 떠야.
import re, time
import auto_probe as ap

Q = [
    ("5개", "ETF 적립식으로 연금 투자하고 싶은데 20대이고 공격형이야. 종목 5가지를 리스트로 추천해줘"),
    ("10개", "공격형인데 연금으로 담을 ETF 종목 10가지 리스트로 추천해줘"),
]
COMPET = re.compile(r"KODEX|KBSTAR|ARIRANG|HANARO")
for i, (tag, q) in enumerate(Q):
    if i:
        time.sleep(3)
    a, t, c = ap.ask(tag, q)
    head = a.strip().split("\n")[0]
    # [참고 문서] 꼬리를 떼고 본문 끝맺음만 본다
    body = re.sub(r"\n*\[참고 문서\][^\n]*$", "", a.strip()).strip()
    tail = body[-25:]
    nums = re.findall(r"(?m)^\s*(\d+)[.)]\s", a)
    complete = bool(re.search(r"[.。%원다요음니다\)]\s*$", body))
    print("=" * 60)
    print(f"[{tag}] {q}")
    print(f"  서두 개수공지: {'✅ 있음' if '근거가 확인되는' in head else '없음'}")
    print(f"  제시 항목 수: {len(nums)}  번호: {nums}")
    print(f"  경쟁사 브랜드 창작: {COMPET.findall(a) or '없음 ✅'}")
    print(f"  끝맺음 정상(잘림 없음): {'✅' if complete else '❌ 잘린 듯'}  …끝: '{tail}'")
    print("---- 전문 ----")
    print(a)
    print()
