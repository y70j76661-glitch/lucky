# -*- coding: utf-8 -*-
"""patch_v1370.py — v1369(c67afd80) main.py 에 v13.70 적용. (v1369 적용 후 실행)
  [mini46 리뷰 반영] ① S4: 1,500만원·5.5~3.3퍼센트 일반화 문장을 부분 치환하다 어구가 잘리던 문제('차후 점에') → 표준 조건 문장으로 통째 교체
   ② B11: '세액공제 받지 않은 금액만 인출하여 세금을 피할 수 있다' → '기타소득세 부담 없이(과세제외금액 범위 내, 인출 순서·재원 구분 확인) 인출'
   ③ M2: '~분들께 적합합니다'·'고수익을 기대하는' 단정 완화, 원금 보전 머리말 아래 펀드 블록에 '원리금보장형은 별도 확인·아래 펀드는 원금보장 상품 아님' 고지
자동백업·자가검증. 이미 v13.70이면 스킵. 검증 md5==5e8bafde39b3a44868ec0dfe81db1f2e"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='c67afd804fdb11dfdca6db7efd222a1f'
EXPECT_AFTER='5e8bafde39b3a44868ec0dfe81db1f2e'
HUNKS=[["                    if re.search(r\"1,?500\\s*만\\s*원\", s_) and re.search(r\"5\\.5|3\\.3\", s_) and not re.search(r\"요건|연령별|합계\", s_):   # v13.69: 조건 없는 일반화 → 조건 부착\n                        s_ = re.sub(r\"(?:만\\s*55세\\s*이후에?\\s*)?연금(?:으로)?\\s*수령(?:할\\s*때|\\s*시)?\\s*\", \"\", s_, count=1)\n                        s_ = re.sub(r\"(연\\s*1,?500\\s*만\\s*원\\s*이하)(?:로|의\\s*금액에\\s*대해서는|이면|라면)?\\s*(?:인출하면|수령하면)?\\s*(5\\.5\\s*%?\\s*[~∼-]\\s*3\\.3\\s*%)\",\n                                    r\"연금 수령 요건(만 55세 이후, 연금 수령 한도 내)을 갖춰 연금으로 받을 때 연금소득 합계 \\1에 대해 연령별 \\2\", s_)\n                        _n19 += 1\n", "                    if re.search(r\"1,?500\\s*만\\s*원\", s_) and re.search(r\"5\\.5|3\\.3\", s_) and not re.search(r\"요건|연령별|합계\", s_):   # v13.69/70: 조건 없는 일반화 → 표준 조건 문장으로 통째 교체(부분 치환은 어구가 잘림)\n                        _lead_kw = re.match(r\"^\\s*(?:이는\\s*과세이연(?:의\\s*일종으로|\\s*효과로),?\\s*|또한,?\\s*|대신,?\\s*|즉,?\\s*)?\", s_).group(0)\n                        s_ = (_lead_kw + \"연금 수령 요건(만 55세 이후, 연금 수령 한도 내)을 갖춰 연금으로 받을 때는 연금소득 합계가 연 1,500만원 이하이면 \"\n                              \"연령별 5.5%~3.3%의 연금소득세가 적용됩니다.\")\n                        _n19 += 1\n"], ["            if _n8:\n                ans = \"\\n\".join(_b8); clean_note += f\" 중도해지 세율 혼입·무관 대안 {_n8}건 제거\"\n", "            if _n8:\n                ans = \"\\n\".join(_b8); clean_note += f\" 중도해지 세율 혼입·무관 대안 {_n8}건 제거\"\n            _b8b, _n8b = re.subn(r\"(세액\\s*공제를?\\s*받지\\s*않은\\s*(?:금액|납입금|원금)[^.!?\\n]{0,10}?인출[^.!?\\n]{0,8}?)세금을\\s*(?:피할|내지\\s*않을|면할)\\s*수\\s*있\",\n                                 r\"\\1기타소득세 부담 없이(과세제외금액 범위 내, 인출 순서·재원 구분은 계좌 규정에 따라 확인) 인출할 수 있\", ans)   # v13.70(B11)\n            if _n8b:\n                ans = _b8b; clean_note += f\" 중도해지 '세금 회피' 표현 완화 {_n8b}건\"\n"], ["    (re.compile(r\"(분)(?:들)?(?:에게|께)\\s*(?:잘\\s*)?어울립니다\"), r\"\\1이 검토할 수 있는 후보입니다\"),\n", "    (re.compile(r\"(분)(?:들)?(?:에게|께)\\s*(?:잘\\s*)?어울립니다\"), r\"\\1이 검토할 수 있는 후보입니다\"),\n    (re.compile(r\"(분들?|투자자|사용자|고객)(?:에게|께)\\s*(?:더\\s*|가장\\s*)?적합(?:합니다|한\\s*상품입니다|한\\s*선택입니다)\"), r\"\\1이 검토할 수 있는 후보입니다\"),   # v13.70(M2)\n    (re.compile(r\"고수익(?:을|이)?\\s*(?:기대하는|기대할\\s*수\\s*있는|노리는)\"), \"높은 수익을 목표로 하되 그만큼 손실 가능성도 감수하는\"),\n"], ["    new = ([head] if head is not None else []) + risk + others\n", "    new = ([head] if head is not None else []) + _rr_capital_note(head, nm, p) + risk + others   # v13.70(M2): 원금 보전 머리말 + 펀드 → 원리금보장형 별도 확인 고지\n"], ["        new = ([head] if head is not None else []) + risk + _plines + _generic\n", "        new = ([head] if head is not None else []) + _rr_capital_note(head, \" \".join(_plines), p) + risk + _plines + _generic   # v13.70(M2)\n"], ["def _rr_block(lines, used, allowed, cited, st):\n", "def _rr_capital_note(head, names_text, block_text=\"\"):\n    \"\"\"v13.70(M2): 머리말이 '원금 보전·원금 보장·안정' 조건인데 아래 상품이 펀드(실적배당형)면, 원리금보장형은 별도 확인이 필요함을 먼저 밝힌다(멱등).\"\"\"\n    if \"아래 펀드는 원금보장 상품이 아닙니다\" in (block_text or \"\"):\n        return []\n    if head and re.search(r\"원금\\s*(?:보전|보장)|안정\", head) and re.search(r\"펀드|투자신탁|ETF|TDF|상장지수\", names_text or \"\") \\\n            and not re.search(r\"예금|원리금\\s*보장|ELB|DLB\", names_text or \"\"):\n        return [\" - 원금 보장이 필요하시면 예금 등 원리금보장형 상품을 별도로 확인하셔야 하며, 아래 펀드는 원금보장 상품이 아닙니다(투자원금·수익 비보장).\"]\n    return []\n\n\ndef _rr_block(lines, used, allowed, cited, st):\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "def _rr_capital_note(" in src: print("[스킵] 이미 v13.70 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[중단] 적용전 md5가 예상 v1369와 다름 → 서버 파일이 갈라짐. main_v1370_full.py 로 통째 교체하세요."); sys.exit(4)
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v1369_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
