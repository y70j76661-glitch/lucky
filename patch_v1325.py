# -*- coding: utf-8 -*-
"""patch_v1325.py — v1324(29e3a475) main.py 에 v13.25 적용. (v1324 적용 후 실행)
  [cite_check 실측 — 출처 줄과 본문의 불일치 2종 + M2 잔여]
   N6: 코드가 고정하는 연금소득세 연령-세율 문장(70세 미만 5.5% …)의 근거 문서가 출처 줄에 없었음 → 기동 시 근거 청크의
       문서를 1회 찾아두고, 그 문장이 들어간 답변의 [참고 문서]에 포함.
   M2: 답변에 이름이 나온 상품(인덱스12M)의 문서가 출처 5개 절단으로 빠짐 → 절단된 문서 중 답변 상품명이 있는 문서는 되살림.
   M2: 세금 질문 아닌 추천 답변의 '조세특례제한법 … 비과세' 법령 인용 문장 제거(구 개인연금 설명서 유래).
자동백업·자가검증. 이미 v13.25면 스킵. 검증 md5==aea56ab9f6fd64147fc28da787feac20"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='29e3a475af29cfeed710a60bdfa0cf2a'
EXPECT_AFTER='aea56ab9f6fd64147fc28da787feac20'
HUNKS=[["matrix = np.array([e[\"embedding\"] for e in embs])\nmatrix = matrix / np.linalg.norm(matrix, axis=1, keepdims=True)\nprint(f\"로딩 완료: 청크 {len(idx_list)}개\")\n# v13.13(일반 게이트 1): 상품명 대조용 코퍼스 블롭(공백 제거). Primary Source = 주입 문서 전체.\n_CORPUS_NORM = \"\\u0001\".join(re.sub(r\"\\s+\", \"\", (c.get(\"text\", \"\") if isinstance(c, dict) else str(c)))\n                            for c in (chunks if isinstance(chunks, list) else chunks.values()))\n", "matrix = np.array([e[\"embedding\"] for e in embs])\nmatrix = matrix / np.linalg.norm(matrix, axis=1, keepdims=True)\nprint(f\"로딩 완료: 청크 {len(idx_list)}개\")\n# v13.25(cite_check N6): 코드가 고정하는 연금소득세 연령-세율 문장의 근거 문서 — 출처 줄에 반드시 포함시키기 위해 기동 시 1회 탐색\n_AGE_SRC = \"\"\nfor _c in (chunks if isinstance(chunks, list) else chunks.values()):\n    _t = re.sub(r\"\\s+\", \"\", _c.get(\"text\", \"\") if isinstance(_c, dict) else str(_c))\n    if \"70세\" in _t and \"5.5%\" in _t and \"4.4%\" in _t and \"3.3%\" in _t:\n        _AGE_SRC = _c.get(\"source\", \"\") if isinstance(_c, dict) else \"\"\n        break\n_PROD_CITE = re.compile(r\"[가-힣A-Za-z0-9()\\[\\]·\\-]{6,}(?:증권자?투자신탁|투자신탁|펀드|ETF)\")\n# v13.13(일반 게이트 1): 상품명 대조용 코퍼스 블롭(공백 제거). Primary Source = 주입 문서 전체.\n_CORPUS_NORM = \"\\u0001\".join(re.sub(r\"\\s+\", \"\", (c.get(\"text\", \"\") if isinstance(c, dict) else str(c)))\n                            for c in (chunks if isinstance(chunks, list) else chunks.values()))\n"], ["            _ml, _nm = [], 0\n            for _ln in ans.split(\"\\n\"):\n                _ss = re.split(r\"(?<=[.!?])\\s+\", _ln)\n                _kp = [x for x in _ss if not (re.search(r\"소득공제|세액공제|비과세|이자소득세|세제\\s*혜택\", x)\n                                              and re.search(r\"\\d+\\s*(?:%|만\\s*원|년)\", x))]\n                _nm += len(_ss) - len(_kp)\n                if _ln.strip() and not \"\".join(_kp).strip():\n                    continue\n", "            _ml, _nm = [], 0\n            for _ln in ans.split(\"\\n\"):\n                _ss = re.split(r\"(?<=[.!?])\\s+\", _ln)\n                _kp = [x for x in _ss if not ((re.search(r\"소득공제|세액공제|비과세|이자소득세|세제\\s*혜택\", x)\n                                               and re.search(r\"\\d+\\s*(?:%|만\\s*원|년)\", x))\n                                              or \"조세특례제한법\" in x)]          # v13.25: 구 개인연금 설명서의 법령 인용 문장\n                _nm += len(_ss) - len(_kp)\n                if _ln.strip() and not \"\".join(_kp).strip():\n                    continue\n"], ["        if srcs:\n            # v12.1(P1-2): 근거 과다(6개+) 방지 — used는 관련도순이므로 상위 5개까지만 표기.\n            #   (len≤5이면 무변화 → 3~4개 정상 답변은 손대지 않고 6·7·8개만 5로 절단.)\n            ans = ans.rstrip() + \"\\n\\n[참고 문서] \" + \", \".join(srcs[:5])\n\n        # [8단계] v9.22: 출력 최종 정리 — 반드시 마지막에 실행되어야 하는 것만 모은다.\n        #   중간에서 지웠는데 최종 출력에 남는 일이 있어 위치를 끝으로 옮기고,\n", "        if srcs:\n            # v12.1(P1-2): 근거 과다(6개+) 방지 — used는 관련도순이므로 상위 5개까지만 표기.\n            #   (len≤5이면 무변화 → 3~4개 정상 답변은 손대지 않고 6·7·8개만 5로 절단.)\n            _keep_src = srcs[:5]\n            if len(srcs) > 5:\n                # v13.25(cite_check M2): 답변에 이름이 나온 상품의 문서가 절단으로 빠지면(출처 불일치) 그 문서는 되살린다\n                _cores = set()\n                for _pm in _PROD_CITE.finditer(ans):\n                    _cc = re.sub(r\"\\s+\", \"\", re.sub(r\"(?:증권자?투자신탁|투자신탁|펀드|ETF).*$\", \"\", _pm.group(0))).strip(\"·-\")\n                    if len(_cc) >= 4:\n                        _cores.add(_cc)\n                for _s in srcs[5:]:\n                    _txt = re.sub(r\"\\s+\", \"\", \"\".join(c[\"text\"] for c in used if c[\"source\"] == _s))\n                    if any(_cc in _txt for _cc in _cores):\n                        _keep_src.append(_s)\n            ans = ans.rstrip() + \"\\n\\n[참고 문서] \" + \", \".join(_keep_src)\n\n        # [8단계] v9.22: 출력 최종 정리 — 반드시 마지막에 실행되어야 하는 것만 모은다.\n        #   중간에서 지웠는데 최종 출력에 남는 일이 있어 위치를 끝으로 옮기고,\n"], ["        ans = _final_cleanup(ans)\n        if ans != _pre:\n            clean_note += \" 9) 최종정리(글리치·중복·흉터)\"\n        if src_tail:                      # v9.25: 출처 줄을 맨 끝으로 되돌린다\n            ans = ans.rstrip() + \"\\n\\n\" + src_tail.strip()\n        if clean_note:\n", "        ans = _final_cleanup(ans)\n        if ans != _pre:\n            clean_note += \" 9) 최종정리(글리치·중복·흉터)\"\n        if \"문서 기준 만 70세 미만 5.5%\" in ans and _AGE_SRC and src_tail and _AGE_SRC not in src_tail:\n            src_tail = src_tail.rstrip() + \", \" + _AGE_SRC          # v13.25: 코드 고정 문장의 근거 문서를 출처에 포함\n        if src_tail:                      # v9.25: 출처 줄을 맨 끝으로 되돌린다\n            ans = ans.rstrip() + \"\\n\\n\" + src_tail.strip()\n        if clean_note:\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "_AGE_SRC = \"\"" in src: print("[스킵] 이미 v13.25 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[경고] 적용전 md5가 예상 v1324과 다름. 훅 매칭되면 계속.")
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v1324_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
