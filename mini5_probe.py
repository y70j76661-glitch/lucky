# -*- coding: utf-8 -*-
"""mini5_probe.py — v13.22 런타임 확인 6문항(계산 경로 E7/D9/D4/M3b + N4b + S1). 전체 회귀 아님.
사용: cd /root/app && source venv/bin/activate && python mini5_probe.py"""
import re, time, requests

BASE = "http://127.0.0.1:8000/answer"
def _sum_ok(a, credit):
    m = re.search(r"^계산 결과 요약:.*$", a, re.M)
    return ([] if m else ["★요약줄_없음"]) + ([] if (m and credit in m.group(0)) else ["★요약줄_공제액_불일치"])
Q = [
    ("E7", "연봉 1억 2천만원, 연금저축 600만원 납입 시 공제액은?",
     lambda a: _sum_ok(a, "79.2") + ([] if not re.search(r"대상\s*금액은\s*300|(?:한도|제한)[^.\n]{0,12}300\s*만|300\s*만\s*원[^.\n]{0,12}(?:한도|제한)|고소득", a) else ["★옛규정/대상액_잔존"])),
    ("D9", "총급여 5,500만원, 연금저축 500만원과 IRP 500만원 납입하면 공제액은?",
     lambda a: _sum_ok(a, "148.5") + ([] if not re.search(r"초과된\s*약\s*148|IRP\s*(?:500|900)\s*만\s*원\s*[x×X*]", a) else ["★초과분/IRP식_오류"]) + ([] if "초과 100만원" in a else ["요약_초과분_없음"])),
    ("D4", "총급여 5,000만원, 연금저축 700만원과 IRP 200만원 넣었어요. 세액공제 얼마?",
     lambda a: _sum_ok(a, "132") + ([] if not re.search(r"115\.5|148\.5", a) else ["★700×16.5/900×16.5_잔존"])),
    ("M3b", "연봉 5,300만원이고 연금저축 750만원, 개인형 퇴직연금 250만원 넣었어요. 돌려받는 돈이 얼마죠?",
     lambda a: _sum_ok(a, "140.3") + ([] if not re.search(r"140\.2(?!\d)|132만|132\.7", a) else ["★표기불일치/오답_잔존"])),
    ("N4b", "IRP 세액공제 받을 수 있는 금액은?",
     lambda a: ([] if re.search(r"900\s*만", a) else ["900_없음"]) + ([] if not re.search(r"(?m)(?:이하|초과)\)?\s*[:：]\s*(?:16\.5|13\.2)\s*$", a) else ["★%누락_잔존"])),
    ("S1", "또박또박연금펀드의 클래스별 총보수를 알려주세요.",
     lambda a: ([] if "0.87" in a else ["0.87_없음"]) + ([] if not re.search(r"클래스\s*(?:A|C-P)\s*[:：]\s*0\.8", a) else ["★근거없는_클래스보수_잔존"])),
]


def main():
    ft = open("mini5_out.txt", "w", encoding="utf-8")
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
    print("6문항 모두 OK → v13.22 런타임 확인 통과" if not bad else f"확인 필요 {bad}문항 → mini5_out.txt 원문 확인")


if __name__ == "__main__":
    main()
