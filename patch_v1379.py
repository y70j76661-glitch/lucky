# -*- coding: utf-8 -*-
"""patch_v1379.py — v1378(3c63f433) main.py 에 v13.79 적용. (v1378 적용 후 실행) — 기준 mini55 대비 유형별 소수정
  ① 계산 답변(C2): '총 N만원의 세액공제를…' 교체 시 '총' 잔재 제거 ② DB/DC 질문(S1): '현행 퇴직금 제도와 동일하게 … 일정한 금액을 보장받습니다' 변형 완화, '퇴직 시 받을 연금액' → 퇴직급여
자동백업·자가검증. 이미 v13.79이면 스킵. 검증 md5==b43e9f18629365d7f86d302d0019f18f"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='3c63f433923ab4b6943ec1bf388d3fea'
EXPECT_AFTER='b43e9f18629365d7f86d302d0019f18f'
HUNKS=[["        ans, _n23 = re.subn(r\"(?:약\\s*)?([\\d.,]+\\s*만\\s*원)의\\s*세액\\s*공제를\\s*받으실\\s*수\\s*있습니다\",\n", "        ans, _n23 = re.subn(r\"(?:총\\s*)?(?:약\\s*)?([\\d.,]+\\s*만\\s*원)의\\s*세액\\s*공제를\\s*받으실\\s*수\\s*있습니다\",   # v13.79: '총' 잔재 제거\n"], ["            ans = re.sub(r\"(?:이는\\s*)?(?:현행|기존)\\s*퇴직금\\s*제도와\\s*동일한\\s*방식입니다\", \"급여 산정 구조가 확정급여형이라는 점에서 기존 퇴직금 제도와 유사합니다\", ans)\n", "            ans = re.sub(r\"(?:이는\\s*)?(?:현행|기존)\\s*퇴직금\\s*제도와\\s*동일한\\s*방식입니다\", \"급여 산정 구조가 확정급여형이라는 점에서 기존 퇴직금 제도와 유사합니다\", ans)\n            ans = re.sub(r\"(?:이는\\s*)?(?:현행|기존)\\s*퇴직금\\s*제도와\\s*동일하게,?\\s*\", \"급여 산정 구조가 확정급여형이라는 점에서 기존 퇴직금 제도와 유사하게, \", ans)   # v13.79\n            ans = re.sub(r\"일정한\\s*금액을\\s*보장받습니다\", \"사전에 정해진 산식에 따른 퇴직급여를 받습니다\", ans)\n            ans = re.sub(r\"퇴직\\s*시(?:의)?\\s*(?:받을\\s*)?연금액(이|은|가|는)?\", lambda m_: \"퇴직 시 받을 퇴직급여\" + {\"이\": \"가\", \"은\": \"는\"}.get(m_.group(1) or \"\", m_.group(1) or \"\"), ans)\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "# v13.79: '총' 잔재 제거" in src: print("[스킵] 이미 v13.79 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[중단] 적용전 md5가 예상 v1378과 다름 → 서버 파일이 갈라짐. main_v1379_full.py 로 통째 교체하세요."); sys.exit(4)
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v1378_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
