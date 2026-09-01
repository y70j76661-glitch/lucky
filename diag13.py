import re, requests
Q = "명퇴하는 교사예요. 명퇴수당을 연금계좌에 넣으면 세금 감면이 어마어마하다던데, 절세법만 알려주세요."
Q24 = "IRP에 연 2000만원 넣으면 세액공제 얼마나 받아?"
dpat = re.compile(r"\d+\s*(?:영업일|일|개월|년)\s*(?:이내|내에|안에|까지)")

def run(tag, q):
    d = requests.get("http://localhost:8000/answer",
                     params={"question_id": tag, "question": q}, timeout=300).json()
    ctx, ans = d.get("retrieved_context", ""), d.get("answer", "")
    print("=" * 72); print(f"[{tag}] {q[:50]}")
    print("[trace]", d.get("think_trace", "")); print()
    qterms = {w[:3] for w in re.findall(r"[0-9A-Za-z가-힣]{3,}", q)}
    print("질문 어절 앞3글자:", sorted(qterms)); print()
    sents = []
    for sent in re.split(r"(?<=[.!?])\s+|\n+", ctx):
        sent = re.sub(r"\s+", " ", sent).strip()
        if sent and dpat.search(sent) and sent not in sents:
            sents.append(sent)
    print(f"기한 문장 {len(sents)}개 (앞 4개만 프롬프트에 들어감)")
    for i, t in enumerate(sents[:6], 1):
        hit = [w for w in qterms if w in t]
        print(f"  {i}) 겹침 {len(hit)} {hit}")
        print(f"     {t[:180]}")
    print()
    print("답변에 '60일' 포함:", "60일" in ans)
    print("답변 앞 200자:", ans[:200].replace("\n", " "))
    print()

run("D13", Q)
run("D24", Q24)
