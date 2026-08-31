# 일관성 테스트: 공식 참고 질의 5문항을 각각 3회씩 실행해 답변이 얼마나 일정한지 측정
# 사용법: 서버 켠 상태에서 → python3 test_consistency.py
import re, requests

BASE = "http://localhost:8000/answer"
RUNS = 3

# (질문, 반드시 들어가야 할 핵심 키워드들)
CASES = [
    ("DC와 DB, 퇴직금이 정해지는 방식이랑 운용 주체가 어떻게 다른가요?",
     ["DC", "DB", "운용"]),
    ("연금저축이랑 IRP에 넣으면 세액공제 얼마까지 되나요? 다 합쳐서요.",
     ["900", "600"]),
    ("명퇴하는 교사예요. 명퇴수당을 연금계좌에 넣으면 세금 감면이 어마어마하다던데, 절세법만 알려주세요.",
     ["60일", "감면", "과세이연"]),
    ("솔로몬 국공채 단기·중장기·장기, 뭐가 달라요? 안정적인 걸 원해요.",
     ["솔로몬", "|"]),          # '|' = 비교 표가 생성됐는지
    ("좋은 연금 상품 하나 추천해 주세요.",
     ["?"]),                    # 되묻기(역질문)가 나왔는지
]


def main():
    print(f"일관성 테스트: {len(CASES)}문항 × {RUNS}회 = {len(CASES)*RUNS}회 실행\n")
    all_ok = 0
    all_total = 0
    for i, (q, must) in enumerate(CASES, 1):
        print("=" * 70)
        print(f"[{i}] {q[:50]}")
        print(f"    필수 요소: {must}")
        types, lens, hits = [], [], []
        for r in range(1, RUNS + 1):
            try:
                res = requests.get(BASE, params={"question_id": f"{i}-{r}", "question": q},
                                   timeout=300)
                d = res.json()
                trace = d.get("think_trace", "")
                ans = d.get("answer", "")
                m = re.search(r"유형 분류: '([^']+)'", trace)
                qtype = m.group(1) if m else "?"
                miss = [k for k in must if k not in ans]
                ok = (len(miss) == 0)
                types.append(qtype)
                lens.append(len(ans))
                hits.append(ok)
                all_total += 1
                all_ok += 1 if ok else 0
                print(f"    {r}회: 유형={qtype:<5s} 길이={len(ans):<5d} "
                      f"필수요소={'전부 포함' if ok else '누락:' + ','.join(miss)}")
            except Exception as e:
                types.append("오류")
                hits.append(False)
                all_total += 1
                print(f"    {r}회: 오류 {e}")
        # 문항별 판정
        same_type = len(set(types)) == 1
        print(f"    → 유형 일관성: {'O 동일(' + types[0] + ')' if same_type else 'X 흔들림 ' + str(types)}"
              f" / 필수요소 충족: {sum(hits)}/{RUNS}회"
              f" / 답변 길이 편차: {max(lens)-min(lens) if lens else 0}자")
        print()

    print("=" * 70)
    print(f"===== 종합: 필수요소 충족 {all_ok}/{all_total}회 "
          f"({all_ok/all_total*100:.0f}%) =====")
    print("유형이 매번 동일하고 필수요소 100%면 심사에서도 같은 품질이 나올 확률이 높습니다.")


if __name__ == "__main__":
    main()
