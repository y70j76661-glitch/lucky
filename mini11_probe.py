# -*- coding: utf-8 -*-
"""mini11_probe.py — v13.29 확인 5문항(N6·M2·D9·S3·X2). 전체 회귀 아님.
사용: cd /root/app && source venv/bin/activate && python mini11_probe.py && python3 cite_check.py mini11_out.txt"""
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
    if re.search(r"지방소득세", b) and "doc1.pdf" not in a: f.append("지방소득세_표기(출처 doc1 없음)")
    return f
def _m2(a):
    b = a.split("[참고 문서]")[0]
    f = []
    if re.search(r"손실의?\s*가능성을\s*최소화합니다|원금\s*보전에\s*초점|(?:투자자|고객)에게\s*(?:알맞|적절|적합)|목적에\s*부합합니다|안정적인\s*수익을\s*제공|수익을\s*보장|원금\s*손실을\s*최소화합니다|무위험|조세특례제한법|소득공제", b): f.append("★표현_잔존")
    if re.search(r"확인되지 않는 상품명", b): f.append("★실재상품_오탐")
    if re.search(r"(?m)^\s*[-•]\s*(?:수수료|투자\s*대상)\s*[:：][^\d\n]*$", b): f.append("★숫자없는_일반불릿_잔존")
    if not re.search(r"등급", b): f.append("상품/등급_없음")
    return f
Q = [
    ("N6", "중도해지 세금은 빼고, 연금으로 받을 때 세금만 알려줘.", _n6),
    ("D9", "총급여 5,500만원, 연금저축 500만원과 IRP 500만원 납입하면 공제액은?",
     lambda a: ([] if re.search(r"^계산 결과 요약:.*148\.5", a, re.M) else ["★요약줄/공제액"]) + ([] if re.search(r"doc41|doc23", a) else ["한도근거문서_미인용"])),
    ("S3", "삼성퇴직연금인덱스12M 채권 펀드의 위험등급과 총보수를 알려주세요.",
     lambda a: ([] if re.search(r"6\s*등급", a) and "0.42" in a else ["등급/보수_없음"])),
    ("M2", "좋은 연금상품 하나 추천해주세요.", _m2),
    ("X2", "세액공제 제외 대상은 뭐예요?",
     lambda a: ([] if not any(("받지 않은" in st or "과세제외" in st) and re.search(r"(?:마지막|나중)(?:에|으로)\s*인출", st) and "먼저" not in st for st in re.split(r"(?<=[.!?])\s+", a.split("[참고 문서]")[0])) else ["★인출순서_반대"]) + ([] if not re.search(r"ISA[^.\n]*세액공제\s*대상이\s*아", a) else ["★ISA_과대서술"])),
]


def main():
    ft = open("mini11_out.txt", "w", encoding="utf-8")
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
    print("5문항 모두 OK → v13.29 확인 통과" if not bad else f"확인 필요 {bad}문항 → mini11_out.txt 원문 확인")


if __name__ == "__main__":
    main()
