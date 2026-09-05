# -*- coding: utf-8 -*-
"""patch_v1348.py — v1347(6296e8a0) main.py 에 v13.48 적용. (v1347 적용 후 실행)
  [실측 mini25 G11] 최상급 질문에서 순위 단정 문장을 지운 뒤 붙는 '총보수 순위 비교표가 없고…' 고지는 지운 문장이 보수·수수료 순위였을 때만 붙인다
   (원금 손실 질문에 총보수 고지가 붙던 무관 정보 제거). 일반 순위 고지(답변 첫 줄)는 그대로.
자동백업·자가검증. 이미 v13.48이면 스킵. 검증 md5==cccb88aa333f01d44d6e0708364d7a76"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='6296e8a0f8b1228b40cc1256743b08ea'
EXPECT_AFTER='cccb88aa333f01d44d6e0708364d7a76'
HUNKS=[["    removed, out = 0, []\n    for line in ans.split(\"\\n\"):\n        if \"|\" in line or not line.strip():      # 표·빈 줄은 그대로\n            out.append(line)\n            continue\n        sents = re.split(r\"(?<![0-9]\\.)(?<=[.!?])\\s+\", line)\n        keep = []\n        for sent in sents:\n            if _RANK_CLAIM.search(sent) and not _RANK_NEG.search(sent):\n                removed += 1\n                continue\n            keep.append(sent)\n        out.append(\" \".join(keep))\n    if not removed:\n        return ans, 0\n    ans = re.sub(r\"\\n{3,}\", \"\\n\\n\", \"\\n\".join(out)).strip()\n    # 근거를 남기기 위해 한 문장으로 대체 (이미 같은 취지의 문장이 있으면 넣지 않는다)\n    if not re.search(r\"순위[^\\n]{0,20}(없|확인)\", ans):", "    removed, out, _fee_rm = 0, [], False\n    for line in ans.split(\"\\n\"):\n        if \"|\" in line or not line.strip():      # 표·빈 줄은 그대로\n            out.append(line)\n            continue\n        sents = re.split(r\"(?<![0-9]\\.)(?<=[.!?])\\s+\", line)\n        keep = []\n        for sent in sents:\n            if _RANK_CLAIM.search(sent) and not _RANK_NEG.search(sent):\n                removed += 1\n                _fee_rm = _fee_rm or bool(re.search(r\"보수|수수료|비용\", sent))\n                continue\n            keep.append(sent)\n        out.append(\" \".join(keep))\n    if not removed:\n        return ans, 0\n    ans = re.sub(r\"\\n{3,}\", \"\\n\\n\", \"\\n\".join(out)).strip()\n    # 근거를 남기기 위해 한 문장으로 대체 (이미 같은 취지의 문장이 있으면 넣지 않는다)\n    # v13.48(G11 실측): 총보수 고지는 지운 문장이 보수·수수료 순위였을 때만 — 그 외 최상급 질문은 (1-3) 일반 순위 고지가 맡는다\n    if _fee_rm and not re.search(r\"순위[^\\n]{0,20}(없|확인)\", ans):"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "v13.48(G11 실측)" in src: print("[스킵] 이미 v13.48 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[경고] 적용전 md5가 예상 v1347과 다름. 훅 매칭되면 계속.")
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v1347_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
