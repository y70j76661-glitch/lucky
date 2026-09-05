# -*- coding: utf-8 -*-
"""patch_v130.py — v129(b49881c6) main.py 에 v13.0 적용.
  [공통 검증층 2] 정보부족 안전모드: '나이·성향 모두 미상(되묻기 모드)'으로 판정된 추천에만
  단정 고정문구 완화('가장 적합할 것입니다'→'우선 고려 대상이 될 수 있습니다' 등).
  성향·소득을 준 맞춤 모드 질문은 건드리지 않음(조건 있는 질문 일괄 완화 금지).
자동백업·자가검증. 이미 v13.0이면 스킵. 검증 md5==32a19ceb289af98c68d8ef562de0a21e"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='b49881c61a2e1245edf67dabc53abb2c'
EXPECT_AFTER='32a19ceb289af98c68d8ef562de0a21e'
HUNKS=[["                                      \"단정하기는 어려우며, 투자기간·손실 감내 수준·기존 \"\n                                      \"자산배분 등을 함께 고려하셔야 합니다.\")\n                clean_note += \" 추천 균형 캐비엇 보강\"\n            # ⑤ v9.99u: 수익률·성과 수치가 있으면 '과거 성과≠미래 보장' 1회 고지\n            if re.search(r\"수익률|초과수익|\\d+(?:\\.\\d+)?\\s*%|성과\", ans) \\\n                    and \"미래 수익을 보장\" not in ans and \"미래의 수익을 보장\" not in ans:\n", "                                      \"단정하기는 어려우며, 투자기간·손실 감내 수준·기존 \"\n                                      \"자산배분 등을 함께 고려하셔야 합니다.\")\n                clean_note += \" 추천 균형 캐비엇 보강\"\n            # [공통검증층 2단계] v13.0: '정보 부족'(나이·성향 모두 미상 → 되묻기 모드)으로 판정된\n            #   추천에만 단정 표현을 완화한다. 성향·소득을 준 맞춤 모드 질문은 건드리지 않는다\n            #   (사용자 제약: 조건이 있는 질문까지 일괄 완화 금지 → 답변 약화 방지). 고정문구만.\n            if was_askback:\n                _soft = [(\"가장 적합할 것입니다\", \"우선 고려 대상이 될 수 있습니다\"),\n                         (\"가장 적합합니다\", \"우선 고려 대상이 됩니다\"),\n                         (\"가장 적합한 상품입니다\", \"우선 고려해 볼 수 있는 상품입니다\"),\n                         (\"가장 적합한\", \"우선 고려해 볼 만한\"),\n                         (\"가장 좋은 상품입니다\", \"고려해 볼 수 있는 상품입니다\")]\n                _ns = 0\n                for _a, _b in _soft:\n                    if _a in ans:\n                        ans = ans.replace(_a, _b)\n                        _ns += 1\n                if _ns:\n                    clean_note += f\" 정보부족 추천 단정완화 {_ns}건\"\n            # ⑤ v9.99u: 수익률·성과 수치가 있으면 '과거 성과≠미래 보장' 1회 고지\n            if re.search(r\"수익률|초과수익|\\d+(?:\\.\\d+)?\\s*%|성과\", ans) \\\n                    and \"미래 수익을 보장\" not in ans and \"미래의 수익을 보장\" not in ans:\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "[공통검증층 2단계] v13.0" in src: print("[스킵] 이미 v13.0 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[경고] 적용전 md5가 예상 v129와 다름. 훅 매칭되면 계속.")
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v129_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
