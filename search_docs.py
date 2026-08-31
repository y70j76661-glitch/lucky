# 전체 문서(chunks.json)에서 키워드 검색
# 사용법: python3 search_docs.py 키워드
import json, sys

kw = sys.argv[1] if len(sys.argv) > 1 else "ETF"
chunks = json.load(open("chunks.json", encoding="utf-8"))
hits = [c for c in chunks if kw in c["text"]]

print(f"'{kw}' 포함 청크: {len(hits)}개 / 전체 {len(chunks)}개")

# 어떤 문서에 많이 나오는지
srcs = {}
for c in hits:
    srcs[c["source"]] = srcs.get(c["source"], 0) + 1
for s, n in sorted(srcs.items(), key=lambda x: -x[1])[:10]:
    print(f"  {s}: {n}개 청크")

# 내용 미리보기 3개
for c in hits[:3]:
    print("-" * 50)
    print(c["source"])
    print(c["text"][:250])
