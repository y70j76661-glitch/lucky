# -*- coding: utf-8 -*-
"""patch_v125.py — v124(42e3522d) main.py 에 v12.5 적용.
  G05: '최대 세액공제액'에 실제 개인 공제액은 다를 수 있다는 구분 caveat(결정적).
  N01: '세액공제 받지 않았다면 그에 따른 세금' → '그 납입 원금에 대한 세금'으로 범위 명확화(결정적).
  G06: '수령 나이'만 물으면 만 55세 먼저 답하고 수급기간·거치는 섞지 말라는 제도 프롬프트 넛지.
자동백업·자가검증. 이미 v12.5면 스킵. 검증 md5==a6c8c33f71544156b67b0c446412e64d"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='42e3522d230d6961fdeb2193d502d23c'
EXPECT_AFTER='a6c8c33f71544156b67b0c446412e64d'
HUNKS=[["            \"① 연금계좌 가입기간 5년 이상 ② 만 55세 이후 인출 ③ 연간 연금수령한도 이내 인출, \"\n            \"이 세 가지다. 여기서 5년은 '계좌를 유지한 가입기간'이지 '나눠 받는 기간'이 아니다. \"\n            \"계좌에 퇴직금이 들어 있으면 가입기간 5년 요건은 적용되지 않는다.\\n\"\n            # v9.13: 소득 없는 사람의 가입 자격 오답 (오류사냥 [8]) — 근거 doc41.docx\n            \"- 가입 자격은 상품별로 구분해서 답해라. 연금저축은 소득이 없어도 누구나 가입할 수 \"\n            \"있지만, 세액공제는 종합소득(근로·사업 등)이 있어야 받을 수 있다. IRP는 직장인·\"\n", "            \"① 연금계좌 가입기간 5년 이상 ② 만 55세 이후 인출 ③ 연간 연금수령한도 이내 인출, \"\n            \"이 세 가지다. 여기서 5년은 '계좌를 유지한 가입기간'이지 '나눠 받는 기간'이 아니다. \"\n            \"계좌에 퇴직금이 들어 있으면 가입기간 5년 요건은 적용되지 않는다.\\n\"\n            # v12.5(G06): 수령 '나이'만 묻는 질문은 만 55세를 먼저 한 문장으로 답하고, 다른 요건·부수설명은 섞지 마라\n            \"- 사용자가 '수령 나이'만 물으면 먼저 '만 55세'를 한 문장으로 명확히 답해라. \"\n            \"가입기간·연간 수령한도·거치(연금대기)·수급기간 같은 다른 요건이나 부수 정보를 \"\n            \"나이 답변과 같은 문장에 섞지 말고, 필요하면 '그 밖의 수령 요건은 다음과 같습니다'처럼 \"\n            \"뒤에 분리해서 제시해라. 질문이 나이만 물었다면 수급기간·거치 설명은 넣지 않아도 된다.\\n\"\n            # v9.13: 소득 없는 사람의 가입 자격 오답 (오류사냥 [8]) — 근거 doc41.docx\n            \"- 가입 자격은 상품별로 구분해서 답해라. 연금저축은 소득이 없어도 누구나 가입할 수 \"\n            \"있지만, 세액공제는 종합소득(근로·사업 등)이 있어야 받을 수 있다. IRP는 직장인·\"\n"], ["                    clean_note += \" 단위 오표기 고지 보강\"\n                    break\n\n        # (1-4c) v9.55: 소득을 모르는데 금액을 하나로 확정하는 일이 반복된다(R31 변종).\n        #   구간 계산기가 돌았으면 두 경우를 조건 없이 코드가 붙인다.\n        if band_vals:\n", "                    clean_note += \" 단위 오표기 고지 보강\"\n                    break\n\n        # (1-4e) v12.5(G05): '최대 세액공제액'을 물으면 그 값은 '대상 납입액을 모두 채웠을 때의\n        #   상한'이다. 실제 개인 공제액은 소득·납입액·세율에 따라 다를 수 있음을 한 줄로 구분해 붙인다.\n        if re.search(r\"최대|최고|얼마까지\", question) \\\n                and re.search(r\"세액공제|공제\", question) \\\n                and re.search(r\"\\d[\\d,]*\\s*만\\s*[0-9천]*\\s*원\", ans) \\\n                and not re.search(r\"실제.*공제|달라질\\s*수|개인.*공제액\", ans):\n            ans = ans.rstrip() + (\"\\n\\n※ 참고: 위 금액은 세액공제 대상 납입액을 모두 채웠을 때의 \"\n                                  \"최대 공제액이며, 실제 공제액은 소득·납입액·적용 세율에 따라 \"\n                                  \"달라질 수 있습니다.\")\n            clean_note += \" 최대/실제 공제액 구분\"\n\n        # (1-4c) v9.55: 소득을 모르는데 금액을 하나로 확정하는 일이 반복된다(R31 변종).\n        #   구간 계산기가 돌았으면 두 경우를 조건 없이 코드가 붙인다.\n        if band_vals:\n"], ["        if n_prem and \"받지 않은 납입금은 인출해도 세금이 없\" in ans and _EXEMPT_CARD in ans:\n            ans = ans.replace(_EXEMPT_CARD, \"\")\n            clean_note += \" 과세제외 중복 ※카드 제거\"\n\n        # (1-6b) v9.41: ISA 전환금 질문이면 '대상 총액'을 코드가 계산해 붙인다.\n        #   조건 없이 붙인다 — '이미 썼는지'를 판단하려 들면 그 판단이 또 어긋난다.\n", "        if n_prem and \"받지 않은 납입금은 인출해도 세금이 없\" in ans and _EXEMPT_CARD in ans:\n            ans = ans.replace(_EXEMPT_CARD, \"\")\n            clean_note += \" 과세제외 중복 ※카드 제거\"\n        # v12.5(N01): '세액공제를 받지 않았다면 그에 따른 세금은…'의 '그에 따른'은 대상이 모호해\n        #   (계좌 전체 무과세로 오해). 앞에 '세액공제를 받지 않'이 있을 때만 대상을 원금으로 좁힌다.\n        _n01, _n01n = re.subn(r\"(세액공제를?\\s*받지\\s*않았?다면\\s*)그에\\s*따른\\s*세금\",\n                              r\"\\1그 납입 원금에 대한 세금\", ans)\n        if _n01n:\n            ans = _n01\n            clean_note += \" 과세제외 범위 명확화\"\n\n        # (1-6b) v9.41: ISA 전환금 질문이면 '대상 총액'을 코드가 계산해 붙인다.\n        #   조건 없이 붙인다 — '이미 썼는지'를 판단하려 들면 그 판단이 또 어긋난다.\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "v12.5(G05)" in src: print("[스킵] 이미 v12.5 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[경고] 적용전 md5가 예상 v124와 다름. 훅 매칭되면 계속.")
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v124_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
