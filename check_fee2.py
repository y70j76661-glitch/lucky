import json, re
chunks = json.load(open("chunks.json", encoding="utf-8"))
NUM = re.compile(r"\d+\.\d+")
TOL = 0.006          # 반올림 오차 허용치

rows, bad = 0, []
for c in chunks:
    if "종류" not in c["text"]:
        continue
    # '종류A ...' 단위로 잘라 각 클래스 행의 숫자열을 본다
    for seg in re.split(r"(?=종류\s*[A-Za-z])", c["text"]):
        m = re.match(r"종류\s*([A-Za-z][\w\-]*)", seg)
        if not m:
            continue
        vals = [float(v) for v in NUM.findall(seg[:220])]
        if len(vals) < 5:
            continue
        a, b, cc, d, total = vals[:5]
        if not (0 < total < 5):        # 보수율 범위 밖이면 표가 아님
            continue
        rows += 1
        s = a + b + cc + d
        if abs(s - total) > TOL:
            bad.append((c["source"], m.group(1), [a, b, cc, d], total, round(s, 4)))

print(f"검산한 클래스 행: {rows}개 / 합계가 어긋난 행: {len(bad)}개\n")
seen = set()
for src, cls, parts, total, s in bad[:40]:
    key = (src, cls, total, s)
    if key in seen:
        continue
    seen.add(key)
    print(f"[{src}] 종류{cls}")
    print(f"    구성항목 {parts} 합계={s}  ↔  표기된 총보수={total}   차이 {round(abs(s-total),4)}")
print("\n(어긋난 행이 0개면 우리 문서에는 그 결함이 없다는 뜻)")
