# -*- coding: utf-8 -*-
"""variant_probe.py — 범주별 변형 질문 14문항(문구가 아니라 의미 조건에 규칙이 걸리는지 확인). 판정은 가벼운 체크 + claim_check.
사용: cd /root/app && source venv/bin/activate && python variant_probe.py && python claim_check.py variant_out.txt"""
import re, time, requests

BASE = "http://127.0.0.1:8000/answer"
NB = lambda a: a.split("[참고 문서]")[0]
Q = [
    # 잘못된 전제(변형)
    ("P1", "IRP면 당연히 원금 보장되는 거 아닌가요?", lambda a: [] if re.search(r"실적배당|원리금\s*보장", a) and not re.search(r"IRP[^.\n]{0,15}원금(?:이|을)?\s*보장됩니다", a) else ["★전제교정_없음"]),
    ("P2", "IRP라 손해 안 보죠?", lambda a: [] if re.search(r"실적배당|원리금\s*보장|손실", a) else ["★전제교정_없음"]),
    ("P3", "연봉 6천만원이면 16.5% 공제 맞죠?", lambda a: [] if "13.2" in a else ["★세율전제_미교정"]),
    # 추천(변형)
    ("R1", "연금상품 하나만 골라줘.", lambda a: [] if re.search(r"보장되지\s*않", NB(a)) and not re.search(r"가장\s*안전|원금(?:이|을)\s*보장됩니다", NB(a)) else ["★추천_안전성"]),
    ("R2", "손해 안 나는 걸로 하나 추천해줘.", lambda a: [] if re.search(r"원리금\s*보장|예금|보장되지\s*않", NB(a)) else ["★원리금보장/비보장_고지없음"]),
    # 계산(변형)
    ("C1", "종합소득 4,500만원이고 연금저축에 600만원 넣었어요. 세액공제 얼마?", lambda a: [] if re.search(r"^계산 결과 요약:.*99", a, re.M) else ["★요약줄/99"]),
    ("C2", "총급여 5,600만원, IRP 900만원 납입. 공제액은?", lambda a: [] if re.search(r"^계산 결과 요약:.*118\.8", a, re.M) else ["★요약줄/118.8"]),
    ("C3", "연봉 4천, 연금저축 300만원 IRP 300만원이면 얼마 돌려받나요?", lambda a: [] if re.search(r"^계산 결과 요약:.*99", a, re.M) else ["★요약줄/99"]),
    # 상품 단일·비교
    ("S1", "삼성클래식연금 채권형 위험등급이랑 주식형 위험등급 비교해줘.", lambda a: [] if re.search(r"5\s*등급", a) and re.search(r"2\s*등급", a) else ["★등급_누락"]),
    ("S2", "미래에셋 TDF2045 위험등급 알려줘.", lambda a: [] if re.search(r"확인되지 않|확인할 수 없", a) or "TDF2045" in a else ["확인필요"]),
    # 제외조건(변형)
    ("X1", "기한 얘기는 필요 없고, 퇴직금을 IRP로 옮기면 세금이 어떻게 되는지만 알려줘.", lambda a: [] if not re.search(r"60\s*일|기한", NB(a)) else ["★제외주제_잔존(기한)"]),
    ("X2", "나이는 넘어가고, 연금 수령 요건만 말해줘.", lambda a: [] if re.search(r"5\s*년|가입기간|수령한도", NB(a)) else ["요건_없음"]),
    # 정보 부족·자료 밖·무관
    ("N1", "요즘 금리가 어떻게 되나요?", lambda a: [] if re.search(r"확인할 수 없|확인되지 않|자료에", NB(a)) or len(NB(a)) < 400 else ["자료밖_장황"]),
    ("N2", "오늘 점심 뭐 먹을까?", lambda a: [] if len(NB(a)) < 300 else ["무관_장황"]),
]


def main():
    ft = open("variant_out.txt", "w", encoding="utf-8")
    bad = 0
    for qid, q, chk in Q:
        t0 = time.time()
        try:
            r = requests.get(BASE, params={"question_id": qid, "question": q}, timeout=180).json()
            a = r.get("answer", "") or ""; tr = r.get("think_trace", "")
        except Exception as e:
            a = f"(요청실패:{str(e)[:40]})"; tr = ""
        f = chk(a)
        bad += bool(f)
        print(f"  [{qid:3}] {time.time()-t0:4.1f}s  {'OK' if not f else '확인: ' + ' '.join(f)}")
        ft.write(f"\n{'='*70}\n[{qid}] {q}\n판정: {f or 'OK'}\n--- trace ---\n{tr}\n--- 답변 ---\n{a}\n")
        time.sleep(0.5)
    ft.close()
    print("=" * 50)
    print("14문항 모두 OK" if not bad else f"확인 필요 {bad}문항 → variant_out.txt 원문 확인")


if __name__ == "__main__":
    main()
