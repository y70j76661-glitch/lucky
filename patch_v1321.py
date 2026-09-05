# -*- coding: utf-8 -*-
"""patch_v1321.py — v1320(4f6ce2f1) main.py 에 v13.21 적용. (v1320 적용 후 실행)
  [429 안전망 보강 — fb_test FB1 실패 원인] 유형 분류(classify)·금액 추출(extract_json)도 LLM 호출이라 429면
   '일반'으로 떨어져 계산기가 안 돌았다 → 분류 실패 시 결정적 키워드 분류(세금어→세제, 추천어→추천, 상품어→상품설명,
   그 외 제도), 429 직후엔 두 호출의 재시도를 짧게(quick), 납입액 추출기가 비면 '700만원 납입/넣었'을 결정적으로 추출.
   정상 경로(LLM 성공) 무변화.
자동백업·자가검증. 이미 v13.21이면 스킵. 검증 md5==202518dfb5ba8f0fd642346977e13853"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='4f6ce2f130be38eaf3015fd6c58ff12c'
EXPECT_AFTER='202518dfb5ba8f0fd642346977e13853'
HUNKS=[["    raise last_err\n\n\ndef chat(system, user_msg, max_tokens=500, temperature=0.15):\n    \"\"\"HCX-005 호출 공통 함수 (재시도 포함)\"\"\"\n    body = {\n        \"messages\": [\n            {\"role\": \"system\", \"content\": system},\n", "    raise last_err\n\n\ndef chat(system, user_msg, max_tokens=500, temperature=0.15, quick=False):\n    \"\"\"HCX-005 호출 공통 함수 (재시도 포함). quick=True: 대체 경로가 있는 보조 호출은 429 재시도를 짧게(v13.20)\"\"\"\n    body = {\n        \"messages\": [\n            {\"role\": \"system\", \"content\": system},\n"], ["        \"maxTokens\": max_tokens,\n        \"temperature\": temperature,\n    }\n    res = post_with_retry(CHAT_URL, body, timeout=60)\n    return res.json().get(\"result\", {}).get(\"message\", {}).get(\"content\", \"\")\n\n\ndef classify(question):\n    \"\"\"질문을 5개 유형 중 하나로 분류. 실패하면 '일반'(폴백).\"\"\"\n    try:\n        text = chat(CLASSIFY_SYSTEM, question, max_tokens=10, temperature=0.1)\n        for label in LABELS:\n            if label in text:\n                return label\n    except Exception:\n        pass\n    return \"일반\"\n\n\ndef extract_json(system, question):\n    \"\"\"LLM으로 질문에서 정보를 JSON 형태로 추출. 실패하면 빈 dict.\"\"\"\n    try:\n        text = chat(system, question, max_tokens=100, temperature=0.1)\n        m = re.search(r\"\\{.*\\}\", text, re.S)\n        if m:\n            return json.loads(m.group())\n", "        \"maxTokens\": max_tokens,\n        \"temperature\": temperature,\n    }\n    res = post_with_retry(CHAT_URL, body, timeout=60, quick=quick)\n    return res.json().get(\"result\", {}).get(\"message\", {}).get(\"content\", \"\")\n\n\n_KW_TAX = re.compile(r\"세액\\s*공제|공제\\s*(?:액|율|한도|받|대상)|세금|세율|과세|연말정산|소득세|환급|절세|돌려받|연봉|총급여|종합소득\")\n_KW_RECO = re.compile(r\"추천|골라|어떤\\s*(?:상품|펀드|ETF)|좋은\\s*(?:상품|펀드)|뭐가\\s*(?:좋|나)|적합한\")\n_KW_PROD = re.compile(r\"펀드|ETF|TDF|보수|수수료|위험\\s*등급|수익률|투자신탁|클래스|종목\")\n\n\ndef _classify_kw(question):\n    \"\"\"v13.20: LLM 분류가 429 등으로 실패했을 때의 결정적 키워드 분류(정상 경로에서는 쓰이지 않음).\n    계산기·한도 카드는 '세제'에서만 돌므로 세금 질문을 놓치지 않는 쪽을 우선한다.\"\"\"\n    if _KW_TAX.search(question):\n        return \"세제\"\n    if _KW_RECO.search(question):\n        return \"추천\"\n    if _KW_PROD.search(question):\n        return \"상품설명\"\n    return \"제도\"\n\n\ndef classify(question):\n    \"\"\"질문을 5개 유형 중 하나로 분류. 실패하면 키워드 분류(v13.20; 그전엔 '일반').\"\"\"\n    try:\n        text = chat(CLASSIFY_SYSTEM, question, max_tokens=10, temperature=0.1, quick=_recent_429())\n        for label in LABELS:\n            if label in text:\n                return label\n    except Exception:\n        return _classify_kw(question)\n    return \"일반\"\n\n\ndef extract_json(system, question):\n    \"\"\"LLM으로 질문에서 정보를 JSON 형태로 추출. 실패하면 빈 dict.\"\"\"\n    try:\n        text = chat(system, question, max_tokens=100, temperature=0.1, quick=_recent_429())   # v13.20\n        m = re.search(r\"\\{.*\\}\", text, re.S)\n        if m:\n            return json.loads(m.group())\n"], ["                if _acc:\n                    paid = sum(float(x.replace(\",\", \"\")) for x in _acc)\n                    action_note += f\" → 납입액 결정적 합산({len(_acc)}계좌={int(paid):,}만원)\"\n            if salary and paid:\n                _lim, _lab = pension_limit(question)     # v9.32: 상품별 한도\n                _sub = split_accounts(question, paid) if _lim == 900 else None   # v13.7: 계좌별 분리\n", "                if _acc:\n                    paid = sum(float(x.replace(\",\", \"\")) for x in _acc)\n                    action_note += f\" → 납입액 결정적 합산({len(_acc)}계좌={int(paid):,}만원)\"\n                else:\n                    # v13.20: 추출기(LLM)가 429로 비었을 때 '700만원 납입/넣었' 형태를 결정적으로 잡는다\n                    _mp2 = re.search(r\"([\\d,]+)\\s*만\\s*원[^\\d\\n]{0,8}?(?:납입|넣|불입|입금|저축)\", question)\n                    if _mp2:\n                        _pv = float(_mp2.group(1).replace(\",\", \"\"))\n                        if _pv > 0 and (not salary or abs(_pv - salary) > 0.5):\n                            paid = _pv\n                            action_note += f\" → 납입액 결정적 추출({int(paid):,}만원)\"\n            if salary and paid:\n                _lim, _lab = pension_limit(question)     # v9.32: 상품별 한도\n                _sub = split_accounts(question, paid) if _lim == 900 else None   # v13.7: 계좌별 분리\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "def _classify_kw(" in src: print("[스킵] 이미 v13.21 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[경고] 적용전 md5가 예상 v1320과 다름. 훅 매칭되면 계속.")
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v1320_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
