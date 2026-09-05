# -*- coding: utf-8 -*-
"""patch_v1340.py — v1339(1c4f2432) main.py 에 v13.40 적용. (v1339 적용 후 실행)
  [S1] 비교표 위험등급 행('낮음; 높음')을 정답표 등급으로 채우는 규칙이 마크다운 표(| 위험등급 | … |) 단계에서 동작하도록 보강.
자동백업·자가검증. 이미 v13.40이면 스킵. 검증 md5==b1b569e2603ee6590d36b41c792f1e6d"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='1c4f2432e47e6c405e89d131623411ec'
EXPECT_AFTER='b1b569e2603ee6590d36b41c792f1e6d'
HUNKS=[["            # v13.38(S1 실측): 표의 상품이 정답표(PRODUCT_FACTS, 코퍼스 확인값)에 있고 표 등급이 정답표와 같으면\n            #   '원문 대조 불가' 고지는 사실이 아니므로 제거한다(대조가 코드로 이미 된 것).\n            if RISK_WARN_MARK in ans and _pf_hits and len(_pf_hits) >= 2:\n                _hd = next((ln for ln in ans.splitlines() if re.search(r\"\\bvs\\b\", ln)), \"\")\n                _ordered = sorted([f for f in _pf_hits if re.search(f[\"key\"], _hd)], key=lambda f: re.search(f[\"key\"], _hd).start())\n                # v13.39: 비교표의 위험등급 행이 '낮음; 높음'처럼 숫자 없이 나오면 정답표 등급(머리말 순서)으로 채운다\n                if len(_ordered) == len(_pf_hits) >= 2:\n                    _row = \"- 위험등급: \" + \"; \".join(f[\"grade\"] for f in _ordered)\n                    ans, _nr = re.subn(r\"(?m)^\\s*-\\s*위험\\s*등급\\s*[:：][^\\n]*$\", _row, ans, count=1)\n                    if _nr:\n                        clean_note += \" 위험등급 행 정답표로 확정\"\n                _facts_ok = all((re.match(r\"(\\d)\", f[\"grade\"]).group(1) + \"등급\") in ans.replace(\" \", \"\")\n", "            # v13.38(S1 실측): 표의 상품이 정답표(PRODUCT_FACTS, 코퍼스 확인값)에 있고 표 등급이 정답표와 같으면\n            #   '원문 대조 불가' 고지는 사실이 아니므로 제거한다(대조가 코드로 이미 된 것).\n            if RISK_WARN_MARK in ans and _pf_hits and len(_pf_hits) >= 2:\n                _hd = next((ln for ln in ans.splitlines() if re.search(r\"\\bvs\\b\", ln) or re.match(r\"^\\s*\\|\\s*(?:비교\\s*)?항목\\s*\\|\", ln)), \"\")\n                _ordered = sorted([f for f in _pf_hits if re.search(f[\"key\"], _hd)], key=lambda f: re.search(f[\"key\"], _hd).start())\n                # v13.39/40: 비교표의 위험등급 행이 '낮음; 높음'처럼 숫자 없이 나오면 정답표 등급(머리말 순서)으로 채운다(마크다운 표 형태 포함)\n                if len(_ordered) == len(_pf_hits) >= 2:\n                    _nr = 0\n                    if _hd.lstrip().startswith(\"|\"):\n                        _row = \"| 위험등급 | \" + \" | \".join(f[\"grade\"] for f in _ordered) + \" |\"\n                        ans, _nr = re.subn(r\"(?m)^\\s*\\|\\s*위험\\s*등급\\s*\\|[^\\n]*$\", _row, ans, count=1)\n                    else:\n                        _row = \"- 위험등급: \" + \"; \".join(f[\"grade\"] for f in _ordered)\n                        ans, _nr = re.subn(r\"(?m)^\\s*-\\s*위험\\s*등급\\s*[:：][^\\n]*$\", _row, ans, count=1)\n                    if _nr:\n                        clean_note += \" 위험등급 행 정답표로 확정\"\n                _facts_ok = all((re.match(r\"(\\d)\", f[\"grade\"]).group(1) + \"등급\") in ans.replace(\" \", \"\")\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "v13.39/40: 비교표의 위험등급 행" in src: print("[스킵] 이미 v13.40 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[경고] 적용전 md5가 예상 v1339과 다름. 훅 매칭되면 계속.")
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v1339_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
