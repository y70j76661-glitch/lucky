# -*- coding: utf-8 -*-
"""mini3_probe.py — v13.19 런타임 확인 8문항(잔여 버그 4 + 정답표 3 + 제외 파서 1). 전체 회귀 아님.
사용: cd /root/app && source venv/bin/activate && python mini3_probe.py"""
import re, time, requests

BASE = "http://127.0.0.1:8000/answer"
Q = [
    ("E7", "연봉 1억 2천만원, 연금저축 600만원 납입 시 공제액은?",
     lambda a: ([] if not re.search(r"300\s*만\s*원", a) else ["★옛규정_300만_잔존"]) + ([] if not re.search(r"소득이\s*높|고소득", a) else ["★고소득한도_문장잔존"]) + ([] if "79.2" in a else ["정답_없음"])),
    ("D9", "총급여 5,500만원, 연금저축 500만원과 IRP 500만원 납입하면 공제액은?",
     lambda a: ([] if "초과 100만원" in a else ["★요약줄_초과분_오류"]) + ([] if not re.search(r"149", a) else ["★149_잔존"]) + ([] if "148.5" in a else ["정답_없음"])),
    ("N6", "중도해지 세금은 빼고, 연금으로 받을 때 세금만 알려줘.",
     lambda a: ([] if not re.search(r"기타소득세|연금\s*외|중도\s*해지|55\s*세\s*미만", a.split("[참고 문서]")[0]) else ["★제외주제_잔존"]) + ([] if re.search(r"70\s*세", a) else ["연령구간_없음"])),
    ("M2", "좋은 연금상품 하나 추천해주세요.",
     lambda a: ([] if not re.search(r"원금(?:을|이)\s*보호|원금\s*보전에\s*중점|가장\s*안전한\s*선택|원금\s*손실의?\s*가능성을\s*최소화", a) else ["★원금보장_과장표현"])),
    ("S3", "삼성퇴직연금인덱스12M 채권 펀드의 위험등급과 총보수를 알려주세요.",
     lambda a: ([] if re.search(r"6\s*등급", a) else ["6등급_없음"]) + ([] if not re.search(r"1\s*년\s*[:：]\s*[\d.]+\s*%", a) else ["★기간별_오독_잔존"]) + ([] if "0.42" in a else ["총보수0.42_없음"])),
    ("S1", "또박또박연금펀드의 클래스별 총보수를 알려주세요.",
     lambda a: ([] if "0.87" in a else ["0.87_없음"]) + ([] if not re.search(r"클래스\s*(?:A|C-P)\s*[:：]\s*0\.8", a) else ["★근거없는_클래스보수_잔존"])),
    ("S2", "삼성클래식연금 주식형과 채권형의 위험등급은 각각 몇 등급인가요?",
     lambda a: ([] if re.search(r"2\s*등급", a) and re.search(r"5\s*등급", a) else ["등급_누락"]) + ([] if not re.search(r"확인되지 않는 상품", a) else ["★실재상품_미확인"])),
    ("X1", "수수료 얘기는 빼고 또박또박연금펀드 위험등급만 알려줘.",
     lambda a: ([] if not re.search(r"보수|수수료", a.split("[참고 문서]")[0]) else ["★제외주제(수수료)_잔존"]) + ([] if "보통위험" in a else ["등급_없음"])),
]


def main():
    ft = open("mini3_out.txt", "w", encoding="utf-8")
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
    print("8문항 모두 OK → v13.19 런타임 확인 통과" if not bad else f"확인 필요 {bad}문항 → mini3_out.txt 원문 확인")


if __name__ == "__main__":
    main()
