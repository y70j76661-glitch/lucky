# 라우팅 분류 정확도 자동 테스트
# 사용법: 서버(uvicorn)를 켜둔 상태에서 → python3 test_routing.py
import re, requests

BASE = "http://localhost:8000/answer"

# (질문, 기대 유형) — 유형별 5개씩 총 25개
CASES = [
    # 제도
    ("국민연금은 몇 살부터 받을 수 있어?", "제도"),
    ("퇴직금 중간정산은 언제 가능해?", "제도"),
    ("IRP 계좌는 누가 가입할 수 있어?", "제도"),
    ("DB형과 DC형의 차이가 뭐야?", "제도"),
    ("퇴직연금은 언제부터 수령 가능해?", "제도"),
    # 세제
    ("연금저축 세액공제 한도 알려줘", "세제"),
    ("퇴직소득세는 어떻게 계산해?", "세제"),
    ("IRP로 세액공제 얼마나 받을 수 있어?", "세제"),
    ("연금 수령할 때 세금 얼마나 내?", "세제"),
    ("연금저축 중도 해지하면 세금 불이익 있어?", "세제"),
    # 상품설명
    ("TDF가 어떤 상품이야?", "상품설명"),
    ("디폴트옵션이 뭐야?", "상품설명"),
    ("TDF 수수료는 얼마야?", "상품설명"),
    ("원리금보장형 상품은 어떤 게 있어?", "상품설명"),
    ("ETF랑 펀드는 뭐가 달라?", "상품설명"),
    # 추천
    ("나한테 맞는 연금 상품 추천해줘", "추천"),
    ("20대인데 어떤 연금 상품이 좋아?", "추천"),
    ("안정적인 걸 원하는데 뭘 고르면 좋을까?", "추천"),
    ("IRP랑 연금저축 중에 뭐가 나아?", "추천"),
    ("은퇴가 5년 남았는데 어떤 상품을 골라야 해?", "추천"),
    # 무관
    ("오늘 점심 뭐 먹을까?", "무관"),
    ("BTS 콘서트 티켓 예매 방법", "무관"),
    ("아이폰이랑 갤럭시 중에 뭐가 나아?", "무관"),
    ("내일 날씨 어때?", "무관"),
    ("김치찌개 맛있게 끓이는 법 알려줘", "무관"),
]


def predicted_type(trace):
    """think_trace에서 분류 결과를 추출"""
    m = re.search(r"유형 분류: '([^']+)'", trace)
    if m:
        return m.group(1)
    if "무관" in trace:
        return "무관"
    return "?"


def main():
    results = []
    print(f"총 {len(CASES)}개 질문 테스트 시작 (질문마다 몇 초씩 걸립니다)\n")
    for i, (q, expect) in enumerate(CASES, 1):
        try:
            r = requests.get(BASE, params={"question_id": str(i), "question": q}, timeout=120)
            trace = r.json().get("think_trace", "")
            got = predicted_type(trace)
        except Exception as e:
            got = f"오류({e})"
        ok = "O" if got == expect else "X"
        results.append((q, expect, got, ok))
        print(f"  [{ok}] {i:2d}. 기대={expect:<4s} 결과={got:<4s} | {q}")

    # 요약
    total = len(results)
    correct = sum(1 for _, _, _, ok in results if ok == "O")
    print(f"\n===== 전체 정확도: {correct}/{total} ({correct/total*100:.0f}%) =====")

    by_type = {}
    for _, expect, _, ok in results:
        c, t = by_type.get(expect, (0, 0))
        by_type[expect] = (c + (ok == "O"), t + 1)
    for t, (c, n) in by_type.items():
        print(f"  {t}: {c}/{n}")

    wrong = [(q, e, g) for q, e, g, ok in results if ok == "X"]
    if wrong:
        print("\n틀린 질문:")
        for q, e, g in wrong:
            print(f"  - {q}  (기대: {e} / 결과: {g})")
    else:
        print("\n전부 정답! 라우터 완성입니다.")


if __name__ == "__main__":
    main()
