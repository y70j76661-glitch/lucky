# -*- coding: utf-8 -*-
"""patch_v1312.py — v1311(27aabd67) main.py 에 v13.12 적용.
  [product_neg 측정 실결함 3건 — 게이트 2 + 문서 표 기준 교정 1, 전부 결정적]
   ① N4: 수령요건 카드 부정 가드에 '넘어가|됐고|생략|건너뛰|괜찮' 추가('수령 나이는 넘어가고').
   ② N6: 인출·해지어 뒤 12자 안에 제외 표현(빼고·말고·제외·넘어가·됐고·생략·건너뛰)이 오면 과세제외 ※카드 미부착.
   ③ N6: 연금소득세 연령-세율 짝이 문서 표(만 70세 미만 5.5% / 70~79세 4.4% / 80세 이상 3.3%, 미포함 5/4/3%)와
      어긋나는 문장만 문서 표 문장으로 교체(실측: 55~64세 5.0 / 65~69세 4.0 / 70세 이상 3.3). 짝이 맞거나
      표의 세율이 아닌 수치(16.5% 등)는 불변. 코퍼스 실측 근거: '연금소득세(만 70세미만 5.5%, 70세이상 80세미만 4.4%, 80세이상 3.3%)'.
자동백업·자가검증. 이미 v13.12면 스킵. 검증 md5==d6ee16c00a374f706d8a3b105dc9c94e"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='27aabd67c2a8e2937f4d89098fdfb968'
EXPECT_AFTER='d6ee16c00a374f706d8a3b105dc9c94e'
HUNKS=[["                      r\"부어야|부어도|채워야|되나|될까|자격|몇\\s*년|몇\\s*살|나이|몇\\s*세\")\n# v12.3(G06): 수령/나이 주제를 '부정'한 질문(예: '나이는 묻지 않고', '수령 말고')엔 요건 카드 미부착.\n#   '나이' 추가로 G06('몇 살')은 잡되, G07('나이는 묻지 않고 세액공제만')은 이 가드로 차단.\n_REQ_NEG = re.compile(r\"(?:나이|수령|살|요건|개시)[^\\n]{0,8}(?:묻지\\s*않|말고|제외|빼고|아니라|아닌)\")\n# v11.7: 기한 카드는 '기한을 실제로 묻는' 질문에만 붙인다(무관 질문에 붙던 오탐 차단).\n_DL_ACT = (\"이전\", \"이체\", \"전환\", \"입금\", \"옮기\", \"납입\", \"납부\", \"해지\", \"환매\", \"인출\", \"가입\")\n_DL_VERB = r\"(?:하면|하려|하려면|해야|하는|하고|할|한다|하시|합니까|하나요|하죠|하면서|하게)\"\n", "                      r\"부어야|부어도|채워야|되나|될까|자격|몇\\s*년|몇\\s*살|나이|몇\\s*세\")\n# v12.3(G06): 수령/나이 주제를 '부정'한 질문(예: '나이는 묻지 않고', '수령 말고')엔 요건 카드 미부착.\n#   '나이' 추가로 G06('몇 살')은 잡되, G07('나이는 묻지 않고 세액공제만')은 이 가드로 차단.\n_REQ_NEG = re.compile(r\"(?:나이|수령|살|요건|개시)[^\\n]{0,8}(?:묻지\\s*않|말고|제외|빼고|아니라|아닌|넘어가|됐고|생략|건너뛰|괜찮)\")\n# v13.12(N4): '수령 나이는 넘어가고'처럼 제외 표현 변형 추가\n# v11.7: 기한 카드는 '기한을 실제로 묻는' 질문에만 붙인다(무관 질문에 붙던 오탐 차단).\n_DL_ACT = (\"이전\", \"이체\", \"전환\", \"입금\", \"옮기\", \"납입\", \"납부\", \"해지\", \"환매\", \"인출\", \"가입\")\n_DL_VERB = r\"(?:하면|하려|하려면|해야|하는|하고|할|한다|하시|합니까|하나요|하죠|하면서|하게)\"\n"], ["            _keep.append(_s)\n        _out.append(\" \".join(k for k in _keep if k.strip()))\n    ans = \"\\n\".join(_out)\n    return ans.strip()\n\n\n", "            _keep.append(_s)\n        _out.append(\" \".join(k for k in _keep if k.strip()))\n    ans = \"\\n\".join(_out)\n    #    K4 (N6) v13.12: 연금소득세 연령-세율 짝 교정. 문서 표(코퍼스 실측): 만 70세 미만 5.5%, 70세 이상\n    #       80세 미만 4.4%, 80세 이상 3.3%(지방소득세 포함; 미포함 5/4/3%). 답변의 연령 구간·세율 짝이\n    #       이 표와 어긋나면(실측 N6: 55~64세 5.0 / 65~69세 4.0 / 70세 이상 3.3) 그 문장들만 문서 표 문장으로\n    #       교체. 세율이 이 표의 값이 아니면(16.5% 등) 대상 아님. 짝이 맞으면 불변.\n    if \"연금소득세\" in ans:\n        _AGE_RATE = re.compile(r\"(?:(\\d{2})\\s*[~\\-–∼]\\s*)?(\\d{2})\\s*세\\s*(미만|이하|이상|초과|부터)?[^\\n%]{0,20}?(\\d(?:\\.\\d)?)\\s*%\")\n        _TABLE = {5.5: 5.5, 5.0: 5.5, 4.4: 4.4, 4.0: 4.4, 3.3: 3.3, 3.0: 3.3}\n        def _expected(age):\n            return 5.5 if age < 70 else (4.4 if age < 80 else 3.3)\n        def _pair_wrong(m):\n            r = float(m.group(4))\n            if r not in _TABLE: return False\n            a, b, rel = m.group(1), int(m.group(2)), m.group(3)\n            if a:                                   # '55~64세' 범위형: 하한으로 판정 + 상한은 69/79만 허용\n                lo, hi = int(a), b\n                if hi not in (69, 79) and hi < 100: return True\n                return _TABLE[r] != _expected(lo)\n            if rel == \"미만\": return _TABLE[r] != _expected(b - 1)     # '70세 미만' = 70 아래 구간\n            if rel == \"이하\": return _TABLE[r] != _expected(b)\n            return _TABLE[r] != _expected(b)                          # 이상/부터/없음 = 하한\n        _wrong = [m for m in _AGE_RATE.finditer(ans) if _pair_wrong(m)]\n        if _wrong:\n            _fixed = (\"연금소득세율(지방소득세 포함)은 문서 기준으로 만 70세 미만 5.5%, \"\n                      \"70세 이상 80세 미만 4.4%, 80세 이상 3.3%입니다.\")\n            _lines, _done = [], False\n            for _ln in ans.split(\"\\n\"):\n                if any(_pair_wrong(m) for m in _AGE_RATE.finditer(_ln)):\n                    if not _done:\n                        _lines.append(_fixed); _done = True\n                    continue\n                _lines.append(_ln)\n            ans = \"\\n\".join(_lines)\n    return ans.strip()\n\n\n"], ["        _fire = (any(k in question for k in _EXEMPT_ACT)\n                 or (any(k in question for k in _EXEMPT_HINT)\n                     and any(k in question for k in _EXEMPT_TAX)))\n        # v11.7: '세액공제로 돌려받/환급'은 환급 문맥이지 인출 과세가 아님.\n        #   세액공제·공제 질문인데 실제 인출·해지어가 없으면 과세제외 카드 미부착(E01 오탐 차단).\n        if _fire and re.search(r\"세액공제|공제(?:액|율|금액|한도)|환급\", question) \\\n", "        _fire = (any(k in question for k in _EXEMPT_ACT)\n                 or (any(k in question for k in _EXEMPT_HINT)\n                     and any(k in question for k in _EXEMPT_TAX)))\n        # v13.12(N6): '중도해지 세금은 빼고, 연금으로 받을 때 세금만' — 인출·해지어 뒤 12자 안에\n        #   제외 표현이 오면 그 주제를 빼달라는 것이므로 인출 과세 카드를 붙이지 않는다.\n        if _fire and re.search(r\"(?:인출|해지|출금|환매|중도)[^\\n]{0,12}?(?:빼고|말고|제외|넘어가|됐고|생략|건너뛰)\", question):\n            _fire = False\n        # v11.7: '세액공제로 돌려받/환급'은 환급 문맥이지 인출 과세가 아님.\n        #   세액공제·공제 질문인데 실제 인출·해지어가 없으면 과세제외 카드 미부착(E01 오탐 차단).\n        if _fire and re.search(r\"세액공제|공제(?:액|율|금액|한도)|환급\", question) \\\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "v13.12(N4)" in src: print("[스킵] 이미 v13.12 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[경고] 적용전 md5가 예상 v1311과 다름. 훅 매칭되면 계속.")
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v1311_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
