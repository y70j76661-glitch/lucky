# -*- coding: utf-8 -*-
"""patch_v1345.py — v1344(2f7e30c0) main.py 에 v13.45 적용. (v1344 적용 후 실행)
  [실측 mini22] ① 추천 계약의 등급 교정 창을 '다음 상품명 앞까지'로 자르고 창·문장에 등급이 하나일 때만 교정
   ('A 혹은 B … (5등급 및 6등급)'에서 A 등급을 B 값으로 덮어쓰던 오류 차단) ② 예금 상품 없이 펀드만 든 답변의 '이러한 원리금보장형 상품들…' 오분류 문장 제거
   ③ 상품명 없는 문단의 표준 문장 주어 '이 상품은' → '이러한 상품은'
자동백업·자가검증. 이미 v13.45면 스킵. 검증 md5==be009f1e28d9ee27c942ab7a604675b3"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='2f7e30c03cced3c936a28189f382bd8a'
EXPECT_AFTER='be009f1e28d9ee27c942ab7a604675b3'
HUNKS=[["            g = re.search(r\"(?<![\\d.])(\\d)\\s*등급\", ln[m.end(): m.end() + 40])\n            if g:\n", "            # v13.45(M2 실측 '5등급 및 6등급'): 등급 창은 다음 상품명 앞까지로 자르고, 창 안에 등급이 정확히 하나일 때만 교정한다\n            #   (두 상품을 나란히 쓴 문장에서 앞 상품의 등급을 뒤 상품 값으로 덮어쓰던 오류 차단)\n            _nx = next((mm.start() for mm in _PROD_CITE.finditer(ln, m.end()) if mm.start() > m.end()), len(ln))\n            _win = ln[m.end(): min(m.end() + 40, _nx)]\n            _gs = re.findall(r\"(?<![\\d.])(\\d)\\s*등급\", _win)\n            g = re.search(r\"(?<![\\d.])(\\d)\\s*등급\", _win) if len(_gs) == 1 and len(re.findall(r\"(?<![\\d.])\\d\\s*등급\", ln)) == 1 else None\n            if g:\n"], ["                else:\n                    # v13.42(R2 실측): 답변의 상품이 하나뿐이면 그 이름을 주어로(띄어쓰기 상품명 'NH-Amundi 하나로 단기채 …'도 인식)\n                    _spans = [m_.group(0).strip(\"·-'\\\"\") for m_ in _PROD_SPAN.finditer(ans)] or [m_.group(0).strip(\"·-'\\\"\") for m_ in _PROD_CITE.finditer(ans)]\n                    _cores = {_rr_core(x_) for x_ in _spans if len(_rr_core(x_)) >= 4}\n                    _sj = (_spans[0] + \"은(는) \") if len(_cores) == 1 else \"이 상품은 \"\n", "                else:\n                    # v13.42(R2 실측): 답변의 상품이 하나뿐이면 그 이름을 주어로(띄어쓰기 상품명 'NH-Amundi 하나로 단기채 …'도 인식)\n                    _spans = [m_.group(0).strip(\"·-'\\\"\") for m_ in _PROD_SPAN.finditer(ans)] or [m_.group(0).strip(\"·-'\\\"\") for m_ in _PROD_CITE.finditer(ans)]\n                    _cores = {_rr_core(x_) for x_ in _spans if len(_rr_core(x_)) >= 4}\n                    _sj = (_spans[0] + \"은(는) \") if len(_cores) == 1 else \"이러한 상품은 \"   # v13.45: 상품명 없는 문단은 '이러한 상품은'\n"], ["    body = \"\\n\\n\".join(paras)\n    # 상품이 둘 이상인 답변에서 문단 첫머리 '이 상품은 실적배당형…'(주어 불명) → '위 상품들은 모두'\n", "    body = \"\\n\\n\".join(paras)\n    # v13.45(R2 실측): 예금·원리금보장 '상품'이 하나도 없이 펀드만 든 답변에서 '이러한 원리금보장형 상품들은 …' 문장은 펀드를 원리금보장형으로\n    #   잘못 부른 것 → 그 문장만 제거\n    _has_dep = re.search(r\"(?m)^[^\\n]{0,40}(?:예금|ELB|DLB|발행어음|RP)\\s*[:：]\", body) or re.search(r\"[가-힣A-Za-z]+(?:은행|증권|저축은행)\\s*(?:정기)?예금\", body)\n    if all_names and not _has_dep and re.search(r\"이러한\\s*원리금\\s*보장형\\s*상품들?\", body):\n        _nl = []\n        for l in body.split(\"\\n\"):\n            if re.search(r\"이러한\\s*원리금\\s*보장형\\s*상품들?\", l) and not l.lstrip().startswith(\"※\"):\n                ss = re.split(r\"(?<=[.!?])\\s+\", l.strip())\n                kp = [x for x in ss if not re.search(r\"이러한\\s*원리금\\s*보장형\\s*상품들?\", x)]\n                st[\"fix\"] += len(ss) - len(kp)\n                if kp:\n                    _nl.append(\" \".join(kp))\n            else:\n                _nl.append(l)\n        body = re.sub(r\"\\n{3,}\", \"\\n\\n\", \"\\n\".join(_nl))\n    # 상품이 둘 이상인 답변에서 문단 첫머리 '이 상품은 실적배당형…'(주어 불명) → '위 상품들은 모두'\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "v13.45(M2 실측" in src: print("[스킵] 이미 v13.45 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[경고] 적용전 md5가 예상 v1344와 다름. 훅 매칭되면 계속.")
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v1344_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
