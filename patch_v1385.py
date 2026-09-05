# -*- coding: utf-8 -*-
"""patch_v1385.py — v1384(51c38192) main.py 에 v13.85 적용. (v1384 적용 후 실행) — 9훅
  B10 생략형 합산 계약의 발동을 LLM 본문(900 포함 여부)에서 떼어 질문만으로 (되묻기 회귀 차단)  B5 과세 시점 3단계 글머리 분리
  T15 요약 계약 일반화: '- 라벨:' 글머리 요약도 검사, 표에 없는 숫자(범위 일반화)·추측성('가능성이 큽니다') 항목 제거, 근거 토큰 0.7, '요약:' 빈 머리 제거, '알 수 없음' 칸 정규화
  S2 세제 효과 단정 완화('같은 효과(요건 충족 시)', '요건을 충족하면 줄어들 수'), 마무리 '전문가와 상담' 제거  B3 적용 시점(4주·2주) 근거 보강(근거 문서에 있을 때만)
자동백업·자가검증. 이미 v13.85이면 스킵. 검증 md5==3d743021166bad4504c1d9a9b2874085"""






import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='51c38192a8cf04afd06d4431a30cfedd'
EXPECT_AFTER='3d743021166bad4504c1d9a9b2874085'
HUNKS=[["                and qtype != \"추천\" and not re.search(r\"유리|먼저|어디|추천\", question) and not re.search(r\"900\", ans):\n", "                and qtype != \"추천\" and not re.search(r\"유리|먼저|어디|추천\", question):      # v13.85: LLM 본문에 900이 있어도(되묻기 안에 섞임) 코드 문장만 — 발동을 LLM 출력에 걸지 않는다\n"], ["                ans = (_mv6 + _TAXDEF + \"\\n\\n※ 위 과세는 퇴직급여 재원에 대한 것이며, IRP에 본인이 추가로 납입한 금액의 세액공제·인출 과세는 별도로 적용됩니다.\")\n", "                ans = (_mv6.rstrip() + \"\\n\\n세금은 다음 시점에 나뉘어 부과됩니다(퇴직급여 재원 기준).\\n\"\n                       \"- IRP로 이전받는 시점: 퇴직소득세가 원천징수되지 않고 과세이연됩니다.\\n\"\n                       \"- 연금으로 수령할 때: 이연퇴직소득세를 감면(연금수령 한도 내 30%, 실제 수령연차 10년 초과분 40%)받아 납부합니다.\\n\"\n                       \"- 연금 외 일시금으로 인출하면 감면 없이 퇴직소득세가 부과됩니다.\\n\\n\"\n                       \"※ 위 과세는 퇴직급여 재원에 대한 것이며, IRP에 본인이 추가로 납입한 금액의 세액공제·인출 과세는 별도로 적용됩니다.\")   # v13.85: 시점별 분리\n"], ["            for _ln in ans.split(\"\\n\"):\n                _mi = re.match(r\"^\\s*\\d+[.)]\\s*([가-힣\\s·]{2,10})\\s*[:：]\\s*(.+)$\", _ln)\n                if _mi:\n", "            _tblnum = set(re.findall(r\"\\d+(?:\\.\\d+)?\", \" \".join(l_ for l_ in ans.split(\"\\n\") if l_.strip().startswith(\"|\"))))   # v13.85: 표 칸의 숫자 집합\n            for _ln in ans.split(\"\\n\"):\n                _mi = re.match(r\"^\\s*(?:\\d+[.)]|[-•·])\\s*([가-힣\\s·()]{2,12})\\s*[:：]\\s*(.+)$\", _ln) if not _ln.strip().startswith(\"|\") else None   # v13.85: '- 라벨: …' 글머리 요약도\n                if _mi and any(v_ not in _tblnum for v_ in re.findall(r\"\\d+(?:\\.\\d+)?\", _mi.group(2))):        # 표에 없는 숫자(범위 일반화 '0.45%-0.65%')\n                    _n16b += 1; continue\n                if _mi and re.search(r\"가능성이\\s*(?:큽|높|있)|것으로\\s*보입니다|예상됩니다|추정됩니다\", _mi.group(2)):   # 추측성 요약\n                    _n16b += 1; continue\n                if _mi:\n"], ["                    if _toks and sum(1 for t_ in _toks if t_[:3] in _evt) / len(_toks) < 0.6:\n", "                    if _toks and sum(1 for t_ in _toks if t_[:3] in _evt) / len(_toks) < 0.7:      # v13.85: 0.6 → 0.7\n"], ["            ans = re.sub(r\"(?m)^(\\|[^\\n]*)$\", lambda m_: re.sub(r\"(?:데이터|정보|자료)\\s*없음|확인\\s*불가|확인되지\\s*않음\", \"자료 없음\", m_.group(1)), ans)\n", "            ans = re.sub(r\"(?m)^(\\|[^\\n]*)$\", lambda m_: re.sub(r\"(?:데이터|정보|자료)\\s*없음|확인\\s*불가|확인되지\\s*않음|알\\s*수\\s*없음|미확인|해당\\s*없음|N/?A\", \"자료 없음\", m_.group(1)), ans)   # v13.85: '알 수 없음'\n"], ["        if system is COMPARE_SYSTEM:                                                   # v13.84: 항목이 모두 빠진 '핵심 차이 요약' 머리 제거\n            ans = re.sub(r\"(?m)^핵심 차이 요약[:：]?\\s*\\n(?=\\s*\\n|\\Z)\", \"\", ans); ans = re.sub(r\"\\n{3,}\", \"\\n\\n\", ans)\n", "        if system is COMPARE_SYSTEM:                                                   # v13.84/85: 항목이 모두 빠진 '핵심 차이 요약'·'요약:' 머리 제거\n            ans = re.sub(r\"(?m)^(?:핵심\\s*차이\\s*)?요약[:：]?\\s*\\n(?=\\s*\\n|\\Z)\", \"\", ans); ans = re.sub(r\"\\n{3,}\", \"\\n\\n\", ans)\n"], ["                _kp = [s_ for s_ in _ss if not re.search(r\"추천\\s*(?:드립니다|합니다|드려요|해\\s*드립니다)|권장\\s*(?:드립니다|합니다|드려요)|권해\\s*드립니다\", s_)]\n", "                _kp = [s_ for s_ in _ss if not re.search(r\"추천\\s*(?:드립니다|합니다|드려요|해\\s*드립니다)|권장\\s*(?:드립니다|합니다|드려요)|권해\\s*드립니다|전문가(?:와|에게)\\s*(?:상담|상의|문의)하(?:는\\s*것이\\s*좋|시기\\s*바랍니다|세요|시길)\", s_)]   # v13.85: 전문가 상담 권유\n"], ["        # v13.84(B3) [디폴트옵션 제도 설명 범위 계약]", "        # v13.85(S2) [세제 효과 표현 계약]: '동일한 효과를 얻을 수 있습니다', '효과적으로 줄일 수 있습니다' 같은 결과 단정은 요건 충족을 전제로 한 조건형으로\n        if qtype == \"세제\" or re.search(r\"세금|절세|세액|과세\", question):\n            ans, _n85 = re.subn(r\"동일한\\s*효과를\\s*얻을\\s*수\\s*있습니다\", \"같은 효과를 얻을 수 있습니다(요건 충족 시)\", ans)\n            ans, _n85b = re.subn(r\"(퇴직소득세|세금|세\\s*부담|세부담|세액)(?:을|를)\\s*효과적으로\\s*(?:줄일|절감할|관리할)\\s*수\\s*있(?:습니다|으니)\",\n                                 lambda m_: m_.group(1) + (\"이\" if m_.group(1).endswith((\"금\", \"담\", \"액\")) else \"가\") + \" 요건을 충족하면 줄어들 수 있습니다\", ans)\n            ans = re.sub(r\"효과적으로\\s*(?:줄일|절감할|관리할)\\s*수\\s*있(?:습니다|으니)\", \"요건을 충족하면 줄어들 수 있습니다\", ans)\n            ans = re.sub(r\"줄어들\\s*수\\s*있습니다\\s*상황에\\s*맞게[^.!?\\n]*[.!?]\", \"줄어들 수 있습니다.\", ans)\n            if _n85 or _n85b:\n                clean_note += f\" 세제 효과 단정 완화 {_n85 + _n85b}건\"\n        # v13.84(B3) [디폴트옵션 제도 설명 범위 계약]"], ["            if \"적용 조건\" not in ans:\n", "            # v13.85(B3) [적용 시점 근거 보강]: 질문이 '언제 적용'을 물었는데 답변에 4주·2주 시점이 없으면 근거 문서(doc31 Q3)의 시점을 코드가 붙인다\n            if re.search(r\"언제|시점|적용\", question) and not re.search(r\"4\\s*주\", ans) and any(re.search(r\"4\\s*주\\s*후\\s*익영업일|만기일로부터\\s*4주\", c_.get(\"text\", \"\")) for c_ in used):\n                ans = ans.rstrip() + (\"\\n\\n적용 시점(근거 문서 기준): 운용상품의 만기가 도래하면 만기일로부터 4주 후 익영업일에 디폴트옵션 적용 통지를 받고, 통지 후 2주 이내에 별도의 운용지시가 없으면 디폴트옵션 상품으로 매수됩니다.\"\n                                     + (\" 2022년 12월 2일 이후 신규 가입자는 최초 부담금 납입 익영업일에 통지를 받습니다.\" if any(\"최초 부담금\" in c_.get(\"text\", \"\") for c_ in used) else \"\"))\n                clean_note += \" 디폴트옵션 적용 시점 근거 보강\"\n            if \"적용 조건\" not in ans:\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "v13.85(S2) [세제 효과 표현 계약]" in src: print("[스킵] 이미 v13.85 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[중단] 적용전 md5가 예상 v1384와 다름 → 서버 파일이 갈라짐. main_v1385_full.py 로 통째 교체하세요."); sys.exit(4)
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v1384_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
