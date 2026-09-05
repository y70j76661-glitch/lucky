# -*- coding: utf-8 -*-
"""mini7_probe.py — v13.25 런타임 확인 3문항(N6 출처·M2 출처/법령문장·S3). 전체 회귀 아님.
사용: cd /root/app && source venv/bin/activate && python mini7_probe.py && python3 cite_check.py mini7_out.txt"""
import re, time, requests

BASE = "http://127.0.0.1:8000/answer"
Q = [
    ("N6", "중도해지 세금은 빼고, 연금으로 받을 때 세금만 알려줘.",
     lambda a: ([] if re.search(r"70\s*세", a) else ["연령구간_없음"]) + ([] if not re.search(r"기타소득세|연금\s*외|중도\s*해지", a.split("[참고 문서]")[0]) else ["★제외주제_잔존"])),
    ("M2", "좋은 연금상품 하나 추천해주세요.",
     lambda a: ([] if not re.search(r"72\s*만\s*원|40\s*%|소득공제|조세특례제한법", a) else ["★세제문장_잔존"]) + ([] if not re.search(r"확인되지 않는 상품", a) else ["★실재상품_미확인"])),
    ("S3", "삼성퇴직연금인덱스12M 채권 펀드의 위험등급과 총보수를 알려주세요.",
     lambda a: ([] if re.search(r"6\s*등급", a) else ["6등급_없음"]) + ([] if "0.42" in a else ["총보수0.42_없음"])),
]


def main():
    ft = open("mini7_out.txt", "w", encoding="utf-8")
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
    print("3문항 모두 OK → v13.25 런타임 확인 통과" if not bad else f"확인 필요 {bad}문항 → mini7_out.txt 원문 확인")


if __name__ == "__main__":
    main()
