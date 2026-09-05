# -*- coding: utf-8 -*-
"""rf_probe.py — API 호출 없음. 서버 main.py의 recommend_finalize / _rr_evidence 가 실제로 어떻게 동작하는지 확인(T11 '수상 경력' 잔존 원인 추적).
사용: python rf_probe.py"""
import re, hashlib, inspect
import main as M
print("main.py md5:", hashlib.md5(open("main.py", "rb").read()).hexdigest())
src = inspect.getsource(M.recommend_finalize)
print("PROMO 분기:", [l.strip() for l in src.splitlines() if "_RF_PROMO.search" in l])
T11 = ("30대 직장인이시고, 공격적인 투자를 선호하신다면 차이나리치투게더연금펀드를 후보로 검토하실 수 있습니다.\n"
       " - 근거 문서: R2_KR516702010M.pdf — 위험등급 2등급(높은위험)\n"
       " - 유의: 차이나리치투게더연금펀드은(는) 실적배당형으로, 투자원금과 수익(분배금)은 보장되지 않습니다.\n\n"
       "1. 투자 특징: 이 펀드는 중국을 중심으로 한 아시아 지역에 투자하는 상품입니다.\n"
       "2. 또한, 이 펀드는 과거 여러 수상 경력이 있어 성과를 인정받은 바 있습니다.\n"
       "3. 유의 사항: 중국 시장의 변동성이 크고 정치적 리스크가 존재하므로, 이러한 점들을 유의하셔야 합니다.\n")
out, note = M.recommend_finalize(T11, [], "30대 직장인인데 공격적으로 굴릴 연금펀드 하나 추천해줘")
print("finalize note:", repr(note), "| 수상 잔존:", "수상" in out)
used = [{"source": "R2_KR516702010M.pdf", "text": M._src_text("R2_KR516702010M.pdf")[:4000]}]
for nm in ["차이나리치투게더연금펀드", "에셋플러스 코리아 리치투게더 연금 증권 자투자신탁 1호(주식)"]:
    print("_rr_evidence", nm, "->", M._rr_evidence(nm, used, {"R2_KR516702010M.pdf"}))
t = re.sub(r"\s+", "", M._src_text("R2_KR516702010M.pdf"))
print("R2_KR516702010M head:", t[:150]); print("  '차이나리치투게더' pos:", t.find("차이나리치투게더"), "| '코리아리치투게더' pos:", t.find("코리아리치투게더"))
for nm in ["미래에셋 TDF2030", "미래에셋 TDF2050", "삼성클래식연금증권전환형자투자신탁 제1호[주식]"]:
    print("_grade_evidence", nm, "->", M._grade_evidence(nm))
