# -*- coding: utf-8 -*-
"""patch_v133.py — v132(d7a132e9) main.py 에 v13.3 적용.
  [CMP3 사실오류 교정] DB형을 '회사 운용 결과에 따라 퇴직금이 변한다'고 서술하는 오류를
  _FALSE_PREMISE 규칙으로 교정(코퍼스 근거 확인: DB=급여 사전확정·회사 운용·손익 회사 귀속).
  DC 정상 서술·DB 정상 서술은 보호. 교정문은 근거 문서 내용 그대로.
자동백업·자가검증. 이미 v13.3이면 스킵. 검증 md5==04a321f61ccd1be6cdaec1d519175c24"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='d7a132e91d5f1c5d56182ced85a1b876'
EXPECT_AFTER='04a321f61ccd1be6cdaec1d519175c24'
HUNKS=[["                r\"과세[\\s*_]*되지[\\s*_]*않|세금[\\s*_]*이[\\s*_]*없)[^\\n]*\"),\n     \"중도해지하면 세액공제를 받은 납입금과 운용수익에 대해 기타소득세 16.5%가 부과됩니다. \"\n     \"다만 세액공제를 받지 않은 납입금은 인출해도 세금이 없습니다.\"),\n]\n\n\n", "                r\"과세[\\s*_]*되지[\\s*_]*않|세금[\\s*_]*이[\\s*_]*없)[^\\n]*\"),\n     \"중도해지하면 세액공제를 받은 납입금과 운용수익에 대해 기타소득세 16.5%가 부과됩니다. \"\n     \"다만 세액공제를 받지 않은 납입금은 인출해도 세금이 없습니다.\"),\n    # v13.3(CMP3): DB형을 '회사 운용 결과에 따라 퇴직금이 변한다'고 쓰는 오류 교정.\n    #   문서 근거(코퍼스 실측): DB는 근로자 급여가 사전 확정(운용 결과와 무관), 회사가 적립금을\n    #   운용하고 운용 손익·적립금 부담 변동은 회사(사용자) 귀속. DC는 회사 부담금 확정, 근로자 운용.\n    #   '회사가 운용 + 급여가 변동'은 DB(급여 고정)에도 DC(근로자 운용)에도 맞지 않는 서술.\n    #   '근로자가 운용…급여 변동'(DC 정상 서술)은 '회사' 조건 때문에 매칭되지 않아 보호됨.\n    (re.compile(r\"[^\\n]*회사(?:의|가)?\\s*운용\\s*(?:결과|성과)[^\\n]{0,25}?(?:퇴직금|급여)\"\n                r\"[^\\n]{0,20}?(?:변|달라|결정|좌우)[^\\n]*\"),\n     \"DB형(확정급여형)은 근로자가 받을 급여가 사전에 확정되어 운용 결과와 무관하며, 회사가 적립금을 \"\n     \"운용하고 운용 손익은 회사에 귀속됩니다. DC형(확정기여형)은 회사 부담금이 사전에 확정되고 \"\n     \"근로자가 직접 운용하며 운용 결과가 근로자의 급여에 반영됩니다.\"),\n]\n\n\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "v13.3(CMP3)" in src: print("[스킵] 이미 v13.3 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[경고] 적용전 md5가 예상 v132와 다름. 훅 매칭되면 계속.")
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v132_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
