# -*- coding: utf-8 -*-
"""mini12_probe.py — v13.30 최종 확인 4문항(D9 계좌별 서술·M2 표현·D4·M2b). 전체 회귀 아님.
사용: cd /root/app && source venv/bin/activate && python mini12_probe.py && python3 claim_check.py mini12_out.txt"""
import re, time, requests

BASE = "http://127.0.0.1:8000/answer"
BAD_M2 = r"원금을\s*유지|(?<![가-힣])적합합니다|안전\s*자산|바람직합니다|수익을\s*보장|안정적인\s*수익을\s*(?:제공|추구할\s*수)|손실의?\s*가능성을\s*최소화합니다|무위험|투자자에게\s*(?:알맞|적절)|조세특례제한법|소득공제|확인되지 않는 상품명"
Q = [
    ("D9", "총급여 5,500만원, 연금저축 500만원과 IRP 500만원 납입하면 공제액은?",
     lambda a: ([] if re.search(r"^계산 결과 요약:.*연금저축 500 \+ IRP 400.*초과 100만원은 대상 아님.*148\.5", a, re.M) else ["★요약줄_계좌별대상_없음"]) + ([] if not re.search(r"IRP\s*500\s*만\s*원(?:에\s*대한|을|를)[^\n]{0,30}500\s*만\s*원?\s*[x×X*]", a) else ["★IRP500전액_식_잔존"])),
    ("D4", "총급여 5,000만원, 연금저축 700만원과 IRP 200만원 넣었어요. 세액공제 얼마?",
     lambda a: ([] if re.search(r"^계산 결과 요약:.*132", a, re.M) else ["★요약줄/공제액"]) + ([] if not re.search(r"115\.5|148\.5", a) else ["★700×16.5/900×16.5_잔존"])),
    ("M2", "좋은 연금상품 하나 추천해주세요.",
     lambda a: ([] if not re.search(BAD_M2, a.split("[참고 문서]")[0]) else ["★표현_잔존:" + (re.search(BAD_M2, a.split("[참고 문서]")[0]).group(0))])),
    ("M2b", "은퇴가 10년 남았는데 안정적인 연금펀드 추천해줘.",
     lambda a: ([] if not re.search(BAD_M2, a.split("[참고 문서]")[0]) else ["★표현_잔존:" + (re.search(BAD_M2, a.split("[참고 문서]")[0]).group(0))]) + ([] if not re.search(r"원금(?:이|을|은)?\s*보장(?:되|하|이\s*되)(?!지)", a.split("[참고 문서]")[0]) else ["★원금보장_단정"])),
]


def main():
    ft = open("mini12_out.txt", "w", encoding="utf-8")
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
    print("4문항 모두 OK → v13.30 확인 통과" if not bad else f"확인 필요 {bad}문항 → mini12_out.txt 원문 확인")


if __name__ == "__main__":
    main()
