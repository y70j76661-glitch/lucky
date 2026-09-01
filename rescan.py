# -*- coding: utf-8 -*-
# rescan.py — 이미 받아놓은 답변(probe.jsonl)을 '고친 검사기'로 다시 채점한다.
#   API를 한 번도 부르지 않는다 → 크레딧 0원.
#   검사기를 고칠 때마다 이걸 돌리면, 같은 710건을 몇 번이고 다시 볼 수 있다.
import json, os, re, sys, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("ap", os.path.join(HERE, "auto_probe.py"))
ap = importlib.util.module_from_spec(spec)
sys.argv = ["rescan"]
spec.loader.exec_module(ap)

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "probe.jsonl")
OUT = os.path.join(HERE, "probe_flags2.txt")

rows = []
with open(SRC, encoding="utf-8") as f:
    for ln in f:
        try:
            rows.append(json.loads(ln))
        except Exception:
            pass
print(f"재채점 대상 {len(rows)}건  (검사기: garble_score = main.py 현재 버전)")

hard_c, soft_c, n_hard, n_soft = {}, {}, 0, 0
old_hard = sum(1 for r in rows if r.get("hard"))
with open(OUT, "w", encoding="utf-8") as w:
    for r in rows:
        item = {"kind": r.get("kind", "A"), "q": r.get("q", "")}
        ctx = r.get("ctx")            # 예전 파일에는 없다 → 숫자 검사만 생략
        hard, soft = ap.check(item, r.get("answer", ""), r.get("trace", ""), ctx)
        # 예전 결과에서 '근거에 없는 숫자'는 그대로 이어받는다 (근거를 다시 못 보므로)
        if ctx is None:
            soft += [x for x in r.get("soft", []) if x.startswith("근거에 없는 숫자")]
        if not (hard or soft):
            continue
        n_hard += bool(hard)
        n_soft += bool(soft and not hard)
        for h in hard:
            hard_c[h.split(":")[0]] = hard_c.get(h.split(":")[0], 0) + 1
        for x in soft:
            soft_c[x.split(":")[0]] = soft_c.get(x.split(":")[0], 0) + 1
        w.write(f"\n[{r['id']}] ({r.get('kind')}) {r.get('q')}\n")
        if r.get("src"):
            w.write(f"  근거 문서: {r['src']}\n")
        for h in hard:
            w.write(f"  [오류] {h}\n")
        for x in soft:
            w.write(f"  [의심] {x}\n")
        w.write("  답변: " + re.sub(r"\s+", " ", r.get("answer", ""))[:400] + "\n")

print(f"\n이전 검사기: 오류 {old_hard}건")
print(f"고친 검사기: 오류 {n_hard}건 / 의심 {n_soft}건")
print("\n== 오류 종류별 ==")
for k, v in sorted(hard_c.items(), key=lambda x: -x[1]):
    print(f"  {v:4d}  {k}")
print("== 의심 종류별 ==")
for k, v in sorted(soft_c.items(), key=lambda x: -x[1]):
    print(f"  {v:4d}  {k}")
print(f"\n→ {OUT}")
