# -*- coding: utf-8 -*-
"""mini71_probe.py — 블라인드 세트(처음 보는 표현 6문항). 판정은 공통 검사(생성실패·출처줄·문장잘림·등급범위·창작 지표)만 — 원문 확인용.
사용: python mini71_probe.py"""
import re, time, requests
BASE = "http://127.0.0.1:8000/answer"


def _common(a):
    f = []
    if re.search(r"요청실패|답변 생성에 실패|429|일시적인 오류", a):
        f.append("★생성실패")
    if "[참고 문서]" not in a:
        f.append("★출처줄_없음")
    _body = a.split("[참고 문서]")[0]; _ls = [l.strip() for l in _body.split("\n") if l.strip() and not l.strip().startswith(("※", "[", "(", "|", "-"))]
    if _ls and not re.search(r"[.!?)\]”\"':]$", _ls[-1]):
        f.append("★문장_잘림")
    if re.search(r"(?<![\d.])(?:[07-9]|\d{2,})\s*등급", _body):
        f.append("★등급범위밖")
    if re.search(r"추천\s*(?:드립니다|합니다)|가장\s*(?:좋|유리)|보다\s*(?:더\s*)?(?:안전|위험|유리)합니다", _body):
        f.append("단정·권유_후보")
    if re.search(r"은\(는\)|(?<!\*)\*(?!\*)|\)\s*%", _body):
        f.append("표기_잔재")
    return f


def _ask(qid, q):
    r = requests.get(BASE, params={"question_id": qid, "question": q}, timeout=180).json()
    return r.get("answer", "") or "", r.get("think_trace", "")


Q = [
    ("N1", "연금저축 계좌 안에서 ETF 사고팔면 그때그때 세금 떼나요?"),
    ("N2", "퇴직금을 IRP로 받아뒀는데 급전이 필요해서 그냥 해지하려고요. 세금 얼마나 떼요?"),
    ("N3", "55세 넘었는데 연금으로 안 받고 한꺼번에 다 찾으면 세금이 어떻게 되나요?"),
    ("N4", "미래에셋 TDF2045 위험등급이 몇 등급이에요?"),
    ("N5", "소득이 없는 주부도 연금저축 세액공제 받을 수 있나요?"),
    ("N6", "IRP 계좌 수수료는 얼마예요?"),
]


def main():
    ft = open("mini71_out.txt", "w", encoding="utf-8"); bad = 0
    for qid, q in Q:
        t0 = time.time()
        try:
            a, tr = _ask(qid, q)
        except Exception as e:
            a = f"(요청실패:{str(e)[:40]})"; tr = ""
        f = _common(a); bad += bool(f)
        print(f"  [{qid:3}] {time.time()-t0:4.1f}s  {'OK' if not f else '확인: ' + ' '.join(f)}")
        ft.write(f"\n{'='*70}\n[{qid}] {q}\n판정: {f or 'OK'}\n--- trace ---\n{tr}\n--- 답변 ---\n{a}\n"); time.sleep(0.5)
    ft.close(); print("=" * 50); print("6문항 공통검사 OK" if not bad else f"확인 필요 {bad}문항 → mini71_out.txt (원문 확인)")


if __name__ == "__main__":
    main()
