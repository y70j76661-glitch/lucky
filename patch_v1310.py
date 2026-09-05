# -*- coding: utf-8 -*-
"""patch_v1310.py — v139(0bfe0c80) main.py 에 v13.10 적용.
  [제도 프롬프트 한 줄 넛지 — 기능 확장 아님, 근거 없는 후속 결과 단정 제한]
   "기한을 지키지 못했을 때의 불이익·해지·중도인출·혜택 상실 등 후속 결과는 근거 문서에 명시된 경우에만
    설명하라. 문서에 없으면 추정하지 말고 확인할 수 없다고 밝혀라." (실측 V02 환각의 생성 원인 차단)
   코드 경로 불변. 회귀에서 기존 정상 답변이 바뀌면 main.py.bak_v139_* 로 롤백.
자동백업·자가검증. 이미 v13.10이면 스킵. 검증 md5==791990d6ca2f3ed18306f14ec677894c"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='0bfe0c80b78da76944d67924ac41caa5'
EXPECT_AFTER='791990d6ca2f3ed18306f14ec677894c'
HUNKS=[["            \"있지만, 세액공제는 종합소득(근로·사업 등)이 있어야 받을 수 있다. IRP는 직장인·\"\n            \"자영업자·직역연금가입자 등 가입 대상이 정해져 있다. 소득이 없는 사람(예: 전업주부)이 \"\n            \"물으면 IRP 가입 가능 여부를 먼저 밝히고, 연금저축이라는 대안과 \"\n            \"'세액공제는 소득이 있어야 가능'하다는 점을 반드시 함께 안내해라.\"\n        ),\n    },\n    \"세제\": {\n", "            \"있지만, 세액공제는 종합소득(근로·사업 등)이 있어야 받을 수 있다. IRP는 직장인·\"\n            \"자영업자·직역연금가입자 등 가입 대상이 정해져 있다. 소득이 없는 사람(예: 전업주부)이 \"\n            \"물으면 IRP 가입 가능 여부를 먼저 밝히고, 연금저축이라는 대안과 \"\n            \"'세액공제는 소득이 있어야 가능'하다는 점을 반드시 함께 안내해라.\\n\"\n            # v13.10(V02): 60일 기한 문맥에서 문서의 다른 문맥(55세 전 중도인출 시 해지)을 이어 붙여\n            #   '기한 놓치면 이전 불가·해지해야'로 단정한 실측 환각. 후속 결과는 근거 있을 때만.\n            \"- 기한을 지키지 못했을 때의 불이익·해지·중도인출·혜택 상실 등 후속 결과는 근거 문서에 \"\n            \"그 내용이 명시된 경우에만 설명해라. 문서에 없으면 추정해서 말하지 말고 \"\n            \"'자료에서 확인할 수 없다'고 밝혀라.\"\n        ),\n    },\n    \"세제\": {\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "v13.10(V02)" in src: print("[스킵] 이미 v13.10 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[경고] 적용전 md5가 예상 v139와 다름. 훅 매칭되면 계속.")
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v139_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
