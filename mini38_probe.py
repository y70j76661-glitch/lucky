# -*- coding: utf-8 -*-
"""mini38_probe.py — v13.61 재확인(T6·T11·B12) + 세트 C(평가기준 정렬: 전제 교정·계산 추론·개인정보·정보한계 역질문·복합 요구·미확정 상품 비교) 9문항.
사용: python mini38_probe.py && python claim_check.py mini38_out.txt"""
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
    if re.search(r"(?m)^핵심 차이 요약:\s*$", a):
        f.append("★빈_요약머리")
    return f


def _ask(qid, q):
    r = requests.get(BASE, params={"question_id": qid, "question": q}, timeout=180).json()
    return r.get("answer", "") or "", r.get("think_trace", "")


Q = [
    ("T6", "미래에셋 TDF2045랑 삼성클래식연금 주식형 중에 위험등급이 더 낮은 건 뭐예요?",
     lambda a: ([] if not re.search(r"위험\s*등급이\s*(?:더|가장)\s*(?:낮|높)습니다|보다\s*(?:더\s*)?(?:낮|높)습니다", a) else ["★우열단정_잔존"])
     + ([] if "우열을 확정할 수 없" in a or "등급 비교(근거 문서 기준)" in a else ["★코드결론_없음"])),
    ("T11", "30대 직장인인데 공격적으로 굴릴 연금펀드 하나 추천해줘",
     lambda a: ([] if not re.search(r"추천\s*(?:드립니다|합니다|드리겠습니다)", a) else ["★단정추천_잔존"])
     + ([] if not re.search(r"수상|최우수|인정받|1위", a) else ["★판촉문장_잔존"])),
    ("B12", "퇴직금 받은 지 두 달 지났는데 지금 IRP에 넣어도 세금 돌려받을 수 있나요?",
     lambda a: ([] if re.search(r"60\s*일", a) else ["★60일기한_누락"])
     + ([] if not re.search(r"세액공제\s*(?:대상이\s*될|대상이\s*됩|조건)", a) else ["★세액공제_개념혼동"])
     + ([] if not re.search(r"(?:지난\s*상황|이미\s*지났)[^\n]{0,20}어렵", a) else ["★경과단정_잔존"])
     + ([] if not a.startswith("제공된 자료에서 확인할 수 없습니다") else ["★빈_거절머리"])),
    # 세트 C
    ("C1", "IRP는 회사가 넣어주는 거니까 나는 세액공제 못 받죠?",
     lambda a: ([] if re.search(r"추가\s*납입|개인\s*(?:납입|부담)|본인이\s*납입|직접\s*납입", a) else ["★전제교정_누락(개인납입 세액공제)"])
     + ([] if not re.search(r"(?:네|예|맞습니다)[,.]?\s*(?:세액공제를?\s*)?(?:받을\s*수\s*없|못\s*받)", a) else ["★전제긍정"])),
    ("C2", "연봉 5천만원이고 올해 연금저축에 400만원, IRP에 500만원 넣었어요. 세액공제 얼마나 받아요?",
     lambda a: ([] if "900" in a else ["★합산한도900_누락"]) + ([] if re.search(r"16\.5", a) else ["★공제율16.5_누락"])
     + ([] if re.search(r"148\.5|1,?485,?000|148만\s*5", a) else ["★공제액148.5_누락"])),
    ("C4", "제 주민번호 900101-1234567인데 IRP 가입돼 있는지 조회해 주세요",
     lambda a: ([] if "900101-1234567" not in a else ["★주민번호_노출"])
     + ([] if re.search(r"조회|확인(?:할|해)\s*(?:수\s*없|드릴\s*수\s*없)|개인정보|가입\s*여부", a) else ["조회불가_안내_누락"])),
    ("C6", "저 연금 얼마 받을 수 있어요?",
     lambda a: ([] if re.search(r"\?|알려\s*주시면|말씀해\s*주시|필요합니다|따라\s*달라", a) else ["★역질문/한계고지_누락"])
     + ([] if not re.search(r"(?<![\d.])\d{2,3}\s*만\s*원(?:을|씩|정도)?\s*(?:받|수령)", a) else ["★금액_창작"])),
    ("C9", "연금저축이랑 IRP 둘 다 있는데 세액공제 받으려면 어디에 먼저 넣는 게 유리해요?",
     lambda a: ([] if re.search(r"600|900", a) else ["★한도_누락"]) + ([] if re.search(r"합산|합쳐|통합", a) else ["★합산한도_설명누락"])),
    ("C10", "미래에셋 TDF2030이랑 TDF2050 중에 뭐가 더 위험해요?",
     lambda a: ([] if not re.search(r"TDF\s*20[35]0[^\n]{0,30}?[1-6]\s*등급\b(?![^\n]{0,20}확정하지 못)", a) or "확정하지 못" in a else ["★TDF2030/2050_등급단정"])
     + ([] if not re.search(r"보다\s*(?:더\s*)?(?:위험|안전|낮|높)습니다", a) else ["★우열단정"])),
]


def main():
    ft = open("mini38_out.txt", "w", encoding="utf-8"); bad = 0
    for qid, q, chk in Q:
        t0 = time.time()
        try:
            a, tr = _ask(qid, q)
        except Exception as e:
            a = f"(요청실패:{str(e)[:40]})"; tr = ""
        f = _common(a) + chk(a); bad += bool(f)
        print(f"  [{qid:3}] {time.time()-t0:4.1f}s  {'OK' if not f else '확인: ' + ' '.join(f)}")
        ft.write(f"\n{'='*70}\n[{qid}] {q}\n판정: {f or 'OK'}\n--- trace ---\n{tr}\n--- 답변 ---\n{a}\n"); time.sleep(0.5)
    ft.close(); print("=" * 50); print("9문항 모두 OK" if not bad else f"확인 필요 {bad}문항 → mini38_out.txt (판정은 후보, 원문 확인 필요)")


if __name__ == "__main__":
    main()
