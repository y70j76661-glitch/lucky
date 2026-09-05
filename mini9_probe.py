# -*- coding: utf-8 -*-
"""mini9_probe.py — v13.27 런타임 확인 3문항(N6 세율 체계·M2 오탐/표현·X2 ISA). 전체 회귀 아님.
사용: cd /root/app && source venv/bin/activate && python mini9_probe.py && python3 cite_check.py mini9_out.txt"""
import re, time, requests

BASE = "http://127.0.0.1:8000/answer"
Q = [
    ("X2", "세액공제 제외 대상은 뭐예요?",
     lambda a: ([] if not any(("받지 않은" in st or "과세제외" in st or "이러한 금액" in st) and re.search(r"(?:마지막|나중)(?:에|으로)\s*인출", st) and "먼저" not in st for st in re.split(r"(?<=[.!?])\s+", a.split("[참고 문서]")[0])) else ["★인출순서_반대_잔존"]) + ([] if not re.search(r"ISA[^.\n]*세액공제\s*대상이\s*아", a) else ["★ISA_과대서술_잔존"]) + ([] if "세액공제" in a else ["근거누락"])),
    ("M2", "좋은 연금상품 하나 추천해주세요.",
     lambda a: ([] if not re.search(r"손실의?\s*가능성을\s*최소화합니다|원금\s*보전에\s*초점|투자자에게\s*(?:알맞|적절|적합)|목적에\s*부합합니다|안정적인\s*수익을\s*제공|조세특례제한법|소득공제", a) else ["★표현_잔존"]) + ([] if not re.search(r"확인되지 않는 상품명", a) else ["★실재상품_오탐"])),
    ("N6", "중도해지 세금은 빼고, 연금으로 받을 때 세금만 알려줘.",
     lambda a: ([] if re.search(r"70\s*세", a) else ["연령구간_없음"]) + ([] if not re.search(r"기타소득세|연금\s*외|중도\s*해지", a.split("[참고 문서]")[0]) else ["★제외주제_잔존"]) + ([] if not re.search(r"1\.1\s*%|2\.2\s*%|55\s*세(?:에서|~|-)\s*64", a) else ["★잘못된_세율구간_잔존"]) + ([] if len(re.findall(r"\d{2}\s*세[^\n%]{0,25}?\d(?:\.\d)?\s*%", a.split("[참고 문서]")[0])) <= 3 else ["연령세율_중복체계"])),
]


def main():
    ft = open("mini9_out.txt", "w", encoding="utf-8")
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
    print("3문항 모두 OK → v13.27 런타임 확인 통과" if not bad else f"확인 필요 {bad}문항 → mini9_out.txt 원문 확인")


if __name__ == "__main__":
    main()
