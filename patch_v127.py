# -*- coding: utf-8 -*-
"""patch_v127.py — v126(5d53e2d0) main.py 에 v12.7 적용.
  빈불릿 제거: 내용 없는 고아 리스트 마커('1.'만 있는 줄) 제거 + C)병합이 마커끼리 붙지 않게 보강.
  (추천 답변의 빈 항목 결함 G11 대응. 정상 번호목록·내용 줄은 보존.)
자동백업·자가검증. 이미 v12.7면 스킵. 검증 md5==27e76a370e8194d184695d1a80420fb2"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='5d53e2d0f1f60cecccca1e0bf5c8585f'
EXPECT_AFTER='27e76a370e8194d184695d1a80420fb2'
HUNKS=[["    ans = re.sub(r\"자료\\s*원문\\s*아래\\s*참고\\s*문서\", \"자료 원문\", ans)\n    ans = re.sub(r\"제공된\\s*자료\\s*아래\\s*참고\\s*문서\", \"아래 참고 문서\", ans)\n    lines = ans.split(\"\\n\")\n    # C) 깨진 번호목록 병합\n    merged = []\n    i = 0\n    while i < len(lines):\n        cur = lines[i]\n        if re.fullmatch(r\"\\s*\\d+[.)]\\s*\", cur) and i + 1 < len(lines) and lines[i + 1].strip():\n            merged.append(cur.rstrip() + \" \" + lines[i + 1].lstrip())\n            i += 2\n            continue\n        merged.append(cur)\n        i += 1\n    lines = merged\n    # D) 연속 중복 줄 제거(목록마커·공백 무시)\n    def _key(ln):\n        k = re.sub(r\"^\\s*(?:\\d+[.)]|[-*•])\\s*\", \"\", ln)\n", "    ans = re.sub(r\"자료\\s*원문\\s*아래\\s*참고\\s*문서\", \"자료 원문\", ans)\n    ans = re.sub(r\"제공된\\s*자료\\s*아래\\s*참고\\s*문서\", \"아래 참고 문서\", ans)\n    lines = ans.split(\"\\n\")\n    # C) 깨진 번호목록 병합 (단, 다음 줄이 또 다른 목록마커면 병합 안 함 — 마커끼리 붙는 것 방지)\n    merged = []\n    i = 0\n    while i < len(lines):\n        cur = lines[i]\n        if re.fullmatch(r\"\\s*\\d+[.)]\\s*\", cur) and i + 1 < len(lines) and lines[i + 1].strip() \\\n                and not re.match(r\"\\s*(?:\\d+[.)]|[-*•·])\\s\", lines[i + 1]):\n            merged.append(cur.rstrip() + \" \" + lines[i + 1].lstrip())\n            i += 2\n            continue\n        merged.append(cur)\n        i += 1\n    lines = merged\n    # C2) v12.7: 내용 없는 고아 리스트 마커('1.'·'-'만 있는 줄) 제거 — 빈불릿 버그(G11).\n    #   병합(C)에서 내용이 붙지 못하고 남은 마커는 빈 항목이므로 뗀다(내용 줄은 보존).\n    lines = [ln for ln in lines if not re.fullmatch(r\"\\s*(?:\\d+[.)]|[-*•·])\\s*\", ln)]\n    # D) 연속 중복 줄 제거(목록마커·공백 무시)\n    def _key(ln):\n        k = re.sub(r\"^\\s*(?:\\d+[.)]|[-*•])\\s*\", \"\", ln)\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "v12.7:" in src: print("[스킵] 이미 v12.7 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[경고] 적용전 md5가 예상 v126과 다름. 훅 매칭되면 계속.")
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v126_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
