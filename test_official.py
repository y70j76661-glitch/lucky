# 공식 참고 질의 5문항 실전 테스트 (대회 요강의 참고용 질의 set 그대로)
# 사용법: 서버 켠 상태에서 → python3 test_official.py
import requests

BASE = "http://localhost:8000/answer"

CASES = [
    ("하-제도(Closed)", "DC와 DB, 퇴직금이 정해지는 방식이랑 운용 주체가 어떻게 다른가요?",
     "복합 2요소: ①퇴직금 산정 방식 차이 ②운용 주체 차이 — 둘 다 답해야 '요구사항 충족'"),
    ("하-세제(Closed)", "연금저축이랑 IRP에 넣으면 세액공제 얼마까지 되나요? 다 합쳐서요.",
     "합산 900만원(연금저축 단독 600만)이 정확히 나와야 함"),
    ("상-종합(Open)", "명퇴하는 교사예요. 명퇴수당을 연금계좌에 넣으면 세금 감면이 어마어마하다던데, 절세법만 알려주세요.",
     "과세이연·연금수령 감면(30/40/50%) 절세 전략 — 이전 테스트에서 통과했던 답변 유지되는지"),
    ("중-상품비교(Open)", "솔로몬 국공채 단기·중장기·장기, 뭐가 달라요? 안정적인 걸 원해요.",
     "비교 질문 감지(비교 테이블 모드) + 문서 근거 상품 비교 + '안정 선호' 반영"),
    ("중-조건부추천(Open)", "좋은 연금 상품 하나 추천해 주세요.",
     "정보 없음 → 되묻기(역질문)가 정답 — 평가지표 '정보한계 대응' 직결"),
]


def main():
    print(f"공식 참고 질의 {len(CASES)}문항 테스트\n")
    for i, (level, q, check) in enumerate(CASES, 1):
        print("=" * 70)
        print(f"[{i}] ({level}) {q}")
        print(f"    확인 포인트: {check}")
        print("-" * 70)
        try:
            r = requests.get(BASE, params={"question_id": str(i), "question": q}, timeout=300)
            d = r.json()
            print("[trace]", d.get("think_trace", ""))
            print()
            print("[answer]")
            print(d.get("answer", ""))
        except Exception as e:
            print(f"오류: {e}")
        print()
    print("=" * 70)
    print("끝! 각 답변이 확인 포인트를 충족하는지, [참고 문서] 출처가 붙었는지 봐주세요.")


if __name__ == "__main__":
    main()
