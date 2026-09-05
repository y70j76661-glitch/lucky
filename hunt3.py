# -*- coding: utf-8 -*-
# hunt3.py — 3차 사냥 (40문항, ~600원)
#   축: ①상품 6축 심화 ②계좌구조 이해 ③디폴트옵션 심화 ④인출순서·과세정밀
#      ⑤답없는 질문 정직성(거절+역질문). 전부 미래에셋 문서 범위 안.
#   사용법: python3 hunt3.py [--dry]   결과: probe3.jsonl / probe3_flags.txt
import json, os, re, sys, time, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("ap", os.path.join(HERE, "auto_probe.py"))
ap = importlib.util.module_from_spec(spec)
_argv = sys.argv
sys.argv = ["hunt3"]
spec.loader.exec_module(ap)
sys.argv = _argv

C = [
    # ── 상품 6축 심화 ──
    ("상품6축", "미래에셋 솔로몬 장기국공채 펀드의 판매 클래스별로 총보수가 어떻게 다른가요?",
     ["클래스"], []),
    ("상품6축", "솔로몬 단기국공채 펀드 위험등급이 몇 등급이에요?",
     ["5등급"], ["4등급"]),
    ("상품6축", "TDF는 위험등급이 어떻게 되나요?",
     [], []),
    ("상품6축", "원리금보장형 상품에는 어떤 게 있어요?",
     [], []),
    ("상품6축", "퇴직연금 펀드는 일반 펀드보다 수수료가 싼가요?",
     [], []),
    ("상품6축", "연금저축 펀드 두 개 비교해줘. 수익률이랑 시장잔고 위주로.",
     [], []),
    ("상품6축", "C-P 클래스랑 C-P2 클래스가 뭐가 달라요?",
     [], []),
    ("상품6축", "실적배당형 상품은 원금 보장이 되나요?",
     [], ["원금이 보장", "원금 보장됩니다"]),

    # ── 계좌구조 이해 ──
    ("계좌구조", "DB형이랑 DC형 퇴직연금이 뭐가 다르고 누가 운용하는 거예요?",
     ["운용"], []),
    ("계좌구조", "IRP랑 연금저축은 뭐가 달라요?",
     [], []),
    ("계좌구조", "DC형은 회사가 운용해주는 거죠?",
     [], []),
    ("계좌구조", "제 퇴직연금이 DB인지 DC인지 어떻게 알아요?",
     [], []),
    ("계좌구조", "확정급여형이면 제가 운용 신경 안 써도 되나요?",
     [], []),
    ("계좌구조", "개인형 IRP는 아무나 가입할 수 있나요?",
     [], []),

    # ── 디폴트옵션 심화 (L20·L29 잔여 포함) ──
    ("디폴트심화", "예금 만기됐는데 그냥 두면 어떻게 되나요?",
     ["6주"], []),
    ("디폴트심화", "디폴트옵션 안정형은 예금이니까 원금 보장되죠?",
     [], ["무조건 원금", "원금이 보장됩니다"]),
    ("디폴트심화", "디폴트옵션을 두 개 들고 있는데 하나 더 사고 싶어요. 되나요?",
     [], []),
    ("디폴트심화", "디폴트옵션 안 쓰고 싶은데 어떻게 빼요?",
     [], []),
    ("디폴트심화", "회사가 디폴트옵션을 안 정해줬는데 저는 어떻게 지정해요?",
     [], []),
    ("디폴트심화", "부담금이 자동으로 디폴트옵션으로 안 가게 하려면요?",
     ["입금매수", "현금성자산"], []),
    ("디폴트심화", "같은 예금이 두 번째 만기되면 또 6주 기다려요?",
     ["즉시"], []),

    # ── 인출 순서·과세 정밀 ──
    ("인출과세", "연금계좌에서 돈 뺄 때 어느 돈부터 나가나요?",
     ["세액공제"], []),
    ("인출과세", "퇴직금이랑 세액공제 받은 돈이랑 안 받은 돈이 섞였으면 인출 순서가 어떻게 돼요?",
     ["퇴직"], []),
    ("인출과세", "세액공제 안 받은 돈을 빼면 세금 내나요?",
     ["없", "비과세"], []),
    ("인출과세", "퇴직금을 연금으로 받으면 퇴직소득세가 얼마나 감면돼요?",
     ["30"], []),
    ("인출과세", "연금저축이랑 퇴직금 연금은 세금 계산이 같아요?",
     [], []),
    ("인출과세", "연금소득세는 나이 많을수록 세율이 올라가나요 내려가나요?",
     ["3.3", "5.5"], []),

    # ── 답 없는 질문 정직성 (거절 + 역질문) ──
    ("정직성", "미래에셋 주가 지금 얼마예요?",
     [], []),
    ("정직성", "제 연금 계좌 잔액이 지금 얼마인지 알려주세요.",
     [], []),
    ("정직성", "내년 연금저축 세액공제 한도가 얼마로 바뀌나요?",
     [], []),
    ("정직성", "미래에셋이랑 삼성증권 중 어디가 수익률이 더 좋아요?",
     [], []),
    ("정직성", "비트코인 연금으로 투자할 수 있어요?",
     [], []),
    ("정직성", "제 나이에 맞는 상품 추천해주세요.",
     [], []),

    # ── 자연어·복합 마무리 ──
    ("복합마무리", "이직하는데 전 회사 퇴직연금이랑 새 회사 퇴직연금 어떻게 합쳐요?",
     [], []),
    ("복합마무리", "50대인데 지금이라도 연금저축 시작하면 세제 혜택 받을 수 있어요?",
     ["600"], []),
    ("복합마무리", "ISA 만기 자금 연금으로 옮기는 거랑 그냥 새로 넣는 거랑 세액공제가 달라요?",
     ["300"], []),
    ("복합마무리", "퇴직연금으로 채권 사려는데 위험하지 않아요? 한도도 있어요?",
     ["40"], []),
    ("복합마무리", "연금 언제부터 받을지 정했는데 나중에 바꿀 수 있어요?",
     [], []),
    ("복합마무리", "디폴트옵션이랑 입금매수상품 지정이랑 뭐가 달라요?",
     [], []),
]

