# -*- coding: utf-8 -*-
"""patch_v135.py — v134(68b79e50) main.py 에 v13.5 적용.
  [OP1/G12 60일 조건 누락] 기한 각주(v12.0 경로)가 고유어 '넣으면/넣고/넣으려/넣어야'를
  '납입/입금'과 같은 절차로 인식하도록 동의어 1개 추가. '넣어준/넣어주'(회사가 넣어준 DC, A12)는
  명시 제외 → 오부착 재발 방지. 기존 '이전하면' 경로·관형어 제외는 바이트 동일(무변경).
자동백업·자가검증. 이미 v13.5면 스킵. 검증 md5==c753b27153c031bdfc36920d061cf37b"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='68b79e50ac9aaa415bd4f0acae02fbaa'
EXPECT_AFTER='c753b27153c031bdfc36920d061cf37b'
HUNKS=[["        for a in _DL_ACT:\n            if a in t and a in question and re.search(re.escape(a) + _DL_VERB, question):\n                return \"· 참고: \" + t.strip().lstrip(\"…\").rstrip(\"…\")\n    return None\n\n\n", "        for a in _DL_ACT:\n            if a in t and a in question and re.search(re.escape(a) + _DL_VERB, question):\n                return \"· 참고: \" + t.strip().lstrip(\"…\").rstrip(\"…\")\n        # v13.5(OP1): 고유어 '넣으면/넣고/넣으려/넣어야'(내가 넣는 행위)는 문장의 '납입/입금'과\n        #   같은 절차다(실측 OP1·G12 '연금계좌에 넣으면 절세' → 60일 조건 누락). 단 '넣어준/넣어주'\n        #   (회사가 넣어준 DC 부담금, A12)는 남이 넣는 관형·수혜 표현이라 제외해 오부착 재발 방지.\n        if re.search(r\"넣(?:으면|으려|어야|을|는다|고)\", question) \\\n                and not re.search(r\"넣어\\s*(?:준|주)\", question) \\\n                and re.search(r\"납입|입금\", t):\n            return \"· 참고: \" + t.strip().lstrip(\"…\").rstrip(\"…\")\n    return None\n\n\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "v13.5(OP1)" in src: print("[스킵] 이미 v13.5 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[경고] 적용전 md5가 예상 v134와 다름. 훅 매칭되면 계속.")
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v134_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
