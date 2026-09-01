from pdf2image import convert_from_path
import pytesseract

pages = convert_from_path("docs/pension_pdf/docs_renamed/doc1.pdf", dpi=200)
print(f"페이지 수: {len(pages)}")

text = pytesseract.image_to_string(pages[0], lang="kor")
print("=" * 50)
print(text[:1500])
