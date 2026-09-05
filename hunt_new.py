# -*- coding: utf-8 -*-
# hunt_new.py — 재추출한 14개 문서를 겨냥한 표적 사냥.
#   전사본(reocr/*.txt)의 Q줄을 그대로 질문으로 뽑아 현재 서버에 묻는다.
#   기존 사냥 기록은 전부 '깨진 옛 문서' 기준이라, 새 문서에 대한 사냥은
#   이번이 처음이다. 검사기는 auto_probe의 check()를 그대로 재사용한다.
#
#   사용법:
#     python3 hunt_new.py --dry          질문만 출력 (0원)
#     python3 hunt_new.py                실행 (~N건 × 15원)
#     python3 hunt_new.py --max 100     100건만
#   결과: probe_new.jsonl (전체) / probe_new_flags.txt (걸린 것만)
import json, os, re, sys, time, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("ap", os.path.join(HERE, "auto_probe.py"))
ap = importlib.util.module_from_spec(spec)
_argv = sys.argv
sys.argv = ["hunt_new"]
spec.loader.exec_module(ap)
sys.argv = _argv

DOCS = ["doc2", "doc3", "doc5", "doc7", "doc8", "doc9", "doc22", "doc24",
        "doc27", "doc30", "doc31", "doc32", "doc37", "doc54"]

# ── 1) 전사본에서 질문 추출 ─────────────────────────────────────────
def extract_questions(path):
    """'Q1. ...' / 'Q4-1. ...' 줄에서 질문 문장을 뽑는다.
    한 줄에 물음표 문장이 여럿이면 그대로 둔다(사람이 그렇게 묻기도 한다)."""
    qs = []
    for ln in open(path, encoding="utf-8"):
        m = re.match(r"^Q\s*\d+(?:-\d+)?\.\s*(?:\((?:BEST|DC 가입자)\)\s*)?(.+)$",
                     ln.strip())
        if not m:
            continue
        q = m.group(1).strip()
        q = re.sub(r"\s*\(매체별\)\s*$", "", q)     # 화면 안내용 꼬리표 제거
        q = re.sub(r"\s*#\S+\s*$", "", q)           # '#수수료' 태그 제거
        if len(q) >= 8:
            qs.append(q)
    return qs

# Q줄이 없는 매뉴얼형 문서는 내용의 핵심 사실을 겨냥한 질문을 직접 붙인다
EXTRA = {
    "doc2": ["구개인연금은 몇 살부터, 얼마나 가입해야 연금으로 받을 수 있나요?",
             "연금저축은 가입 5년만 채우면 55세에 연금 개시할 수 있나요?",
             "연금수령한도는 어떻게 계산하나요?",
             "2013년 3월 1일 전에 가입한 연금저축은 연금수령연차를 몇 년차부터 계산하나요?"],
    "doc3": ["연금저축계좌에 있는 펀드를 담보로 대출받으면 평가금액의 몇 퍼센트까지 가능한가요?",
             "연금계좌 담보대출 이자를 안 내면 어떻게 되나요?",
             "연금계좌 증권담보융자의 대출 기간은 얼마나 되나요?"],
    "doc5": ["연금저축계좌에서 중도인출하면 세금이 어떻게 되나요?",
             "부득이한 사유로 연금저축을 인출하면 세율이 달라지나요?",
             "6개월 이상 요양이 필요할 때 의료비는 얼마까지 인출할 수 있나요?"],
    "doc7": ["퇴직연금 계좌로 장외채권을 사려면 몇 시까지 주문해야 하나요?",
             "M-STOCK으로 산 장외채권을 앱에서 팔 수도 있나요?",
             "퇴직연금에서 회사채에 투자할 때 한도가 있나요?",
             "장외채권 매수 신청을 취소하려면 언제까지 해야 하나요?"],
    "doc22": ["IRP 계좌를 다른 증권사로 옮길 때 보유 상품 그대로 이전되나요?",
              "IRP 중도인출은 어떤 경우에 가능한가요?",
              "IRP를 해지하면 세금을 얼마나 내나요?"],
    "doc24": ["퇴직연금 계좌로 유상청약할 때 초과청약도 가능한가요?",
              "퇴직연금 유상청약은 청약 마감일 몇 시까지 신청할 수 있나요?",
              "퇴직연금 유상청약 신청을 취소할 수 있나요?"],
    "doc37": ["연금 인출기에는 주식 비중을 어떻게 조절하는 게 좋나요?",
              "연금을 오래 받으려면 인출 시기 자산 운용은 어떻게 해야 하나요?"],
}

