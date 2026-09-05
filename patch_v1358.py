# -*- coding: utf-8 -*-
"""patch_v1358.py — v1357(a46cea0b) main.py 에 v13.58 적용. (v1357 적용 후 실행)
  [검증값 전파 — 표 셀] 비교표 상품 중 근거 등급을 확정하지 못했고 원문 대조도 실패한 상품의 등급 셀은 LLM 값(예: '2등급(높은위험)')을 두지 않고
   '자료에서 확정하지 못함'으로 표기(T6: 고지는 '미확정'인데 표는 '2등급'이던 불일치 제거)
자동백업·자가검증. 이미 v13.58이면 스킵. 검증 md5==52f336444cf7adf46ef090976984b955"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='a46cea0ba2878cc2111a60488e8a6ea5'
EXPECT_AFTER='52f336444cf7adf46ef090976984b955'
HUNKS=[["                        if not _g:\n                            if re.search(r\"\\d\\s*등급[^;]*\\d\\s*등급\", _vals[_j]) or len(re.findall(r\"위험\\)\", _vals[_j])) >= 2 or re.search(r\"등급[^;]*/\\s*\\(\", _vals[_j]):\n                                _vals[_j] = \"자료에서 확정하지 못함(표기 상충)\"; _nfix += 1      # v13.52(T6): 근거 없는 상충 셀은 단정하지 않는다\n                            continue", "                        if not _g:\n                            if re.search(r\"\\d\\s*등급[^;]*\\d\\s*등급\", _vals[_j]) or len(re.findall(r\"위험\\)\", _vals[_j])) >= 2 or re.search(r\"등급[^;]*/\\s*\\(\", _vals[_j]):\n                                _vals[_j] = \"자료에서 확정하지 못함(표기 상충)\"; _nfix += 1      # v13.52(T6): 근거 없는 상충 셀은 단정하지 않는다\n                            elif RISK_WARN_MARK in ans and re.search(r\"\\d\\s*등급\", _vals[_j]):\n                                _vals[_j] = \"자료에서 확정하지 못함\"; _nfix += 1                  # v13.58 [검증값 전파]: 원문 대조도 실패한 상품의 등급 셀은 값으로 두지 않는다\n                            continue"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "v13.58 [검증값 전파]" in src: print("[스킵] 이미 v13.58 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[경고] 적용전 md5가 예상 v1357과 다름. 훅 매칭되면 계속.")
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v1357_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
