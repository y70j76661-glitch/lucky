import requests
Q = [("R02", "연금저축이랑 IRP에 넣으면 세액공제 얼마까지 되나요? 다 합쳐서요."),
     ("R13", "명퇴하는 교사예요. 명퇴수당을 연금계좌에 넣으면 세금 감면이 어마어마하다던데, 절세법만 알려주세요."),
     ("R20", "수수료가 가장 적은 연금 상품 하나만 딱 골라주세요")]
for i, q in Q:
    print("=" * 72); print(f"[{i}] {q}"); print("-" * 72)
    d = requests.get("http://localhost:8000/answer",
                     params={"question_id": i, "question": q}, timeout=300).json()
    print("[trace]", d.get("think_trace", "")); print()
    print("[answer]"); print(d.get("answer", "")); print()
