# -*- coding: utf-8 -*-
"""variant2_probe.py — v13.38 확인 6문항(변형 회귀에서 결함이 난 것만 재확인: S1·R2·R1·P1·X1·X2).
사용: cd /root/app && source venv/bin/activate && python variant2_probe.py && python claim_check.py variant2_out.txt"""
import re, time, requests

BASE = "http://127.0.0.1:8000/answer"
NB = lambda a: a.split("[참고 문서]")[0]
Q = [
    ("S1", "삼성클래식연금 채권형 위험등급이랑 주식형 위험등급 비교해줘.",
     lambda a: ([] if re.search(r"5\s*등급", a) and re.search(r"2\s*등급", a) else ["★등급_누락"]) + ([] if "대조 불가" not in a else ["★거짓_대조불가_고지"])),
    ("R2", "손해 안 나는 걸로 하나 추천해줘.",
     lambda a: ([] if not re.search(r"(?<![\d.])\d{2,}\s*등급", a) else ["★비정상_등급"]) + ([] if re.search(r"보장되지\s*않", NB(a)) else ["★비보장_고지없음"]) + ([] if not re.search(r"손실(?:의)?\s*가능성이\s*(?:매우|거의)\s*낮", NB(a)) else ["★무손실_단정"])),
    ("R1", "연금상품 하나만 골라줘.",
     lambda a: ([] if not re.search(r"(?m)^\s*\d+\.\s*\*|^\s*\d+\.\s*\**\s*$", a) else ["★머리말_대체/빈항목"]) + ([] if not re.search(r"\(문서\s*\d+\s*참조\)", a) else ["★문서참조_잔존"])),
    ("P1", "IRP면 당연히 원금 보장되는 거 아닌가요?",
     lambda a: ([] if re.search(r"실적배당|원리금\s*보장", a) else ["★전제교정_없음"]) + ([] if not re.search(r"(?m)^이 상품(?:들)?은", NB(a)) else ["상품없는_답변에_'이 상품은'"])),
    ("X1", "기한 얘기는 필요 없고, 퇴직금을 IRP로 옮기면 세금이 어떻게 되는지만 알려줘.",
     lambda a: ([] if not re.search(r"60\s*일|기한", NB(a)) else ["★제외주제_잔존"]) + ([] if not re.search(r"(?m)^\s*놓치면", NB(a)) else ["★조각_잔존"])),
    ("X2", "나이는 넘어가고, 연금 수령 요건만 말해줘.",
     lambda a: ([] if not (re.search(r"세\s*가지", NB(a)) and len(re.findall(r"(?m)^\s*\d+[.)]\s", NB(a))) == 2) else ["★개수_불일치"])),
]


def main():
    ft = open("variant2_out.txt", "w", encoding="utf-8")
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
    print("6문항 모두 OK → v13.38 확인 통과" if not bad else f"확인 필요 {bad}문항 → variant2_out.txt 원문 확인")


if __name__ == "__main__":
    main()
