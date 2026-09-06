# -*- coding: utf-8 -*-
"""patch_v1389.py — v1388(03f0e295) main.py 에 v13.89 적용. (v1388 적용 후 실행) — 6훅
  T15 비교 표 수치 칸: '약 1%' 근사값·정수 %값도 근거 대조(창작 수익률 차단)  C10 표가 '확정하지 못함'인 속성(상품분류·투자전략)을 글머리 문장이 단정하면 제거
  권유 게이트 확장('…는 것이/도 좋습니다' 일반형, '신중하게 결정', '최종 결정'), 마무리 연락처·세부 문의 안내 확장, 인출 과세 답변의 '다른 대안 고려' 제거
자동백업·자가검증. 이미 v13.89이면 스킵. 검증 md5==73cf01d1af8bb691b428d70922eca238"""










import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='03f0e295929a33d543c45ad57d7df80c'
EXPECT_AFTER='73cf01d1af8bb691b428d70922eca238'
HUNKS=[["                        _vals = set(re.findall(r\"\\d+\\.\\d+\", _c))\n                        _labn = len(re.findall(r\"\\d+\\.\\d+\\s*%?\\s*\\(\\s*(?:[A-Za-z][A-Za-z0-9-]{0,6}|온라인|오프라인|퇴직연금)\\s*(?:클래스)?\\s*\\)\", _c))   # v13.82: 값마다 클래스 표기가 있을 때만 복수 허용\n                        if len(_vals) >= 2 and not (_labn >= len(_vals) or re.search(r\"1년|3년|투자신탁|비교지수\", _c)):\n                            _new.append(\" 자료에서 확정하지 못함(복수 값) \"); _nv += 1\n                        elif _vals and any(v_ not in _evtxt for v_ in _vals):                                    # v13.82: 근거 문서에 없는 수치는 칸 단위로 확정 불가\n                            _new.append(\" 자료에서 확정하지 못함(근거 문서에 없는 값) \"); _nv += 1\n", "                        _vals = set(re.findall(r\"\\d+\\.\\d+\", _c))\n                        _pcts = set(re.findall(r\"(\\d+(?:\\.\\d+)?)\\s*%\", _c))                                     # v13.89: 정수 %값('약 1%')도 근거 대조\n                        _labn = len(re.findall(r\"\\d+\\.\\d+\\s*%?\\s*\\(\\s*(?:[A-Za-z][A-Za-z0-9-]{0,6}|온라인|오프라인|퇴직연금)\\s*(?:클래스)?\\s*\\)\", _c))   # v13.82: 값마다 클래스 표기가 있을 때만 복수 허용\n                        if re.search(r\"약\\s*\\d|대략|정도의?\\s*\\d|\\d\\s*%?\\s*내외\", _c) and _pcts:                    # v13.89: 근사 표현은 문서 수치가 아니다\n                            _new.append(\" 자료에서 확정하지 못함(근사값 표기) \"); _nv += 1\n                        elif len(_vals) >= 2 and not (_labn >= len(_vals) or re.search(r\"1년|3년|투자신탁|비교지수\", _c)):\n                            _new.append(\" 자료에서 확정하지 못함(복수 값) \"); _nv += 1\n                        elif _vals and any(v_ not in _evtxt for v_ in _vals):                                    # v13.82: 근거 문서에 없는 수치는 칸 단위로 확정 불가\n                            _new.append(\" 자료에서 확정하지 못함(근거 문서에 없는 값) \"); _nv += 1\n                        elif _pcts and any(not re.search(re.escape(p_) + r\"\\s*%\", _evtxt) for p_ in _pcts):        # v13.89: 'N%' 표기가 근거에 없으면 확정 불가\n                            _new.append(\" 자료에서 확정하지 못함(근거 문서에 없는 값) \"); _nv += 1\n"], ["            _ATTR16 = {\"총보수\": r\"총\\s*보수|보수|수수료\", \"시장잔고\": r\"시장\\s*잔고|설정액|순자산|규모\", \"수익률\": r\"수익률|성과\", \"판매클래스\": r\"클래스\", \"투자기간\": r\"투자\\s*기간|만기\", \"위험등급\": r\"위험\\s*등급\"}\n", "            _ATTR16 = {\"총보수\": r\"총\\s*보수|보수|수수료\", \"시장잔고\": r\"시장\\s*잔고|설정액|순자산|규모\", \"수익률\": r\"수익률|성과\", \"판매클래스\": r\"클래스\", \"투자기간\": r\"투자\\s*기간|만기\", \"위험등급\": r\"위험\\s*등급\",\n                       \"상품분류\": r\"상품\\s*분류|자산\\s*유형|상품\\s*유형\", \"투자전략\": r\"투자\\s*(?:대상|전략)|운용\\s*전략\"}   # v13.89(C10): 표가 '확정하지 못함'인 속성을 글머리 문장이 단정하던 경로\n"], ["(?:하는|활용하는|설정하는|납입하는|넣는|가입하는|이전하는|두는|하시는)\\s*(?:것|방식|편|쪽)이\\s*(?:유리|좋|바람직|낫)|", "[가-힣]+(?:는|은|할)\\s*(?:것|방식|편|쪽)(?:이|도)\\s*(?:유리|좋|바람직|낫)|신중하게\\s*(?:이루어|결정|선택|접근)|최종\\s*결정(?:을|은)|"], ["(?:추가적인\\s*정보|자세한\\s*(?:사항|내용))(?:은|는)?\\s*[^.!?\\n]{0,40}?(?:확인하실\\s*수|문의하시)\")   # v13.84(B2·B3·T15·T6)", "(?:추가적인\\s*정보|자세한\\s*(?:사항|내용))(?:은|는|가)?\\s*[^.!?\\n]{0,40}?(?:확인하실\\s*수|확인해\\s*주세요|확인하시기|문의하시|문의해\\s*주세요)\")   # v13.84/89(B2·B3·T15·T6)"], ["(?:자세한|구체적인|보다\\s*상세한)\\s*(?:사항|내용|정보)(?:은|는)?\\s*[^.!?\\n]{0,45}?(?:확인|문의|참고)하(?:시기\\s*바랍니다|세요|십시오|시길)\", s_)]   # v13.85/86: 전문가 상담·연락처 안내 마무리", "(?:자세한|구체적인|보다\\s*상세한|세부)\\s*[^.!?\\n]{0,20}?(?:사항|내용|정보|방안)[^.!?\\n]{0,45}?(?:확인|문의|참고)하(?:시기\\s*바랍니다|세요|십시오|시길|는\\s*것이\\s*좋|여\\s*확인)\", s_)]   # v13.85/86/89: 전문가 상담·연락처 안내 마무리"], ["                _kp = [s_ for s_ in _ss if not re.search(r\"(?:것이|게|편이|쪽이)\\s*(?:유리|좋|바람직|낫)|유리합니다|권장\\s*(?:드|합)|권해\\s*드|추천\\s*(?:드|합)|최대한\\s*누릴|혜택을\\s*누릴|효과를\\s*누릴\", s_)]   # v13.82: 지운 권고를 받는 '이렇게 하면 …누릴' 도\n", "                _kp = [s_ for s_ in _ss if not re.search(r\"(?:것이|것도|게|편이|쪽이)\\s*(?:유리|좋|바람직|낫)|유리합니다|권장\\s*(?:드|합)|권해\\s*드|추천\\s*(?:드|합)|최대한\\s*누릴|혜택을\\s*누릴|효과를\\s*누릴|(?:대안|방법)을\\s*(?:고려|검토|찾아)\", s_)]   # v13.82/89: '다른 대안을 고려해보는 것도 좋은 방법'\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "v13.89(C10): 표가 '확정하지 못함'인 속성을" in src: print("[스킵] 이미 v13.89 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[중단] 적용전 md5가 예상 v1388과 다름 → 서버 파일이 갈라짐. main_v1389_full.py 로 통째 교체하세요."); sys.exit(4)
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v1388_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
