# -*- coding: utf-8 -*-
"""x2_check.py — X2 답변의 두 단정('ISA 전환금액은 세액공제 대상 아님/과세 안 됨', '가장 마지막에 인출')이 출처 문서
(doc39.docx, doc41.docx)에 그대로 있는지 원문 대조(API 호출 0회). 사용: cd /root/app && python3 x2_check.py > x2_check_out.txt"""
import json, re
d = json.load(open("chunks.json", encoding="utf-8")); it = d if isinstance(d, list) else d.values()
ts = [(c.get("text", ""), c.get("source", "")) for c in it if isinstance(c, dict)]
def show(title, srcs, must, width=500):
    print("=" * 90); print(f"## {title}")
    hits = [(t, s) for t, s in ts if s in srcs and all(re.search(m, t) for m in must)]
    print(f"청크 {len(hits)}개")
    for t, s in hits[:6]:
        tt = re.sub(r"\s+", " ", t)
        m = re.search(must[0], tt); a = max(0, (m.start() if m else 0) - width // 3)
        print(f"  [{s}] {tt[a:a + width]}")
S = ("doc39.docx", "doc41.docx")
show("ISA 전환금 — 세액공제/과세제외 서술", S, [r"ISA", r"세액공제|과세\s*제외|과세제외"])
show("ISA 전환금 — 조건(10%·300만원 한도 등)", S, [r"ISA", r"10\s*%|300\s*만"])
show("인출 순서 — '마지막'·'순서'", S, [r"인출\s*순서|마지막|먼저\s*인출|순서로\s*인출"])
show("세액공제 받지 않은 납입금 — 과세제외", S, [r"세액공제[를을]?\s*받지\s*않은|과세제외금액"])
show("(참고) ISA 전환 — 전체 코퍼스에서 '전환' 규정", tuple({s for _, s in ts}), [r"ISA", r"전환", r"연금계좌"])
print("=" * 90); print("끝")
