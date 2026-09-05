# -*- coding: utf-8 -*-
"""patch_v1334.py — v1333(f2627a3a) main.py 에 v13.34 적용. (v1333 적용 후 실행)
  [답변 계약 5 — 질문 요구사항 누락(RequirementContract)] 질문이 명시적으로 요구한 속성(위험등급·총보수·수익률·세액공제·한도·
   설정액·클래스·운용사)이 답변에 한 번도 나오지 않으면, 정답표에 값이 있으면 그 값을(출처 포함), 없으면 '이 답변에서 확인해 드리지
   못했습니다 — 별도 확인 필요' 한 줄을 붙인다(누락 대신 명시). 제외 요청('수수료 얘기는 빼고')된 속성은 요구로 보지 않음.
   상품설명·추천·세제 유형에만 적용. LLM 파서 없음. 검사기(claim_check.py)는 같은 REQUEST_SLOTS를 main.py에서 import.
자동백업·자가검증. 이미 v13.34면 스킵. 검증 md5==c02a2fce4a55709dbefb7a9fa999c8bf"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='f2627a3aaf51665be3cf890a8908819b'
EXPECT_AFTER='c02a2fce4a55709dbefb7a9fa999c8bf'
HUNKS=[["\n# v13.28 [답변 계약 2 — 추천 상품 연결]: 추천 답변의 각 상품은 '상품명 ∈ 사용 근거 문서' 이고, 답변이 붙인 위험등급이 그 문서(또는\n#   정답표)의 등급과 같아야 한다. 연결이 끊긴 상품의 줄은 제거하고 한 줄로 알린다(문구 치환이 아니라 주장 단위 차단).\ndef deposit_guarantee_contract(ans, used):\n    if not re.search(r\"원리금\\s*보장|원리금보장|예금\", ans):\n        return ans, \"\"\n", "\n# v13.28 [답변 계약 2 — 추천 상품 연결]: 추천 답변의 각 상품은 '상품명 ∈ 사용 근거 문서' 이고, 답변이 붙인 위험등급이 그 문서(또는\n#   정답표)의 등급과 같아야 한다. 연결이 끊긴 상품의 줄은 제거하고 한 줄로 알린다(문구 치환이 아니라 주장 단위 차단).\n# v13.34 [답변 계약 5 — 질문 요구사항 누락]: 질문이 명시적으로 요구한 속성(위험등급·총보수·수익률·세액공제·한도·설정액·클래스)이\n#   답변에 한 번도 나오지 않으면, 정답표에 값이 있으면 그 값을, 없으면 '자료에서 확인되지 않았다'는 한 줄을 붙인다(누락 대신 명시).\n#   제외 요청('수수료 얘기는 빼고')된 속성은 요구로 보지 않는다. LLM 파서 없이 결정적 슬롯.\n_EXCL_NEG = r\"(?:빼고|말고|제외하고|제외한\\s|넘어가고|됐고|필요\\s*없(?:고|으니|어서)|생략하고|건너뛰고|안\\s*해도\\s*(?:되니|돼서|되고))\"\nREQUEST_SLOTS = [\n    (\"위험등급\", r\"위험\\s*등급|등급\", r\"\\d\\s*등급|(?:매우\\s*)?(?:높은|낮은|보통|다소\\s*높은)\\s*위험|등급\"),\n    (\"총보수\", r\"총\\s*보수|보수|수수료\", r\"보수|수수료\"),\n    (\"수익률\", r\"수익률\", r\"수익률\"),\n    (\"세액공제\", r\"세액\\s*공제|공제액|공제\\s*금액\", r\"세액공제|공제\"),\n    (\"한도\", r\"한도\", r\"한도|까지\"),\n    (\"설정액\", r\"설정액|운용\\s*규모\", r\"설정액|규모|억\"),\n    (\"클래스\", r\"클래스\", r\"클래스|C-P|\\(C|Ce\\)\"),\n    (\"운용사\", r\"운용사\", r\"자산운용|운용사\"),\n]\n\n\ndef requirement_contract(question, ans, pf_hits):\n    body = ans.split(\"[참고 문서]\")[0]\n    missing = []\n    for name, qpat, apat in REQUEST_SLOTS:\n        if not re.search(qpat, question):\n            continue\n        if re.search(r\"(\" + qpat + r\")[^\\n]{0,14}?\" + _EXCL_NEG, question):\n            continue                                              # 제외 요청된 속성\n        if re.search(apat, body):\n            continue\n        missing.append(name)\n    if not missing:\n        return ans, \"\"\n    adds = []\n    for name in missing:\n        filled = False\n        for f in (pf_hits or []):\n            if name == \"위험등급\":\n                adds.append(f\"{f['name']}의 위험등급은 {f['grade']}입니다(출처 {f['src']}).\"); filled = True\n            elif name == \"총보수\" and f.get(\"fee\"):\n                adds.append(f\"{f['name']}의 보수: {f['fee']}(출처 {f['src']}).\"); filled = True\n        if not filled:\n            adds.append(f\"요청하신 '{name}'은(는) 이 답변에서 확인해 드리지 못했습니다. 사용한 자료 범위에서 별도 확인이 필요합니다.\")\n    head, tail = (ans.split(\"[참고 문서]\", 1) + [\"\"])[:2]\n    tail = (\"[참고 문서]\" + tail) if \"[참고 문서]\" in ans else \"\"\n    out = head.rstrip() + \"\\n\\n\" + \"\\n\".join(adds) + (\"\\n\\n\" + tail if tail else \"\")\n    return out, f\" (요구사항 계약: 누락 속성 {len(missing)}건 보강 — {', '.join(missing)})\"\n\n\ndef deposit_guarantee_contract(ans, used):\n    if not re.search(r\"원리금\\s*보장|원리금보장|예금\", ans):\n        return ans, \"\"\n"], ["        #   근거 문서에 없는 '중도 해지 시 이자 손실' 서술은 제거\n        ans, _c4 = deposit_guarantee_contract(ans, used)\n        clean_note += _c4\n        # v13.19: 정답표 상품의 등급·보수가 답변에서 다르게 쓰였으면 교정(질문에 그 상품이 있을 때)\n        if _pf_hits:\n            ans, _npf = enforce_product_facts(ans, _pf_hits)\n", "        #   근거 문서에 없는 '중도 해지 시 이자 손실' 서술은 제거\n        ans, _c4 = deposit_guarantee_contract(ans, used)\n        clean_note += _c4\n        # v13.34 [계약 5 — 요구사항 누락]: 질문이 요구한 속성이 답변에 없으면 정답표 값 또는 '확인되지 않음'으로 명시\n        if qtype in (\"상품설명\", \"추천\", \"세제\"):\n            ans, _c5 = requirement_contract(question, ans, _pf_hits)\n            clean_note += _c5\n        # v13.19: 정답표 상품의 등급·보수가 답변에서 다르게 쓰였으면 교정(질문에 그 상품이 있을 때)\n        if _pf_hits:\n            ans, _npf = enforce_product_facts(ans, _pf_hits)\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "def requirement_contract(" in src: print("[스킵] 이미 v13.34 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[경고] 적용전 md5가 예상 v1333과 다름. 훅 매칭되면 계속.")
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v1333_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
