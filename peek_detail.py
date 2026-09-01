import glob, re, pdfplumber

f = sorted(glob.glob("docs/fund_pdf/**/*.pdf", recursive=True))[0]
NUM = re.compile(r"\d+\.\d+")
print(f); print("=" * 96)

with pdfplumber.open(f) as pdf:
    for pno, page in enumerate(pdf.pages, 1):
        txt = page.extract_text() or ""
        if "신탁업자" not in txt or "집합투자업자" not in txt:
            continue
        lines = [re.sub(r"\s+", " ", l).strip() for l in txt.split("\n")]
        idx = [i for i, l in enumerate(lines) if len(NUM.findall(l)) >= 4]
        if not idx:
            continue
        lo, hi = max(0, min(idx) - 8), min(len(lines), max(idx) + 3)
        print(f"\n----- p.{pno} (줄 {lo}~{hi}) -----")
        for i in range(lo, hi):
            print(f"  {i:3d}| {lines[i][:150]}")
