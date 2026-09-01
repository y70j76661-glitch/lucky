# 프롬프트에 박아넣은 규칙들이 실제로 제공 문서에 근거가 있는지 확인한다.
#   문서에 없는 규칙 = 외부 지식 주입 → 제거하거나 문서 기준으로 교체해야 함
# 사용법: python3 verify_rules.py   (서버 안 켜도 됨)
import json

chunks = json.load(open("chunks.json", encoding="utf-8"))

# (규칙 설명, 함께 등장해야 할 키워드들)
RULES = [
    ("연금저축 세액공제 한도 600만원",        ["600만원", "세액공제"]),
    ("연금계좌 합산 한도 900만원",            ["900만원", "세액공제"]),
    ("400만원은 과거 기준",                   ["400만원", "세액공제"]),
    ("연 1,800만원은 납입 한도",              ["1,800만원"]),
    ("중도해지 기타소득세 16.5%",             ["16.5", "기타소득"]),
    ("기타소득세 = 15% + 지방세 1.5%",        ["16.5"]),
    ("15.4%는 이자·배당 금융소득세",          ["15.4"]),
    ("연금소득세 3.3~5.5%",                   ["5.5", "3.3"]),
    ("소득 경계: 4,500만원과 5,500만원 동시", ["4,500만원", "5,500만원"]),
    ("공제율 16.5% / 13.2%",                  ["16.5", "13.2"]),
    ("퇴직소득세 감면 30%/40%",               ["30%", "감면"]),
    ("연금 수령 60일 이내 입금",              ["60일"]),
]


def main():
    print(f"전체 청크 {len(chunks):,}개에서 규칙 근거 확인\n")
    for desc, kws in RULES:
        hits = [c for c in chunks if all(k in c["text"] for k in kws)]
        srcs = {}
        for c in hits:
            srcs[c["source"]] = srcs.get(c["source"], 0) + 1
        top = sorted(srcs.items(), key=lambda x: -x[1])[:3]
        mark = "O" if hits else "X"
        print(f"[{mark}] {desc}")
        print(f"     키워드 {kws} → {len(hits)}개 청크")
        if top:
            print(f"     주요 출처: {', '.join(f'{s}({n})' for s, n in top)}")
            # 가장 짧은 청크의 해당 부분을 미리보기
            c = min(hits, key=lambda x: len(x["text"]))
            i = c["text"].find(kws[0])
            snippet = c["text"][max(0, i - 120):i + 160].replace("\n", " ")
            print(f"     예시: …{snippet}…")
        print()


if __name__ == "__main__":
    main()
