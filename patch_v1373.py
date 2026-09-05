# -*- coding: utf-8 -*-
"""patch_v1373.py — v1372(0eaf1b7d) main.py 에 v13.73 적용. (v1372 적용 후 실행)
  [mini49 리뷰 반영] ① M2: 앞 블록에서 이미 구조화된 상품이 다른 사례 블록에 비교 언급으로 끼어들면 재삽입하지 않음(블록 간 중복 방지), 원금 보전 고지는 머리말 바로 아래로 고정(멱등)
   ② M2: '미래에셋증권은 … 상품을 제공' 홍보성 일반론 제거(근거 문서에 없을 때) ③ S4: '거래 자체로는 세금이 발생하지 않는다' 형태도 표준 문장 범주로, '연금저축(IRP 포함)' → '연금저축·IRP 등 연금계좌'(전 유형)
자동백업·자가검증. 이미 v13.73이면 스킵. 검증 md5==a32184c1c2e9e5b7667159a7a1e01267"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='0eaf1b7d90a3ca922f2bbc83f6beced7'
EXPECT_AFTER='a32184c1c2e9e5b7667159a7a1e01267'
HUNKS=[["        _generic = [l for l in others if not _rr_groups(l)]        # 상품명이 없는 일반 서술 줄만 유지\n        _plines, _kept = [], 0\n        for g in groups:\n            nm_ = max(g, key=lambda x: len(x[0]))[1]\n            core_ = min(g, key=lambda x: len(x[0]))[0]\n", "        _generic = [l for l in others if not _rr_groups(l) and \"아래 펀드는 원금보장 상품이 아닙니다\" not in l]   # 상품명이 없는 일반 서술 줄만 유지(고지 줄은 재생성)\n        _plines, _kept = [], 0\n        _rendered = st.setdefault(\"rendered\", [])\n        for g in groups:\n            nm_ = max(g, key=lambda x: len(x[0]))[1]\n            core_ = min(g, key=lambda x: len(x[0]))[0]\n            if any(_rr_same(core_, r_) for r_ in _rendered) and (head is None or not any(_rr_same(core_, hg[0][0]) for hg in _rr_groups(head))):\n                continue                                          # v13.73(M2): 앞 블록의 상품이 비교 언급으로 끼어든 경우 → 재삽입 금지\n            _rendered.append(core_)\n"], ["    core = min(groups[0], key=lambda x: len(x[0]))[0]             # 포함 검사용: 가장 짧은 표기\n    nm = max(groups[0], key=lambda x: len(x[0]))[1]               # 표시·근거 대조용: 가장 구체적인 표기\n    grade, srcs = _rr_evidence(nm, used, allowed)\n", "    core = min(groups[0], key=lambda x: len(x[0]))[0]             # 포함 검사용: 가장 짧은 표기\n    nm = max(groups[0], key=lambda x: len(x[0]))[1]               # 표시·근거 대조용: 가장 구체적인 표기\n    st.setdefault(\"rendered\", []).append(core)                   # v13.73: 블록 간 상품 중복 방지용\n    grade, srcs = _rr_evidence(nm, used, allowed)\n"], ["            if re.search(r\"(?:수수료|보수|세제\\s*혜택)[^.!?\\n]{0,25}?고려(?:하였|했|하여|해)\", st) and not re.search(r\"\\d+(?:\\.\\d+)?\\s*%\", body):   # v13.72(M2): 수치 없는 '수수료·세제 고려' 주장 제거\n", "            if re.search(r\"미래에셋증권(?:의\\s*경우|은|는|에서는?)[^.!?\\n]{0,40}?(?:제공|솔루션|다양한\\s*(?:상품|자산))\", st) and not re.search(r\"자산배분솔루션|다양한자산배분\", _docs):   # v13.73(M2): 홍보성 일반론\n                n += 1; continue\n            if re.search(r\"(?:수수료|보수|세제\\s*혜택)[^.!?\\n]{0,25}?고려(?:하였|했|하여|해)\", st) and not re.search(r\"\\d+(?:\\.\\d+)?\\s*%\", body):   # v13.72(M2): 수치 없는 '수수료·세제 고려' 주장 제거\n"], ["                    elif re.search(r\"(?:양도소득세|배당소득세|세금|과세)[^.!?\\n]{0,25}?(?:내지\\s*않|부과되지\\s*않|없습니다|면제|과세되지\\s*않)\", s_) \\\n", "                    elif re.search(r\"(?:양도소득세|배당소득세|세금|과세)[^.!?\\n]{0,25}?(?:내지\\s*않|부과되지\\s*않|없습니다|면제|과세되지\\s*않|발생하지\\s*않)\", s_) \\\n"], ["        ans = re.sub(r\"(?<!\\*)\\*(?!\\*)\", \"\", ans)                                   # v13.69(C9): 마크다운 잔재 홀수 별표 제거\n", "        ans = re.sub(r\"(?<!\\*)\\*(?!\\*)\", \"\", ans)                                   # v13.69(C9): 마크다운 잔재 홀수 별표 제거\n        ans = re.sub(r\"연금저축\\s*\\(\\s*IRP\\s*포함\\s*\\)\", \"연금저축·IRP 등 연금계좌\", ans)          # v13.73(S4): IRP는 연금저축이 아니라 별도 연금계좌\n"], ["        new = ([head] if head is not None else []) + _rr_capital_note(head, \" \".join(_plines), p) + risk + _plines + _generic   # v13.70(M2)\n", "        new = ([head] if head is not None else []) + _rr_capital_note(head, \" \".join(_plines), \"\") + risk + _plines + _generic   # v13.70/73(M2): 고지는 머리말 바로 아래(멱등)\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "v13.73(M2): 앞 블록의 상품" in src: print("[스킵] 이미 v13.73 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[중단] 적용전 md5가 예상 v1372와 다름 → 서버 파일이 갈라짐. main_v1373_full.py 로 통째 교체하세요."); sys.exit(4)
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v1372_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
