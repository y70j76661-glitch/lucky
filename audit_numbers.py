# 문서의 금액 표기·산술식 점검
import json, re
chunks = json.load(open("chunks.json", encoding="utf-8"))
print(f"청크 {len(chunks):,}개 점검\n")

# ── 1. 단위 의심 표기: '148만 5천만원'처럼 만+천만원이 겹친 형태
print("=" * 74)
print("[1] 단위 의심 표기  (예: 148만 5천'만'원)")
print("=" * 74)
P1 = re.compile(r"\d[\d,]*\s*만\s*\d[\d,]*\s*천\s*만\s*원|\d[\d,]*만\s*\d+천만원")
hit1 = 0
for c in chunks:
    for m in P1.finditer(c["text"]):
        s = max(0, m.start() - 80)
        print(f"--- {c['source']}")
        print("   …" + c["text"][s:m.end() + 80].replace("\n", " ") + "…")
        hit1 += 1
        if hit1 >= 10: break
    if hit1 >= 10: break
if hit1 == 0: print("(없음)")

# ── 2. '148만 5천' 표기 전수 확인
print("\n" + "=" * 74)
print("[2] '만 ○천' 형태의 금액 표기 (단위가 원인지 만원인지 확인)")
print("=" * 74)
P2 = re.compile(r"(\d[\d,]*)\s*만\s*(\d[\d,]*)\s*천\s*(만\s*)?원")
seen = {}
for c in chunks:
    for m in P2.finditer(c["text"]):
        key = re.sub(r"\s+", "", m.group(0))
        seen.setdefault(key, [0, c["source"], c["text"][max(0, m.start()-70):m.end()+50]])
        seen[key][0] += 1
for k, (n, src, ctx) in sorted(seen.items(), key=lambda x: -x[1][0])[:12]:
    mark = " ★단위의심" if "만원" in k[-3:] else ""
    print(f"  {n:3d}회  {k}{mark}   [{src}]")
    print(f"        …{ctx.replace(chr(10),' ')}…")
if not seen: print("(없음)")

# ── 3. 'A만원 × B%' 식과 뒤따르는 결과값 대조
print("\n" + "=" * 74)
print("[3] 산술식 검산  (A만원 × B% 의 결과가 맞게 적혀 있는가)")
print("=" * 74)
P3 = re.compile(r"([\d,]+)\s*만\s*원?\s*[×xX*]\s*([\d.]+)\s*%")
bad = 0
for c in chunks:
    for m in P3.finditer(c["text"]):
        try:
            a = float(m.group(1).replace(",", "")); r = float(m.group(2))
        except ValueError:
            continue
        want = a * r / 100                      # 만원 단위
        tail = c["text"][m.end():m.end() + 60]
        nums = re.findall(r"([\d,]+(?:\.\d+)?)\s*만", tail)
        if not nums:
            continue
        got = float(nums[0].replace(",", ""))
        if abs(got - want) > max(0.05, want * 0.01):
            bad += 1
            print(f"--- {c['source']}")
            print(f"    식: {m.group(0)}  → 계산값 {want:,.1f}만원 / 표기값 {got:,.1f}만원")
            print(f"    본문: …{c['text'][max(0,m.start()-60):m.end()+70]}…".replace("\n"," "))
            if bad >= 10: break
    if bad >= 10: break
if bad == 0: print("(어긋난 식 없음)")
