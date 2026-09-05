# -*- coding: utf-8 -*-
"""patch_v1323.py — v1322(5f4c07a6) main.py 에 v13.23 적용. (v1322 적용 후 실행)
  [S4b 실측] '자료에서 확인할 수 없다'고 한 답변에 붙은 '대략적인 범위를 예상/추정할 수는 있지만 … 일반적인 경향'
   문장 제거(근거 없는 여지). 문장 삭제만, 값·의미 재해석 없음. 자료에 없다는 고백이 없는 답변은 불변.
자동백업·자가검증. 이미 v13.23이면 스킵. 검증 md5==236cc642f7320ecd8c9e6a5eb6f4aa81"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='5f4c07a60050e568fb75e7619a132e63'
EXPECT_AFTER='236cc642f7320ecd8c9e6a5eb6f4aa81'
HUNKS=[["        _keep = []\n        for _s in _sents:\n            _bad = (re.search(r\"(?:놓치|놓쳤|지나|경과)[^.!?]*이전(?:이|은|도|은)?\\s*(?:불가능|불가|할\\s*수\\s*없|안\\s*됩)\", _s)\n                    or re.search(r\"계좌를\\s*해지[^.!?]*(?:되찾|기한|기간|60\\s*일)|(?:되찾|기한|기간|60\\s*일)[^.!?]*계좌를\\s*해지\", _s))\n            if _bad:\n                _dropped = True\n                continue\n", "        _keep = []\n        for _s in _sents:\n            _bad = (re.search(r\"(?:놓치|놓쳤|지나|경과)[^.!?]*이전(?:이|은|도|은)?\\s*(?:불가능|불가|할\\s*수\\s*없|안\\s*됩)\", _s)\n                    or re.search(r\"계좌를\\s*해지[^.!?]*(?:되찾|기한|기간|60\\s*일)|(?:되찾|기한|기간|60\\s*일)[^.!?]*계좌를\\s*해지\", _s)\n                    # K3b v13.23(S4b 실측): '자료에 없다' 뒤 '대략적인 … 예상/추정할 수는 있지만 … 일반적인 경향' — 근거 없는 여지\n                    or (re.search(r\"(?:예상|추정|짐작)할\\s*수는?\\s*있(?:지만|으나|습니다)\", _s) and _NOINFO.search(ans)))\n            if _bad:\n                _dropped = True\n                continue\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "K3b v13.23" in src: print("[스킵] 이미 v13.23 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[경고] 적용전 md5가 예상 v1322과 다름. 훅 매칭되면 계속.")
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v1322_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
