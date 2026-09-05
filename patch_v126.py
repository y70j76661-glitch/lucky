# -*- coding: utf-8 -*-
"""patch_v126.py — v125(a6c8c33f) main.py 에 v12.6 적용.
  최종 답변에서 마크다운 볼드 마커('**') 제거 — 평가/표시 화면이 raw 텍스트여도 '**'가
  글자로 노출되지 않도록. 내용·숫자·간격은 불변. (_final_cleanup 마지막 단계 한 줄)
자동백업·자가검증. 이미 v12.6면 스킵. 검증 md5==5d53e2d0f1f60cecccca1e0bf5c8585f"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='a6c8c33f71544156b67b0c446412e64d'
EXPECT_AFTER='5d53e2d0f1f60cecccca1e0bf5c8585f'
HUNKS=[["    # F) 선두 빈 줄 제거 + 과다 빈 줄 축소\n    ans = re.sub(r\"^\\s*\\n+\", \"\", ans)\n    ans = re.sub(r\"\\n{3,}\", \"\\n\\n\", ans)\n    return ans.strip()\n\n\n", "    # F) 선두 빈 줄 제거 + 과다 빈 줄 축소\n    ans = re.sub(r\"^\\s*\\n+\", \"\", ans)\n    ans = re.sub(r\"\\n{3,}\", \"\\n\\n\", ans)\n    # G) v12.6: 마크다운 볼드 마커 제거 — 평가/표시 화면이 raw 텍스트여도 '**'가 글자로\n    #    노출되지 않도록 최종 답변에서 볼드 마커만 뗀다(내용·숫자·간격은 그대로).\n    ans = ans.replace(\"**\", \"\")\n    return ans.strip()\n\n\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "v12.6:" in src: print("[스킵] 이미 v12.6 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[경고] 적용전 md5가 예상 v125와 다름. 훅 매칭되면 계속.")
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v125_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
