import json, re
chunks = json.load(open("chunks.json", encoding="utf-8"))
def show(title, pat, limit=4, win=230):
    print("=" * 72); print(title)
    rx = re.compile(pat); n = 0
    for c in chunks:
        m = rx.search(c["text"])
        if not m: continue
        s = max(0, m.start() - win); e = m.end() + win
        print(f"--- {c['source']}")
        print("   " + c["text"][s:e].replace("\n", " ")); n += 1
        if n >= limit: break
    if n == 0: print("(문서에 없음)")
    print()
show("[F] 기타소득세 16.5%가 '무엇에' 부과되는가", r"기타소득세")
show("[G] 중도해지 시 세액공제 추징/환수 표현", r"추징|환수|세액공제.{0,15}반환")
show("[H] 세액공제 한도 700만원이 나오는 맥락", r"700만\s*원")
