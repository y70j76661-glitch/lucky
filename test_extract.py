from pypdf import PdfReader

# 연금 문서 1번으로 테스트
reader = PdfReader("docs/pension_pdf/docs_renamed/doc1.pdf")

print(f"총 페이지 수: {len(reader.pages)}")
print("=" * 50)

# 첫 페이지의 글자 뽑기
text = reader.pages[0].extract_text()
print(text[:1000])   # 앞 1000자만 출력
