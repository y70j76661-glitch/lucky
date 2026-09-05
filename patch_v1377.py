# -*- coding: utf-8 -*-
"""patch_v1377.py — v1376(cbfe70e3) main.py 에 v13.77 적용. (v1376 적용 후 실행)
  [mini53] S4: 코드 표준 문장 뒤에 LLM이 붙이는 인과 연결('이는 … 손익을 통산하기 때문입니다')은 논리 오귀속 → 제거
자동백업·자가검증. 이미 v13.77이면 스킵. 검증 md5==31467c2cbbd23b0ba70c3f20fedc4c3f"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='cbfe70e3b0a7ae9a9e3a29003dfd7891'
EXPECT_AFTER='31467c2cbbd23b0ba70c3f20fedc4c3f'
HUNKS=[["                    if re.search(r\"통산|상계\", s_) and not re.search(r\"통산|상계\", _docs_t):\n                        _n19 += 1; continue\n", "                    if re.search(r\"통산|상계\", s_) and not re.search(r\"통산|상계\", _docs_t):\n                        _n19 += 1; continue\n                    if re.search(r\"통산|상계\", s_) and re.search(r\"^\\s*(?:이는|이것은|그\\s*이유는)|때문입니다\\s*$\", s_):   # v13.77: 코드 문장 뒤에 붙는 LLM 인과 연결('이는 … 통산하기 때문')은 논리 오귀속 → 제거\n                        _n19 += 1; continue\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "v13.77: 코드 문장 뒤에" in src: print("[스킵] 이미 v13.77 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[중단] 적용전 md5가 예상 v1376과 다름 → 서버 파일이 갈라짐. main_v1377_full.py 로 통째 교체하세요."); sys.exit(4)
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v1376_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
