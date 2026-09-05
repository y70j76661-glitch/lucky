# -*- coding: utf-8 -*-
"""patch_v1347.py — v1346(2a1cc65e) main.py 에 v13.47 적용. (v1346 적용 후 실행)
  [실측 mini24] ① 블록 안 1~6 밖 등급 오출력('16등급')은 자리표시가 되기 전에 근거 등급으로 채움 ② 도입·맺음 중복 표준 문장 제거가 항목 기호(- ) 줄에도 적용
   ③ 펀드 서술 계약: '원금 손실 가능성을 최소화' 단정 포함 ④ 근거 없는 절세 단정('이자소득세를 피할 수 있는 장점') 제거
자동백업·자가검증. 이미 v13.47이면 스킵. 검증 md5==6296e8a0f8b1228b40cc1256743b08ea"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='2a1cc65e154046b44f722a22de506d97'
EXPECT_AFTER='6296e8a0f8b1228b40cc1256743b08ea'
HUNKS=[["        _ph = \"(위험등급: 자료에서 확인 필요)\"\n        if any(_ph in l for l in others):\n            others = [l.replace(_ph, g0 + \"등급\") for l in others]\n            st[\"fix\"] += 1\n", "        _ph = \"(위험등급: 자료에서 확인 필요)\"\n        if any(_ph in l for l in others):\n            others = [l.replace(_ph, g0 + \"등급\") for l in others]\n            st[\"fix\"] += 1\n        # v13.47(R2 실측): 1~6 밖의 등급 표기('16등급' 같은 오출력)는 뒤 단계가 자리표시로 바꾸기 전에 근거 등급으로 채운다\n        _bad2 = re.compile(r\"(?<![\\d.])\\d{2,}(\\s*등급)\")\n        if any(_bad2.search(l) for l in others):\n            others = [_bad2.sub(lambda mm: g0 + mm.group(1), l) for l in others]\n            st[\"fix\"] += 1\n"], ["                ss = re.split(r\"(?<=[.!?])\\s+\", l.strip())\n                kp = [x for x in ss if not _BAD_CLAIM.search(x)\n                      and (pi in _done or (re.sub(r\"\\s+\", \"\", x) not in _cav and not (_cav and _GEN_CANON.match(x))))]\n                if len(kp) != len(ss):\n                    st[\"fix\"] += len(ss) - len(kp)\n                    if kp:\n                        _nl.append(re.match(r\"^\\s*\", l).group(0) + \" \".join(kp))\n                else:\n                    _nl.append(l)", "                _lead = re.match(r\"^\\s*(?:[-•·*]\\s*|\\d+[.)]\\s*)?\", l).group(0)     # v13.47: 항목 기호는 떼고 문장을 본다\n                ss = re.split(r\"(?<=[.!?])\\s+\", l[len(_lead):].strip())\n                kp = [x for x in ss if not _BAD_CLAIM.search(x)\n                      and (pi in _done or (re.sub(r\"\\s+\", \"\", x) not in _cav and not (_cav and _GEN_CANON.match(x))))]\n                if len(kp) != len(ss):\n                    st[\"fix\"] += len(ss) - len(kp)\n                    if kp:\n                        _nl.append(_lead + \" \".join(kp))\n                else:\n                    _nl.append(l)"], ["    _BAD_CLAIM = re.compile(r\"고소득자(?:에게|일수록|층에)?\\s*(?:더욱?\\s*)?유리\")", "    _BAD_CLAIM = re.compile(r\"고소득자(?:에게|일수록|층에)?\\s*(?:더욱?\\s*)?유리|(?:이자소득세|기타소득세|세금|과세)[^.!?]{0,15}(?:피할\\s*수|회피|면제받)\")   # v13.47: 근거 없는 절세 단정"], ["r\"손실(?:의\\s*가능성|\\s*위험)?[을이]?\\s*(?:최소화|거의\\s*없|없)|", "r\"손실(?:의?\\s*가능성|\\s*위험)?[을이]?\\s*(?:최소화|거의\\s*없|없)|"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "v13.47(R2 실측)" in src: print("[스킵] 이미 v13.47 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[경고] 적용전 md5가 예상 v1346과 다름. 훅 매칭되면 계속.")
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v1346_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