dry = "--dry" in sys.argv
by = {}
for t, *_ in C:
    by[t] = by.get(t, 0) + 1
print(f"3차 사냥: {len(C)}문항 ({', '.join(f'{k}{v}' for k, v in by.items())})")
if dry:
    for i, (t, q, m, n) in enumerate(C, 1):
        print(f"  P{i:02d} [{t}] {q}")
    sys.exit(0)

OUT = os.path.join(HERE, "probe3.jsonl")
FLAGS = os.path.join(HERE, "probe3_flags.txt")
n_bad = n_warn = 0
cat_bad = {}
t0 = time.time()
with open(OUT, "w", encoding="utf-8") as w, open(FLAGS, "w", encoding="utf-8") as f:
    for i, (cat, q, must, never) in enumerate(C, 1):
        qid = f"P{i:02d}"
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
            f.write("  답변: " + re.sub(r"\s+", " ", ans)[:350] + "\n")
        if i % 10 == 0 or i == len(C):
            print(f"[{i}/{len(C)}] 오류 {n_bad} / 의심 {n_warn} "
                  f"(경과 {(time.time()-t0)/60:.1f}분)")
        time.sleep(1.0)

print(f"\n완료: 오류 {n_bad} / 의심 {n_warn} → {FLAGS}")
if cat_bad:
    print("유형별 오류:", cat_bad)
print("※ 정직성·계좌구조·상품6축은 답 전문을 봐야 판단됩니다:")
print("  python3 -c \"import json; [print('\\n['+r['id']+'] '+r['q']+'\\n'+r['answer'][:500]) \"\\")
print("            \"for r in map(json.loads, open('probe3.jsonl')) if r['cat'] in ('정직성','계좌구조','상품6축')]\"")
