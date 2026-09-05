# -*- coding: utf-8 -*-
"""grade_probe.py — API 호출 없음. 서버 main.py의 _grade_evidence가 상품명→등급을 어느 문서에서 읽는지 확인(v13.62 머리 영역 규칙 회귀 점검).
사용: python grade_probe.py"""
import re
import main as M

NAMES = ["삼성클래식연금증권전환형자투자신탁 제1호[주식]", "삼성클래식연금증권전환형투자신탁 제1호[채권]", "미래에셋 TDF2045",
         "미래에셋 TDF2030", "미래에셋 TDF2050", "삼성퇴직연금인덱스12M", "미래애셋퇴직플랜증권자투자신탁1호(주식)".replace("애", "에"),
         "에셋플러스 코리아 리치투게더 연금 증권 자투자신탁 1호(주식)", "하나IT코리아증권자투자신탁(제1호)[주식]", "NH-Amundi 하나로 단기채"]
print("== _grade_evidence (prefer=None) ==")
for n in NAMES:
    try:
        print(f"  {n!r:60} -> {M._grade_evidence(n)}")
    except Exception as e:
        print(f"  {n!r:60} -> ERR {type(e).__name__}: {e}")
print("== 문서 머리·등급 (TDF 관련 R2_) ==")
items = dict(M._src_norm_items())
for s, t in items.items():
    if re.search(r"TDF|타겟데이트|목표시점", t[:3000]) or s in ("R2_KR510902777M.pdf", "R2_KR5129420025.pdf", "R2_KR5114450222.pdf"):
        g = M._read_grade(M._src_text(s))
        pos = {k: t.find(k) for k in ("TDF2030", "TDF2045", "TDF2050", "미래에셋", "삼성") if k in t}
        print(f"  {s}: grade={g} pos={pos}\n     head={t[:160]}")
