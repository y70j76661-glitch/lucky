# -*- coding: utf-8 -*-
# hunt_multi.py — 복합 다중요구 질문 사냥 (20문항, ~400원)
#   한 질문에 2~4개 요구를 담아, 모든 요구를 빠짐없이 충족하는지(요구사항 충족
#   완전성 축) 검사. must에는 각 요구가 답해졌을 때 반드시 나올 앵커만 건다.
#   실제 소비자의 긴 사연형·다중 질문에 강한지 확인. 전부 문서 범위 안.
#   사용법: python3 hunt_multi.py [--dry]   결과: probe_multi.jsonl / probe_multi_flags.txt
import json, os, re, sys, time, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("ap", os.path.join(HERE, "auto_probe.py"))
ap = importlib.util.module_from_spec(spec)
_argv = sys.argv
sys.argv = ["hunt_multi"]
spec.loader.exec_module(ap)
sys.argv = _argv

C = [
    # ── 2중 요구 ──
    ("2중요구", "예금 만기되면 어떻게 되고, 자동으로 안 넘어가게 하려면 어떻게 해요?",
     ["6주"], []),
    ("2중요구", "DC형이 뭐고 상품은 누가 고르는 거예요?",
     [], []),
    ("2중요구", "연금저축 중도해지하면 세금 얼마고, 안 떼는 경우도 있어요?",
     ["16.5", "부득이"], []),
    ("2중요구", "IRP는 아무나 가입돼요? 그리고 55세 전에 빼려면요?",
     [], []),

    # ── 3중 요구 ──
    ("3중요구", "IRP랑 연금저축 차이가 뭐고, 각각 세액공제 한도는 얼마고, 언제부터 찾을 수 있어요?",
     ["900", "55"], []),
    ("3중요구", "디폴트옵션이 뭐고, 안 정하면 어떻게 되고, 나중에 바꿀 수 있어요?",
     [], []),
    ("3중요구", "퇴직금을 IRP로 받으면 세금이 어떻게 되고, 연금으로 받으면 얼마 감면되고, 일시금이랑 뭐가 달라요?",
     ["30"], []),
    ("3중요구", "연금 언제부터 받을 수 있고, 몇 년 이상 받아야 하고, 나중에 수령시점 바꿀 수 있어요?",
     ["5년"], []),
    ("3중요구", "채권 언제 살 수 있고, 밤에도 되고, 한도는 어떻게 돼요?",
     ["15", "40"], []),
    ("3중요구", "ISA 만기 자금 연금으로 옮기면 공제 얼마 되고, 기존 한도랑 겹치고, 며칠 안에 옮겨야 해요?",
     ["300"], []),

    # ── 4중 요구 (고난도) ──
    ("4중요구", "연금저축 중도해지하면 세율 얼마고, 부득이한 사유면 어떻게 되고, 그 사유엔 뭐가 있고, 세율은 달라져요?",
     ["16.5"], []),
    ("4중요구", "총급여 5천만원인데 연금저축 600 IRP 300 넣으면 얼마 돌려받고, 급전 필요하면 뭘 먼저 빼야 손해 적고, 그때 세금은 어떻게 돼요?",
     ["16.5"], []),
    ("4중요구", "55세이고 IRP에 퇴직금이랑 개인납입금이 섞였는데, 연금으로 받으면 각각 세금이 어떻게 다르고, 어느 돈부터 나가고, 얼마나 나눠 받아야 유리해요?",
     [], []),

    # ── 긴 사연형(구어) 다중 요구 ──
    ("사연형", "제가 이번에 이직을 하는데요, 전 회사에선 DC였어요. 새 회사 퇴직연금이랑 어떻게 합치고, 그 사이에 돈은 어떻게 되고, 세금 나가는 건 없어요?",
     [], []),
    ("사연형", "노후에 매달 받고 싶은데요, 뭘 준비해야 하고, 세제 혜택은 얼마나 되고, 언제부터 받을 수 있어요?",
     ["900"], []),
    ("사연형", "50대 후반이고 이제 연금저축 시작하려는데, 늦은 건 아닌지, 세액공제는 받는지, 5년 채워야 한다는데 맞는지 알려주세요.",
     ["600", "5년"], []),

    # ── 비교 + 절차 혼합 요구 ──
    ("혼합요구", "원리금보장상품이랑 실적배당상품 뭐가 다르고, 각각 예금자보호는 되는지, 디폴트옵션엔 뭐가 들어가요?",
     [], []),
    ("혼합요구", "연금저축이랑 퇴직연금 세금 계산이 같은지 다른지, 인출 순서는 어떻게 되고, 종합과세 기준은 얼마예요?",
     ["1,500"], []),
    ("혼합요구", "담보대출이 뭐고, 얼마까지 되고, 중도인출이랑 뭐가 달라요?",
     ["담보"], []),
    ("혼합요구", "MP가 뭐고, 아무나 되는지, 디폴트옵션이랑 뭐가 달라요?",
     [], []),
]

dry = "--dry" in sys.argv
by = {}
for t, *_ in C:
    by[t] = by.get(t, 0) + 1
print(f"복합 다중요구 사냥: {len(C)}문항 ({', '.join(f'{k}{v}' for k, v in by.items())})")
if dry:
    for i, (t, q, m, n) in enumerate(C, 1):
        print(f"  M{i:02d} [{t}] {q}")
    sys.exit(0)

OUT = os.path.join(HERE, "probe_multi.jsonl")
FLAGS = os.path.join(HERE, "probe_multi_flags.txt")
n_bad = n_warn = 0
cat_bad = {}
t0 = time.time()
with open(OUT, "w", encoding="utf-8") as w, open(FLAGS, "w", encoding="utf-8") as f:
    for i, (cat, q, must, never) in enumerate(C, 1):
        qid = f"M{i:02d}"
        ans, trace, ctx = ap.ask(qid, q)
        hard, soft = ap.check({"kind": "A", "q": q}, ans, trace, ctx)
        miss = [m for m in must if m not in ans]
        hit = [n for n in never if n in ans]
        if miss:
            hard.append("필수(요구 앵커) 누락: " + ", ".join(miss))
        if hit:
            hard.append("금지어 출현: " + ", ".join(hit))
        w.write(json.dumps({"id": qid, "cat": cat, "q": q, "answer": ans,
                            "trace": trace, "hard": hard, "soft": soft},
                           ensure_ascii=False) + "\n")
        n_bad += bool(hard)
        n_warn += bool(soft and not hard)
        if hard:
            cat_bad[cat] = cat_bad.get(cat, 0) + 1
        if hard or soft:
            f.write(f"\n[{qid}] [{cat}] {q}\n")
            for h in hard:
                f.write(f"  [오류] {h}\n")
            for s in soft:
                f.write(f"  [의심] {s}\n")
            f.write("  답변: " + re.sub(r"\s+", " ", ans)[:400] + "\n")
        if i % 8 == 0 or i == len(C):
            print(f"[{i}/{len(C)}] 오류 {n_bad} / 의심 {n_warn} "
                  f"(경과 {(time.time()-t0)/60:.1f}분)")
        time.sleep(1.0)

print(f"\n완료: 오류 {n_bad} / 의심 {n_warn} → {FLAGS}")
if cat_bad:
    print("유형별 오류:", cat_bad)
print("※ 복합 질문은 '모든 요구를 답했는지'를 답 전문으로 봐야 합니다:")
print("  python3 report.py probe_multi.jsonl")
