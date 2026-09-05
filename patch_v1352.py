# -*- coding: utf-8 -*-
"""patch_v1352.py — v1351(d4d5b4f6) main.py 에 v13.52 적용. (v1351 적용 후 실행)
  [mini29 실측] ① 추천 계약: 근거 미연결 상품의 머리말이 제거되면 그 블록의 설명 항목줄도 제거(설명 조각만 남던 T11), 상품이 하나도 안 남으면
   근거 자료 발췌로 대체, 제외 고지의 상품명 중복 제거 ② 비교: 근거 등급이 없는 상충 표기 셀('2등급(높은위험) / (보통위험)')은 '자료에서 확정하지 못함'으로
자동백업·자가검증. 이미 v13.52면 스킵. 검증 md5==58844e5d04036d7fc77357018c29f1a3"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='d4d5b4f6c52d2b4b7fc4ccfb390e968f'
EXPECT_AFTER='58844e5d04036d7fc77357018c29f1a3'
HUNKS=[["    lines = body.split(\"\\n\")\n    out = []\n    for ln0 in lines:\n        # 문장 단위로 처리: 같은 줄의 다른(실재) 상품 문장은 남긴다\n        _sents = re.split(r\"(?<=[.!?])\\s+\", ln0)\n        _kept = []\n        for ln in _sents:\n            drop = False\n            ln, drop = _rc_sentence(ln, _docs, removed, _fixed_box)\n            if not drop:\n                _kept.append(ln)\n        if ln0.strip() and not \"\".join(_kept).strip():\n            continue\n        out.append(\" \".join(_kept))\n    fixed = _fixed_box[0]\n    body = \"\\n\".join(out)", "    lines = body.split(\"\\n\")\n    out = []\n    _skip_blk = False                                             # v13.52(T11 실측): 머리말 상품이 제거되면 그 블록의 항목줄(설명)도 함께 제거\n    for ln0 in lines:\n        _is_head = bool(ln0.strip()) and not re.match(r\"^\\s*[-•·*]\\s\", ln0)\n        if not ln0.strip() or (_is_head and re.match(r\"^\\s*\\d+[.)]\\s\", ln0)):\n            _skip_blk = False\n        if _skip_blk and re.match(r\"^\\s*[-•·*]\\s\", ln0):\n            continue\n        # 문장 단위로 처리: 같은 줄의 다른(실재) 상품 문장은 남긴다\n        _sents = re.split(r\"(?<=[.!?])\\s+\", ln0)\n        _kept = []\n        for ln in _sents:\n            drop = False\n            ln, drop = _rc_sentence(ln, _docs, removed, _fixed_box)\n            if not drop:\n                _kept.append(ln)\n        if ln0.strip() and not \"\".join(_kept).strip():\n            if _is_head:\n                _skip_blk = True\n            continue\n        out.append(\" \".join(_kept))\n    fixed = _fixed_box[0]\n    body = \"\\n\".join(out)\n    removed = list(dict.fromkeys(removed))\n    if removed and not (_PROD_SPAN.search(body) or _PROD_CITE.search(body)):\n        # 근거 미연결 상품을 지우고 나니 상품이 하나도 없다 → 설명 조각 대신 근거 자료 발췌로 대체(빈 추천 방지)\n        _fb = fallback_answer(_question_hint[0] if _question_hint else \"\", used, None, [f for f in PRODUCT_FACTS if _question_hint and re.search(f[\"key\"], _question_hint[0])])\n        body = (\"문의하신 조건에 맞는 상품을 제공된 자료 안에서 확정하지 못했습니다. 아래는 자료에서 확인되는 내용입니다.\\n\\n\" + _fb).rstrip()\n        _fixed_box[0] += 1"], ["                    for _j, (_nm, _g) in enumerate(_ge):\n                        if not _g:\n                            continue", "                    for _j, (_nm, _g) in enumerate(_ge):\n                        if not _g:\n                            if re.search(r\"\\d\\s*등급[^;]*\\d\\s*등급\", _vals[_j]) or len(re.findall(r\"위험\\)\", _vals[_j])) >= 2 or re.search(r\"등급[^;]*/\\s*\\(\", _vals[_j]):\n                                _vals[_j] = \"자료에서 확정하지 못함(표기 상충)\"; _nfix += 1      # v13.52(T6): 근거 없는 상충 셀은 단정하지 않는다\n                            continue"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "v13.52(T11 실측)" in src: print("[스킵] 이미 v13.52 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[경고] 적용전 md5가 예상 v1351과 다름. 훅 매칭되면 계속.")
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v1351_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
