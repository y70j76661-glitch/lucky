# -*- coding: utf-8 -*-
"""mini65_probe.py — 세트 B 회귀(v13.60 이후 재실행 없던 문항 12개). 판정식은 원 프로브(mini36·mini39·mini28)와 동일.
B1 중도인출 사유 / B2 1,500만원 / B3 디폴트옵션 / B4 실물이전 / B5 DC→IRP / B6 클래스 보수 / B7 3년 수익률 / B11 55세 전 해지 /
S2 명퇴 교사 / S3 세액공제 반환 전제 / T15 솔로몬 국공채 비교 / B10 멀티턴.
사용: python mini65_probe.py && python golden_check.py mini65_out.txt base_setB.txt && python claim_check.py mini65_out.txt"""
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
    if "[참고 문서]" not in a:
        f.append("★출처줄_없음")
    _body = a.split("[참고 문서]")[0]; _ls = [l.strip() for l in _body.split("\n") if l.strip() and not l.strip().startswith(("※", "[", "(", "|", "-"))]
    if _ls and not re.search(r"[.!?)\]”\"':]$", _ls[-1]):
        f.append("★문장_잘림")
    if "은(는)" in a or re.search(r"(?<!\*)\*(?!\*)", a):
        f.append("표기_잔재")
    return f


def _ask(qid, q):
    r = requests.get(BASE, params={"question_id": qid, "question": q}, timeout=180).json()
    return r.get("answer", "") or "", r.get("think_trace", "")


Q = [
    ("B1", "IRP 중도인출 되는 경우가 뭐예요?",
     lambda a: ([] if len(re.findall(r"주택|요양|파산|회생|천재지변|재난", a)) >= 2 else ["★중도인출사유_부족"])),
    ("B2", "연금으로 받는 돈이 연 1,500만원 넘으면 어떻게 돼요?",
     lambda a: ([] if re.search(r"1,?500\s*만", a) else ["★1500만원_누락"]) + ([] if re.search(r"종합과세|분리과세", a) else ["★과세방식_누락"])),
    ("B3", "디폴트옵션이 뭐고 언제 적용돼요?",
     lambda a: ([] if re.search(r"디폴트\s*옵션|사전지정", a) else ["★디폴트옵션_미답"]) + ([] if re.search(r"주|일|만기|운용지시", a) else ["적용시점_누락"])),
    ("B4", "다른 증권사 연금저축을 미래에셋으로 옮길 때 갖고 있는 펀드를 그대로 옮길 수 있나요?",
     lambda a: ([] if re.search(r"실물\s*이전|현물\s*이전|이전", a) else ["★이전_미답"])),
    ("B5", "회사 DC 계좌가 있고 개인 IRP도 있는데, 퇴직하면 DC 돈은 어디로 가고 세금은 언제 내요?",
     lambda a: ([] if "IRP" in a and re.search(r"이전|이체|입금", a) else ["★DC→IRP_누락"]) + ([] if "퇴직소득세" in a else ["퇴직소득세_누락"]) + ([] if re.search(r"인출|수령|받을 때|찾을 때", a) else ["과세시점_누락"])),
    ("B6", "또박또박연금펀드 C-P2 말고 다른 클래스 보수는 얼마예요?",
     lambda a: ([] if re.search(r"확인되지 않|확인할 수 없|확인해 드리지 못|확인하지 못", a) else ["★정보한계_미고지"]) + ([] if not re.search(r"(?<!0\.8)(?<!0\.87)\b0\.\d{1,2}\s*%", a.replace("0.87%", "")) else ["★근거없는_보수값"])),
    ("B7", "삼성퇴직연금인덱스12M 최근 3년 수익률 얼마예요?",
     lambda a: ([] if "3.84" in a else ["★3년연평균3.84_누락"]) + ([] if re.search(r"과거|보장하지 않", a) else ["과거성과고지_누락"])),
    ("B11", "연금저축은 55세 전에 해지해도 세금 없죠?",
     lambda a: ([] if "16.5" in a else ["★기타소득세16.5_누락"]) + ([] if not re.search(r"(?:네|예|맞습니다)[,.]?\s*세금이?\s*없", a) else ["★전제긍정"])),
    ("S2", "명예퇴직한 교사인데 퇴직금 세금 줄이려면 어떻게 해야 해요?",
     lambda a: ([] if "IRP" in a or "연금계좌" in a else ["★IRP이전_누락"]) + ([] if re.search(r"30\s*%|감면|연금으로\s*수령|연금\s*수령", a) else ["★연금수령감면_누락"])
     + ([] if not re.search(r"세액공제\s*(?:혜택|대상이\s*될|신청)", a) else ["★세액공제_개념혼동"])),
    ("S3", "연금저축 해지하면 그동안 받은 세액공제 전부 다시 토해내야 하죠?",
     lambda a: ([] if "16.5" in a else ["★기타소득세16.5_누락"]) + ([] if re.search(r"세액공제를?\s*받은\s*(?:납입)?금액|세액공제\s*받은\s*금액|공제받은|운용\s*수익", a) else ["과세대상_설명누락"])
     + ([] if not re.search(r"(?:네|예|맞습니다)[,.]?\s*(?:전부|모두|다)\s*(?:토해|반환|돌려)", a) else ["★전제긍정"])),
    ("T15", "솔로몬 국공채 단기·중장기·장기, 뭐가 달라요? 안정적인 걸 원해요.",
     lambda a: ([] if re.search(r"[1-6]\s*등급", a) else ["등급_누락"]) + ([] if "대조 불가" not in a else ["대조불가_고지"])
     + ([] if len(re.findall(r"단기국공채|중장기국공채|장기국공채", a)) >= 3 else ["★3상품_누락"])
     + ([] if not re.search(r"추천\s*(?:드립니다|합니다|드리겠습니다)", a) else ["★단정추천"])),
]


def main():
    ft = open("mini65_out.txt", "w", encoding="utf-8"); bad = 0
    for qid, q, chk in Q:
        t0 = time.time()
        try:
            a, tr = _ask(qid, q)
        except Exception as e:
            a = f"(요청실패:{str(e)[:40]})"; tr = ""
        f = _common(a) + chk(a); bad += bool(f)
        print(f"  [{qid:3}] {time.time()-t0:4.1f}s  {'OK' if not f else '확인: ' + ' '.join(f)}")
        ft.write(f"\n{'='*70}\n[{qid}] {q}\n판정: {f or 'OK'}\n--- trace ---\n{tr}\n--- 답변 ---\n{a}\n"); time.sleep(0.5)
    # 멀티턴: 직전 질문 뒤 후속 질문
    t0 = time.time()
    try:
        _ask("B10a", "연금저축 세액공제 한도가 얼마예요?"); time.sleep(0.5)
        a, tr = _ask("B10b", "IRP까지 합치면요?")
    except Exception as e:
        a = f"(요청실패:{str(e)[:40]})"; tr = ""
    f = _common(a) + ([] if "900" in a else ["★멀티턴_합산900_누락"]); bad += bool(f)
    print(f"  [B10] {time.time()-t0:4.1f}s  {'OK' if not f else '확인: ' + ' '.join(f)}")
    ft.write(f"\n{'='*70}\n[B10] (멀티턴) 연금저축 세액공제 한도가 얼마예요? → IRP까지 합치면요?\n판정: {f or 'OK'}\n--- trace ---\n{tr}\n--- 답변 ---\n{a}\n")
    ft.close(); print("=" * 50); print("12문항 모두 OK" if not bad else f"확인 필요 {bad}문항 → mini65_out.txt (판정은 후보, golden_check 결과가 우선)")


if __name__ == "__main__":
    main()
