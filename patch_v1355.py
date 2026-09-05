# -*- coding: utf-8 -*-
"""patch_v1355.py — v1354(9c766a17) main.py 에 v13.55 적용. (v1354 적용 후 실행)
  [mini32 실측] ① 비교 우열 문장 감지에 '위험등급이 더 낮습니다'(보다 없이) 포함 → 근거 없으면 제거(T6)
   ② 추천 계약의 대체 답변: 자료 원문 덤프(수상 이력 등) 대신 검색된 투자설명서에서 코드가 읽은 (상품명·위험등급·근거 문서) 목록으로,
   질문 성향(공격/안정)에 맞는 등급대 우선(T11) ③ '(출처: …)' 인용 줄의 파일명은 치환하지 않음
자동백업·자가검증. 이미 v13.55면 스킵. 검증 md5==3cb5efece4642860d4aa53d591ce62dc"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='9c766a173f656ca639415c2a8d5f6c25'
EXPECT_AFTER='3cb5efece4642860d4aa53d591ce62dc'
HUNKS=[["                            _m = re.search(r\"보다\\s*(?:위험(?:등급|도)?이\\s*)?(?:더\\s*)?(높|낮)\", _s) \\\n                                or re.search(r\"(?:상대적으로|비교적|더|가장)\\s*(낮|높)은\\s*위험\\s*등급\", _s)      # v13.53(T6): '상대적으로 낮은 위험등급' 단정", "                            _m = re.search(r\"보다\\s*(?:위험(?:등급|도)?이\\s*)?(?:더\\s*)?(높|낮)\", _s) \\\n                                or re.search(r\"(?:상대적으로|비교적|더|가장)\\s*(낮|높)은\\s*위험\\s*등급\", _s) \\\n                                or re.search(r\"위험\\s*등급이\\s*(?:상대적으로|비교적|더|가장)\\s*(낮|높)\", _s)      # v13.55(T6): '위험등급이 더 낮습니다' 단정"], ["        _fb = fallback_answer(_question_hint[0] if _question_hint else \"\", used, None, [f for f in PRODUCT_FACTS if _question_hint and re.search(f[\"key\"], _question_hint[0])])\n        body = (\"문의하신 조건에 맞는 상품을 제공된 자료 안에서 확정하지 못했습니다. 아래는 자료에서 확인되는 내용입니다.\\n\\n\" + _fb).rstrip()\n        _fixed_box[0] += 1", "        # v13.55(T11 실측): 원문 덤프 대신 검색된 투자설명서에서 코드가 읽은 (상품명, 위험등급, 출처) 목록으로 대체\n        _prof = extract_risk_profile(list(dict.fromkeys(c.get(\"source\", \"\") for c in used if str(c.get(\"source\", \"\")).startswith(\"R2_\"))))\n        _hint_q = _question_hint[0] if _question_hint else \"\"\n        _aggr = bool(re.search(r\"공격|고수익|높은\\s*수익|성장\", _hint_q)); _safe = bool(re.search(r\"안정|안전|원금|손해|손실\", _hint_q))\n        _items = sorted(_prof.items(), key=lambda kv: kv[1][\"grade\"])\n        if _aggr:\n            _items = [kv for kv in _items if kv[1][\"grade\"] <= 3] or _items\n        elif _safe:\n            _items = [kv for kv in _items if kv[1][\"grade\"] >= 4] or _items\n        _lines_ = []\n        for _n, _r in _items[:4]:\n            _lab = (_r.get(\"label\") or _LABEL_BY_GRADE.get(_r[\"grade\"], \"\")).replace(\" \", \"\")\n            _lines_.append(f\"- {_n}: 위험등급 {_r['grade']}등급({_lab}) — 근거 문서: {_r['src']}\\n - 유의: {_n}은(는) 실적배당형으로, 투자원금과 수익(분배금)은 보장되지 않습니다.\")\n        if _lines_:\n            body = (\"문의하신 조건에 맞는 상품을 제공된 자료 안에서 확정하지 못했습니다. 검색된 투자설명서에서 확인되는 상품과 위험등급은 다음과 같으며, \"\n                    \"후보로 검토하실 수 있습니다(1등급이 가장 높은 위험, 6등급이 가장 낮은 위험):\\n\\n\" + \"\\n\".join(_lines_))\n        else:\n            body = (\"문의하신 조건에 맞는 상품을 제공된 자료 안에서 확정하지 못했습니다. 투자 기간·감내 위험·계좌 종류를 알려주시면 \"\n                    \"제공된 자료 범위에서 다시 확인해 드리겠습니다.\")\n        _fixed_box[0] += 1"], ["            _l if (_l.strip().startswith(\"[참고 문서]\") or re.match(r\"\\s*[-•·*]?\\s*근거 문서\\s*:\", _l))   # v13.43: 렌더러의 근거 문서 줄은 출처 인용(참고 문서 목록과 동일 이름)", "            _l if (_l.strip().startswith(\"[참고 문서]\") or re.match(r\"\\s*[-•·*]?\\s*근거 문서\\s*:\", _l) or _l.lstrip().startswith(\"(출처\"))   # v13.43/55: 근거 문서 줄·인용 줄은 출처 표기"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "v13.55(T11 실측)" in src: print("[스킵] 이미 v13.55 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[경고] 적용전 md5가 예상 v1354와 다름. 훅 매칭되면 계속.")
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v1354_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
