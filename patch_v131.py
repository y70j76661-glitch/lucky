# -*- coding: utf-8 -*-
"""patch_v131.py (갱신본) — v130(32a19ceb) main.py 에 v13.1 적용.
  [공통 검증층 4단계] 출력품질 2건:
   (H) 미닫힘 따옴표 정리 — 본문 따옴표 홀수면 짝 없는(마지막) 따옴표만 제거(실측 G01).
   (I) 마크다운 이스케이프 잔재 제거 — 특수문자 앞 백슬래시('\~','\*' 등) 제거(3.3\~5.5%→3.3~5.5%).
  둘 다 내용 불변, [참고 문서] 영역 미접촉. 앞서 보낸 v131 대체.
자동백업·자가검증. 이미 v13.1이면 스킵. 검증 md5==827b029ecafcc218246be0b7d9be0817"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='32a19ceb289af98c68d8ef562de0a21e'
EXPECT_AFTER='827b029ecafcc218246be0b7d9be0817'
HUNKS=[["    # G) v12.6: 마크다운 볼드 마커 제거 — 평가/표시 화면이 raw 텍스트여도 '**'가 글자로\n    #    노출되지 않도록 최종 답변에서 볼드 마커만 뗀다(내용·숫자·간격은 그대로).\n    ans = ans.replace(\"**\", \"\")\n    return ans.strip()\n\n\n", "    # G) v12.6: 마크다운 볼드 마커 제거 — 평가/표시 화면이 raw 텍스트여도 '**'가 글자로\n    #    노출되지 않도록 최종 답변에서 볼드 마커만 뗀다(내용·숫자·간격은 그대로).\n    ans = ans.replace(\"**\", \"\")\n    # H) v13.1(4단계): 미닫힘 따옴표 정리 — 본문의 따옴표 개수가 홀수면 짝 없는(마지막) 따옴표만\n    #    제거한다. 한국어 본문의 따옴표는 열고-닫음 쌍이라 홀수 = 미닫힘(실측 G01 '부득이한 사유(…).\n    #    [참고 문서] 줄은 이미 분리된 상태라 안전. 내용은 안 건드리고 고아 마커만 뗀다.\n    for _qc in (\"'\", '\"'):\n        if ans.count(_qc) % 2 == 1:\n            _last = ans.rfind(_qc)\n            ans = ans[:_last] + ans[_last + 1:]\n    # I) v13.1(4단계): 마크다운 이스케이프 잔재 제거 — 특수문자 앞 백슬래시('\\~','\\*','\\_' 등)를\n    #    뗀다(예: '3.3\\~5.5%' → '3.3~5.5%'). 한국어 본문엔 정상 백슬래시가 없어 안전. 내용 불변.\n    ans = re.sub(r\"\\\\(?=[^\\w\\s])\", \"\", ans)\n    return ans.strip()\n\n\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "v13.1(4단계)" in src: print("[스킵] 이미 v13.1 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[경고] 적용전 md5가 예상 v130과 다름. 훅 매칭되면 계속.")
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v130_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
