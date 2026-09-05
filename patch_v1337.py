# -*- coding: utf-8 -*-
"""patch_v1337.py — v1336(ab104d8e) main.py 에 v13.37 적용. (v1336 적용 후 실행)
  [잘못된 전제 감지 일반화] 'IRP는 원금이 보장되죠?' 외에 'IRP면 당연히 원금 보장되는 거 아닌가요?', 'IRP라 손해 안 보죠?',
   '연금저축은 원금 손실 없는 거 맞죠?' 같은 변형(손해/손실 없음·안전 단정 + 확인 어미 잖아·아닌가·아니야)도 같은 전제 교정
   카드로 처리. 문구가 아니라 의미 조건(계좌 + 무손실 단정 + 확인 질문)에 걸린다.
자동백업·자가검증. 이미 v13.37이면 스킵. 검증 md5==5a6b4e581e806cf83df6dd4f64f29305"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='ab104d8ecbb27027a67c3c7b135af148'
EXPECT_AFTER='5a6b4e581e806cf83df6dd4f64f29305'
HUNKS=[["        # (1-6c) v13.9(F01): 'IRP는 원금이 보장되죠?' 전제 교정 — 계좌 자체는 원금 보장이 아니며 안에서\n        #   고르는 상품에 따라 다르다(코퍼스 근거: IRP 원리금보장상품 존재(디폴트옵션 FAQ),\n        #   투자신탁은 투자원금을 보장하지 않음(투자설명서)). 답변이 이미 그 구분을 담았으면 불변.\n        if re.search(r\"(?:IRP|연금저축|연금계좌|퇴직연금|DC)[^\\n]{0,25}?원금[^\\n]{0,6}?보장\", question) \\\n                and re.search(r\"죠|나요|맞|되나|인가|가요\", question) \\\n                and not re.search(r\"실적배당|원리금\\s*보장\", ans):\n            _f01 = (\"IRP(연금계좌) 자체가 원금을 보장하는 것은 아닙니다. 계좌 안에서 예금 등 원리금보장상품을 \"\n                    \"선택하면 원리금이 보장되지만, 펀드·ETF 등 실적배당형 상품은 투자원금을 보장하지 않아 \"\n", "        # (1-6c) v13.9(F01): 'IRP는 원금이 보장되죠?' 전제 교정 — 계좌 자체는 원금 보장이 아니며 안에서\n        #   고르는 상품에 따라 다르다(코퍼스 근거: IRP 원리금보장상품 존재(디폴트옵션 FAQ),\n        #   투자신탁은 투자원금을 보장하지 않음(투자설명서)). 답변이 이미 그 구분을 담았으면 불변.\n        if re.search(r\"(?:IRP|연금저축|연금계좌|퇴직연금|DC)[^\\n]{0,25}?(?:원금[^\\n]{0,6}?보장|손해\\s*(?:안|없)|손실\\s*(?:안|없|이\\s*없)|원금\\s*(?:손실|손해)\\s*(?:없|안)|안전한\\s*거|안전하)\", question) \\\n                and re.search(r\"죠|나요|맞|되나|인가|가요|잖아|아닌가|거\\s*아냐|아니야\", question) \\\n                and not re.search(r\"실적배당|원리금\\s*보장\", ans):\n            _f01 = (\"IRP(연금계좌) 자체가 원금을 보장하는 것은 아닙니다. 계좌 안에서 예금 등 원리금보장상품을 \"\n                    \"선택하면 원리금이 보장되지만, 펀드·ETF 등 실적배당형 상품은 투자원금을 보장하지 않아 \"\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "손해\\s*(?:안|없)|손실\\s*(?:안|없|이\\s*없)" in src: print("[스킵] 이미 v13.37 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[경고] 적용전 md5가 예상 v1336과 다름. 훅 매칭되면 계속.")
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v1336_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
