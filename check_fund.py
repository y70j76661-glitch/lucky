from pypdf import PdfReader
import glob

files = sorted(glob.glob("docs/fund_pdf/투자설명서/*/*.pdf"))
print(f"검사할 PDF: {len(files)}개\n")

ok, scan = 0, 0
for f in files:
    try:
        reader = PdfReader(f)
        text = reader.pages[0].extract_text() or ""
        if len(text.strip()) > 50:
            status = "OK"
            ok += 1
        else:
            status = "!! 스캔본"
            scan += 1
        print(f"{f.split('/')[-1]:15s} 글자수:{len(text.strip()):5d}  {status}")
    except Exception as e:
        print(f"{f.split('/')[-1]:15s} 에러: {e}")

print(f"\n텍스트형: {ok}개 / 스캔본: {scan}개")

