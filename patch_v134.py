# -*- coding: utf-8 -*-
"""patch_v134.py — v133(04a321f6) main.py 에 v13.4 적용.
  [갭1 결정적 확장] 결정적으로 판정 가능한 형식 오류만 추가(퍼지 없음, 내용 불변):
   J1 중복 단위('%%'→'%', '원원'→'원'), J2 미닫힘 괄호(짝 없는 쪽 하나 제거), J3 완전 동일 ※주석 중복 제거.
  전부 맞는 텍스트엔 절대 걸리지 않는 조합만.
자동백업·자가검증. 이미 v13.4면 스킵. 검증 md5==68b79e50ac9aaa415bd4f0acae02fbaa"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='04a321f61ccd1be6cdaec1d519175c24'
EXPECT_AFTER='68b79e50ac9aaa415bd4f0acae02fbaa'
HUNKS=[["    # I) v13.1(4단계): 마크다운 이스케이프 잔재 제거 — 특수문자 앞 백슬래시('\\~','\\*','\\_' 등)를\n    #    뗀다(예: '3.3\\~5.5%' → '3.3~5.5%'). 한국어 본문엔 정상 백슬래시가 없어 안전. 내용 불변.\n    ans = re.sub(r\"\\\\(?=[^\\w\\s])\", \"\", ans)\n    return ans.strip()\n\n\n", "    # I) v13.1(4단계): 마크다운 이스케이프 잔재 제거 — 특수문자 앞 백슬래시('\\~','\\*','\\_' 등)를\n    #    뗀다(예: '3.3\\~5.5%' → '3.3~5.5%'). 한국어 본문엔 정상 백슬래시가 없어 안전. 내용 불변.\n    ans = re.sub(r\"\\\\(?=[^\\w\\s])\", \"\", ans)\n    # J) v13.4(갭1 결정적 확장): 결정적으로 판정 가능한 형식 오류만 추가(퍼지 없음, 내용 불변).\n    #    J1 중복 단위: '%%'→'%', '원원'→'원', '만원원'→'만원' (맞는 텍스트엔 절대 없는 조합)\n    ans = re.sub(r\"%\\s*%\", \"%\", ans)\n    ans = re.sub(r\"원\\s*원\", \"원\", ans)     # 만원원·천원원·원원 모두 → 단일 '원'\n    #    J2 미닫힘 괄호: '(' 와 ')' 개수가 다르면 짝 없는 마지막 쪽 하나만 제거(따옴표 H와 동일 원칙)\n    _op, _cl = ans.count(\"(\"), ans.count(\")\")\n    if _op > _cl:\n        _p = ans.rfind(\"(\"); ans = ans[:_p] + ans[_p + 1:]\n    elif _cl > _op:\n        _p = ans.rfind(\")\"); ans = ans[:_p] + ans[_p + 1:]\n    #    J3 완전 동일 ※주석 중복: 같은 ※줄(공백 무시 exact)이 2회 이상이면 첫 것만 유지\n    _seen, _kept = set(), []\n    for _ln in ans.split(\"\\n\"):\n        if _ln.strip().startswith(\"※\"):\n            _k = re.sub(r\"\\s+\", \"\", _ln)\n            if _k in _seen:\n                continue\n            _seen.add(_k)\n        _kept.append(_ln)\n    ans = \"\\n\".join(_kept)\n    return ans.strip()\n\n\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "v13.4(갭1 결정적 확장)" in src: print("[스킵] 이미 v13.4 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[경고] 적용전 md5가 예상 v133과 다름. 훅 매칭되면 계속.")
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v133_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
