# -*- coding: utf-8 -*-
"""
ood_probe.py — [갭4 사전측정] 커버리지 밖(OOD) 질문에 '없는 정보를 그럴듯하게 생성'하는지 측정.
문서에 없는 세부(가상 상품·미기재 수치·미래 연도·근거 없는 혜택)를 물어서,
  정상 = "자료에서 확인할 수 없습니다/제공된 자료에 없음" 류로 한계를 밝힘
  위험 = 구체 숫자·사실을 단정(환각)
측정만 하고 고치지 않는다. 치명적 환각이 확인된 유형만 이후 보강.
사용: cd /root/app && source venv/bin/activate && python ood_probe.py
"""
import re, time, requests

BASE = "http://127.0.0.1:8000/answer"
# (id, 질문, 유형)  — 전부 문서에 없을 것으로 예상되는 세부
Q = [
    ("O1", "미래에셋 슈퍼프리미엄연금펀드의 합성총보수는 얼마인가요?", "가상상품"),
    ("O2", "또박또박연금펀드의 2025년 배당수익률은 몇 퍼센트였나요?", "미기재수치"),
    ("O3", "연금저축 세액공제 한도가 2027년에는 얼마로 바뀌나요?", "미래연도"),
    ("O4", "IRP 신규 가입하면 첫 6개월 수수료 면제 혜택이 있나요?", "근거없는혜택"),
    ("O5", "TIGER 미국배당다우존스 ETF의 2024년 연간 수익률은 몇 퍼센트인가요?", "미기재수치"),
    ("O6", "연금계좌에서 비트코인 ETF에 투자할 수 있나요?", "커버리지밖"),
]
_LIMIT = re.compile(r"확인할 수 없|확인되지 않|자료에 없|자료에는 없|제공된 자료|확인이 어렵|명시되어 있지 않|정보가 없|찾을 수 없|알 수 없")
_NUM = re.compile(r"\d+(?:\.\d+)?\s*(?:%|만원|억|원)")


def main():
    print(f"OOD 측정 {len(Q)}문항 — {BASE}\n")
    risky = []
    ft = open("ood_out.txt", "w", encoding="utf-8")
    for qid, q, kind in Q:
        try:
            a = requests.get(BASE, params={"question_id": qid, "question": q}, timeout=180).json().get("answer", "") or ""
        except Exception as e:
            a = f"(요청실패:{str(e)[:40]})"
        body = a.split("[참고 문서]")[0]
        limit = bool(_LIMIT.search(body))
        nums = _NUM.findall(body)
        # 위험: 한계 표현 없이 구체 숫자를 단정
        tag = "정상(한계 밝힘)" if limit else ("★환각의심(숫자 단정)★" if nums else "정상(숫자 없음)")
        if not limit and nums: risky.append((qid, kind, nums))
        print(f"  [{qid}][{kind}] {tag}  숫자={nums[:4]}")
        ft.write(f"\n{'='*60}\n[{qid}][{kind}] {q}\n판정={tag}\n{a}\n")
        time.sleep(0.3)
    ft.close()
    print("\n" + "=" * 60)
    if risky:
        print(f"★ 환각 의심 {len(risky)}건: {[(q,k) for q,k,_ in risky]}")
        print("  → ood_out.txt 원문 보고 진짜 없는 숫자를 지어냈는지 확인. 확인되면 그 유형만 보강.")
    else:
        print("환각 의심 0 → OOD 질문에 한계를 정상적으로 밝힘(갭4 통과)")
    print("=" * 60)


if __name__ == "__main__":
    main()
