# -*- coding: utf-8 -*-
"""
output_quality_probe.py — [4단계] 출력품질 전수 감사.
20 골든 답변에서 '확실한 형식 결함'만 자동 점검한다(내용 판단 아님).
  · 빈불릿(내용 없는 마커)   · 볼드 '**' 잔재   · 백슬래시
  · 본문 문서명 노출(‘[참고 문서]’ 영역 제외)   · 따옴표 짝 불균형   · 괄호 짝 불균형   · 빈 괄호
사용: cd /root/app && source venv/bin/activate && python output_quality_probe.py
결과: 결함 있는 문항만 나열 → 실제 결함이면 그 유형만 결정적으로 고친다.
"""
import re, time, requests

BASE = "http://127.0.0.1:8000/answer"
Q = [
    ("G01","IRP를 중도해지하면 세금이 어떻게 되나요?"),
    ("G02","퇴직금을 IRP로 이전하면 세금 혜택이 있나요?"),
    ("G03","퇴직금을 IRP로 옮길 때 언제까지 해야 하나요?"),
    ("G04","연금저축과 IRP 세액공제 한도는 얼마인가요?"),
    ("G05","세액공제 최대 금액만 알려주세요."),
    ("G06","연금 수령 나이는 몇 살인가요?"),
    ("G07","연금수령 나이는 묻지 않고 세액공제만 알려주세요."),
    ("G08","회사가 넣어준 DC 부담금도 공제되나요?"),
    ("G09","확정급여형(DB)과 확정기여형(DC)의 차이는 무엇인가요?"),
    ("G10","좋은 연금상품 하나 추천해주세요."),
    ("G11","원금 손실 없이 가장 좋은 상품은요?"),
    ("G12","명예퇴직금을 연금계좌에 넣으면 절세할 수 있나요?"),
    ("V01","퇴직금을 IRP로 옮기면 언제까지 해야 하나요?"),
    ("V02","퇴직금 IRP 입금 기한 알려줘"),
    ("N01","IRP로 이전하지 않고 중도해지하면 세금이 어떻게 되나요?"),
    ("N02","IRP 이전 말고 세액공제 한도만 알려주세요."),
    ("F01","IRP는 원금이 보장되죠?"),
    ("F02","세액공제는 납입액 전부를 돌려받는 거죠?"),
    ("F03","60일이 지나면 무조건 혜택을 못 받죠?"),
    ("P01","또박또박연금펀드의 합성총보수와 위험등급을 알려주세요."),
]
_EMPTYBUL = re.compile(r"(?m)^\s*(?:[-*•]|\d+[.)])\s*$")
_FNAME = re.compile(r"(?:doc\d+|R\d+_[A-Za-z0-9]+)\.(?:pdf|xlsx|docx|hwp|pptx|txt)", re.I)


def defects(ans):
    d = []
    body = ans.split("[참고 문서]")[0]          # 본문만(출처 영역 제외)
    if _EMPTYBUL.search(ans): d.append("빈불릿")
    if "**" in ans: d.append("볼드잔재")
    if "\\" in ans: d.append("백슬래시")
    if _FNAME.search(body): d.append("본문문서명")
    for q in ("'", '"'):
        if body.count(q) % 2: d.append(f"따옴표홀수({q})")
    if body.count("(") != body.count(")"): d.append("괄호불균형")
    if re.search(r"[(\[]\s*[)\]]", body): d.append("빈괄호")
    return d


def main():
    print(f"출력품질 감사 {len(Q)}문항 — {BASE}\n")
    flagged = []
    for qid, q in Q:
        try:
            r = requests.get(BASE, params={"question_id": qid, "question": q}, timeout=180)
            a = r.json().get("answer", "") or ""
        except Exception as e:
            a = f"(요청실패:{str(e)[:40]})"
        d = defects(a)
        print(f"  [{qid}] {'OK' if not d else ' '.join(d)}")
        if d: flagged.append((qid, d, a))
        time.sleep(0.3)
    print("\n" + "=" * 60)
    if flagged:
        print(f"형식 결함 {len(flagged)}문항:")
        for qid, d, a in flagged:
            print(f"  [{qid}] {d}")
        # 결함 원문 일부 저장
        with open("oq_out.txt", "w", encoding="utf-8") as f:
            for qid, d, a in flagged:
                f.write(f"\n{'='*60}\n[{qid}] 결함={d}\n{a}\n")
        print("결함 원문: oq_out.txt")
    else:
        print("형식 결함 0 → 출력품질 통과(4단계 확인 완료)")
    print("=" * 60)


if __name__ == "__main__":
    main()
