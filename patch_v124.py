# -*- coding: utf-8 -*-
"""patch_v124.py — v123(22dd682c) main.py 에 v12.4 적용.
  G05: 오표기 숫자(148만 5천만원) 답변 재현 억제 — build_number_card 프롬프트 + (1-4b) 주석 게이트/리워드.
  N01: 과세제외 ※카드 가드를 띄어쓰기·'원금' 변형까지 확장(본문에 이미 있으면 카드 미부착 → 단일 출력).
자동백업·자가검증. 이미 v12.4면 스킵. 검증 기준은 md5==42e3522d230d6961fdeb2193d502d23c"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='22dd682c4a7f4b4ea8911ec1057dbcaa'
EXPECT_AFTER='42e3522d230d6961fdeb2193d502d23c'
HUNKS=[["    for n in hits:\n        lines.append(f\"- {n['src']}에 '{n['wrong']}'으로 적혀 있으나, {n['basis']}이므로 \"\n                     f\"계산상 '{n['right']}'이다.\")\n    lines.append(\"※ 답변할 때 계산값을 쓰되, 자료 원문에는 다르게 적혀 있다는 사실을 \"\n                 \"함께 밝혀라. 어느 쪽이 옳은지 단정하지 말고 확인이 필요하다고 안내하라.\")\n    return \"\\n\".join(lines), hits\n\n\n", "    for n in hits:\n        lines.append(f\"- {n['src']}에 '{n['wrong']}'으로 적혀 있으나, {n['basis']}이므로 \"\n                     f\"계산상 '{n['right']}'이다.\")\n    lines.append(\"※ 답변에는 위 계산값만 사용하라. 사용자가 원문·표기·문서 오기를 직접 \"\n                 \"묻지 않았다면 잘못된 원문 숫자를 답변에 그대로 옮겨 적지 마라(오기 재현 금지). \"\n                 \"원문 오류를 밝혀야 할 때도 틀린 숫자를 반복하지 말고 '원문 표기에 단위 오류가 \"\n                 \"있으나 계산상 금액은 …'처럼 간단히 안내하라.\")\n    return \"\\n\".join(lines), hits\n\n\n"], ["            for _n in num_hits:\n                _w = re.sub(r\"\\s+\", \"\", _n[\"wrong\"])\n                _r = re.sub(r\"\\s+\", \"\", _n[\"right\"])\n                # v11.7: 최대/얼마까지 금액을 묻거나, 원문 오기를 직접 인용했을 때만 고지.\n                _unit_ask = (_w in _q) or bool(re.search(\n                    r\"최대|얼마까지|얼마.*돌려받|최고|한도\\s*금액\", question))\n                if _unit_ask and (_r in _flat or _w in _q) and \"자료 원문에는\" not in ans:\n                    ans = ans.rstrip() + (\n                        f\"\\n\\n※ 자료 원문({_n['src']})에는 '{_n['wrong']}'으로 적혀 있으나, \"\n                        f\"{_n['basis']}이므로 계산상 '{_n['right']}'이 맞습니다.\")\n                    clean_note += \" 단위 오표기 고지 보강\"\n                    break\n\n", "            for _n in num_hits:\n                _w = re.sub(r\"\\s+\", \"\", _n[\"wrong\"])\n                _r = re.sub(r\"\\s+\", \"\", _n[\"right\"])\n                # v12.4(G05): 원문 오기 '재현'은 사용자가 원문·표기를 직접 물었을 때만.\n                #   '최대 금액' 질문엔 answer에 계산값(right)만 있으면 충분 — 틀린 숫자(wrong)를\n                #   다시 노출하지 않는다. 밝힐 때도 wrong 숫자를 반복하지 않고 '단위 오류'로만 안내.\n                _orig_ask = (_w in _q) or bool(\n                    re.search(r\"원문|표기|문서에는|오기|왜.*다르\", question))\n                if _orig_ask and (_r in _flat or _w in _q) and \"자료 원문에는\" not in ans \\\n                        and \"단위 오류\" not in ans:\n                    ans = ans.rstrip() + (\n                        f\"\\n\\n※ 참고: 원문({_n['src']}) 표기에 단위 오류가 있으나, \"\n                        f\"{_n['basis']}이므로 계산상 금액은 '{_n['right']}'입니다.\")\n                    clean_note += \" 단위 오표기 고지 보강\"\n                    break\n\n"], ["                            (\"인출\", \"해지\", \"출금\", \"환매\", \"중도\", \"깨\", \"빼\", \"찾\")):\n            _fire = False\n        if _fire and not any(k in question for k in _OPER_Q) \\\n                and \"받지 않은 납입금\" not in ans and \"과세제외\" not in ans:\n            ans = ans.rstrip() + (\n                \"\\n\\n※ 기타소득세 16.5%는 세액공제를 받은 납입금과 운용수익을 인출할 때 \"\n                \"적용됩니다. 세액공제를 받지 않은 납입금(과세제외금액)은 인출하더라도 \"\n", "                            (\"인출\", \"해지\", \"출금\", \"환매\", \"중도\", \"깨\", \"빼\", \"찾\")):\n            _fire = False\n        if _fire and not any(k in question for k in _OPER_Q) \\\n                and not re.search(r\"받지\\s*않은\\s*납입\\s*(?:금|원금)\", ans) \\\n                and not re.search(r\"과세\\s*제외\", ans):\n            ans = ans.rstrip() + (\n                \"\\n\\n※ 기타소득세 16.5%는 세액공제를 받은 납입금과 운용수익을 인출할 때 \"\n                \"적용됩니다. 세액공제를 받지 않은 납입금(과세제외금액)은 인출하더라도 \"\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "v12.4(G05)" in src: print("[스킵] 이미 v12.4 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[경고] 적용전 md5가 예상 v123과 다름. 훅 매칭되면 계속.")
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v123_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    print("  ✓ 훅",len(HUNKS),"개 적용")
    ok = (after==EXPECT_AFTER)
    print("백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅ (md5 일치·컴파일 OK)" if ok else "확인 필요 ❌")
    print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
