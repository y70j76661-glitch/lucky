# -*- coding: utf-8 -*-
# report.py — 사냥 결과(probe*.jsonl)를 한 파일로 정리한다.
#   사용법: python3 report.py probe3.jsonl [probe_reco.jsonl ...]
#   출력: 화면 + report_out.txt (걸린 것 전체 + 유형별 답변 요약 + 통계)
import json, re, sys, os

files = sys.argv[1:] or ["probe3.jsonl"]
OUT = "report_out.txt"
lines = []


def w(s=""):
    lines.append(s)


for path in files:
    if not os.path.exists(path):
        w(f"[없음] {path}")
        continue
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    w("=" * 70)
    w(f"파일: {path}  (총 {len(rows)}문항)")
    w("=" * 70)

    # 1) 걸린 것(오류/의심) — 답변 300자
    flagged = [r for r in rows if r.get("hard") or r.get("soft")]
    hard_n = sum(1 for r in rows if r.get("hard"))
    soft_n = sum(1 for r in rows if r.get("soft") and not r.get("hard"))
    w(f"\n── 걸린 문항: 오류 {hard_n} / 의심 {soft_n} ──")
    for r in flagged:
        tag = "오류" if r.get("hard") else "의심"
        w(f"\n[{r['id']}] ({r.get('cat', '?')}) [{tag}] {r['q']}")
        for h in r.get("hard", []):
            w(f"   ⚠ {h}")
        for s in r.get("soft", []):
            w(f"   · {s}")
        w("   답변: " + re.sub(r"\s+", " ", r.get("answer", ""))[:300])

    # 2) 유형별 통계
    cats = {}
    for r in rows:
        c = r.get("cat", "?")
        cats.setdefault(c, [0, 0])
        if r.get("hard"):
            cats[c][0] += 1
        cats[c][1] += 1
    w("\n── 유형별 (오류/전체) ──")
    for c, (b, t) in cats.items():
        w(f"   {c}: {b}/{t}")

    # 3) 역질문 통계(추천 사냥에 askback 필드가 있으면)
    if any("askback" in r for r in rows):
        ab = sum(1 for r in rows if r.get("askback"))
        w(f"\n── 역질문(되묻기) 나온 문항: {ab}/{len(rows)} ──")

    # 4) 전체 답변 요약 — 유형별로 답변 400자씩 (사람이 태도·논리 확인용)
    w("\n── 전체 답변(유형별, 400자) ──")
    for c in cats:
        w(f"\n▼▼▼ [{c}] ▼▼▼")
        for r in rows:
            if r.get("cat") == c:
                w(f"\n[{r['id']}] {r['q']}")
                w(re.sub(r"\s+", " ", r.get("answer", ""))[:400])

txt = "\n".join(lines)
open(OUT, "w", encoding="utf-8").write(txt)
print(txt)
print(f"\n\n※ 위 전체 내용이 {OUT} 에도 저장됨. 이 화면 전체를 복사해서 붙여주면 됩니다.")
