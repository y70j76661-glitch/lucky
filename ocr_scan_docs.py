from pdf2image import convert_from_path
from pypdf import PdfReader
import pytesseract, glob, json, re

CHUNK_SIZE, OVERLAP = 800, 100

def split_text(text):
    text = re.sub(r"\s+", " ", text).strip()
    chunks, start = [], 0
    while start < len(text):
        chunks.append(text[start:start + CHUNK_SIZE])
        start += CHUNK_SIZE - OVERLAP
    return chunks

# 기존 청크 불러오기
with open("chunks.json", encoding="utf-8") as f:
    all_chunks = json.load(f)
already = {c["source"] for c in all_chunks}
before = len(all_chunks)

for path in sorted(glob.glob("docs/pension_pdf/docs_renamed/*.pdf")):
    name = path.split("/")[-1]
    # 텍스트형인지 재확인 (스캔본만 OCR)
    reader = PdfReader(path)
    if len((reader.pages[0].extract_text() or "").strip()) > 50:
        continue  # 텍스트형은 이미 처리됨, 건너뜀
    print(f"[OCR 중] {name} ...")
    pages = convert_from_path(path, dpi=200)
    text = "\n".join(pytesseract.image_to_string(p, lang="kor") for p in pages)
    if len(text.strip()) < 50:
        print(f"  → 실패(글자 안 나옴)")
        continue
    for i, c in enumerate(split_text(text)):
        all_chunks.append({"source": name, "type": "pension",
                           "chunk_id": i, "text": c, "ocr": True})
    print(f"  → 완료 ({len(split_text(text))}개 청크)")

with open("chunks.json", "w", encoding="utf-8") as f:
    json.dump(all_chunks, f, ensure_ascii=False, indent=1)
print(f"\n총 청크: {before} → {len(all_chunks)} (+{len(all_chunks)-before}개 추가)")

