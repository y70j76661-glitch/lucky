# -*- coding: utf-8 -*-
"""patch_v1339.py — v1338(cea136d9) main.py 에 v13.39 적용. (v1338 적용 후 실행)
  [S1 비교 실측] 비교표 머리말 한 줄에 상품이 둘('A … vs B …')이면 정답표 등급 교정이 다른 상품 등급까지 덮어쓰던 오류
   (주식형이 5등급으로 표기) → 각 상품 이름 뒤 ~ 다음 상품 이름 앞 구간에서만 교정. '- 위험등급: 낮음; 높음'처럼 숫자 없는 행은
   정답표 등급(머리말 순서)으로 확정. 정답표 등급이 답변에 모두 있으면 '원문 대조 불가' 고지(거짓) 제거.
자동백업·자가검증. 이미 v13.39면 스킵. 검증 md5==1c4f2432e47e6c405e89d131623411ec"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='cea136d92709df500b54fc825f6d32b2'
EXPECT_AFTER='1c4f2432e47e6c405e89d131623411ec'
HUNKS=[["            _others = [o for o in PRODUCT_FACTS if o is not f]\n            out = []\n            for ln in body.split(\"\\n\"):\n                _mine = bool(re.search(f[\"key\"], ln))\n                _other = any(re.search(o[\"key\"], ln) for o in _others)\n                if _mine or (len(hits) == 1 and not _other and \"등급\" in ln):\n                    ln = re.sub(r\"(\\d)\\s*등급(\\s*\\([^)]{2,12}\\))?\", _grade_fix, ln)\n                out.append(ln)\n            body = \"\\n\".join(out)\n", "            _others = [o for o in PRODUCT_FACTS if o is not f]\n            out = []\n            for ln in body.split(\"\\n\"):\n                _mm = re.search(f[\"key\"], ln)\n                _mine = bool(_mm)\n                _other_pos = [o_m.start() for o in _others for o_m in [re.search(o[\"key\"], ln)] if o_m]\n                _other = bool(_other_pos)\n                if _mine and _other:\n                    # v13.39(S1 실측): 한 줄에 상품이 둘 이상(비교표 머리말 'A … vs B …')이면 이 상품의 이름 뒤 ~ 다음 상품 이름 앞\n                    #   구간에서만 등급을 교정한다(다른 상품 등급을 덮어쓰던 오류 차단)\n                    _st = _mm.end()\n                    _en = min([p_ for p_ in _other_pos if p_ > _st] or [len(ln)])\n                    ln = ln[:_st] + re.sub(r\"(\\d)\\s*등급(\\s*\\([^)]{2,12}\\))?\", _grade_fix, ln[_st:_en]) + ln[_en:]\n                elif _mine or (len(hits) == 1 and not _other and \"등급\" in ln):\n                    ln = re.sub(r\"(\\d)\\s*등급(\\s*\\([^)]{2,12}\\))?\", _grade_fix, ln)\n                out.append(ln)\n            body = \"\\n\".join(out)\n"], ["            clean_note += _rnote\n            # v13.38(S1 실측): 표의 상품이 정답표(PRODUCT_FACTS, 코퍼스 확인값)에 있고 표 등급이 정답표와 같으면\n            #   '원문 대조 불가' 고지는 사실이 아니므로 제거한다(대조가 코드로 이미 된 것).\n            if RISK_WARN_MARK in ans and _pf_hits and len(_pf_hits) >= 1:\n                _tbl = next((ln for ln in ans.splitlines() if re.search(r\"위험\\s*등급\", ln) and (ln.count(\"|\") >= 2 or ln.count(\";\") >= 1)), \"\")\n                _facts_ok = all((re.match(r\"(\\d)\", f[\"grade\"]) and re.match(r\"(\\d)\", f[\"grade\"]).group(1) + \"등급\" in _tbl.replace(\" \", \"\"))\n                                for f in _pf_hits if re.match(r\"\\d\", f[\"grade\"]))\n                if _tbl and _facts_ok:\n                    ans = re.sub(r\"\\n*\\[위험등급 원문 대조[^\\n]*\", \"\", ans)\n                    clean_note += \" (정답표 일치로 대조 불가 고지 제거)\"\n        # v9.99f: 카테고리 비교(TDF·원리금보장형 등)라 원문 상품을 못 찾으면\n", "            clean_note += _rnote\n            # v13.38(S1 실측): 표의 상품이 정답표(PRODUCT_FACTS, 코퍼스 확인값)에 있고 표 등급이 정답표와 같으면\n            #   '원문 대조 불가' 고지는 사실이 아니므로 제거한다(대조가 코드로 이미 된 것).\n            if RISK_WARN_MARK in ans and _pf_hits and len(_pf_hits) >= 2:\n                _hd = next((ln for ln in ans.splitlines() if re.search(r\"\\bvs\\b\", ln)), \"\")\n                _ordered = sorted([f for f in _pf_hits if re.search(f[\"key\"], _hd)], key=lambda f: re.search(f[\"key\"], _hd).start())\n                # v13.39: 비교표의 위험등급 행이 '낮음; 높음'처럼 숫자 없이 나오면 정답표 등급(머리말 순서)으로 채운다\n                if len(_ordered) == len(_pf_hits) >= 2:\n                    _row = \"- 위험등급: \" + \"; \".join(f[\"grade\"] for f in _ordered)\n                    ans, _nr = re.subn(r\"(?m)^\\s*-\\s*위험\\s*등급\\s*[:：][^\\n]*$\", _row, ans, count=1)\n                    if _nr:\n                        clean_note += \" 위험등급 행 정답표로 확정\"\n                _facts_ok = all((re.match(r\"(\\d)\", f[\"grade\"]).group(1) + \"등급\") in ans.replace(\" \", \"\")\n                                for f in _pf_hits if re.match(r\"\\d\", f[\"grade\"]))\n                if _facts_ok:\n                    ans = re.sub(r\"\\n*\\[위험등급 원문 대조[^\\n]*\", \"\", ans)\n                    clean_note += \" (정답표 일치로 대조 불가 고지 제거)\"\n        # v9.99f: 카테고리 비교(TDF·원리금보장형 등)라 원문 상품을 못 찾으면\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "v13.39(S1 실측)" in src: print("[스킵] 이미 v13.39 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[경고] 적용전 md5가 예상 v1338과 다름. 훅 매칭되면 계속.")
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v1338_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
