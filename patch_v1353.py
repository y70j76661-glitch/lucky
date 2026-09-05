# -*- coding: utf-8 -*-
"""patch_v1353.py — v1352(58844e5d) main.py 에 v13.53 적용. (v1352 적용 후 실행)
  [mini30 실측] ① 정답표 등급 교정이 다른 상품(TDF2045 등) 줄까지 덮던 오류 차단(T6 요약 'TDF2045 … 2등급(높은위험)') ② 비교 우열 필터에
   '상대적으로 낮은 위험등급' 단정 포함(근거 없는 상품이면 제거) ③ 사례 머리말 판정(NUMHEAD)은 줄 끝 근처만 — '…성향을 가지셨기 때문에 이 펀드가 적합' 문장이 계약을 비켜가던 문제(T11)
자동백업·자가검증. 이미 v13.53이면 스킵. 검증 md5==2eff73b366d4e3c35df1df844ec234ae"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='58844e5d04036d7fc77357018c29f1a3'
EXPECT_AFTER='2eff73b366d4e3c35df1df844ec234ae'
HUNKS=[["                elif _mine or (len(hits) == 1 and not _other and \"등급\" in ln):\n                    ln = re.sub(r\"(\\d)\\s*등급(\\s*\\([^)]{2,12}\\))?\", _grade_fix, ln)", "                elif _mine or (len(hits) == 1 and not _other and \"등급\" in ln\n                               and not (_PROD_SPAN.search(ln) or _PROD_CITE.search(ln) or re.search(r\"TDF\\s*\\d{4}|ETF|리츠\", ln))):   # v13.53(T6): 다른 상품 줄은 덮지 않음\n                    ln = re.sub(r\"(\\d)\\s*등급(\\s*\\([^)]{2,12}\\))?\", _grade_fix, ln)"], ["                            _m = re.search(r\"보다\\s*(?:위험(?:등급|도)?이\\s*)?(?:더\\s*)?(높|낮)\", _s)\n                            if _m and re.search(r\"등급|위험\", _s):", "                            _m = re.search(r\"보다\\s*(?:위험(?:등급|도)?이\\s*)?(?:더\\s*)?(높|낮)\", _s) \\\n                                or re.search(r\"(?:상대적으로|비교적|더|가장)\\s*(낮|높)은\\s*위험\\s*등급\", _s)      # v13.53(T6): '상대적으로 낮은 위험등급' 단정\n                            if _m and re.search(r\"등급|위험\", _s):"], ["    NUMHEAD = re.compile(r\"^\\s*\\d+[.)]\\s*\\**[^\\n]{0,90}(?:경우|성향|선호|중시|원하)\")", "    NUMHEAD = re.compile(r\"^\\s*\\d+[.)]\\s*\\**[^\\n]{0,90}(?:경우|성향|선호|중시|원하)[^\\n.!?]{0,14}$\")   # v13.53(T11): 머리말은 줄 끝 근처('… 성향을 가지셨기 때문에 … 적합' 문장은 제외)"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "v13.53(T6): 다른 상품 줄은" in src: print("[스킵] 이미 v13.53 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[경고] 적용전 md5가 예상 v1352와 다름. 훅 매칭되면 계속.")
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v1352_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
