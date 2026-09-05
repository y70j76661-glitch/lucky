# -*- coding: utf-8 -*-
"""patch_v1388.py — v1387(9ec67bde) main.py 에 v13.88 적용. (v1387 적용 후 실행) — 2훅
  S3 '16.5%(지방소득세 포함)%가' 글리치 정리  T15 비교 답변: 질문이 세제를 묻지 않으면 '세액공제 가능' 요약 문장 제거, 위험등급 행 '자료 없음' → '확정하지 못함' 표기 통일(C10)
자동백업·자가검증. 이미 v13.88이면 스킵. 검증 md5==03f0e295929a33d543c45ad57d7df80c"""









import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='9ec67bdecec6fe9c86baeccfa4574e3d'
EXPECT_AFTER='03f0e295929a33d543c45ad57d7df80c'
HUNKS=[["    if not ans:\n        return ans\n", "    if not ans:\n        return ans\n    ans = re.sub(r\"(\\d\\s*%\\s*\\([^()\\n]{1,20}\\))\\s*%\", r\"\\1\", ans)                    # v13.88: '16.5%(지방소득세 포함)%가' 글리치\n"], ["            # v13.84(T15) [안정성 비교 도입문 — 코드 생성]", "            # v13.88(T15) [비교 답변 관련성]: 질문이 세제를 묻지 않으면 '세액공제 가능' 류 문장(표 밖 요약·산문)은 계좌 단위 혜택이라 제거; 위험등급 행의 미확정 표기 통일\n            if not re.search(r\"세제|세금|세액|과세|공제\", question):\n                _o88, _n88 = [], 0\n                for _ln in ans.split(\"\\n\"):\n                    if not _is_prose_line(_ln) and not re.match(r\"^\\s*\\d+[.)]\\s\", _ln):\n                        _o88.append(_ln); continue\n                    _lead = _PROSE_LEAD.match(_ln).group(0)\n                    _ss = re.split(r\"(?<=[.!?])\\s+\", _ln[len(_lead):])\n                    _kp = [s_ for s_ in _ss if not re.search(r\"세액\\s*공제|세제\\s*혜택\", s_)]\n                    _n88 += len(_ss) - len(_kp)\n                    if not _ln.strip():\n                        _o88.append(_ln)\n                    elif _kp:\n                        _o88.append(_lead + \" \".join(_kp))\n                if _n88:\n                    ans = re.sub(r\"\\n{3,}\", \"\\n\\n\", \"\\n\".join(_o88)); clean_note += f\" 질문 밖 세제 문장 {_n88}건 제거\"\n            ans = re.sub(r\"(?m)^(\\|\\s*위험\\s*등급\\s*\\|[^\\n]*)$\", lambda m_: re.sub(r\"(?<=\\|)\\s*자료\\s*없음\\s*(?=\\|)\", \" 자료에서 확정하지 못함(해당 상품 투자설명서 미특정) \", m_.group(1)), ans)\n            # v13.84(T15) [안정성 비교 도입문 — 코드 생성]"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "v13.88(T15) [비교 답변 관련성]" in src: print("[스킵] 이미 v13.88 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[중단] 적용전 md5가 예상 v1387과 다름 → 서버 파일이 갈라짐. main_v1388_full.py 로 통째 교체하세요."); sys.exit(4)
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v1387_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
