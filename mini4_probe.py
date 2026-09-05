# -*- coding: utf-8 -*-
"""mini4_probe.py — v13.20 런타임 확인 5문항(게이트 S4b·제외 파서 오탐·N4 한도 + E7/D9 재확인). 전체 회귀 아님.
사용: cd /root/app && source venv/bin/activate && python mini4_probe.py"""
import re, time, requests

BASE = "http://127.0.0.1:8000/answer"
Q = [
    ("S4b", "미래에셋TDF2030 위험등급은?",
     lambda a: ([] if re.search(r"확인되지 않는 상품|확인되지 않|확인할 수 없", a) else ["★미확인_고지없음"]) + ([] if not re.search(r"[1-6]\s*등급", a.split("[참고 문서]")[0]) else ["★지어낸_등급"])),
    ("X2", "세액공제 제외 대상은 뭐예요?",
     lambda a: [] if re.search(r"세액공제", a.split("[참고 문서]")[0]) else ["★세액공제_문장_전부삭제"]),
    ("N4b", "IRP 세액공제 받을 수 있는 금액은?",
     lambda a: ([] if re.search(r"900\s*만", a) else ["900_없음"]) + ([] if re.search(r"600\s*만", a) else ["600_없음"])),
    ("E7", "연봉 1억 2천만원, 연금저축 600만원 납입 시 공제액은?",
     lambda a: ([] if not re.search(r"(?:한도|제한)[^.\n]{0,12}300\s*만|300\s*만\s*원[^.\n]{0,12}(?:한도|제한)|소득이\s*높|고소득", a) else ["★옛규정/고소득_잔존"]) + ([] if "79.2" in a else ["정답_없음"])),
    ("D9", "총급여 5,500만원, 연금저축 500만원과 IRP 500만원 납입하면 공제액은?",
     lambda a: ([] if "초과 100만원" in a else ["★요약줄_초과분_오류"]) + ([] if "148.5" in a else ["정답_없음"])),
]


def main():
    ft = open("mini4_out.txt", "w", encoding="utf-8")
    bad = 0
    for qid, q, chk in Q:
        t0 = time.time()
        try:
            a = requests.get(BASE, params={"question_id": qid, "question": q}, timeout=180).json().get("answer", "") or ""
        except Exception as e:
            a = f"(요청실패:{str(e)[:40]})"
        f = chk(a)
        bad += bool(f)
        print(f"  [{qid:3}] {time.time()-t0:4.1f}s  {'OK' if not f else '확인: ' + ' '.join(f)}")
        ft.write(f"\n{'='*70}\n[{qid}] {q}\n판정: {f or 'OK'}\n--- 답변 ---\n{a}\n")
        time.sleep(0.3)
    ft.close()
    print("=" * 50)
    print("5문항 모두 OK → v13.20 런타임 확인 통과" if not bad else f"확인 필요 {bad}문항 → mini4_out.txt 원문 확인")


if __name__ == "__main__":
    main()
