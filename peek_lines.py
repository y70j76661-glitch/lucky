import glob, re, pdfplumber

files = sorted(glob.glob("docs/fund_pdf/**/*.pdf", recursive=True))[:2]
NUM = re.compile(r"\d+\.\d+")

for f in files:
    print("=" * 96); print(f); print("=" * 96)
    with pdfplumber.open(f) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            txt = page.extract_text() or ""
            if "총보수" not in txt or "종류" not in txt:
                continue
            lines = [re.sub(r"\s+", " ", l).strip() for l in txt.split("\n")]
            # 보수표로 보이는 구간만: '종류'로 시작하거나 숫자가 3개 이상인 줄
            idx = [i for i, l in enumerate(lines)
                   if l.startswith("종류") or len(NUM.findall(l)) >= 3]
            if not idx:
                continue
            lo, hi = max(0, min(idx) - 6), min(len(lines), max(idx) + 2)
            print(f"\n----- p.{pno} (줄 {lo}~{hi}) -----")
            for i in range(lo, hi):
                print(f"  {i:3d}| {lines[i][:150]}")
            break        # 파일당 첫 보수표 페이지만
    print()
