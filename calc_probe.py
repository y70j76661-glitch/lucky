# -*- coding: utf-8 -*-
"""
calc_probe.py — [#5] 소득·납입액이 주어진 세액공제 계산 검증.
기대값을 코드로 계산해 답변과 대조한다(정답이 결정적 → 오탐 없음).
규칙(문서 기준): 총급여 5,500만 이하 → 16.5% / 초과 → 13.2% (경계 5,500만은 '이하'=16.5%)
  공제대상 = min(납입액, 한도)  한도: 연금저축 단독 600만 / IRP 또는 합산 900만
  공제액 = 공제대상 × 세율
검증: ①세율 구간 ②공제대상 금액 ③공제액 — 셋 다 답변에 있는지.
사용: cd /root/app && source venv/bin/activate && python calc_probe.py
"""
import re, time, requests

BASE = "http://127.0.0.1:8000/answer"

# (id, 질문, 총급여(만), 연금저축(만), IRP(만))
Q = [
    ("K1", "연봉 4,000만원인데 IRP에 연 700만원 넣으면 세액공제 얼마 받나요?", 4000, 0, 700),
    ("K2", "총급여 6,000만원이고 연금저축에 800만원 납입했어요. 세액공제액은요?", 6000, 800, 0),
    ("K3", "연봉이 딱 5,500만원이고 IRP에 900만원 넣었습니다. 공제액이 얼마죠?", 5500, 0, 900),
    ("K4", "총급여 5,600만원, 연금저축 500만원 납입 시 세액공제는?", 5600, 500, 0),
    ("K5", "연봉 3,000만원, 연금저축 400만원과 IRP 300만원 넣었어요. 세액공제 얼마?", 3000, 400, 300),
    ("K6", "총급여 7,000만원이고 연금저축 600만원, IRP 600만원 납입했습니다. 공제액은?", 7000, 600, 600),
]


def expect(salary, ps, irp):
    rate = 16.5 if salary <= 5500 else 13.2
    ps_cap = min(ps, 600)                # 연금저축 단독 상한 600
    target = min(ps_cap + irp, 900)      # 합산(IRP 포함) 상한 900
    amount = round(target * rate / 100, 1)   # 만원 단위
    return rate, target, amount


def amt_forms(m):
    """공제액(만원)을 답변에 나올 수 있는 표기들로 — 예 115.5 → '115만 5천', '115.5만', '1,155,000'"""
    forms = set()
    won = int(round(m * 10000))
    forms.add(f"{won:,}")                              # 1,155,000
    forms.add(str(won))                                # 1155000
    if m == int(m):
        forms.add(f"{int(m)}만")                        # 115만
        forms.add(f"{m:.1f}만")                         # 66.0만 (정수도 소수 표기 가능)
    else:
        i, f = int(m), int(round((m - int(m)) * 10))
        forms.add(f"{i}만{f}천"); forms.add(f"{i}만 {f}천")   # 115만 5천
        forms.add(f"{m}만")                              # 115.5만
    return forms


def main():
    print(f"계산 검증 {len(Q)}문항 — {BASE}\n")
    bad = []
    ft = open("calc_out.txt", "w", encoding="utf-8")
    for qid, q, sal, ps, irp in Q:
        rate, target, amount = expect(sal, ps, irp)
        try:
            a = requests.get(BASE, params={"question_id": qid, "question": q}, timeout=180).json().get("answer", "") or ""
        except Exception as e:
            a = f"(요청실패:{str(e)[:40]})"
        flat = re.sub(r"\s+", "", a)
        ok_rate = str(rate) in flat
        wrong_rate = (str(13.2 if rate == 16.5 else 16.5) in flat)   # 반대 세율이 '적용'으로 쓰였나(구간 설명은 OK라 참고용)
        ok_target = (f"{target}만" in flat) or (f"{target:,}만" in flat)
        ok_amount = any(re.sub(r"\s+", "", f) in flat for f in amt_forms(amount))
        tag = "OK" if (ok_rate and ok_target and ok_amount) else "★확인★"
        print(f"  [{qid}] 기대 세율{rate}% 대상{target}만 공제{amount}만 | 세율={ok_rate} 대상={ok_target} 공제액={ok_amount} {tag}")
        if tag != "OK": bad.append(qid)
        ft.write(f"\n{'='*70}\n[{qid}] {q}\n기대: 세율 {rate}% / 대상 {target}만 / 공제액 {amount}만\n"
                 f"판정: 세율={ok_rate} 대상={ok_target} 공제액={ok_amount}\n--- 답변 ---\n{a}\n")
        time.sleep(0.3)
    ft.close()
    print("\n" + "=" * 60)
    if bad:
        print(f"★ 확인 필요 {len(bad)}: {bad} → calc_out.txt 원문으로 표기차인지 실오류인지 판단")
    else:
        print("6문항 모두 세율·대상·공제액 일치 → 계산 검증 통과")
    print("=" * 60)


if __name__ == "__main__":
    main()
