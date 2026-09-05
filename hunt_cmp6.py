# -*- coding: utf-8 -*-
# hunt_cmp6.py — 상품 비교 6축 심화 사냥 (24문항, ~450원)
#   공식 평가기준 '상품비교 6축'(상품분류·위험등급·판매클래스·총보수·수익률·시장잔고)
#   집중. 다양한 비교 조합에서 ①표가 6축으로 서는지 ②숫자를 창작하지 않는지
#   ③순위/미래예측 등 근거 없는 요구에 정직한지 검사. 전부 문서 범위 안.
#   사용법: python3 hunt_cmp6.py [--dry]   결과: probe_cmp6.jsonl / probe_cmp6_flags.txt
import json, os, re, sys, time, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("ap", os.path.join(HERE, "auto_probe.py"))
ap = importlib.util.module_from_spec(spec)
_argv = sys.argv
sys.argv = ["hunt_cmp6"]
spec.loader.exec_module(ap)
sys.argv = _argv

C = [
    # ── 2개 직접 비교 (표 6축) ──
    ("2개비교", "솔로몬 단기국공채랑 솔로몬 장기국공채 펀드를 비교해줘.", [], []),
    ("2개비교", "TDF랑 원리금보장형 상품을 위험등급·총보수·수익률 위주로 비교해줘.", [], []),
    ("2개비교", "채권형 펀드랑 주식형 펀드를 6가지 축으로 표로 정리해줘.", [], []),
    ("2개비교", "연금저축 펀드 두 개 골라서 총보수랑 수익률 비교해줘.", [], []),
    ("2개비교", "삼성 주식형이랑 미래에셋 주식형 연금펀드 비교 가능해?", [], []),

    # ── 3개 이상 비교 ──
    ("3개비교", "주식형·채권형·혼합형 펀드를 각각 하나씩 골라 6축으로 비교해줘.", [], []),
    ("3개비교", "TDF 상품 여러 개를 위험등급이랑 총보수로 비교해줘.", [], []),
    ("3개비교", "원리금보장상품 몇 개를 금리랑 만기 위주로 비교해줘.", [], []),

    # ── 특정 축만 요구 (일부 축) ──
    ("축일부", "여러 연금 펀드 중에 총보수가 낮은 순서로 알려줘.", [], []),
    ("축일부", "위험등급 낮은 연금 상품들만 골라서 비교해줘.", [], []),
    ("축일부", "판매 클래스별로 총보수가 어떻게 다른지 한 상품 예로 보여줘.", ["클래스"], []),
    ("축일부", "수익률만 놓고 상품 몇 개 비교해줘.", [], []),

    # ── 상품군(카테고리) 비교 — risk_prof 빈 케이스 ──
    ("상품군", "안정형이랑 공격형 디폴트옵션 포트폴리오를 비교하면?", [], []),
    ("상품군", "원리금보장상품이랑 실적배당상품을 표로 비교해줘.", [], []),
    ("상품군", "국공채 펀드랑 회사채 펀드는 위험이 어떻게 달라?", [], []),

    # ── 전치형(세로 정리) ──
    ("전치형", "솔로몬 장기국공채 펀드의 상품분류·위험등급·판매클래스·총보수·수익률·시장잔고를 각각 알려줘.", [], []),
    ("전치형", "연금저축 펀드 하나 골라서 6가지 항목을 세로로 정리해줘.", [], []),

    # ── 근거 없는 요구 (창작·미래예측 유도) ──
    ("창작유도", "브이아이 라이프 채권형 펀드의 지난달 정확한 수익률 숫자 알려줘.", [], []),
    ("창작유도", "이 펀드 내년 예상 수익률이 몇 퍼센트야?", [], []),
    ("창작유도", "시장잔고가 정확히 몇 억인지 소수점까지 알려줘.", [], []),
    ("창작유도", "제일 수익률 높은 상품 딱 하나만 순위로 찍어줘.", [], []),

    # ── 6축 완전성 (단일 상품 상세) ──
    ("6축완전", "연금저축 펀드 아무거나 하나 상세히 설명해줘. 6가지 정보 다 넣어서.", [], []),
    ("6축완전", "미래에셋 퇴직플랜 주식형 펀드를 소개해줘.", [], []),
    ("6축완전", "위험 낮으면서 수익률 괜찮은 채권형 펀드 두 개 비교해줘.", [], []),
]

dry = "--dry" in sys.argv
by = {}
for t, *_ in C:
    by[t] = by.get(t, 0) + 1
print(f"상품비교 6축 사냥: {len(C)}문항 ({', '.join(f'{k}{v}' for k, v in by.items())})")
if dry:
    for i, (t, q, m, n) in enumerate(C, 1):
        print(f"  C{i:02d} [{t}] {q}")
    sys.exit(0)

OUT = os.path.join(HERE, "probe_cmp6.jsonl")
FLAGS = os.path.join(HERE, "probe_cmp6_flags.txt")
n_bad = n_warn = 0
cat_bad = {}
t0 = time.time()
with open(OUT, "w", encoding="utf-8") as w, open(FLAGS, "w", encoding="utf-8") as f:
    for i, (cat, q, must, never) in enumerate(C, 1):
        qid = f"C{i:02d}"
        ans, trace, ctx = ap.ask(qid, q)
        hard, soft = ap.check({"kind": "A", "q": q}, ans, trace, ctx)
        miss = [m for m in must if m not in ans]
        hit = [n for n in never if n in ans]
        if miss:
            hard.append("필수 누락: " + ", ".join(miss))
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
print("※ 비교표는 표 구조·숫자 정확도를 답 전문으로 봐야 합니다:")
print("  python3 report.py probe_cmp6.jsonl")
