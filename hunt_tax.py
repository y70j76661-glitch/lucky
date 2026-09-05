# -*- coding: utf-8 -*-
# hunt_tax.py — 세제 '개정 전후' 혼동 사냥 (8문항, ~120원)
#   구기준(400만·700만·1,200만)을 미끼로 던져 현행 기준으로 교정하는지 본다.
#   사용법: python3 hunt_tax.py [--dry]   결과: probe_tax.jsonl / probe_tax_flags.txt
import json, os, re, sys, time, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("ap", os.path.join(HERE, "auto_probe.py"))
ap = importlib.util.module_from_spec(spec)
_argv = sys.argv
sys.argv = ["hunt_tax"]
spec.loader.exec_module(ap)
sys.argv = _argv

C = [
    ("개정", "연금저축 세액공제 한도가 언제부터 600만원으로 늘어났나요?", ["2023"], []),
    ("개정", "예전엔 연금저축 세액공제가 400만원까지였다던데, 지금은 얼마예요?", ["600"], []),
    ("개정", "연금계좌 세액공제 한도가 700만원에서 900만원으로 바뀐 게 맞나요?", ["900"], []),
    ("개정", "연금소득 종합과세 기준이 연 1,200만원 아니었어요?", ["1,500"], []),
    ("개정", "연금을 연 1,500만원 넘게 받으면 무조건 종합과세인가요, 다른 선택지도 있나요?", [], []),
    ("개정", "세액공제율이 15%라는 데도 있고 16.5%라는 데도 있던데 뭐가 맞아요?", ["지방"], []),
    ("개정", "ISA 만기자금을 연금계좌로 전환하면 세액공제를 얼마나 더 받을 수 있어요?", ["300"], []),
    ("개정", "맞벌이 부부인데 세액공제 한도는 부부 합산으로 계산하나요?", [], []),
]

dry = "--dry" in sys.argv
print(f"세제 개정 사냥: {len(C)}문항")
if dry:
    for i, (t, q, m, n) in enumerate(C, 1):
        print(f"  T{i:02d} {q}")
    sys.exit(0)

OUT = os.path.join(HERE, "probe_tax.jsonl")
FLAGS = os.path.join(HERE, "probe_tax_flags.txt")
n_bad = n_warn = 0
with open(OUT, "w", encoding="utf-8") as w, open(FLAGS, "w", encoding="utf-8") as f:
    for i, (cat, q, must, never) in enumerate(C, 1):
        qid = f"T{i:02d}"
        ans, trace, ctx = ap.ask(qid, q)
        hard, soft = ap.check({"kind": "A", "q": q}, ans, trace, ctx)
        miss = [m for m in must if m not in ans]
        hit = [n for n in never if n in ans]
        if miss:
            hard.append("필수 누락: " + ", ".join(miss))
        if hit:
            hard.append("금지어 출현: " + ", ".join(hit))
        w.write(json.dumps({"id": qid, "kind": "A", "cat": cat, "q": q,
                            "answer": ans, "trace": trace, "hard": hard,
                            "soft": soft}, ensure_ascii=False) + "\n")
        n_bad += bool(hard)
        n_warn += bool(soft and not hard)
        tag = "통과" if not (hard or soft) else ("오류" if hard else "의심")
        print(f"[{qid}] {tag} | {q}")
        if hard or soft:
            f.write(f"\n[{qid}] {q}\n")
            for h in hard:
                f.write(f"  [오류] {h}\n")
            for s in soft:
                f.write(f"  [의심] {s}\n")
            f.write("  답변: " + re.sub(r"\s+", " ", ans)[:300] + "\n")
        # T05·T08은 판정 기준이 없으니 답 전문을 출력해 사람이 본다
        if qid in ("T05", "T08"):
            print("   답변: " + re.sub(r"\s+", " ", ans)[:350])
        time.sleep(1.0)

print(f"\n완료: 오류 {n_bad} / 의심 {n_warn} → {FLAGS}")
