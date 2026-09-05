# -*- coding: utf-8 -*-
"""patch_v136.py — v135(c753b271) main.py 에 v13.6 적용.
  [K6 계산 오류] LLM 산술에 맡기지 않는 결정적 계산 보강 2겹:
   ① fix_arith: 답변 속 'A만원 × R% = C만원' 식의 C를 코드로 재계산(A×R/100)해 틀리면 교정 +
      본문 재언급도 교정. 계산기 실행 여부와 무관한 최종 안전망(실측 900×13.2%=119.28→118.8).
   ② 두 계좌 납입액 결정적 합산: 추출기가 '연금저축 600, IRP 600'을 합산 못 하면 질문에서 찾아
      합산 → 계산기가 돌게 함(정답을 컨텍스트로 선주입).
  정상 계산·식 없는 답변은 불변.
자동백업·자가검증. 이미 v13.6이면 스킵. 검증 md5==988a436efc86ec3e529023b5c442c227"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='c753b27153c031bdfc36920d061cf37b'
EXPECT_AFTER='988a436efc86ec3e529023b5c442c227'
HUNKS=[["    if cnt[0]:\n        return ans, f\" (계산식 코드 교정 {cnt[0]}건)\"\n    return ans, \"\"\n\n\ndef reconcile_sum_limit(ans, paid, base, limit):\n", "    if cnt[0]:\n        return ans, f\" (계산식 코드 교정 {cnt[0]}건)\"\n    return ans, \"\"\n\n\ndef fix_arith(ans):\n    \"\"\"v13.6(K6): 결정적 산술 검증 — 계산기 실행 여부와 무관하게 답변 속 'A만원 × R% = C만원' 식의\n    C를 코드로 재계산해(A×R/100) 틀리면 바로잡고, 본문에 남은 같은 틀린 값도 교정한다.\n    실측 K6: 추출기가 두 계좌 납입액을 합산 못 해 계산기가 안 돌자 LLM이 900×13.2%=119.28(정답 118.8)로\n    오산. 산술을 LLM에 맡기지 않는 마지막 안전망. 식이 없거나 이미 맞으면 원문 불변.\"\"\"\n    fixes = []\n\n    def _f(m):\n        try:\n            a = float(m.group(1).replace(\",\", \"\"))\n            r = float(m.group(2))\n            c = float(m.group(3).replace(\",\", \"\"))\n        except ValueError:\n            return m.group(0)\n        t = round(a * r / 100, 1)\n        if abs(c - t) < 0.06:            # 반올림 오차 이내 = 정상\n            return m.group(0)\n        fixes.append((m.group(3), f\"{t:,.1f}\"))\n        return f\"{m.group(1)}만원 × {m.group(2)}% = 약 {t:,.1f}만원\"\n\n    ans = _CALC_PAT.sub(_f, ans)\n    for wrong, right in fixes:           # '총 공제액은 약 119.28만원' 같은 본문 재언급도 교정\n        ans = re.sub(r\"(?<![\\d.])\" + re.escape(wrong) + r\"(?=\\s*만\\s*원)\", right, ans)\n    return ans, len(fixes)\n\n\ndef reconcile_sum_limit(ans, paid, base, limit):\n"], ["            info = extract_json(TAX_EXTRACT_SYSTEM, q_llm)\n            salary = to_num(info.get(\"총급여\"))\n            paid = to_num(info.get(\"납입액\"))\n            if salary and paid:\n                _lim, _lab = pension_limit(question)     # v9.32: 상품별 한도\n                calc_result, calc_vals = calc_pension_tax_credit(salary, paid, _lim, _lab)\n", "            info = extract_json(TAX_EXTRACT_SYSTEM, q_llm)\n            salary = to_num(info.get(\"총급여\"))\n            paid = to_num(info.get(\"납입액\"))\n            # v13.6(K6): '연금저축 600만원, IRP 600만원'처럼 두 계좌 금액을 LLM 추출기가 합산 못 해\n            #   납입액이 비면, 질문에서 연금저축/IRP 뒤 금액을 결정적으로 찾아 합산한다(계산기 실행 보장).\n            if not paid:\n                _acc = re.findall(r\"(?:연금저축|IRP|개인형\\s*퇴직연금)[^\\d\\n]{0,12}?([\\d,]+)\\s*만\\s*원\",\n                                  question)\n                if _acc:\n                    paid = sum(float(x.replace(\",\", \"\")) for x in _acc)\n                    action_note += f\" → 납입액 결정적 합산({len(_acc)}계좌={int(paid):,}만원)\"\n            if salary and paid:\n                _lim, _lab = pension_limit(question)     # v9.32: 상품별 한도\n                calc_result, calc_vals = calc_pension_tax_credit(salary, paid, _lim, _lab)\n"], ["        calc_note = \"\"\n        if calc_vals:\n            ans, calc_note = enforce_calc(ans, calc_vals)\n        # v11.6: 소득 미상(band_vals) 합산 맥락 — enforce_calc가 안 도는 경우, LLM이 남긴\n        #   잘못된 '한도 X만원 적용' 결론을 계산된 공제대상으로 재작성(값 기반, 하드코딩 아님).\n        #   순서: (LLM 답변) → 여기서 결론 교정 → 이후 소득미상 카드(base 기준) 부착 → 최종정리.\n", "        calc_note = \"\"\n        if calc_vals:\n            ans, calc_note = enforce_calc(ans, calc_vals)\n        # v13.6(K6): 계산기가 안 돌았든(추출 실패) 돌았든, 답변의 'A×R%=C' 산술을 코드로 재검증.\n        #   LLM 곱셈 오류(예: 900×13.2%=119.28 → 118.8)를 결정적으로 교정. 식 없으면 불변.\n        ans, _na = fix_arith(ans)\n        if _na:\n            calc_note += f\" (산술 재검증 교정 {_na}건)\"\n        # v11.6: 소득 미상(band_vals) 합산 맥락 — enforce_calc가 안 도는 경우, LLM이 남긴\n        #   잘못된 '한도 X만원 적용' 결론을 계산된 공제대상으로 재작성(값 기반, 하드코딩 아님).\n        #   순서: (LLM 답변) → 여기서 결론 교정 → 이후 소득미상 카드(base 기준) 부착 → 최종정리.\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "def fix_arith(" in src: print("[스킵] 이미 v13.6 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[경고] 적용전 md5가 예상 v135와 다름. 훅 매칭되면 계속.")
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v135_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
