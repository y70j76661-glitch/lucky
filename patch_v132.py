# -*- coding: utf-8 -*-
"""patch_v132.py — v131(827b029e) main.py 에 v13.2 적용.
  [갭6 렌더안전] 채점 화면이 raw 텍스트여도 깨지지 않게: '###' 헤더 마커 제거(텍스트 유지),
  '| 표 |' → '(항목 — 열A vs 열B)' + '- 행: 값A; 값B' plain-text 변환. 내용·숫자 불변, 형식만.
  ①②③·※·- 불릿·[참고 문서]는 raw에서도 정상이라 미접촉. 비표 답변은 완전 불변.
자동백업·자가검증. 이미 v13.2면 스킵. 검증 md5==d7a132e91d5f1c5d56182ced85a1b876"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='827b029ecafcc218246be0b7d9be0817'
EXPECT_AFTER='d7a132e91d5f1c5d56182ced85a1b876'
HUNKS=[["    \"\"\"\n    if not ans:\n        return ans\n    # A) 볼드-퍼센트 글리치\n    ans = re.sub(r\"\\*\\*\\s*(\\d+(?:[.,]\\d+)?)\\s*\\*\\*\\s*%\", r\"**\\1%**\", ans)\n    ans = re.sub(r\"(\\d(?:[.,]\\d+)?)\\s*\\*\\*\\s*%\", r\"\\1%\", ans)\n", "    \"\"\"\n    if not ans:\n        return ans\n    # 0) v13.2(갭6 렌더안전): 채점 화면이 raw 텍스트면 깨지는 마크다운을 plain-text로 변환.\n    #    ### 헤더 → 마커 제거(텍스트 유지), | 표 | → '(항목 — 열A / 열B)' + '- 행: 값A / 값B'.\n    #    내용·숫자 불변, 형식만. ①②③·※·- 불릿·[참고 문서]는 raw에서도 정상이라 안 건드림.\n    ans = re.sub(r\"(?m)^\\s*#{1,6}\\s+\", \"\", ans)   # 마크다운 헤더 마커 제거\n    if re.search(r\"(?m)^\\s*\\|.*\\|\\s*$\", ans):\n        _tl = ans.split(\"\\n\")\n        _to = []\n        _ti = 0\n        while _ti < len(_tl):\n            if re.match(r\"\\s*\\|.*\\|\\s*$\", _tl[_ti]) and _ti + 1 < len(_tl) \\\n                    and re.match(r\"\\s*\\|[\\s:\\-|]+\\|\\s*$\", _tl[_ti + 1]):\n                _hd = [c.strip() for c in _tl[_ti].strip().strip(\"|\").split(\"|\")]\n                if _hd[1:]:\n                    _to.append(f\"({_hd[0]} — \" + \" vs \".join(_hd[1:]) + \")\")\n                _ti += 2\n                while _ti < len(_tl) and re.match(r\"\\s*\\|.*\\|\\s*$\", _tl[_ti]):\n                    _ce = [c.strip() for c in _tl[_ti].strip().strip(\"|\").split(\"|\")]\n                    if _ce and any(_ce):\n                        _to.append(f\"- {_ce[0]}: \" + \"; \".join(_ce[1:]) if _ce[1:] else f\"- {_ce[0]}\")\n                    _ti += 1\n            else:\n                _to.append(_tl[_ti])\n                _ti += 1\n        ans = \"\\n\".join(_to)\n    # A) 볼드-퍼센트 글리치\n    ans = re.sub(r\"\\*\\*\\s*(\\d+(?:[.,]\\d+)?)\\s*\\*\\*\\s*%\", r\"**\\1%**\", ans)\n    ans = re.sub(r\"(\\d(?:[.,]\\d+)?)\\s*\\*\\*\\s*%\", r\"\\1%\", ans)\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "v13.2(갭6 렌더안전)" in src: print("[스킵] 이미 v13.2 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[경고] 적용전 md5가 예상 v131과 다름. 훅 매칭되면 계속.")
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v131_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
