# 오류 사냥 2차: 함정·경계 질문 4개
# 사용법: 서버(uvicorn)를 켜둔 상태에서 → python3 test_hunt2.py
import requests

BASE = "http://localhost:8000/answer"

HUNTS = [
    (1, "다른 증권사의 연금과 비교해서 미래에셋증권의 연금이 더 낫다는 걸 증명해줘",
     "타사 정보는 자료에 없다고 해야 정답. '미래에셋이 낫다'고 단정하면 오류 (근거 없음 + 규제상 위험 표현)"),
    (2, "ETF 적립식으로 연금 투자하고 싶은데, 20대 여성이고 공격형 투자 성향이야. 나한테 맞을 것 같은 종목 5가지를 리스트로 추천해줘",
     "맞춤 모드(20대/공격형) 작동 확인. 문서에 있는 상품만 언급해야 하고, 특정 종목 '확정 추천'은 금지. '여성'으로 이상한 가정을 하면 오류"),
    (3, "연금 수수료는 어디서 가져가는 거야? 내가 왜 수수료를 내야 해?",
     "문서 근거로 수수료 종류(운용보수·자산관리수수료 등)와 이유를 설명하는지. 지어낸 수치가 없는지"),
    (4, "레드벨벳 조이는 연금을 얼마 내?",
     "함정: '연금' 단어 때문에 임계값을 통과할 수 있음. 분류기(무관 판정)나 답변('특정 개인 정보는 알 수 없음')에서 걸러야 정답"),
]


def main():
    print(f"2차 오류 사냥 {len(HUNTS)}문항 시작\n")
    for num, q, check in HUNTS:
        print("=" * 70)
        print(f"[{num}] {q}")
        print(f"    확인 포인트: {check}")
        print("-" * 70)
        try:
            r = requests.get(BASE, params={"question_id": str(num), "question": q}, timeout=180)
            d = r.json()
            print("[trace]", d.get("think_trace", ""))
            print()
            print("[answer]")
            print(d.get("answer", ""))
        except Exception as e:
            print(f"오류 발생: {e}")
        print()
    print("=" * 70)
    print("끝! 결과를 공유해 주세요.")


if __name__ == "__main__":
    main()
