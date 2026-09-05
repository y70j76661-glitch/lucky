# -*- coding: utf-8 -*-
"""patch_v1371.py — v1370(5e8bafde) main.py 에 v13.71 적용. (v1370 적용 후 실행)
  [mini47 리뷰 반영] ① B11 중도해지 과세 재원 계약: '운용수익에는 세금이 부과되지 않는다'(근거와 반대) → '운용수익은 세액공제 납입금과 함께 기타소득세 16.5퍼센트 대상, 과세제외금액만 비과세' 표준 문장
   ② S4: '양도소득으로 분류'·'양도소득세가 별도로 과세된다' 같은 근거 없는 반대 단정 제거 ③ M2: '높은 수익을 목표로 합니다' 단정 완화
자동백업·자가검증. 이미 v13.71이면 스킵. 검증 md5==ecfe18ee1484851c2b8348674990ed34"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='5e8bafde39b3a44868ec0dfe81db1f2e'
EXPECT_AFTER='ecfe18ee1484851c2b8348674990ed34'
HUNKS=[["            if _n8b:\n                ans = _b8b; clean_note += f\" 중도해지 '세금 회피' 표현 완화 {_n8b}건\"\n", "            if _n8b:\n                ans = _b8b; clean_note += f\" 중도해지 '세금 회피' 표현 완화 {_n8b}건\"\n            # v13.71(B11 실측): '세액공제를 받지 않은 부분 및 운용수익에는 별도의 세금이 부과되지 않습니다' — 운용수익은 기타소득세 16.5% 대상(근거 문서·※ 고지와 상충)\n            _b8c, _n8c = [], 0\n            for _l in ans.split(\"\\n\"):\n                if _l.lstrip().startswith((\"※\", \"[\")):\n                    _b8c.append(_l); continue\n                _lead = _PROSE_LEAD.match(_l).group(0)\n                _ss = re.split(r\"(?<=[.!?])\\s+\", _l[len(_lead):])\n                _kp = []\n                for s_ in _ss:\n                    if re.search(r\"운용\\s*수익\", s_) and re.search(r\"(?:세금이|세금은|과세가|과세는|기타소득세가|기타소득세는)?\\s*(?:부과되지\\s*않|과세되지\\s*않|비과세|세금이\\s*없)\", s_) \\\n                            and not re.search(r\"연금\\s*수령|이연|연금소득세\", s_):\n                        _kp.append(\"운용수익은 세액공제를 받은 납입금과 함께 기타소득세 16.5%의 과세 대상이며, 세액공제를 받지 않은 납입금(과세제외금액)만 인출 시 과세되지 않습니다.\")\n                        _n8c += 1; continue\n                    _kp.append(s_)\n                if not _l.strip():\n                    _b8c.append(_l)\n                elif _kp:\n                    _b8c.append(_lead + \" \".join(_kp))\n            if _n8c:\n                ans = \"\\n\".join(_b8c); clean_note += f\" 중도해지 과세 재원 교정 {_n8c}건\"\n"], ["                    if re.search(r\"통산|상계\", s_) and not re.search(r\"통산|상계\", _docs_t):\n                        _n19 += 1; continue\n", "                    if re.search(r\"통산|상계\", s_) and not re.search(r\"통산|상계\", _docs_t):\n                        _n19 += 1; continue\n                    if re.search(r\"양도소득(?:으로|세로)\\s*분류\", s_) and \"양도소득으로분류\" not in _docs_t:          # v13.71: 근거 없는 과세 체계 단정\n                        _n19 += 1; continue\n                    if re.search(r\"(?:양도소득세|배당소득세|양도소득)[^.!?\\n]{0,20}?(?:별도로\\s*)?(?:과세됩니다|부과됩니다|납부해야|과세\\s*대상입니다)\", s_) and not re.search(r\"않|이연|인출\", s_):\n                        _n19 += 1; continue                                                                        # v13.71: 표준 문장과 반대되는 '과세된다' 단정 제거\n"], ["    (re.compile(r\"고수익(?:을|이)?\\s*(?:기대하는|기대할\\s*수\\s*있는|노리는)\"), \"높은 수익을 목표로 하되 그만큼 손실 가능성도 감수하는\"),\n", "    (re.compile(r\"고수익(?:을|이)?\\s*(?:기대하는|기대할\\s*수\\s*있는|노리는)\"), \"높은 수익을 목표로 하되 그만큼 손실 가능성도 감수하는\"),\n    (re.compile(r\"높은\\s*수익(?:을|률을)?\\s*목표로\\s*(?:합니다|하는\\s*상품입니다|하고\\s*있습니다)\"), \"높은 수익을 목표로 하지만 시장 변동에 따른 원금 손실 가능성도 있습니다\"),   # v13.71(M2)\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "중도해지 과세 재원 교정" in src: print("[스킵] 이미 v13.71 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[중단] 적용전 md5가 예상 v1370과 다름 → 서버 파일이 갈라짐. main_v1371_full.py 로 통째 교체하세요."); sys.exit(4)
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v1370_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
