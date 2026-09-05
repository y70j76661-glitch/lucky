# -*- coding: utf-8 -*-
"""mini47_probe.py — v13.70 재확인(T11·C6·S4) + 추천 후보 원칙 확인(M2 일반 추천, M2b 안정형 추천). 5문항.
사용: python mini47_probe.py && python claim_check.py mini47_out.txt"""
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
    ("S4", "IRP 계좌에서 ETF 사고팔면 양도소득세나 배당소득세 내나요?",
     lambda a: ([] if re.search(r"즉시|바로|과세\s*이연", a) else ["★과세이연_누락"]) + ([] if re.search(r"기타소득세", a) else ["★범위고지_누락"])
     + ([] if not re.search(r"1,?500\s*만\s*원\s*이하(?:로|이면|라면|의\s*금액)\s*(?:인출|수령|에\s*대해)", a.replace("연금소득 합계가 연 1,500만원 이하이면", "")) else ["★1500_조건없는_일반화"])
     + ([] if "차후 점에" not in a and not re.search(r"연금저축\(IRP 포함\)", a) else ["★어구잘림/용어"])),
    ("B11", "연금저축은 55세 전에 해지해도 세금 없죠?",
     lambda a: ([] if "16.5" in a else ["★기타소득세16.5_누락"]) + ([] if not re.search(r"(?:네|예|맞습니다)[,.]?\s*세금이?\s*없", a) else ["★전제긍정"]) + ([] if "15.4" not in a else ["★15.4_혼입"])
     + ([] if not re.search(r"세금을\s*(?:피할|면할)\s*수", a) else ["★세금회피_표현_잔존"])),
    ("M2", "좋은 연금상품 하나 추천해주세요.",
     lambda a: ([] if not re.search(r"추천\s*(?:드립니다|합니다|드리겠습니다)", a) else ["★단정추천_잔존"])
     + ([] if not re.search(r"근거 문서:[^\n]*확인되지 않아", a) else ["★등급미확인_후보_잔존"])
     + ([] if not re.search(r"꾸준한\s*수익|극복할\s*가능성|안전한\s*투자를\s*지향|손실의?\s*가능성이\s*낮(?:습니다|지만)|분들?께\s*적합|고수익을\s*기대하는", a) else ["★단정/보장성_표현_잔존"])
     + ([] if "자산관리센터" not in a else ["★근거없는_상담유도"])
     + ([] if not re.search(r"원금\s*보전[^\n]*\n(?![^\n]*원리금보장형)", a) else ["원금보전_머리말_고지없음(원문 확인)"])),
    ("T11", "30대 직장인인데 공격적으로 굴릴 연금펀드 하나 추천해줘",
     lambda a: ([] if not re.search(r"추천\s*(?:드립니다|합니다|드리겠습니다)", a) else ["★단정추천_잔존"])
     + ([] if not re.search(r"수상|최우수|인정받|1위", a) else ["★판촉문장_잔존"]) + ([] if not re.search(r"근거 문서:[^\n]*확인되지 않아", a) else ["★등급미확인_후보_잔존"])
     + ([] if "은(는)" not in a and not re.search(r"(?<!\*)\*(?!\*)", a) else ["표기_잔재"])),
]


def main():
    ft = open("mini47_out.txt", "w", encoding="utf-8"); bad = 0
    for qid, q, chk in Q:
        t0 = time.time()
        try:
            a, tr = _ask(qid, q)
        except Exception as e:
            a = f"(요청실패:{str(e)[:40]})"; tr = ""
        f = _common(a) + chk(a); bad += bool(f)
        print(f"  [{qid:3}] {time.time()-t0:4.1f}s  {'OK' if not f else '확인: ' + ' '.join(f)}")
        ft.write(f"\n{'='*70}\n[{qid}] {q}\n판정: {f or 'OK'}\n--- trace ---\n{tr}\n--- 답변 ---\n{a}\n"); time.sleep(0.5)
    ft.close(); print("=" * 50); print("6문항 모두 OK" if not bad else f"확인 필요 {bad}문항 → mini47_out.txt (판정은 후보, 원문 확인 필요)")


if __name__ == "__main__":
    main()
