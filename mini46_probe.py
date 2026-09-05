# -*- coding: utf-8 -*-
"""mini46_probe.py — v13.69 재확인(T11·C6·S4) + 추천 후보 원칙 확인(M2 일반 추천, M2b 안정형 추천). 5문항.
사용: python mini46_probe.py && python claim_check.py mini46_out.txt"""
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
     lambda a: ([] if not re.search(r"(?:양도소득세|배당소득세)[^\n]{0,20}(?:부과되지 않|내지 않)(?![^\n]{0,10}즉시)", a.replace("즉시 납부하지", "")) else ["★면제단정_잔존"])
     + ([] if re.search(r"즉시|과세\s*이연", a) else ["★과세이연_누락"]) + ([] if re.search(r"기타소득세", a) else ["★범위고지_누락"])
     + ([] if not re.search(r"1,?500\s*만\s*원\s*이하(?:로|이면|라면)\s*(?:인출|수령)", a) else ["★1500_조건없는_일반화"])),
    ("C9", "연금저축이랑 IRP 둘 다 있는데 세액공제 받으려면 어디에 먼저 넣는 게 유리해요?",
     lambda a: ([] if "600" in a and "900" in a else ["★한도구조_누락"]) + ([] if not re.search(r"(?<!\*)\*(?!\*)", a) else ["★홀수별표_잔존"])
     + ([] if not re.search(r"(?:IRP|연금저축)의\s*(?:안정성|수익성)|복리\s*효과", a) else ["★계좌_자산화_서술_잔존"])),
    ("M2", "좋은 연금상품 하나 추천해주세요.",
     lambda a: ([] if not re.search(r"추천\s*(?:드립니다|합니다|드리겠습니다)", a) else ["★단정추천_잔존"])
     + ([] if not re.search(r"근거 문서:[^\n]*확인되지 않아", a) else ["★등급미확인_후보_잔존"])
     + ([] if not re.search(r"꾸준한\s*수익|극복할\s*가능성|안전한\s*투자를\s*지향|손실의?\s*가능성이\s*낮(?:습니다|지만)", a) else ["★보장성_표현_잔존"])
     + ([] if "자산관리센터" not in a else ["★근거없는_상담유도"])
     + ([] if not any(s.startswith("R2_") and s not in a.split("[참고 문서]")[0] for s in re.findall(r"[\w.\-]+\.pdf", a.split("[참고 문서]")[-1])) else ["미인용_설명서_출처잔존"])),
    ("T6", "미래에셋 TDF2045랑 삼성클래식연금 주식형 중에 위험등급이 더 낮은 건 뭐예요?",
     lambda a: ([] if not re.search(r"보다\s*(?:더\s*)?(?:낮|높|안정적|안전)", a) else ["★우열단정_잔존"]) + ([] if "우열을 확정할 수 없" in a or "등급 비교(근거 문서 기준)" in a else ["★코드결론_없음"])
     + ([] if "2등급" in a else ["★삼성2등급_유실(회귀)"]) + ([] if "은(는)" not in a else ["조사_미정합"])),
    ("C2", "연봉 5천만원이고 올해 연금저축에 400만원, IRP에 500만원 넣었어요. 세액공제 얼마나 받아요?",
     lambda a: ([] if "900" in a else ["★합산한도900_누락"]) + ([] if re.search(r"16\.5", a) else ["★공제율16.5_누락"]) + ([] if re.search(r"148\.5|1,?485,?000|148만\s*5", a) else ["★공제액148.5_누락"])),
    ("B11", "연금저축은 55세 전에 해지해도 세금 없죠?",
     lambda a: ([] if "16.5" in a else ["★기타소득세16.5_누락"]) + ([] if not re.search(r"(?:네|예|맞습니다)[,.]?\s*세금이?\s*없", a) else ["★전제긍정"]) + ([] if "15.4" not in a else ["★15.4_혼입"])),
]


def main():
    ft = open("mini46_out.txt", "w", encoding="utf-8"); bad = 0
    for qid, q, chk in Q:
        t0 = time.time()
        try:
            a, tr = _ask(qid, q)
        except Exception as e:
            a = f"(요청실패:{str(e)[:40]})"; tr = ""
        f = _common(a) + chk(a); bad += bool(f)
        print(f"  [{qid:3}] {time.time()-t0:4.1f}s  {'OK' if not f else '확인: ' + ' '.join(f)}")
        ft.write(f"\n{'='*70}\n[{qid}] {q}\n판정: {f or 'OK'}\n--- trace ---\n{tr}\n--- 답변 ---\n{a}\n"); time.sleep(0.5)
    ft.close(); print("=" * 50); print("6문항 모두 OK" if not bad else f"확인 필요 {bad}문항 → mini46_out.txt (판정은 후보, 원문 확인 필요)")


if __name__ == "__main__":
    main()
