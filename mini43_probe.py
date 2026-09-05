# -*- coding: utf-8 -*-
"""mini43_probe.py — v13.66 재확인(T11·C6·S4) + 추천 후보 원칙 확인(M2 일반 추천, M2b 안정형 추천). 5문항.
사용: python mini43_probe.py && python claim_check.py mini43_out.txt"""
import re, time, requests
BASE = "http://127.0.0.1:8000/answer"


def _common(a):
    f = []
    if re.search(r"요청실패|답변 생성에 실패|429|일시적인 오류", a):
        f.append("★생성실패")
    if re.search(r"보장되지는 않는 상품은 아닙|보장되지 않는 상품은 아닙", a):
        f.append("★이중부정")
    if re.search(r"(?<![\d.])(?:[07-9]|\d{2,})\s*등급", a.split("[참고 문서]")[0]):
        f.append("★등급범위밖")
    if "(출처:아래" in a or "아래 참고 문서—" in a:
        f.append("★출처표기깨짐")
    if "[참고 문서]" not in a and not re.search(r"범위를 벗어나|응해 드릴 수 없|처리하지 않았습니다", a):
        f.append("출처줄_없음")
    if re.search(r"(?m)^핵심 차이 요약:\s*\n\s*(?:\n|\Z)", a):
        f.append("★빈_요약머리")
    return f


def _ask(qid, q):
    r = requests.get(BASE, params={"question_id": qid, "question": q}, timeout=180).json()
    return r.get("answer", "") or "", r.get("think_trace", "")


Q = [
    ("T11", "30대 직장인인데 공격적으로 굴릴 연금펀드 하나 추천해줘",
     lambda a: ([] if not re.search(r"추천\s*(?:드립니다|합니다|드리겠습니다)", a) else ["★단정추천_잔존"])
     + ([] if not re.search(r"수상|최우수|인정받|1위", a) else ["★판촉문장_잔존"])
     + ([] if not re.search(r"근거 문서:[^\n]*확인되지 않아", a) else ["★등급미확인_후보_잔존"])
     + ([] if re.search(r"위험등급\s*[1-6]\s*등급", a) or "확정하지 못했습니다" in a or "확정하지 않습니다" in a else ["후보_등급표기_없음(원문 확인)"])
     + ([] if "은(는)" not in a else ["조사_미정합"])),
    ("C6", "저 연금 얼마 받을 수 있어요?",
     lambda a: ([] if re.search(r"계산할 수 없습니다", a[:200]) else ["★한계고지_누락"])
     + ([] if not re.search(r"(?m)사용자부담금|수급기간|연금대기자|^\s*\d+[.)]\s", a) else ["★특정계좌_요건목록_잔존"])),
    ("S4", "IRP 계좌에서 ETF 사고팔면 양도소득세나 배당소득세 내나요?",
     lambda a: ([] if not re.search(r"(?:양도소득세|배당소득세)[^\n]{0,20}(?:내지 않습니다|부과되지 않습니다)", a) else ["★무조건면제_단정_잔존"])
     + ([] if re.search(r"즉시 과세되지 않|과세\s*이연", a) else ["★과세이연_누락"]) + ([] if re.search(r"기타소득세|연금\s*외", a) else ["★범위고지_누락"])
     + ([] if "통산" not in a else ["통산_잔존(근거 확인)"])),
    ("M2", "좋은 연금상품 하나 추천해주세요.",
     lambda a: ([] if not re.search(r"추천\s*(?:드립니다|합니다|드리겠습니다)", a) else ["★단정추천_잔존"])
     + ([] if not re.search(r"근거 문서:[^\n]*확인되지 않아", a) else ["★등급미확인_후보_잔존"])
     + ([] if re.search(r"보장되지 않", a) or "예금" in a else ["비보장고지_누락"])),
    ("M2b", "은퇴가 10년 남았는데 안정적인 연금펀드 추천해줘.",
     lambda a: ([] if not re.search(r"근거 문서:[^\n]*확인되지 않아", a) else ["★등급미확인_후보_잔존"])
     + ([] if not re.search(r"원금(?:이|을)?\s*보장(?:됩니다|되는|하는)", a) else ["★펀드_원금보장_단정"])
     + ([] if re.search(r"[1-6]\s*등급|확정하지 못", a) else ["등급표기_없음(원문 확인)"])),
]


def main():
    ft = open("mini43_out.txt", "w", encoding="utf-8"); bad = 0
    for qid, q, chk in Q:
        t0 = time.time()
        try:
            a, tr = _ask(qid, q)
        except Exception as e:
            a = f"(요청실패:{str(e)[:40]})"; tr = ""
        f = _common(a) + chk(a); bad += bool(f)
        print(f"  [{qid:3}] {time.time()-t0:4.1f}s  {'OK' if not f else '확인: ' + ' '.join(f)}")
        ft.write(f"\n{'='*70}\n[{qid}] {q}\n판정: {f or 'OK'}\n--- trace ---\n{tr}\n--- 답변 ---\n{a}\n"); time.sleep(0.5)
    ft.close(); print("=" * 50); print("5문항 모두 OK" if not bad else f"확인 필요 {bad}문항 → mini43_out.txt (판정은 후보, 원문 확인 필요)")


if __name__ == "__main__":
    main()
