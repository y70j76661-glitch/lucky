# -*- coding: utf-8 -*-
"""mini40_probe.py — v13.63 재확인(T11·C6·C9·C10·S1·S3) + 새 2문항(S4 IRP 내 ETF 매매 과세, S5 납입한도 1,800 vs 공제한도 900). 8문항.
사용: python mini40_probe.py && python claim_check.py mini40_out.txt"""
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
     + ([] if not re.search(r"차이나리치투게더[^\n]*\n[^\n]*근거 문서: R2_KR516702010M\.pdf — 위험등급 \d", a) else ["★타상품_설명서_등급귀속"])),
    ("C6", "저 연금 얼마 받을 수 있어요?",
     lambda a: ([] if re.search(r"계산할 수 없습니다|알려\s*주시면", a[:300]) else ["★역질문/한계고지_누락"])
     + ([] if not re.search(r"소득세|과세|세율", a.split("[참고 문서]")[0]) else ["무관세제_잔존"])),
    ("C9", "연금저축이랑 IRP 둘 다 있는데 세액공제 받으려면 어디에 먼저 넣는 게 유리해요?",
     lambda a: ([] if "600" in a and "900" in a else ["★한도구조_누락"]) + ([] if not re.search(r"먼저\s*최대\s*900", a) else ["★IRP먼저900_잔존"])
     + ([] if "문서과 아래 참고" not in a else ["★출처흉터_잔존"]) + ([] if not re.search(r"(?:IRP|연금저축)에\s*(?:집중\s*)?투자", a) else ["★계좌_투자_혼동"])),
    ("C10", "미래에셋 TDF2030이랑 TDF2050 중에 뭐가 더 위험해요?",
     lambda a: ([] if not re.search(r"(?:높은|낮은|매우\s*낮은|매우\s*높은)\s*위험\s*등급을\s*가지", a) else ["★라벨단정_잔존"])
     + ([] if not re.search(r"보다\s*(?:더\s*)?(?:위험|안전|낮|높)습니다", a) else ["★우열단정"])
     + ([] if "우열을 확정할 수 없" in a or "등급 비교(근거 문서 기준)" in a else ["★코드결론_없음"])
     + ([] if not re.search(r"위험\s*등급\s*[:：][^\n]*(?<![\d.])[1-6]\s*등급", a) or "등급 비교(근거 문서 기준)" in a else ["★미확정_등급값_잔존"])),
    ("S1", "DB형이랑 DC형 차이가 뭐예요?",
     lambda a: ([] if re.search(r"확정급여|DB", a) and re.search(r"확정기여|DC", a) else ["★DB/DC_누락"]) + ([] if not re.search(r"(?:퇴직금|연금)(?:을|를)?\s*보장해", a) else ["★DB_보장과장_잔존"])),
    ("S3", "연금저축 해지하면 그동안 받은 세액공제 전부 다시 토해내야 하죠?",
     lambda a: ([] if "16.5" in a else ["★기타소득세16.5_누락"]) + ([] if "철회" not in a else ["★해석문장_잔존"])
     + ([] if not re.search(r"(?:네|예|맞습니다)[,.]?\s*(?:전부|모두|다)\s*(?:토해|반환|돌려)", a) else ["★전제긍정"])),
    ("S4", "IRP 계좌에서 ETF 사고팔면 양도소득세나 배당소득세 내나요?",
     lambda a: ([] if re.search(r"과세\s*이연|이연|인출|수령\s*(?:시|할\s*때)", a) else ["★과세이연_누락"]) + ([] if not re.search(r"(?:양도소득세|배당소득세)(?:를|가)?\s*(?:내야|납부해야|부과됩니다)", a) else ["★즉시과세_오답(원문 확인)"])),
    ("S5", "연금저축이랑 IRP 합쳐서 1년에 최대 얼마까지 넣을 수 있어요?",
     lambda a: ([] if re.search(r"1,?800\s*만", a) else ["★납입한도1800_누락"]) + ([] if not re.search(r"(?:최대|까지)\s*900\s*만\s*원(?:까지)?\s*(?:넣|납입할\s*수)", a) else ["★납입한도를_900으로_오답"])),
]


def main():
    ft = open("mini40_out.txt", "w", encoding="utf-8"); bad = 0
    for qid, q, chk in Q:
        t0 = time.time()
        try:
            a, tr = _ask(qid, q)
        except Exception as e:
            a = f"(요청실패:{str(e)[:40]})"; tr = ""
        f = _common(a) + chk(a); bad += bool(f)
        print(f"  [{qid:3}] {time.time()-t0:4.1f}s  {'OK' if not f else '확인: ' + ' '.join(f)}")
        ft.write(f"\n{'='*70}\n[{qid}] {q}\n판정: {f or 'OK'}\n--- trace ---\n{tr}\n--- 답변 ---\n{a}\n"); time.sleep(0.5)
    ft.close(); print("=" * 50); print("8문항 모두 OK" if not bad else f"확인 필요 {bad}문항 → mini40_out.txt (판정은 후보, 원문 확인 필요)")


if __name__ == "__main__":
    main()
