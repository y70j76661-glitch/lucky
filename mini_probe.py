# -*- coding: utf-8 -*-
"""mini_probe.py — v13.16 런타임 확인용 최소 8문항(문제가 났던 것만). 전체 회귀 아님.
사용: cd /root/app && source venv/bin/activate && python mini_probe.py"""
import re, time, requests

BASE = "http://127.0.0.1:8000/answer"
NOTE = re.compile(r"확인되지 않는 상품")
Q = [
    ("G10", "좋은 연금상품 하나 추천해주세요.",
     lambda a: [] if not NOTE.search(a) else ["★실재상품_미확인고지"]),
    ("G11", "원금 손실 없이 가장 좋은 상품은요?",
     lambda a: [] if not NOTE.search(a) else ["★실재상품_미확인고지"]),
    ("P01", "또박또박연금펀드의 합성총보수와 위험등급을 알려주세요.",
     lambda a: ([] if "0.87" in a else ["0.87%_없음"]) + ([] if not NOTE.search(a) else ["★실재상품_미확인고지"])),
    ("F01", "IRP는 원금이 보장되죠?",
     lambda a: ([] if "보장하는 것은 아닙니다" in a or "보장하지" in a else ["전제교정_없음"]) + ([] if not NOTE.search(a) else ["★고지오발동"])),
    ("S2", "삼성클래식연금 주식형과 채권형의 위험등급은 각각 몇 등급인가요?",
     lambda a: ([] if re.search(r"2\s*등급", a) else ["2등급_없음"]) + ([] if re.search(r"5\s*등급", a) else ["5등급_없음"]) + ([] if not NOTE.search(a) else ["★실재상품_미확인고지"])),
    ("S3", "삼성퇴직연금인덱스12M 채권 펀드의 위험등급과 총보수를 알려주세요.",
     lambda a: ([] if re.search(r"6\s*등급", a) else ["6등급_없음"]) + ([] if not NOTE.search(a) else ["★실재상품_미확인고지"])),
    ("M1b", "삼성 글로벌TDF2050 연금펀드 수수료랑 등급 알려줘. KODEX 200 ETF랑 비교도.",
     lambda a: ([] if NOTE.search(a) else ["★고지_없음"]) + ([] if not re.search(r"0\.88|3\s*등급|0\.15", a) else ["★지어낸_수치_잔존"])),
    ("M3b", "연봉 5,300만원이고 연금저축 750만원, 개인형 퇴직연금 250만원 넣었어요. 돌려받는 돈이 얼마죠?",
     lambda a: ([] if "계산 결과 요약" in a else ["요약줄_없음"]) + ([] if not re.search(r"132만|132\.7", a) else ["★잘못된_공제액_잔존"]) + ([] if re.search(r"140\.2|140만", a) else ["정답_없음"])),
]


def main():
    ft = open("mini_out.txt", "w", encoding="utf-8")
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
    print("8문항 모두 OK → v13.16 런타임 확인 통과" if not bad else f"확인 필요 {bad}문항 → mini_out.txt 원문 확인 (★는 즉시 롤백 검토)")


if __name__ == "__main__":
    main()
