import glob, pdfplumber

files = sorted(glob.glob("docs/fund_pdf/투자설명서/*/*.pdf"))[:2]
print(f"대상 {len(files)}개\n")

def cell(x, w=16):
    x = (x or "").replace("\n", " ").strip()
    return (x[:w]).ljust(w)

for f in files:
    print("=" * 100); print(f); print("=" * 100)
    with pdfplumber.open(f) as pdf:
        shown = 0
        for pno, page in enumerate(pdf.pages, 1):
            txt = page.extract_text() or ""
            if "보수" not in txt:
                continue
            for tno, tbl in enumerate(page.extract_tables(), 1):
                flat = " ".join(cc or "" for row in tbl for cc in row)
                if "총보수" not in flat and "보수" not in flat:
                    continue
                print(f"\n--- p.{pno} 표{tno}  ({len(tbl)}행 x {max(len(r) for r in tbl)}열)")
                for row in tbl[:7]:
                    print("   | " + " | ".join(cell(c) for c in row))
                shown += 1
                if shown >= 4:
                    break
            if shown >= 4:
                break
    print()
