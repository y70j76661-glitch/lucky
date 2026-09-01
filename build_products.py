# 문서 전체에서 상품명(투자신탁)을 추출해 products.json으로 저장
# 사용법: python3 build_products.py  (서버 안 켜도 됨, ~/app에서 실행)
import json, re

chunks = json.load(open("chunks.json", encoding="utf-8"))

# "…투자신탁 제N호(유형)" 패턴을 찾음
pat = re.compile(
    r'[가-힣A-Za-z0-9()\-·&/ ]{3,50}?투자신탁(?:\s?제?\s?\d+\s?호)?(?:\s?\([가-힣A-Za-z0-9\-· ]{1,15}\))?'
)

found = {}
for c in chunks:
    for m in pat.findall(c["text"]):
        name = re.sub(r"\s+", " ", m).strip()
        if len(name) < 10:
            continue
        key = name.replace(" ", "")
        if key not in found:
            found[key] = {"name": name, "source": c["source"]}

items = list(found.values())
print(f"추출된 상품명 후보: {len(items)}개")
print("\n--- 앞 30개 미리보기 ---")
for it in items[:30]:
    print(" -", it["name"], " | 출처:", it["source"])

json.dump(items, open("products.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\nproducts.json 저장 완료")
