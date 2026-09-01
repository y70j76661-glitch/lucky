import requests

Q = [
 ("V1", "미래에셋 장기성장포커스 증권자투자신탁 1호 종류A의 총보수는 얼마이고, "
        "어떤 항목들로 구성되어 있나요?"),
 ("V2", "연금 상품 중에 총보수가 가장 낮은 게 뭐예요?"),
]

for qid, q in Q:
    print("=" * 78)
    print(f"[{qid}] {q}")
    print("=" * 78)
    d = requests.get("http://localhost:8000/answer",
                     params={"question_id": qid, "question": q}, timeout=300).json()
    print("\n[trace]")
    print(d.get("think_trace", ""))
    print("\n[answer]")
    print(d.get("answer", ""))
    print()
