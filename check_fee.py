import json, re
chunks = json.load(open("chunks.json", encoding="utf-8"))
PCT = re.compile(r"(\d+\.\d{2,4})\s*%?")
KEYS = ["총보수", "보수·비용", "보수비용", "총 보수"]

hits = [c for c in chunks if any(k in c["text"] for k in KEYS)]
print(f"'총보수/보수·비용' 포함 청크: {len(hits)}개\n")

bysrc = {}
for c in hits:
    for k in KEYS:
        for m in re.finditer(re.escape(k), c["text"]):
            seg = c["text"][m.start():m.start() + 120]
            for v in PCT.findall(seg):
                bysrc.setdefault(c["source"], set()).add(v)

print("=== 같은 문서 안에 서로 다른 보수 값이 여러 개인 경우 ===")
for src, vals in sorted(bysrc.items(), key=lambda x: -len(x[1])):
    if len(vals) >= 2:
        print(f"  {src}: {sorted(vals)}")

print("\n=== 실제 문장 예시 (앞 6개) ===")
for c in hits[:6]:
    i = max((c["text"].find(k) for k in KEYS if k in c["text"]), default=0)
    print(f"--- {c['source']}")
    print("   " + c["text"][max(0, i-100):i+220].replace("\n", " "))
    print()
