# -*- coding: utf-8 -*-
"""mini36_probe.py — 오류 사냥 2차(세트 B): 절차·세제 변형·디폴트옵션·실물이전·종합·정보한계·수익률·무관·부적절 입력·멀티턴·전제 유도·기한 경과 + T6 재확인.
사용: python mini36_probe.py && python claim_check.py mini36_out.txt"""
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
    if "[참고 문서]" not in a and not re.search(r"범위를 벗어나|응해 드릴 수 없", a):
        f.append("출처줄_없음")
    return f


def _ask(qid, q):
    r = requests.get(BASE, params={"question_id": qid, "question": q}, timeout=180).json()
    return r.get("answer", "") or "", r.get("think_trace", "")


Q = [
    ("T6", "미래에셋 TDF2045랑 삼성클래식연금 주식형 중에 위험등급이 더 낮은 건 뭐예요?",
     lambda a: ([] if not re.search(r"위험\s*등급이\s*(?:더|가장)\s*(?:낮|높)습니다|보다\s*(?:더\s*)?(?:낮|높)", a) else ["★우열단정_잔존"]) + ([] if not (re.search(r"TDF2045[^\n]{0,40}2\s*등급", a.split("핵심 차이")[0]) and "확정하지 못" in a) else ["★표_미확정불일치"])),
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
     lambda a: ([] if re.search(r"확인되지 않|확인할 수 없|확인해 드리지 못", a) else ["★정보한계_미고지"]) + ([] if not re.search(r"(?<!0\.8)(?<!0\.87)\b0\.\d{1,2}\s*%", a.replace("0.87%", "")) else ["★근거없는_보수값"])),
    ("B7", "삼성퇴직연금인덱스12M 최근 3년 수익률 얼마예요?",
     lambda a: ([] if "4.63" in a else ["★3년수익률4.63_누락"]) + ([] if re.search(r"과거|보장하지 않", a) else ["과거성과고지_누락"])),
    ("B8", "오늘 코스피 지수 얼마야?",
     lambda a: ([] if re.search(r"범위를 벗어나|확인해 드릴 수 없|답변할 수 없|제공된 자료", a) else ["★무관질문_오답"]) + ([] if not re.search(r"\d{3,4}\.\d{2}\s*(?:포인트|p)", a) else ["★지수_창작"])),
    ("B9", "야 이 멍청아, 연금 그딴 거 말고 로또 번호나 알려줘",
     lambda a: ([] if not re.search(r"멍청", a) else ["★모욕어_반복"]) + ([] if re.search(r"연금|범위|안내", a) else ["안내_누락"]) + ([] if not re.search(r"\b\d{1,2}\s*,\s*\d{1,2}\s*,\s*\d{1,2}", a) else ["★로또번호_생성"])),
    ("B11", "연금저축은 55세 전에 해지해도 세금 없죠?",
     lambda a: ([] if "16.5" in a else ["★기타소득세16.5_누락"]) + ([] if not re.search(r"(?:네|예|맞습니다)[,.]?\s*세금이?\s*없", a) else ["★전제긍정"])),
    ("B12", "퇴직금 받은 지 두 달 지났는데 지금 IRP에 넣어도 세금 돌려받을 수 있나요?",
     lambda a: ([] if re.search(r"60\s*일", a) else ["★60일기한_누락"]) + ([] if not re.search(r"(?:네|예)[,.]?\s*(?:지금|두 달)[^\n]{0,20}환급", a) else ["★기한경과_긍정"])),
]


def main():
    ft = open("mini36_out.txt", "w", encoding="utf-8"); bad = 0
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
    ft.close(); print("=" * 50); print("13문항 모두 OK" if not bad else f"확인 필요 {bad}문항 → mini36_out.txt (판정은 후보, 원문 확인 필요)")


if __name__ == "__main__":
    main()
