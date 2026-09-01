import json, re
chunks = json.load(open("chunks.json", encoding="utf-8"))

def show(title, pat, limit=4, win=220):
    print("=" * 72); print(title)
    rx = re.compile(pat); n = 0
    for c in chunks:
        m = rx.search(c["text"])
        if not m: continue
        s = max(0, m.start() - win); e = m.end() + win
        print(f"--- {c['source']}")
        print("   " + c["text"][s:e].replace("\n", " "))
        n += 1
        if n >= limit: break
    if n == 0: print("(문서에 없음)")
    print()

show("[A] 연금저축 5년 요건 - 가입기간인가 수령기간인가", r"5년\s*(?:이상|경과|동안)")
show("[B] 60일 기한의 정확한 맥락", r"60일")
show("[C] 6개월 기한의 정확한 맥락", r"6개월")
show("[D] 분기 300만원 / 연 1200만원이 어느 상품 기준인지", r"1,?200만|분기.{0,10}300만")
show("[E] 전업주부 등 소득 없는 사람의 가입 가능 여부", r"전업주부|소득이\s*없")
