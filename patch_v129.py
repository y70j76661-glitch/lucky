# -*- coding: utf-8 -*-
"""patch_v129.py (갱신본) — v128(cdfe8f33) main.py 에 v12.9 적용.
  [공통 검증층 1] 단위 중첩 오표기 일반화(안전제약판): 'N만 M천만원'을 패턴으로 잡되,
  답변에 계산/세율 맥락(×·곱·계산·%)이 있어 '원문표기 ↔ 계산결과' 충돌 근거가 있을 때만
  'N만 M천원'으로 정정. 계산맥락 없는 고립 수치·잘못표기 문맥·정상 숫자는 불변.
자동백업·자가검증. 이미 v12.9면 스킵. 검증 md5==b49881c61a2e1245edf67dabc53abb2c"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='cdfe8f33bb2797d20a0e662cd69d18ab'
EXPECT_AFTER='b49881c61a2e1245edf67dabc53abb2c'
HUNKS=[["                    clean_note += \" 단위 오표기 고지 보강\"\n                    break\n\n        # (1-4e) v12.5(G05): '최대 세액공제액'을 물으면 그 값은 '대상 납입액을 모두 채웠을 때의\n        #   상한'이다. 실제 개인 공제액은 소득·납입액·세율에 따라 다를 수 있음을 한 줄로 구분해 붙인다.\n        if re.search(r\"최대|최고|얼마까지\", question) \\\n", "                    clean_note += \" 단위 오표기 고지 보강\"\n                    break\n\n        # (1-4f) v12.9(일반화): 단위 중첩 오표기 'N만 M천만원'(만+천만 동시 = 불가능한 중첩)을\n        #   NUMBER_NOTES 하드코딩에 없어도 패턴으로 잡아 계산값 'N만 M천원'으로 바로잡는다.\n        #   [1단계 안전제약] '근거 숫자 임의 변경' 금지 — 답변에 계산/세율 맥락(×·곱·계산·%)이 있어\n        #   '원문 표기 ↔ 계산 결과'가 충돌하는 근거가 있을 때만 정정한다. 계산 맥락 없이 고립된\n        #   수치는 건드리지 않는다. 또 \"'…'으로 잘못 표기/오기\"라 밝힌 문맥도 보존(v12.3 G05).\n        if re.search(r\"[×xX]|곱|계산|%\", ans):\n            def _stack_fix(_m):\n                if re.search(r\"잘못|오기|오표기|틀리\", ans[_m.end():_m.end() + 14]):\n                    return _m.group(0)\n                return f\"{_m.group(1)}만 {_m.group(2)}천원\"\n            _stacked, _sc = re.subn(r\"(\\d+)\\s*만\\s*(\\d+)\\s*천\\s*만\\s*원\", _stack_fix, ans)\n            if _sc and _stacked != ans:\n                ans = _stacked\n                clean_note += \" 단위중첩 오표기 정정(계산맥락)\"\n\n        # (1-4e) v12.5(G05): '최대 세액공제액'을 물으면 그 값은 '대상 납입액을 모두 채웠을 때의\n        #   상한'이다. 실제 개인 공제액은 소득·납입액·세율에 따라 다를 수 있음을 한 줄로 구분해 붙인다.\n        if re.search(r\"최대|최고|얼마까지\", question) \\\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "v12.9(일반화)" in src: print("[스킵] 이미 v12.9 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[경고] 적용전 md5가 예상 v128과 다름. 훅 매칭되면 계속.")
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v128_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
