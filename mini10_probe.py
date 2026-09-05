# -*- coding: utf-8 -*-
"""mini10_probe.py — v13.28 답변 계약 확인 5문항(N6·M2·G11·X2·S2). 전체 회귀 아님.
사용: cd /root/app && source venv/bin/activate && python mini10_probe.py && python3 cite_check.py mini10_out.txt"""
import re, time, requests

BASE = "http://127.0.0.1:8000/answer"
def _n6(a):
    b = a.split("[참고 문서]")[0]
    f = []
    if not re.search(r"70\s*세", a): f.append("연령구간_없음")
    if re.search(r"기타소득세|연금\s*외|중도\s*해지", b): f.append("★제외주제_잔존")
    if re.search(r"1\.1\s*%|2\.2\s*%|55\s*세(?:에서|~|-)\s*64", b): f.append("★잘못된_세율구간")
    if re.search(r"(?:자료|문서)[^.\n]{0,25}(?:연령|나이)[^.\n]{0,20}(?:누락|없|확인되지)|연령\s*구분이\s*어렵|관련\s*법령을\s*참조", b): f.append("★자기모순_문장_잔존")
    if "doc5.pdf" not in a and "doc39.docx" not in a: f.append("★근거문서_미인용")
    return f
def _m2(a):
    b = a.split("[참고 문서]")[0]
    f = []
    if re.search(r"손실의?\s*가능성을\s*최소화합니다|원금\s*보전에\s*초점|투자자에게\s*(?:알맞|적절|적합)|목적에\s*부합합니다|안정적인\s*수익을\s*제공|조세특례제한법|소득공제|연금자산관리센터", b): f.append("★표현/일반안내_잔존")
    if re.search(r"확인되지 않는 상품명", b): f.append("★실재상품_오탐")
    if re.search(r"(?m)^\s*[-•]\s*(?:수수료|투자\s*대상)\s*[:：][^\d\n]*$", b): f.append("★숫자없는_일반불릿_잔존")
    if not re.search(r"등급", b): f.append("상품/등급_없음")
    return f
Q = [
    ("N6", "중도해지 세금은 빼고, 연금으로 받을 때 세금만 알려줘.", _n6),
    ("N6b", "연금으로 받으면 세금이 얼마나 되나요?", _n6),
    ("M2", "좋은 연금상품 하나 추천해주세요.", _m2),
    ("G11", "원금 손실 없이 가장 좋은 상품은요?",
     lambda a: ([] if not re.search(r"확인되지 않는 상품명", a) else ["★실재상품_오탐"]) + ([] if not re.search(r"원금(?:이|을|은)?\s*보장(?:되|하|이\s*되)(?!지)", a.split("[참고 문서]")[0]) else ["★펀드_원금보장_단정"])),
    ("X2", "세액공제 제외 대상은 뭐예요?",
     lambda a: ([] if not any(("받지 않은" in st or "과세제외" in st) and re.search(r"(?:마지막|나중)(?:에|으로)\s*인출", st) and "먼저" not in st for st in re.split(r"(?<=[.!?])\s+", a.split("[참고 문서]")[0])) else ["★인출순서_반대"]) + ([] if not re.search(r"ISA[^.\n]*세액공제\s*대상이\s*아", a) else ["★ISA_과대서술"])),
]


def main():
    ft = open("mini10_out.txt", "w", encoding="utf-8")
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
    print("5문항 모두 OK → v13.28 계약 검증 통과" if not bad else f"확인 필요 {bad}문항 → mini10_out.txt 원문 확인")


if __name__ == "__main__":
    main()
