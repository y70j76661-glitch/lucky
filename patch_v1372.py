# -*- coding: utf-8 -*-
"""patch_v1372.py — v1371(ecfe18ee) main.py 에 v13.72 적용. (v1371 적용 후 실행)
  [mini48 리뷰 반영] ① S4: 계좌 밖 과세 체계(해외 상장 ETF 직접거래 22퍼센트·분류과세·금융소득 종합과세)는 계좌 내 과세 질문에서 무관 → 제거, '과세되며/과세되고' 어미 포함
   ② B11: '언제든지 중도 인출 가능' → '가능할 수 있으나(계좌 규정 확인) 인출 재원·방식에 따라 과세될 수 있고'
   ③ M2: '원금 손실 가능성이 낮…' 교체를 어미별 완전 문장으로(끊긴 어미 복구 포함), '안정적인 수익을 원하는'·'안전한 투자를 선호하는' 완화, 수치 없는 '수수료·세제 고려' 문장 제거
   ④ T11: 대체 목록 앞 LLM '후보·추천' 도입문 제거(확정 보류 문장을 맨 앞에)
자동백업·자가검증. 이미 v13.72이면 스킵. 검증 md5==0eaf1b7d90a3ca922f2bbc83f6beced7"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='ecfe18ee1484851c2b8348674990ed34'
EXPECT_AFTER='0eaf1b7d90a3ca922f2bbc83f6beced7'
HUNKS=[["                    if re.search(r\"(?:양도소득세|배당소득세|양도소득)[^.!?\\n]{0,20}?(?:별도로\\s*)?(?:과세됩니다|부과됩니다|납부해야|과세\\s*대상입니다)\", s_) and not re.search(r\"않|이연|인출\", s_):\n                        _n19 += 1; continue                                                                        # v13.71: 표준 문장과 반대되는 '과세된다' 단정 제거\n", "                    if re.search(r\"(?:양도소득세|배당소득세|양도소득)[^.!?\\n]{0,20}?(?:별도로\\s*)?(?:과세됩니다|부과됩니다|납부해야|과세\\s*대상입니다|과세되며|과세되고|부과되며|부과되고)\", s_) and not re.search(r\"않|이연|인출\", s_):\n                        _n19 += 1; continue                                                                        # v13.71/72: 표준 문장과 반대되는 '과세된다' 단정 제거\n                    if re.search(r\"해외\\s*상장|해외\\s*직접|22\\s*%|분류\\s*과세|금융소득\\s*종합과세\", s_) and not re.search(r\"해외|22\", question):   # v13.72: 계좌 밖 과세 체계는 질문 밖\n                        _n19 += 1; continue\n"], ["            if _n19:\n                ans = re.sub(r\"\\n{3,}\", \"\\n\\n\", \"\\n\".join(_b19)).strip(); clean_note += f\" 과세 범위 계약 {_n19}건 교정\"\n", "            if _n19:\n                ans = re.sub(r\"\\n{3,}\", \"\\n\\n\", \"\\n\".join(_b19)).strip(); clean_note += f\" 과세 범위 계약 {_n19}건 교정\"\n                ans = re.sub(r\"(?m)^\\s*-\\s*(?:해외\\s*상장\\s*ETF|국내\\s*상장\\s*해외\\s*ETF)\\s*[:：]\\s*$\\n?\", \"\", ans)   # 내용이 비워진 항목 머리 제거\n"], ["            _b8b, _n8b = re.subn(r\"(세액\\s*공제를?\\s*받지\\s*않은\\s*(?:금액|납입금|원금)[^.!?\\n]{0,10}?인출[^.!?\\n]{0,8}?)세금을\\s*(?:피할|내지\\s*않을|면할)\\s*수\\s*있\",\n", "            ans, _n8d = re.subn(r\"언제든지\\s*(?:중도\\s*)?인출(?:이|을)?\\s*(?:가능(?:하지만|하나|하며|하고|합니다)|할\\s*수\\s*있(?:지만|으나|으며|고|습니다))\",\n                                lambda m_: \"중도 인출이 가능할 수 있으나(계좌 규정 확인 필요) 인출 재원과 방식에 따라 과세될 수 \" + (\"있습니다\" if m_.group(0).endswith((\"합니다\", \"습니다\")) else \"있고\"), ans)   # v13.72(B11)\n            if _n8d:\n                clean_note += f\" 중도인출 '언제든지' 완화 {_n8d}건\"\n            _b8b, _n8b = re.subn(r\"(세액\\s*공제를?\\s*받지\\s*않은\\s*(?:금액|납입금|원금)[^.!?\\n]{0,10}?인출[^.!?\\n]{0,8}?)세금을\\s*(?:피할|내지\\s*않을|면할)\\s*수\\s*있\",\n"], ["    (re.compile(r\"원금\\s*손실(?:의)?\\s*가능성이\\s*낮(?:습니다|지만|고|으며|아)\"), \"원금 손실 가능성이 상대적으로 낮을 수 있으나 없지는 않으며\"),\n", "    (re.compile(r\"원금\\s*손실(?:의)?\\s*가능성이\\s*낮습니다\"), \"원금 손실 가능성이 상대적으로 낮을 수 있지만, 손실 가능성이 없는 것은 아닙니다\"),   # v13.72: 어미별 완전 문장\n    (re.compile(r\"원금\\s*손실(?:의)?\\s*가능성이\\s*낮(?:지만|고|으며|아)\"), \"원금 손실 가능성이 상대적으로 낮을 수 있지만 손실 가능성이 없지는 않으며\"),\n    (re.compile(r\"(?:매우\\s*)?(?:보수적이고\\s*)?안정적인\\s*수익(?:을|를)?\\s*(?:원하는|추구하는|선호하는|바라는|기대하는)\"), \"상대적으로 변동성이 낮은 상품을 원하는\"),   # v13.72(M2)\n    (re.compile(r\"낮을\\s*수\\s*있으나\\s*없지는\\s*않으며\\.\"), \"낮을 수 있지만, 손실 가능성이 없는 것은 아닙니다.\"),   # v13.72: 이전 교체의 끊긴 어미 복구\n    (re.compile(r\"(?:상대적으로\\s*)?안전한\\s*투자를\\s*(?:선호|원|추구)하는\"), \"상대적으로 변동성이 낮은 상품을 선호하는\"),\n"], ["            if re.search(r\"연금자산관리센터|자산관리센터|상담센터|고객센터|지점을\\s*방문\", st) and not re.search(r\"연금자산관리센터|자산관리센터|상담센터|고객센터\", _docs):\n", "            if re.search(r\"(?:수수료|보수|세제\\s*혜택)[^.!?\\n]{0,25}?고려(?:하였|했|하여|해)\", st) and not re.search(r\"\\d+(?:\\.\\d+)?\\s*%\", body):   # v13.72(M2): 수치 없는 '수수료·세제 고려' 주장 제거\n                n += 1; continue\n            if re.search(r\"연금자산관리센터|자산관리센터|상담센터|고객센터|지점을\\s*방문\", st) and not re.search(r\"연금자산관리센터|자산관리센터|상담센터|고객센터\", _docs):\n"], ["                if _rr_groups(_pp) or re.match(r\"^\\s*\\d+[.)]\\s\", _pp) or re.search(r\"알려\\s*주시면|말씀해\\s*주시면|추천을?\\s*드리\", _pp):\n", "                if _rr_groups(_pp) or re.match(r\"^\\s*\\d+[.)]\\s\", _pp) or re.search(r\"알려\\s*주시면|말씀해\\s*주시면|추천을?\\s*드리|후보로\\s*검토|다음과\\s*같은|추천(?:해|드릴)\", _pp):   # v13.72(T11)\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "v13.72(B11)" in src: print("[스킵] 이미 v13.72 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[중단] 적용전 md5가 예상 v1371과 다름 → 서버 파일이 갈라짐. main_v1372_full.py 로 통째 교체하세요."); sys.exit(4)
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v1371_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
