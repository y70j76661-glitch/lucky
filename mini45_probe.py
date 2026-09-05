# -*- coding: utf-8 -*-
"""mini45_probe.py — v13.68 재확인(T11·C6·S4) + 추천 후보 원칙 확인(M2 일반 추천, M2b 안정형 추천). 5문항.
사용: python mini45_probe.py && python claim_check.py mini45_out.txt"""
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
    ("M2", "좋은 연금상품 하나 추천해주세요.",
     lambda a: ([] if not re.search(r"추천\s*(?:드립니다|합니다|드리겠습니다)", a) else ["★단정추천_잔존"])
     + ([] if not re.search(r"근거 문서:[^\n]*확인되지 않아", a) else ["★등급미확인_후보_잔존"])
     + ([] if not re.search(r"꾸준한\s*수익|극복할\s*가능성|안전한\s*투자를\s*지향|손실의?\s*가능성이\s*낮(?:습니다|지만)", a) else ["★보장성_표현_잔존"])
     + ([] if "자산관리센터" not in a else ["★근거없는_상담유도"])
     + ([] if len(re.findall(r"(?m)^\s*-\s*(?:근거 문서:|[가-힣A-Za-z0-9 ]+[\]\)]:\s*위험등급)", a)) >= len(re.findall(r"(?m)^\s*-\s*유의:", a)) - 1 else ["상품별_근거줄_부족(원문 확인)"])),
    ("S4", "IRP 계좌에서 ETF 사고팔면 양도소득세나 배당소득세 내나요?",
     lambda a: ([] if not re.search(r"(?:양도소득세|배당소득세)[^\n]{0,20}(?:부과되지 않|내지 않)", a) else ["★면제단정_잔존"])
     + ([] if re.search(r"즉시 과세되지 않|과세\s*이연", a) else ["★과세이연_누락"]) + ([] if re.search(r"기타소득세", a) else ["★범위고지_누락"])
     + ([] if not re.search(r"상계|통산|15\.4", a) else ["상계/15.4_잔존(근거 확인)"]) + ([] if a.count("즉시 과세되지 않고(과세이연)") <= 1 else ["★표준문장_중복"])),
    ("M2b", "은퇴가 10년 남았는데 안정적인 연금펀드 추천해줘.",
     lambda a: ([] if not re.search(r"근거 문서:[^\n]*확인되지 않아", a) else ["★등급미확인_후보_잔존"])
     + ([] if not re.search(r"원금(?:이|을)?\s*보장(?:됩니다|되는|하는)", a) else ["★펀드_원금보장_단정"]) + ([] if "은(는)" not in a else ["조사_미정합"])),
    ("T11", "30대 직장인인데 공격적으로 굴릴 연금펀드 하나 추천해줘",
     lambda a: ([] if not re.search(r"추천\s*(?:드립니다|합니다|드리겠습니다)", a) else ["★단정추천_잔존"])
     + ([] if not re.search(r"수상|최우수|인정받|1위", a) else ["★판촉문장_잔존"]) + ([] if not re.search(r"근거 문서:[^\n]*확인되지 않아", a) else ["★등급미확인_후보_잔존"])),
    ("C9", "연금저축이랑 IRP 둘 다 있는데 세액공제 받으려면 어디에 먼저 넣는 게 유리해요?",
     lambda a: ([] if "600" in a and "900" in a else ["★한도구조_누락"]) + ([] if "문서과 아래 참고" not in a else ["★출처흉터_잔존"])
     + ([] if not re.search(r"(?:IRP|연금저축)[^\n]{0,40}?(?:수익률?\s*(?:극대화|이\s*높)|높은\s*수익|공격적인\s*포트폴리오|보다\s*(?:공격적|유리))", a) else ["★계좌_수익성비교_잔존"])),
    ("B12", "퇴직금 받은 지 두 달 지났는데 지금 IRP에 넣어도 세금 돌려받을 수 있나요?",
     lambda a: ([] if re.search(r"60\s*일", a) else ["★60일기한_누락"]) + ([] if not re.search(r"세액공제\s*(?:혜택|대상이\s*될|대상이\s*됩|조건|신청)", a) else ["★세액공제_개념혼동"])
     + ([] if a.startswith("'두 달' 표현") else ["판정문장_선두아님"])),
]


def main():
    ft = open("mini45_out.txt", "w", encoding="utf-8"); bad = 0
    for qid, q, chk in Q:
        t0 = time.time()
        try:
            a, tr = _ask(qid, q)
        except Exception as e:
            a = f"(요청실패:{str(e)[:40]})"; tr = ""
        f = _common(a) + chk(a); bad += bool(f)
        print(f"  [{qid:3}] {time.time()-t0:4.1f}s  {'OK' if not f else '확인: ' + ' '.join(f)}")
        ft.write(f"\n{'='*70}\n[{qid}] {q}\n판정: {f or 'OK'}\n--- trace ---\n{tr}\n--- 답변 ---\n{a}\n"); time.sleep(0.5)
    ft.close(); print("=" * 50); print("6문항 모두 OK" if not bad else f"확인 필요 {bad}문항 → mini45_out.txt (판정은 후보, 원문 확인 필요)")


if __name__ == "__main__":
    main()
