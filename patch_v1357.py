# -*- coding: utf-8 -*-
"""patch_v1357.py — v1356(9b248654) main.py 에 v13.57 적용. (v1356 적용 후 실행)
  [표현 2건] ① 비교표 상품 중 일부만 등급이 확정되면 '투자설명서를 찾지 못했습니다' 일괄 고지 대신 확정/미확정을 나눠 사실대로 고지(T6)
   ② 추천 마무리 계약에 '사용자에게 어울립니다' → '사용자가 검토할 수 있는 후보입니다'(T11)
자동백업·자가검증. 이미 v13.57이면 스킵. 검증 md5==a46cea0ba2878cc2111a60488e8a6ea5"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='9b248654ec4e712ec55f662630cf64f7'
EXPECT_AFTER='a46cea0ba2878cc2111a60488e8a6ea5'
HUNKS=[["                if all(g for _, g in _ge) and RISK_WARN_MARK in ans:\n                    ans = re.sub(r\"\\n*\\[위험등급 원문 대조[^\\n]*\", \"\", ans)\n                    clean_note += \" (근거 등급 확정으로 대조 불가 고지 제거)\"", "                if all(g for _, g in _ge) and RISK_WARN_MARK in ans:\n                    ans = re.sub(r\"\\n*\\[위험등급 원문 대조[^\\n]*\", \"\", ans)\n                    clean_note += \" (근거 등급 확정으로 대조 불가 고지 제거)\"\n                elif any(g for _, g in _ge) and RISK_WARN_MARK in ans:\n                    # v13.57(T6 실측): 일부만 확정됐으면 '투자설명서를 찾지 못했다'는 일괄 고지 대신 확정/미확정을 나눠 사실대로 적는다\n                    _okn = [f\"{_nm} {_g}\" for _nm, _g in _ge if _g]\n                    _unk = [_nm for _nm, _g in _ge if not _g]\n                    _msg = (RISK_WARN_MARK + \" 결과] \" + \", \".join(_okn) + \"은(는) 근거 문서에서 확인되었으나, \" + \", \".join(_unk) +\n                            \"은(는) 제공 자료에 동일·유사 계열 정보가 복수 있거나 해당 투자설명서를 특정하지 못해 위험등급을 하나의 값으로 확정하지 못했습니다. \"\n                            \"가입 전 해당 상품의 투자설명서에서 위험등급을 직접 확인하시기 바랍니다.\")\n                    ans = re.sub(r\"\\[위험등급 원문 대조[^\\n]*\", lambda m_: _msg, ans, count=1)\n                    clean_note += \" (대조 고지를 확정/미확정 구분으로 교체)\""], ["    (re.compile(r\"추천\\s*상품\\s*[:：]\"), \"검토 후보:\"),\n]", "    (re.compile(r\"추천\\s*상품\\s*[:：]\"), \"검토 후보:\"),\n    (re.compile(r\"(사용자|투자자)(?:들)?(?:에게|께)\\s*(?:잘\\s*)?어울립니다\"), r\"\\1가 검토할 수 있는 후보입니다\"),          # v13.57(T11)\n    (re.compile(r\"(분)(?:들)?(?:에게|께)\\s*(?:잘\\s*)?어울립니다\"), r\"\\1이 검토할 수 있는 후보입니다\"),\n    (re.compile(r\"(?:에|에게)\\s*(?:잘\\s*)?어울리는\\s*(상품|펀드)입니다\"), r\"에서 검토할 수 있는 \\1입니다\"),\n]"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "v13.57(T6 실측)" in src: print("[스킵] 이미 v13.57 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[경고] 적용전 md5가 예상 v1356과 다름. 훅 매칭되면 계속.")
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v1356_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
