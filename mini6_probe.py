# -*- coding: utf-8 -*-
"""mini6_probe.py — v13.24 런타임 확인 4문항(X1·N4b·M2·X2). 전체 회귀 아님.
사용: cd /root/app && source venv/bin/activate && python mini6_probe.py"""
import re, time, requests

BASE = "http://127.0.0.1:8000/answer"
Q = [
    ("X1", "수수료 얘기는 빼고 또박또박연금펀드 위험등급만 알려줘.",
     lambda a: ([] if not re.search(r"기타소득세|과세제외", a.split("[참고 문서]")[0]) else ["★세금카드_잔존"]) + ([] if "보통위험" in a else ["등급_없음"])),
    ("N4b", "IRP 세액공제 받을 수 있는 금액은?",
     lambda a: ([] if re.search(r"900\s*만", a) else ["900_없음"]) + ([] if re.search(r"600\s*만", a) else ["★600_없음"])),
    ("M2", "좋은 연금상품 하나 추천해주세요.",
     lambda a: ([] if not re.search(r"72\s*만\s*원|40\s*%|소득공제", a) else ["★구규정_세제문장_잔존"])),
    ("X2", "세액공제 제외 대상은 뭐예요?",
     lambda a: ([] if re.search(r"세액공제", a.split("[참고 문서]")[0]) and not re.search(r"^제공된 자료에서 확인할 수 없습니다\.\s*$", a.split("[참고 문서]")[0].strip().split("\n")[0]) else ["★근거누락_확인불가"]) + ([] if "doc41" in a else ["doc41_미참조"])),
]


def main():
    ft = open("mini6_out.txt", "w", encoding="utf-8")
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
    print("4문항 모두 OK → v13.24 런타임 확인 통과" if not bad else f"확인 필요 {bad}문항 → mini6_out.txt 원문 확인")


if __name__ == "__main__":
    main()
