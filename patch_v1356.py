# -*- coding: utf-8 -*-
"""patch_v1356.py — v1355(3cb5efec) main.py 에 v13.56 적용. (v1355 적용 후 실행)
  [비교 불변식 강화·추천 표현] ① 비교표 상품 중 등급 미확정이 하나라도 있으면 표 밖의 등급·위험 우열 관계 문장(숫자 유무 무관: '위험등급이 더 낮습니다')을
   모두 제거하고 코드의 '확정 불가' 결론만 남김(T6) ② 펀드 서술 계약에 '안정성을 극대화/최대화' 단정 추가(M2) ③ 추천 후보 0일 때 대체 답변은 확인 필요 조건 안내로
자동백업·자가검증. 이미 v13.56이면 스킵. 검증 md5==9b248654ec4e712ec55f662630cf64f7"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='3cb5efece4642860d4aa53d591ce62dc'
EXPECT_AFTER='9b248654ec4e712ec55f662630cf64f7'
HUNKS=[["                if _nd2:\n                    ans = \"\\n\".join(_out2)\n                    clean_note += f\" 미검증 등급 문장 {_nd2}건 제거\"", "                if _nd2:\n                    ans = \"\\n\".join(_out2)\n                    clean_note += f\" 미검증 등급 문장 {_nd2}건 제거\"\n                # v13.56 [비교 불변식 강화]: 머리말 상품 중 등급 미확정이 하나라도 있으면, 표 밖의 등급·위험 우열 관계 문장(숫자 없어도)을 모두 제거한다.\n                #   결론은 아래 코드 문장('현재 자료만으로는 우열을 확정할 수 없습니다')만 남긴다.\n                if len(_known) < len(_hp):\n                    _REL = re.compile(r\"(?:등급|위험(?:도|성)?)[^.!?\\n]{0,30}?(?:더|보다|가장|상대적으로|비교적)[^.!?\\n]{0,15}?(?:낮|높|안전|우위|우열)|\"\n                                      r\"(?:더|보다|가장|상대적으로|비교적)[^.!?\\n]{0,15}?(?:낮|높|안전)[^.!?\\n]{0,20}?(?:등급|위험)|(?:등급|위험)[^.!?\\n]{0,20}?(?:우위|우열|낮습니다|높습니다)\")\n                    _out3, _nd3 = [], 0\n                    for _ln in ans.split(\"\\n\"):\n                        if _ln.lstrip().startswith((\"|\", \"※\", \"[\", \"(\", \"-\")) or \"위험등급 우열:\" in _ln:\n                            _out3.append(_ln); continue\n                        _lead = re.match(r\"^\\s*(?:\\d+[.)]\\s*)?\", _ln).group(0)\n                        _ss = re.split(r\"(?<=[.!?])\\s+\", _ln[len(_lead):])\n                        _kp = [s_ for s_ in _ss if not _REL.search(s_)]\n                        _nd3 += len(_ss) - len(_kp)\n                        if not _ln.strip():\n                            _out3.append(_ln)\n                        elif _kp:\n                            _out3.append(_lead + \" \".join(_kp))\n                    if _nd3:\n                        ans = \"\\n\".join(_out3)\n                        clean_note += f\" 미확정 등급 우열 관계 문장 {_nd3}건 제거\""], ["r\"안전성을\\s*(?:제공|보장)|손실(?:의)?\\s*가능성이\\s*(?:매우|거의|아주)\\s*낮|안정성이\\s*(?:가장\\s*)?높\")", "r\"안전성을\\s*(?:제공|보장)|손실(?:의)?\\s*가능성이\\s*(?:매우|거의|아주)\\s*낮|안정성이\\s*(?:가장\\s*)?높|안정성을\\s*(?:극대화|최대화|높이|확보)\")   # v13.56: 안정성을 극대화 단정"], ["            body = (\"문의하신 조건에 맞는 상품을 제공된 자료 안에서 확정하지 못했습니다. 투자 기간·감내 위험·계좌 종류를 알려주시면 \"\n                    \"제공된 자료 범위에서 다시 확인해 드리겠습니다.\")", "            body = (\"문의하신 조건에 맞는 특정 상품을 제공된 자료 안에서 확정하지 못했습니다. 현재 확인된 자료만으로 특정 상품을 추천하기보다, \"\n                    \"투자 기간·손실 감내 수준·계좌 종류(연금저축/IRP)를 추가로 확인한 뒤 후보를 좁히는 것이 적절합니다. 알려주시면 제공된 자료 범위에서 다시 확인해 드리겠습니다.\")"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "v13.56 [비교 불변식 강화]" in src: print("[스킵] 이미 v13.56 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[경고] 적용전 md5가 예상 v1355와 다름. 훅 매칭되면 계속.")
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v1355_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
