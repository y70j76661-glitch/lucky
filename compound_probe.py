# -*- coding: utf-8 -*-
"""
compound_probe.py — 대회 '재부착(single-turn 복합)' 시나리오 검증.
심사위원이 이전 질문 + 새 질문을 하나의 문자열로 붙여서 보낼 때, 두 요구를 모두
답하는지(요구충족) + 카드/후처리가 엉키지 않는지 확인한다.

각 케이스: 앞부분(A)·뒷부분(B) 각각의 '기대 키워드'가 답변에 모두 있는지로 누락을 탐지.
사용: cd /root/app && source venv/bin/activate && python compound_probe.py
"""
import json, re, time, requests

BASE = "http://127.0.0.1:8000/answer"

# (id, 재부착질문, A기대키워드들(하나라도), B기대키워드들(하나라도))
Q = [
    ("C1",
     "연금저축과 IRP 세액공제 한도는 얼마인가요? IRP를 중도해지하면 세금이 어떻게 되나요?",
     ["600", "900"], ["16.5", "기타소득세"]),
    ("C2",
     "IRP를 중도해지하면 세금이 어떻게 되나요? 연금 수령 나이는 몇 살인가요?",
     ["16.5", "기타소득세"], ["55세", "가입기간"]),
    ("C3",
     "세액공제 최대 금액은 얼마인가요? 회사가 넣어준 DC 부담금도 공제되나요?",
     ["148만 5천원", "148.5", "900"], ["회사", "부담금", "공제 대상"]),
    ("C4",
     "퇴직금을 IRP로 옮기면 언제까지 해야 하나요? 연금저축과 IRP 세액공제 한도는요?",
     ["60일"], ["600", "900"]),
    ("C5",
     "연금 수령 나이는 몇 살인가요? 또박또박연금펀드의 합성총보수는 얼마인가요?",
     ["55세"], ["0.87"]),
]


def hit(ans, kws):
    return any(k.replace(" ", "") in ans.replace(" ", "") for k in kws)


def main():
    print(f"복합(재부착) 프로브 {len(Q)}문항 — {BASE}\n")
    bad = []
    ft = open("compound_out.txt", "w", encoding="utf-8")
    for qid, q, ka, kb in Q:
        t0 = time.time()
        try:
            r = requests.get(BASE, params={"question_id": qid, "question": q}, timeout=180)
            a = r.json().get("answer", "") or ""
        except Exception as e:
            a = f"(요청실패: {str(e)[:60]})"
        dt = time.time() - t0
        ha, hb = hit(a, ka), hit(a, kb)
        star = "**" in a
        tag = "OK" if (ha and hb and not star) else "★확인★"
        if not (ha and hb): bad.append((qid, ha, hb))
        print(f"  [{qid}] {dt:4.1f}s  A답={ha} B답={hb} 볼드잔재={star}  {tag}")
        ft.write(f"\n{'='*70}\n[{qid}] {q}\nA기대{ka}={ha} / B기대{kb}={hb} / 볼드={star}\n--- 답변 ---\n{a}\n")
    ft.close()
    print("\n" + "=" * 60)
    if bad:
        print(f"★ 한쪽 요구 누락 의심 {len(bad)}건: {bad}")
        print("  → 재부착 복합질문에서 뒷부분/앞부분이 빠지는지 compound_out.txt로 원문 확인")
    else:
        print("모든 재부착 질문에서 두 요구 모두 응답 → 요구충족 OK")
    print("전문: compound_out.txt")
    print("=" * 60)


if __name__ == "__main__":
    main()
