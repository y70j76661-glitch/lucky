# -*- coding: utf-8 -*-
"""mini26_probe.py — v13.48 확인 2문항(G11 총보수 고지 제거, S3형 보수 순위 질문은 유지). 사용: python mini26_probe.py"""
import re, time, requests
BASE = "http://127.0.0.1:8000/answer"
Q = [
    ("G11", "원금 손실 없이 가장 좋은 상품은요?", lambda a: ([] if "총보수 순위 비교표" not in a else ["★총보수고지_잔존"]) + ([] if "순위나 비교 데이터가 없어" in a else ["일반순위고지_누락"])),
    ("F1", "삼성퇴직연금인덱스12M 채권 펀드랑 또박또박연금펀드 중에 총보수 제일 낮은 게 뭐야?", lambda a: ([] if re.search(r"0\.42|0\.28", a) and "0.87" in a else ["보수값_누락"]) + ([] if not re.search(r"가장\s*(?:낮|저렴)[^\n]{0,20}(?:상품|펀드)입니다", a) else ["순위단정"])),
]
def main():
    ft = open("mini26_out.txt", "w", encoding="utf-8"); bad = 0
    for qid, q, chk in Q:
        t0 = time.time()
        try:
            r = requests.get(BASE, params={"question_id": qid, "question": q}, timeout=180).json(); a = r.get("answer", "") or ""; tr = r.get("think_trace", "")
        except Exception as e:
            a = f"(요청실패:{str(e)[:40]})"; tr = ""
        f = chk(a); bad += bool(f)
        print(f"  [{qid:3}] {time.time()-t0:4.1f}s  {'OK' if not f else '확인: ' + ' '.join(f)}")
        ft.write(f"\n{'='*70}\n[{qid}] {q}\n판정: {f or 'OK'}\n--- trace ---\n{tr}\n--- 답변 ---\n{a}\n"); time.sleep(0.5)
    ft.close(); print("=" * 50); print("2문항 모두 OK → v13.48 확인 통과" if not bad else f"확인 필요 {bad}문항 → mini26_out.txt")
if __name__ == "__main__":
    main()
