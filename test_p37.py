# -*- coding: utf-8 -*-
# test_p37.py — 채권 위험/한도(P37) 한 발 검증. 따옴표 중첩 없이 파일로 실행.
import auto_probe as ap

q = "퇴직연금으로 채권 사려는데 위험하지 않아요? 한도도 있어요?"
a, t, c = ap.ask("P37", q)
print("40 포함:", "40" in a)
print("70 포함:", "70" in a)
print("계열 포함:", "계열" in a)
print("-" * 50)
print(a[:600])