items = []
for d in DOCS:
    p = os.path.join(HERE, "reocr", f"{d}.txt")
    if not os.path.exists(p):
        print(f"  ! {p} 없음 — 건너뜀")
        continue
    for q in extract_questions(p):
        items.append({"kind": "A", "q": q, "src": f"{d}.pdf"})
    for q in EXTRA.get(d, []):
        items.append({"kind": "A", "q": q, "src": f"{d}.pdf"})

# ── 2) 근사중복 제거 (같은 질문을 반복해 세지 않는다) ─────────────────
def _bigrams(s):
    s = re.sub(r"[\s?.!]", "", s)
    return {s[i:i + 2] for i in range(len(s) - 1)}

uniq, seen = [], []
for it in items:
    bg = _bigrams(it["q"])
    if any(len(bg & sb) / max(1, min(len(bg), len(sb))) >= 0.8 for sb in seen):
        continue
    seen.append(bg)
    uniq.append(it)
items = uniq

# ── 3) 실행 ────────────────────────────────────────────────────────
dry = "--dry" in sys.argv
max_n = None
if "--max" in sys.argv:
    max_n = int(sys.argv[sys.argv.index("--max") + 1])
if max_n:
    items = items[:max_n]

print(f"표적 사냥 대상: {len(items)}건 (14개 재추출 문서의 자체 Q)")
if dry:
    for i, it in enumerate(items, 1):
        print(f"  N{i:03d} [{it['src']}] {it['q']}")
    sys.exit(0)

OUT = os.path.join(HERE, "probe_new.jsonl")
FLAGS = os.path.join(HERE, "probe_new_flags.txt")
n_hard = n_soft = 0
t0 = time.time()
with open(OUT, "w", encoding="utf-8") as w, open(FLAGS, "w", encoding="utf-8") as f:
    for i, it in enumerate(items, 1):
        qid = f"N{i:04d}"
        ans, trace, ctx = ap.ask(qid, it["q"])
        hard, soft = ap.check(it, ans, trace, ctx)
        # 표적 사냥 전용 검사: 근거가 그 문서를 찾았는가
        if it["src"] not in (ctx or "") and it["src"] not in (ans or ""):
            soft = soft + [f"대상 문서 미검색: {it['src']}"]
        rec = {"id": qid, "kind": "A", "q": it["q"], "src": it["src"],
               "answer": ans, "trace": trace, "hard": hard, "soft": soft}
        w.write(json.dumps(rec, ensure_ascii=False) + "\n")
        if hard or soft:
            n_hard += bool(hard)
            n_soft += bool(soft and not hard)
            f.write(f"\n[{qid}] [{it['src']}] {it['q']}\n")
            for h in hard:
                f.write(f"  [오류] {h}\n")
            for s in soft:
                f.write(f"  [의심] {s}\n")
            f.write("  답변: " + re.sub(r"\s+", " ", ans)[:300] + "\n")
        if i % 20 == 0 or i == len(items):
            el = (time.time() - t0) / 60
            print(f"[{i}/{len(items)}] 오류 {n_hard} / 의심 {n_soft} "
                  f"(경과 {el:.1f}분)")
        time.sleep(1.0)

print(f"\n완료: 오류 {n_hard} / 의심 {n_soft} → {FLAGS}")
