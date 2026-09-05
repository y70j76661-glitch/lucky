# -*- coding: utf-8 -*-
"""patch_v1367.py — v1366(8f832807) main.py 에 v13.67 적용. (v1366 적용 후 실행)
  [mini43 리뷰 반영] ① S4: '과세이연' 언급만으로 면제 단정 문장이 살아남던 구멍 봉합('즉시 과세되지 않는다'만 예외), 표준 문장 멱등,
     범위 고지 조건을 '기타소득세 부재'로(표준 문장의 문구가 고지를 막던 문제), 연령별 세율·재원·1,500만원 기준 적용 범위 명시
   ② 조사 정합: 닫는 따옴표 뒤 '은(는)'도 처리 ③ M2: '꾸준한 수익 추구' 보장성 표현 완화, '극복할 가능성이 큽니다' 낙관 단정 문장 제거
   ④ M2b: 안정형 질문의 대체 목록 첫머리에 '후보는 모두 펀드(원금 비보장)·원리금보장형은 별도 확인' 명시
자동백업·자가검증. 이미 v13.67이면 스킵. 검증 md5==60f483d4e0a5713ad5207747a0c84298"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='8f832807b9d89a766357f99f8077d414'
EXPECT_AFTER='60f483d4e0a5713ad5207747a0c84298'
HUNKS=[["                    if re.search(r\"(?:양도소득세|배당소득세|세금|과세)[^.!?\\n]{0,25}?(?:내지\\s*않|부과되지\\s*않|없습니다|면제|과세되지\\s*않)\", s_) and not re.search(r\"즉시|당장|인출\\s*(?:전|시)|이연|수령\\s*(?:시|할\\s*때)\", s_):\n", "                    if _STD[:24] in s_:\n                        _std_done = True                                # v13.67: 표준 문장이 이미 있으면 중복 삽입 금지(멱등)\n                    elif re.search(r\"(?:양도소득세|배당소득세|세금|과세)[^.!?\\n]{0,25}?(?:내지\\s*않|부과되지\\s*않|없습니다|면제|과세되지\\s*않)\", s_) \\\n                            and not re.search(r\"(?:즉시|당장|즉각)[^.!?\\n]{0,12}(?:과세되지\\s*않|과세하지\\s*않|과세가\\s*이루어지지)\", s_):   # v13.67: '즉시 과세되지 않는다'만 예외(이연 언급은 예외 아님)\n"], ["                and not re.search(r\"기타소득세|연금\\s*외\\s*(?:수령|인출)|일시금\", ans.split(\"[참고 문서]\")[0]):   # v13.65: 의도 기반\n            _body_, _tail_ = (ans.split(\"[참고 문서]\", 1) + [\"\"])[:2]\n            ans = (_body_.rstrip() + \"\\n\\n※ 위 연금소득세 저율 과세는 연금 수령 요건(만 55세 이후, 연금 수령 한도 내)을 갖춰 연금으로 받을 때 적용되며, \"\n                   \"연금 외 방식(일시금 등)으로 인출하면 세액공제받은 납입금·운용수익에는 기타소득세 16.5%가 적용될 수 있습니다.\" + ((\"\\n\\n[참고 문서]\" + _tail_) if \"[참고 문서]\" in ans else \"\"))\n", "                and \"기타소득세\" not in ans.split(\"[참고 문서]\")[0]:   # v13.65/67: 의도 기반(표준 문장의 '연금 외 수령' 문구는 고지를 막지 않는다)\n            _body_, _tail_ = (ans.split(\"[참고 문서]\", 1) + [\"\"])[:2]\n            _scope15 = (\" 연 1,500만원 기준은 연금소득 합계에 대한 것으로, 이를 넘으면 종합과세 또는 분리과세 선택 대상이 됩니다.\" if re.search(r\"1,?500\\s*만\", _body_) else \"\")\n            ans = (_body_.rstrip() + \"\\n\\n※ 위 연금소득세 저율 과세(연령별 5.5%·4.4%·3.3%)는 연금 수령 요건(만 55세 이후, 연금 수령 한도 내)을 갖춰 연금으로 받을 때, \"\n                   \"세액공제받은 납입금과 운용수익 재원에 적용되며, 연금 외 방식(일시금 등)으로 인출하면 그 재원에는 기타소득세 16.5%가 적용될 수 있습니다.\" + _scope15 +\n                   ((\"\\n\\n[참고 문서]\" + _tail_) if \"[참고 문서]\" in ans else \"\"))\n"], ["        ans = re.sub(r\"([가-힣0-9])([)\\]]?)\\s*은\\(는\\)\", lambda m_: m_.group(1) + m_.group(2) + _josa(m_.group(1)), ans)   # v13.66: 조사 정합\n", "        ans = re.sub(r\"([가-힣0-9])([)\\]'\\\"」]*)\\s*은\\(는\\)\", lambda m_: m_.group(1) + m_.group(2) + _josa(m_.group(1)), ans)   # v13.66/67: 조사 정합(따옴표 뒤 포함)\n"], ["    (re.compile(r\"가장\\s*안전한\\s*(상품|펀드|선택)\"), r\"상대적으로 위험등급이 낮은 \\1\"),\n", "    (re.compile(r\"가장\\s*안전한\\s*(상품|펀드|선택)\"), r\"상대적으로 위험등급이 낮은 \\1\"),\n    (re.compile(r\"꾸준한\\s*(?:수익|성과)(?:을|를)?\\s*(?:추구|기대|제공)(?:합니다|할\\s*수\\s*있습니다|하는)\"), \"상대적으로 낮은 변동성을 목표로 하지만 손실 가능성이 있고 수익은 보장되지 않습니다\"),   # v13.67(M2)\n"], ["_RF_PROMO = re.compile(r\"수상|최우수|우수상|대상\\s*(?:을|를)?\\s*(?:수상|받)|인정받|우수한|우수성|대표적인\\s*(?:상품|펀드)|대표\\s*상품|최고의|업계\\s*(?:최|1위)|1위|선정된|검증된\\s*(?:성과|수익)\")   # v13.59: 판촉·경력 표현\n", "_RF_PROMO = re.compile(r\"수상|최우수|우수상|대상\\s*(?:을|를)?\\s*(?:수상|받)|인정받|우수한|우수성|대표적인\\s*(?:상품|펀드)|대표\\s*상품|최고의|업계\\s*(?:최|1위)|1위|선정된|검증된\\s*(?:성과|수익)|\"\n                       r\"극복할\\s*가능성이\\s*(?:큽|높)|만회할\\s*(?:수\\s*있|가능성)|회복할\\s*가능성이\\s*(?:큽|높)|손실을\\s*(?:상쇄|만회)할\")   # v13.59/67: 판촉·경력·낙관 단정 표현\n"], ["        _one = bool(re.search(r\"하나|한\\s*개|한\\s*가지|1개\", _hint_q))\n", "        _one = bool(re.search(r\"하나|한\\s*개|한\\s*가지|1개\", _hint_q))\n        _safe_head = (\"아래 후보는 모두 펀드(실적배당형)로 투자원금과 수익이 보장되지 않습니다. 원금 보장을 우선하신다면 예금 등 원리금보장형 상품군을 별도로 확인해야 합니다. \" if _safe else \"\")   # v13.67(M2b)\n"], ["        _head = ((\"질문하신 대로 '하나'를 고르기에는 현재 정보(연령·투자성향)만으로는 부족해 특정 상품을 확정하지 않습니다. \" if _one else\n", "        _head = (_safe_head + (\"질문하신 대로 '하나'를 고르기에는 현재 정보(연령·투자성향)만으로는 부족해 특정 상품을 확정하지 않습니다. \" if _one else\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "v13.67(M2b)" in src: print("[스킵] 이미 v13.67 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[중단] 적용전 md5가 예상 v1366과 다름 → 서버 파일이 갈라짐. main_v1367_full.py 로 통째 교체하세요."); sys.exit(4)
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v1366_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
