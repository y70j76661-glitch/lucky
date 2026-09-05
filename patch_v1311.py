# -*- coding: utf-8 -*-
"""patch_v1311.py — v1310(791990d6) main.py 에 v13.11 적용.
  [O4 요구사항 미답 가드 — 추가만, 삭제 없음]
   질문에 판촉성 혜택 전제(수수료 면제·면제 혜택·이벤트·프로모션·할인 혜택·캐시백·경품·사은품)가 있는데
   답변이 그 혜택을 언급도 한계 고지도 없이 일반 설명으로 넘어가면, 맨 앞에
   "문의하신 '…' 혜택은 제공된 자료에서 확인할 수 없습니다. 아래는 자료에서 확인되는 관련 내용입니다." 한 줄 부착.
   판촉 어휘가 없는 질문(골든·계산·상품)엔 불발. 답변이 이미 한계를 밝혔거나 혜택을 다뤘으면 불변.
자동백업·자가검증. 이미 v13.11이면 스킵. 검증 md5==27aabd67c2a8e2937f4d89098fdfb968"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='791990d6ca2f3ed18306f14ec677894c'
EXPECT_AFTER='27aabd67c2a8e2937f4d89098fdfb968'
HUNKS=[["            _body = re.sub(r\"^\\s*제공된\\s*자료에서\\s*확인할\\s*수\\s*없습니다\\.?\\s*(?:다만,?\\s*)?\", \"\", ans)\n            ans = _f01 + \"\\n\\n\" + _body.lstrip()\n            clean_note += \" 원금보장 전제 교정\"\n\n        # (1-6b) v9.41: ISA 전환금 질문이면 '대상 총액'을 코드가 계산해 붙인다.\n        #   조건 없이 붙인다 — '이미 썼는지'를 판단하려 들면 그 판단이 또 어긋난다.\n", "            _body = re.sub(r\"^\\s*제공된\\s*자료에서\\s*확인할\\s*수\\s*없습니다\\.?\\s*(?:다만,?\\s*)?\", \"\", ans)\n            ans = _f01 + \"\\n\\n\" + _body.lstrip()\n            clean_note += \" 원금보장 전제 교정\"\n        # (1-6d) v13.11(O4): 판촉성 혜택 전제('첫 6개월 수수료 면제', '가입 이벤트', '할인')를 물었는데\n        #   답변이 그 혜택을 언급도, 한계 고지도 없이 일반 설명으로 넘어가면(실측 O4: 요구사항 미답)\n        #   맨 앞에 '자료에서 확인할 수 없다'를 한 줄 붙인다. 삭제 없음. 판촉 어휘가 없는 질문엔 불발.\n        _promo = re.search(r\"수수료\\s*면제|면제\\s*혜택|이벤트|프로모션|할인\\s*혜택|캐시백|경품|사은품\", question)\n        if _promo and not re.search(r\"면제|이벤트|프로모션|할인|캐시백|경품|사은품\", ans.split(\"[참고 문서]\")[0]) \\\n                and not _NOINFO.search(ans):\n            ans = (f\"문의하신 '{_promo.group(0)}' 혜택은 제공된 자료에서 확인할 수 없습니다. \"\n                   \"아래는 자료에서 확인되는 관련 내용입니다.\\n\\n\" + ans.lstrip())\n            clean_note += \" 판촉혜택 미확인 고지\"\n\n        # (1-6b) v9.41: ISA 전환금 질문이면 '대상 총액'을 코드가 계산해 붙인다.\n        #   조건 없이 붙인다 — '이미 썼는지'를 판단하려 들면 그 판단이 또 어긋난다.\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "판촉혜택 미확인 고지" in src: print("[스킵] 이미 v13.11 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[경고] 적용전 md5가 예상 v1310과 다름. 훅 매칭되면 계속.")
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v1310_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
