# -*- coding: utf-8 -*-
"""patch_v1324.py — v1323(236cc642) main.py 에 v13.24 적용. (v1323 적용 후 실행)
  [실측 정독 지적 4건 — 무관 정보 제거·근거 보강·표기 보강]
   X1: '수수료 얘기는 빼고'의 '빼'가 인출 행위로 오인돼 기타소득세(과세제외) 카드가 붙음 → 제외 어구를 지운 뒤 판정,
       상품설명·추천 질문에 세금 단어가 없으면 인출 과세 카드 미부착.
   N4b: IRP 세액공제 한도 질문에 900만원(합산)만 있고 연금저축 600만원 하위한도가 없으면 한 줄 보강.
   M2: 세금을 묻지 않은 추천 답변의 수치형 세제 문장('40% 소득공제·연 72만원' 등 구 개인연금 규정) 제거 — 문장 삭제만.
   X2: '세액공제 제외 대상은?'에 검색이 투자설명서 세제 조항만 올려 '확인 불가'로 답함 → doc41 세액공제 안내 청크
       (가입대상·비공제 서술) 필수 근거 보강(MUST_CHUNKS).
자동백업·자가검증. 이미 v13.24면 스킵. 검증 md5==29e3a475af29cfeed710a60bdfa0cf2a"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='236cc642f7320ecd8c9e6a5eb6f4aa81'
EXPECT_AFTER='29e3a475af29cfeed710a60bdfa0cf2a'
HUNKS=[["#   보수표를 직접 끌어오는 v9.20과 같은 방식으로, 확인된 짝만 좁게 넣는다.\n#   각 항목: (질문에 있어야 할 말들, 청크에 있어야 할 말들, 가져올 개수)\nMUST_CHUNKS = [\n    # v9.71: '금융사를 옮기는 맥락'일 때만. 일반 주식계좌→연금계좌 입고는 다른 얘기다.\n    ((\"주식\", \"종목\", \"지분증권\", \"펀드\"), (\"실물이전\", \"현물이전\", \"타사\", \"이관\", \"다른 금융\"),\n     (\"실물이전 불가사유\", \"지분증권/리츠\"), 2),\n", "#   보수표를 직접 끌어오는 v9.20과 같은 방식으로, 확인된 짝만 좁게 넣는다.\n#   각 항목: (질문에 있어야 할 말들, 청크에 있어야 할 말들, 가져올 개수)\nMUST_CHUNKS = [\n    # v13.24(X2 실측): '세액공제 제외 대상은?' — 검색이 펀드 투자설명서의 세제 조항만 올려 doc41의 가입대상·한도·\n    #   비공제 서술이 빠지고 '확인할 수 없다'로 답함 → 세액공제 안내 청크(doc41 고유 문구)를 직접 보강.\n    ((\"세액공제\",),\n     (\"제외\", \"대상이 아\", \"대상은\", \"안 되는\", \"안되는\", \"못 받\", \"받을 수 없\", \"해당하지 않\", \"누가\", \"조건\", \"요건\", \"자격\"),\n     (\"납입액이 모두 세액공제\", \"종합소득이 있어야 세액공제\", \"세액공제를 받지 않은 납입\", \"소득이 없어도 가입이 가능\"), 2),\n    # v9.71: '금융사를 옮기는 맥락'일 때만. 일반 주식계좌→연금계좌 입고는 다른 얘기다.\n    ((\"주식\", \"종목\", \"지분증권\", \"펀드\"), (\"실물이전\", \"현물이전\", \"타사\", \"이관\", \"다른 금융\"),\n     (\"실물이전 불가사유\", \"지분증권/리츠\"), 2),\n"], ["            ans = ans.rstrip() + \"\\n\\n\" + _req\n            calc_note += \" (연금수령 요건 코드 보강)\"\n\n        # [7단계] 출처 표기: 평가 기준 대응 — 사용한 문서의 출처를 답변 본문에 자동 명시\n        srcs = []\n        for c in used:\n", "            ans = ans.rstrip() + \"\\n\\n\" + _req\n            calc_note += \" (연금수령 요건 코드 보강)\"\n\n        # v13.24(N4b): IRP 세액공제 한도 질문에 900만원(합산)만 있고 연금저축 600만원 하위한도가 없으면 한 줄 보강\n        if qtype == \"세제\" and \"IRP\" in question and any(k in question for k in LIMIT_Q) \\\n                and any(k in question for k in LIMIT_Q2) and re.search(r\"900\\s*만\", ans) \\\n                and not re.search(r\"600\\s*만\", ans) and not _NOINFO.search(ans[:120]):\n            ans = ans.rstrip() + (\"\\n\\n참고로 연금저축만 납입하는 경우의 세액공제 한도는 연 600만원이며, \"\n                                  \"IRP를 포함하면 연금저축과 합산해 연 900만원까지입니다.\")\n            calc_note += \" (한도 구조 한 줄 보강)\"\n        # v13.24(M2): 상품 추천 답변에 세금 질문이 아닌데 붙는 수치형 세제 서술('40% 소득공제·연 72만원' 등 구 개인연금 규정)은\n        #   질문·상품 근거와 연결되지 않으므로 그 문장만 제거(위험·기간·보수·손실 중심 유지). 세금을 물었으면 불변.\n        if qtype == \"추천\" and not re.search(r\"세금|세액|세제|과세|소득세|공제|절세\", question):\n            _ml, _nm = [], 0\n            for _ln in ans.split(\"\\n\"):\n                _ss = re.split(r\"(?<=[.!?])\\s+\", _ln)\n                _kp = [x for x in _ss if not (re.search(r\"소득공제|세액공제|비과세|이자소득세|세제\\s*혜택\", x)\n                                              and re.search(r\"\\d+\\s*(?:%|만\\s*원|년)\", x))]\n                _nm += len(_ss) - len(_kp)\n                if _ln.strip() and not \"\".join(_kp).strip():\n                    continue\n                _ml.append(\" \".join(_kp))\n            if _nm:\n                ans = \"\\n\".join(_ml)\n                calc_note += f\" (추천 답변 세제 수치 문장 {_nm}건 제거)\"\n\n        # [7단계] 출처 표기: 평가 기준 대응 — 사용한 문서의 출처를 답변 본문에 자동 명시\n        srcs = []\n        for c in used:\n"], ["        _EXEMPT_TAX = (\"세액공제\", \"공제\", \"과세\", \"세금\", \"기타소득\")\n        _OPER_Q = (\"디폴트옵션\", \"사전지정\", \"운용지시\", \"자동매수\", \"자동적용\",\n                   \"포트폴리오\", \"옵트인\")\n        _fire = (any(k in question for k in _EXEMPT_ACT)\n                 or (any(k in question for k in _EXEMPT_HINT)\n                     and any(k in question for k in _EXEMPT_TAX)))\n        # v13.12(N6): '중도해지 세금은 빼고, 연금으로 받을 때 세금만' — 인출·해지어 뒤 12자 안에\n        #   제외 표현이 오면 그 주제를 빼달라는 것이므로 인출 과세 카드를 붙이지 않는다.\n        if _fire and re.search(r\"(?:인출|해지|출금|환매|중도)[^\\n]{0,12}?(?:빼고|말고|제외|넘어가|됐고|생략|건너뛰)\", question):\n", "        _EXEMPT_TAX = (\"세액공제\", \"공제\", \"과세\", \"세금\", \"기타소득\")\n        _OPER_Q = (\"디폴트옵션\", \"사전지정\", \"운용지시\", \"자동매수\", \"자동적용\",\n                   \"포트폴리오\", \"옵트인\")\n        # v13.24(X1 실측): '수수료 얘기는 빼고'의 '빼'는 인출 행위가 아니라 제외 표현 → 판정 전에 제외 어구를 지운다.\n        #   상품설명·추천 질문에 세금 단어가 없으면 인출 과세 카드는 무관 정보이므로 붙이지 않는다.\n        _qx = re.sub(r\"(?:빼고|빼\\s*주|빼\\s*달|말고|제외하고)\", \" \", question)\n        _fire = (any(k in _qx for k in _EXEMPT_ACT)\n                 or (any(k in _qx for k in _EXEMPT_HINT)\n                     and any(k in _qx for k in _EXEMPT_TAX)))\n        if _fire and qtype in (\"상품설명\", \"추천\") and not re.search(r\"세금|세액|과세|소득세|공제\", question):\n            _fire = False\n        # v13.12(N6): '중도해지 세금은 빼고, 연금으로 받을 때 세금만' — 인출·해지어 뒤 12자 안에\n        #   제외 표현이 오면 그 주제를 빼달라는 것이므로 인출 과세 카드를 붙이지 않는다.\n        if _fire and re.search(r\"(?:인출|해지|출금|환매|중도)[^\\n]{0,12}?(?:빼고|말고|제외|넘어가|됐고|생략|건너뛰)\", question):\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "v13.24(X1 실측)" in src: print("[스킵] 이미 v13.24 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[경고] 적용전 md5가 예상 v1323과 다름. 훅 매칭되면 계속.")
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v1323_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
