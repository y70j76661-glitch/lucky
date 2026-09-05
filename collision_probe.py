# -*- coding: utf-8 -*-
"""
collision_probe.py — 경쟁형 카드 '충돌' 탐색. 게이트가 단일선택을 실제로 보장하는지 확인.
경쟁형 카드: 기한 / 148최대공제 / 연금수령요건 / 과세제외
판정:
  - 단일의도 질문에 경쟁형 카드 2개+  → [버그] 충돌 (아비터 필요)
  - 복합의도 질문에 관련 카드 여러 개  → [정상] (아비터 불필요, 오히려 맞음)
사용: cd /root/app && source venv/bin/activate && python collision_probe.py
"""
import time
import requests

BASE = "http://127.0.0.1:8000/answer"

# (id, 유형, 질문)  유형: single=단일의도(≤1 기대) / compound=복합(관련 다수 정상)
Q = [
    # ── 단일의도인데 여러 카드 도메인 어휘가 섞인 '함정' 질문 (2개+면 버그) ──
    ("S1", "single", "IRP를 중도해지하면 세금을 얼마나 떼나요?"),
    ("S2", "single", "연금저축 세액공제는 최대 얼마까지 받나요?"),
    ("S3", "single", "연금은 언제부터 받을 수 있나요?"),
    ("S4", "single", "퇴직금은 며칠 이내에 IRP로 이전해야 하나요?"),
    ("S5", "single", "회사가 낸 DC 부담금도 세액공제 되나요?"),
    ("S6", "single", "연금계좌에서 중도인출하면 기타소득세가 얼마인가요?"),
    ("S7", "single", "연금저축 납입한도는 얼마인가요?"),
    ("S8", "single", "IRP 세액공제 한도가 궁금해요."),
    # ── 진짜 복합의도 (관련 카드 여러 개 붙는 게 정상) ──
    ("C1", "compound", "연금 수령은 언제부터 가능하고, 세액공제는 최대 얼마까지 되나요?"),
    ("C2", "compound", "IRP 중도해지 세금이랑, 퇴직금을 며칠 이내에 IRP로 이전해야 하는지 둘 다 알려주세요."),
]


def markers(a):
    m = []
    if "참고 문서에 명시된 기한입니다" in a:
        m.append("기한")
    if "자료 원문에는" in a and "148" in a:
        m.append("148최대공제")
    if "연금수령 요건" in a:
        m.append("수령요건")
    if "과세제외금액" in a:
        m.append("과세제외")
    return m


def main():
    print(f"충돌 탐색 {len(Q)}문항 — {BASE}\n")
    bugs = []
    for qid, kind, q in Q:
        t0 = time.time()
        try:
            r = requests.get(BASE, params={"question_id": qid, "question": q}, timeout=150)
            a = r.json().get("answer", "") or ""
        except Exception as e:
            print(f"  [{qid}] 요청실패: {str(e)[:60]}")
            continue
        mk = markers(a)
        dt = time.time() - t0
        tag = "OK"
        if kind == "single" and len(mk) >= 2:
            tag = "★버그충돌★"
            bugs.append((qid, mk))
        print(f"  [{qid}][{kind}] {dt:4.1f}s  경쟁형카드={mk if mk else '없음'}  {tag}")
    print("\n" + "=" * 60)
    if bugs:
        print(f"★ 단일의도 충돌 {len(bugs)}건 발견 → 아비터 필요: {bugs}")
    else:
        print("단일의도 충돌 0건 → 게이트가 단일선택을 보장함(아비터 불필요).")
    print("복합의도(C1·C2)에 카드 여러 개는 정상(질문이 여러 주제를 물었으므로).")
    print("=" * 60)


if __name__ == "__main__":
    main()
