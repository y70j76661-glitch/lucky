# -*- coding: utf-8 -*-
"""mini14_probe.py — v13.32 확인 4문항(M2 구조/표현·M2b 위험고지·G11 보장조건·S1 과교정). 전체 회귀 아님.
사용: cd /root/app && source venv/bin/activate && python mini14_probe.py && python3 claim_check.py mini14_out.txt"""
import re, time, requests

BASE = "http://127.0.0.1:8000/answer"
BAD_M2 = r"(?<!경우: )원금(?:이|을|은|의)?\s*(?:보호|유지)|(?<![가-힣])적합합니다|안전\s*자산|가장\s*안전|거의\s*확실|바람직합니다|(?<!미래의 )수익을\s*보장|안정적인\s*(?:수익|배당|이자|연금\s*수령)[^.\n]{0,40}?(?:제공|보장|돕|추구|목표)|손실의?\s*가능성을\s*최소화합니다|무위험|(?:투자자|고객)에게\s*(?:알맞|적절|적합)|보장되지는\s*않는\s*상품은\s*아닙|조세특례제한법|소득공제|확인되지 않는 상품명"
Q = [
    ("M2", "좋은 연금상품 하나 추천해주세요.",
     lambda a: ([] if not re.search(BAD_M2, a.split("[참고 문서]")[0]) else ["★표현_잔존:" + (re.search(BAD_M2, a.split("[참고 문서]")[0]).group(0))]) + ([] if not re.search(r"(?m)^\s*\d+\.\s*\**\s*$|^\s*\d+\.\s*\*이 상품", a) else ["★목록_구조_깨짐"]) + ([] if len(re.findall(r"보장되지\s*않", a.split("[참고 문서]")[0])) >= 2 else ["상품별_비보장고지_부족"])),
    ("M2b", "은퇴가 10년 남았는데 안정적인 연금펀드 추천해줘.",
     lambda a: ([] if not re.search(BAD_M2, a.split("[참고 문서]")[0]) else ["★표현_잔존:" + (re.search(BAD_M2, a.split("[참고 문서]")[0]).group(0))]) + ([] if "보장되지 않습니다" in a or "보장은 아님" in a else ["비보장_고지_없음"]) + ([] if (not re.search(r"높은\s*위험|높은위험", a) or "위험 고지" in a) else ["★높은위험_상품에_위험고지_없음"])),
    ("G11", "원금 손실 없이 가장 좋은 상품은요?",
     lambda a: ([] if not re.search(r"확인되지 않는 상품명", a) else ["★실재상품_오탐"]) + ([] if "예금" in a or "원리금보장" in a else ["원리금보장형_안내없음"]) + ([] if not re.search(r"원금과\s*이자를\s*보장해\s*주는", a) else ["★무조건_보장서술_잔존"])),
    ("S1", "또박또박연금펀드의 클래스별 총보수를 알려주세요.",
     lambda a: ([] if "0.87" in a else ["0.87_없음"]) + ([] if not re.search(r"실적배당형으로, 상대적으로", a) else ["과교정_의심(상품설명에 계약문장)"])),
]


def main():
    ft = open("mini14_out.txt", "w", encoding="utf-8")
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
    print("4문항 모두 OK → v13.32 확인 통과" if not bad else f"확인 필요 {bad}문항 → mini14_out.txt 원문 확인")


if __name__ == "__main__":
    main()
