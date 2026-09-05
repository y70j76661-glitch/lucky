# -*- coding: utf-8 -*-
"""mini39_probe.py — v13.62 재확인(T6·T11·B12·C6·C9·C10) + 과제 샘플형 3문항(S1 DB/DC 차이, S2 명퇴 교사 절세, S3 해지 시 세액공제 반환 전제). 9문항.
사용: python mini39_probe.py && python claim_check.py mini39_out.txt"""
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
    ("T6", "미래에셋 TDF2045랑 삼성클래식연금 주식형 중에 위험등급이 더 낮은 건 뭐예요?",
     lambda a: ([] if not re.search(r"위험\s*등급이\s*(?:더|가장)\s*(?:낮|높)습니다|보다\s*(?:더\s*)?(?:낮|높)습니다|보다\s*(?:더\s*)?(?:안정적|안전|공격적)", a) else ["★우열단정_잔존"])
     + ([] if "우열을 확정할 수 없" in a or "등급 비교(근거 문서 기준)" in a else ["★코드결론_없음"])
     + ([] if "2등급" in a else ["★삼성2등급_유실(회귀)"])),
    ("T11", "30대 직장인인데 공격적으로 굴릴 연금펀드 하나 추천해줘",
     lambda a: ([] if not re.search(r"추천\s*(?:드립니다|합니다|드리겠습니다)", a) else ["★단정추천_잔존"])
     + ([] if not re.search(r"수상|최우수|인정받|1위", a) else ["★판촉문장_잔존"])),
    ("B12", "퇴직금 받은 지 두 달 지났는데 지금 IRP에 넣어도 세금 돌려받을 수 있나요?",
     lambda a: ([] if re.search(r"60\s*일", a) else ["★60일기한_누락"])
     + ([] if not re.search(r"세액공제\s*(?:혜택|대상이\s*될|대상이\s*됩|조건|신청)", a) else ["★세액공제_개념혼동"])
     + ([] if not re.search(r"두\s*달[^\n]{0,14}(?:지난|지났|지나)[^\n]{0,40}(?:어렵|있습니다|가능)", a.replace("'두 달' 표현만으로는", "")) else ["★두달_경과단정_잔존"])
     + ([] if re.search(r"^(?:\(요청실패|문의하신 경과 기간|'두 달' 표현)", a) else ["판정문장_선두아님"])),
    ("C6", "저 연금 얼마 받을 수 있어요?",
     lambda a: ([] if re.search(r"계산할 수 없습니다|알려\s*주시면", a[:300]) else ["★역질문/한계고지_누락"])
     + ([] if not re.search(r"소득세|과세|세율", a.split("[참고 문서]")[0]) else ["무관세제_잔존"])),
    ("C9", "연금저축이랑 IRP 둘 다 있는데 세액공제 받으려면 어디에 먼저 넣는 게 유리해요?",
     lambda a: ([] if "600" in a and "900" in a else ["★한도구조_누락"]) + ([] if not re.search(r"먼저\s*최대\s*900", a) else ["★IRP먼저900_잔존"])
     + ([] if not re.search(r"IRP(?:는|은)\s*[^\n]{0,25}?(?:투자비율|변동성)", a) else ["★계좌를_자산처럼_서술"])),
    ("C10", "미래에셋 TDF2030이랑 TDF2050 중에 뭐가 더 위험해요?",
     lambda a: ([] if not re.search(r"(?:높은|낮은|매우\s*낮은|매우\s*높은)\s*위험\s*등급을\s*가지", a) else ["★라벨단정_잔존"])
     + ([] if not re.search(r"보다\s*(?:더\s*)?(?:위험|안전|낮|높)습니다", a) else ["★우열단정"])
     + ([] if "우열을 확정할 수 없" in a or "등급 비교(근거 문서 기준)" in a or "자료에서 확정하지 못함" in a else ["코드결론/미확정표시_없음(원문 확인)"])),
    ("S1", "DB형이랑 DC형 차이가 뭐예요?",
     lambda a: ([] if re.search(r"확정급여|DB", a) and re.search(r"확정기여|DC", a) else ["★DB/DC_누락"]) + ([] if re.search(r"회사|사용자|기업", a) and re.search(r"근로자|본인|가입자", a) else ["운용주체_설명누락"])),
    ("S2", "명예퇴직한 교사인데 퇴직금 세금 줄이려면 어떻게 해야 해요?",
     lambda a: ([] if "IRP" in a or "연금계좌" in a else ["★IRP이전_누락"]) + ([] if re.search(r"30\s*%|감면|연금으로\s*수령|연금\s*수령", a) else ["★연금수령감면_누락"])
     + ([] if not re.search(r"세액공제\s*(?:혜택|대상이\s*될|신청)", a) else ["★세액공제_개념혼동"])),
    ("S3", "연금저축 해지하면 그동안 받은 세액공제 전부 다시 토해내야 하죠?",
     lambda a: ([] if "16.5" in a else ["★기타소득세16.5_누락"]) + ([] if re.search(r"세액공제를?\s*받은\s*(?:납입)?금액|세액공제\s*받은\s*금액|공제받은|운용\s*수익", a) else ["과세대상_설명누락"])
     + ([] if not re.search(r"(?:네|예|맞습니다)[,.]?\s*(?:전부|모두|다)\s*(?:토해|반환|돌려)", a) else ["★전제긍정"])),
]


def main():
    ft = open("mini39_out.txt", "w", encoding="utf-8"); bad = 0
    for qid, q, chk in Q:
        t0 = time.time()
        try:
            a, tr = _ask(qid, q)
        except Exception as e:
            a = f"(요청실패:{str(e)[:40]})"; tr = ""
        f = _common(a) + chk(a); bad += bool(f)
        print(f"  [{qid:3}] {time.time()-t0:4.1f}s  {'OK' if not f else '확인: ' + ' '.join(f)}")
        ft.write(f"\n{'='*70}\n[{qid}] {q}\n판정: {f or 'OK'}\n--- trace ---\n{tr}\n--- 답변 ---\n{a}\n"); time.sleep(0.5)
    ft.close(); print("=" * 50); print("9문항 모두 OK" if not bad else f"확인 필요 {bad}문항 → mini39_out.txt (판정은 후보, 원문 확인 필요)")


if __name__ == "__main__":
    main()
