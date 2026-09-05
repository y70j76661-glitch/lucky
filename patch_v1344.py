# -*- coding: utf-8 -*-
"""patch_v1344.py — v1343(7059217c) main.py 에 v13.44 적용. (v1343 적용 후 실행)
  [펀드 서술 계약 정밀화 — 실측 mini21 R2] ① 표준 문장의 고위험형('변동성이 큰 편')은 문단 낱말이 아니라 상품의 근거 등급(정답표→R2_ 투자설명서)으로 결정
   (6등급 채권형에 고위험 문장이 붙던 오류 차단) ② 주어 추출은 띄어쓰기 상품명 전체(_PROD_SPAN) 우선('증권전환형자투자신탁은(는)' 조각 방지)
   ③ 원리금보장 계약: '원금과 약정된 이자를 보장해주는 특성' 형태도 보장 조건 표현으로
자동백업·자가검증. 이미 v13.44면 스킵. 검증 md5==2f7e30c03cced3c936a28189f382bd8a"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='7059217c6f9c19f3864d015acc3ac160'
EXPECT_AFTER='2f7e30c03cced3c936a28189f382bd8a'
HUNKS=[["_PB_CLAIM = re.compile(r\"(?:거의\\s*)?원금(?:이|을|은)?\\s*보장(?:되|하|이\\s*되)\")\n", "_PB_CLAIM = re.compile(r\"(?:거의\\s*)?원금(?:이|을|은)?\\s*보장(?:되|하|이\\s*되)\")\n\n# v13.44(R2 실측): 표준 문장의 '변동성이 큰 편'(고위험형)은 문단의 낱말이 아니라 상품의 근거 등급으로 정한다.\n#   정답표 → 코퍼스의 R2_ 투자설명서(상품명이 든 문서)의 '투자위험등급 N등급' 순. 근거가 없거나 문서마다 다르면 None(→ 문장·줄 낱말로 판단).\n_SRC_NORM_CACHE = {}\n\n\ndef _src_norm_items():\n    if not _SRC_NORM_CACHE:\n        _it = chunks if isinstance(chunks, list) else list(chunks.values())\n        for c in _it:\n            if isinstance(c, dict) and c.get(\"source\", \"\").startswith(\"R2_\"):\n                _SRC_NORM_CACHE[c[\"source\"]] = _SRC_NORM_CACHE.get(c[\"source\"], \"\") + re.sub(r\"\\s+\", \"\", c.get(\"text\", \"\"))\n    return _SRC_NORM_CACHE.items()\n\n\ndef _grade_hint(nm):\n    \"\"\"상품명 → 'hi'(1·2등급/높은위험) | 'lo' | None\"\"\"\n    fact = next((f for f in PRODUCT_FACTS if re.search(f[\"key\"], nm)), None)\n    if fact:\n        return \"hi\" if re.search(r\"^[12]\\s*등급|높은\\s*위험|매우\\s*높\", fact[\"grade\"]) else \"lo\"\n    key = re.sub(r\"\\s+\", \"\", nm).strip(\"·-'\\\"\")\n    if len(key) < 6:\n        return None\n    grades = set()\n    for s, t in _src_norm_items():\n        if key in t:\n            g, _ = _read_grade(_src_text(s))\n            if g is not None:\n                grades.add(g)\n    if len(grades) == 1:\n        return \"hi\" if next(iter(grades)) <= 2 else \"lo\"\n    return None\n"], ["        _hi = bool(HI_RISK.search(_para_text.get(_line_para[_li], \"\") + ln))\n", "        _hi = bool(HI_RISK.search(_para_text.get(_line_para[_li], \"\") + ln))\n        _pm_g = _PROD_SPAN.search(ln) or _PROD_SPAN.search(_para_text.get(_line_para[_li], \"\")) \\\n            or _PROD_CITE.search(ln) or _PROD_CITE.search(_para_text.get(_line_para[_li], \"\"))\n        if _pm_g:\n            _gh = _grade_hint(_pm_g.group(0).strip(\"·-'\\\"\"))\n            if _gh:\n                _hi = (_gh == \"hi\")                                  # v13.44: 근거 등급이 있으면 그 값으로(6등급 채권형에 '변동성이 큰 편' 방지)\n"], ["            pm = _PROD_CITE.search(body) or _PROD_SPAN.search(body)\n", "            pm = _PROD_SPAN.search(body) or _PROD_CITE.search(body)   # v13.44: 띄어쓰기 상품명은 전체 표기 우선('증권전환형자투자신탁은(는)' 조각 방지)\n"], ["                _ppm = _PROD_CITE.search(_pt) or _PROD_SPAN.search(_pt)\n", "                _ppm = _PROD_SPAN.search(_pt) or _PROD_CITE.search(_pt)\n"], ["            if re.search(r\"원금과\\s*이자를\\s*보장|원리금[이을]?\\s*보장(?:해|하|되)\", st) and not re.search(r\"조건|따라|한도|예금자보호|보장하지|보장되지|않\", st):\n                st2 = re.sub(r\"원금과\\s*이자를\\s*보장해\\s*주는\\s*상품(?:으로|이며|입니다)?\", \"해당 금융기관·상품의 보장 조건에 따라 원리금이 보장되는 상품으로\", st)\n                if st2 == st:\n                    st2 = re.sub(r\"원리금[이을]?\\s*보장(?:해\\s*주는|하는|되는)\\s*상품\", \"해당 금융기관·상품의 보장 조건에 따라 원리금이 보장되는 상품\", st)\n                if st2 == st:\n                    st2 = re.sub(r\"원리금[이을]?\\s*보장됩니다\", \"해당 금융기관·상품의 보장 조건에 따라 원리금이 보장됩니다\", st)\n", "            if re.search(r\"원금과\\s*(?:약정된\\s*)?이자를\\s*보장|원리금[이을]?\\s*보장(?:해|하|되)\", st) and not re.search(r\"조건|따라|한도|예금자보호|보장하지|보장되지|않\", st):\n                st2 = re.sub(r\"원금과\\s*(?:약정된\\s*)?이자를\\s*보장해\\s*주는\\s*상품(?:으로|이며|입니다)?\", \"해당 금융기관·상품의 보장 조건에 따라 원리금이 보장되는 상품으로\", st)\n                if st2 == st:\n                    st2 = re.sub(r\"원리금[이을]?\\s*보장(?:해\\s*주는|하는|되는)\\s*상품\", \"해당 금융기관·상품의 보장 조건에 따라 원리금이 보장되는 상품\", st)\n                if st2 == st:\n                    st2 = re.sub(r\"원리금[이을]?\\s*보장됩니다\", \"해당 금융기관·상품의 보장 조건에 따라 원리금이 보장됩니다\", st)\n                if st2 == st:                                     # v13.44(R2 실측): '원금과 약정된 이자를 보장해주는 특성이 있어'\n                    st2 = re.sub(r\"원금과\\s*(?:약정된\\s*)?이자를\\s*보장해\\s*?주는\", \"해당 금융기관·상품의 보장 조건에 따라 원금과 이자가 보장되는\", st)\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "v13.44(R2 실측): 표준 문장의" in src: print("[스킵] 이미 v13.44 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[경고] 적용전 md5가 예상 v1343과 다름. 훅 매칭되면 계속.")
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v1343_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
