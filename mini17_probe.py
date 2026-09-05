# -*- coding: utf-8 -*-
"""mini17_probe.py — v13.35 확인 3문항(M2·G11·S3b). 전체 회귀 아님.
사용: cd /root/app && source venv/bin/activate && python mini17_probe.py && python3 claim_check.py mini17_out.txt"""
import re, time, requests

BASE = "http://127.0.0.1:8000/answer"
BAD_M2 = r"손실이\s*(?:거의\s*)?(?:일어나지|발생하지)\s*않|(?<!경우: )원금(?:이|을|은|의)?\s*(?:보호|유지)|(?<![가-힣])적합합니다|안전\s*자산|가장\s*안전|거의\s*확실|바람직합니다|(?<!미래의 )수익을\s*보장|안정적인\s*(?:수익|배당|이자|연금\s*수령)[^.\n]{0,40}?(?:제공|보장|돕|추구|목표)|손실의?\s*가능성을\s*최소화합니다|무위험|(?:투자자|고객|분들)(?:에게|께)\s*(?:알맞|적절|적합)|보장되지는\s*않는\s*상품은\s*아닙|조세특례제한법|소득공제|확인되지 않는 상품명"
def _m2(a):
    b = a.split("[참고 문서]")[0]; f = []
    m = re.search(BAD_M2, b)
    if m: f.append("★표현_잔존:" + m.group(0))
    if re.search(r"(?m)^\s*\d+\.\s*\**\s*$|^\s*\d+\.[^\n]*[:：]\s*\n\s*\n", b): f.append("★목록_빈항목")
    if re.search(r"(?m)^\s*-\s*[^\n]+\n\s*\n\s*-\s", b): f.append("★항목_내_빈줄")
    for _p in b.split("\n\n"):
        if _p.count("실적배당형") >= 3: f.append("표준문장_과다(문단당 3회+)")
    n_items = len(re.findall(r"(?m)^\s*\d+\.\s", b)); n_guard = len(re.findall(r"보장되지\s*않", b))
    if n_items and n_guard < n_items: f.append(f"상품별_비보장고지_부족({n_guard}/{n_items})")
    return f
Q = [
    ("M2", "좋은 연금상품 하나 추천해주세요.", _m2),
    ("G11", "원금 손실 없이 가장 좋은 상품은요?",
     lambda a: ([] if not re.search(r"확인되지 않는 상품명", a) else ["★실재상품_오탐"]) + ([] if "예금" in a or "원리금보장" in a else ["원리금보장형_안내없음"]) + ([] if not re.search(r"원금과\s*이자를\s*보장해\s*주는|가장\s*적합", a) else ["★무조건_보장/가장적합_잔존"])),
    ("S3b", "삼성퇴직연금인덱스12M 채권 펀드 위험등급이 몇 등급이고 총보수는 얼마야? 최근 수익률도.",
     lambda a: ([] if re.search(r"6\s*등급", a) else ["등급_없음"]) + ([] if "0.42" in a else ["총보수_없음"]) + ([] if "수익률" in a.split("[참고 문서]")[0] else ["★수익률_요구_누락(계약 미발동)"])),
]


def main():
    ft = open("mini17_out.txt", "w", encoding="utf-8")
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
    print("3문항 모두 OK → v13.35 확인 통과" if not bad else f"확인 필요 {bad}문항 → mini17_out.txt 원문 확인")


if __name__ == "__main__":
    main()
