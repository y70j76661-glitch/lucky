# -*- coding: utf-8 -*-
"""mini19_probe.py — v13.39 확인 2문항(S1 비교·S2 단일). 사용: python mini19_probe.py && python claim_check.py mini19_out.txt"""
import re, time, requests
BASE = "http://127.0.0.1:8000/answer"
Q = [
    ("S1", "삼성클래식연금 채권형 위험등급이랑 주식형 위험등급 비교해줘.",
     lambda a: ([] if "대조 불가" not in a else ["★거짓_대조불가_고지"]) + ([] if not re.search(r"\[주식\][^\n]{0,20}5\s*등급", a) else ["★주식형_등급_오기"]) + ([] if re.search(r"2\s*등급", a) and re.search(r"5\s*등급", a) else ["등급_누락"])),
    ("S2", "삼성클래식연금 주식형과 채권형의 위험등급은 각각 몇 등급인가요?",
     lambda a: ([] if re.search(r"\[주식\][^\n]{0,25}2\s*등급|주식[^\n]{0,25}2\s*등급", a) and re.search(r"\[채권\][^\n]{0,25}5\s*등급|채권[^\n]{0,25}5\s*등급", a) else ["★등급_대응_오류"])),
]
def main():
    ft = open("mini19_out.txt", "w", encoding="utf-8"); bad = 0
    for qid, q, chk in Q:
        t0 = time.time()
        try:
            r = requests.get(BASE, params={"question_id": qid, "question": q}, timeout=180).json(); a = r.get("answer", "") or ""; tr = r.get("think_trace", "")
        except Exception as e:
            a = f"(요청실패:{str(e)[:40]})"; tr = ""
        f = chk(a); bad += bool(f)
        print(f"  [{qid:3}] {time.time()-t0:4.1f}s  {'OK' if not f else '확인: ' + ' '.join(f)}")
        ft.write(f"\n{'='*70}\n[{qid}] {q}\n판정: {f or 'OK'}\n--- trace ---\n{tr}\n--- 답변 ---\n{a}\n"); time.sleep(0.5)
    ft.close(); print("=" * 50); print("2문항 모두 OK → v13.39 확인 통과" if not bad else f"확인 필요 {bad}문항 → mini19_out.txt")
if __name__ == "__main__":
    main()
