# -*- coding: utf-8 -*-
"""patch_v128.py — v127(27e76a37) main.py 에 v12.8 적용.
  원리금보장형 정밀화 넛지(추천 프롬프트): '원금 손실 거의 없음' 뭉뚱그림·일반 투자위험 덧붙임 금지,
  '원리금(원금+약정이자) 보장'과 보장 조건을 정확히 밝히도록. (G11 '보장 vs 리스크' 모순 대응)
자동백업·자가검증. 이미 v12.8이면 스킵. 검증 md5==cdfe8f33bb2797d20a0e662cd69d18ab"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='27e76a370e8194d184695d1a80420fb2'
EXPECT_AFTER='cdfe8f33bb2797d20a0e662cd69d18ab'
HUNKS=[["            \"밝힌 뒤 유형 기준으로 안내해.\\n\"\n            \"- 채권혼합·채권형·원리금보장형 상품을 '공격적인 투자자에게 적합하다'고 포장하는 것은 \"\n            \"금지야. 상품의 위험 수준을 사실과 다르게 성향에 끼워 맞추지 마.\\n\"\n            \"- 사용자가 말한 성향과 원하는 자산 배분이 서로 어긋나면(예: '안정형'이라면서 \"\n            \"주식 비중 70%를 원함) 그대로 수용하지 말고, 그 배분이 실제로는 어떤 성향에 \"\n            \"해당하는지 먼저 짚어준 뒤 안내해.\\n\"\n", "            \"밝힌 뒤 유형 기준으로 안내해.\\n\"\n            \"- 채권혼합·채권형·원리금보장형 상품을 '공격적인 투자자에게 적합하다'고 포장하는 것은 \"\n            \"금지야. 상품의 위험 수준을 사실과 다르게 성향에 끼워 맞추지 마.\\n\"\n            # v12.8(G11): 원리금보장형은 '원금 손실 거의 없음'처럼 뭉뚱그리거나 일반 투자상품의\n            #   위험을 갖다 붙이지 말고, 보장 대상·조건을 정확히 밝혀라.\n            \"- 원리금보장형(예금·이율보증형 등) 상품을 안내할 때는 '원금 손실 위험이 거의 없다'처럼 \"\n            \"뭉뚱그리지 말고, '원리금(원금과 약정 이자)이 보장되는 상품'임을 분명히 하고 보장 조건\"\n            \"(만기 상환·중도해지 시 처리 등 자료에 있는 범위)을 함께 밝혀라. 원리금보장형에 \"\n            \"'그래도 일정 부분 리스크가 있다'는 식의 일반 투자상품 위험 서술을 덧붙이지 마라 \"\n            \"— 보장형의 성격과 모순되어 사실과 다르다.\\n\"\n            \"- 사용자가 말한 성향과 원하는 자산 배분이 서로 어긋나면(예: '안정형'이라면서 \"\n            \"주식 비중 70%를 원함) 그대로 수용하지 말고, 그 배분이 실제로는 어떤 성향에 \"\n            \"해당하는지 먼저 짚어준 뒤 안내해.\\n\"\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "v12.8(G11)" in src: print("[스킵] 이미 v12.8 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[경고] 적용전 md5가 예상 v127과 다름. 훅 매칭되면 계속.")
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v127_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
