# -*- coding: utf-8 -*-
"""mini24_probe.py — v13.46(유의 주어·자리표시·중복 정리) 확인 5문항. 사용: python mini24_probe.py && python claim_check.py mini24_out.txt"""
import re, time, requests
BASE = "http://127.0.0.1:8000/answer"


def _blocks_ok(a):
    """상품 블록 검사: 등급 표기가 1~6 범위, '근거 문서' 줄의 문서가 [참고 문서]에 있음, 표준 유의 문장이 같은 블록에 2번 없음"""
    f = []
    body, tail = (a.split("[참고 문서]", 1) + [""])[:2]
    for m in re.finditer(r"근거 문서:\s*([^\n—]+)", body):
        for s in re.split(r",\s*", m.group(1).strip()):
            if s and s not in tail:
                f.append(f"★출처불일치:{s}")
    if re.search(r"(?<![\d.])(?:[07-9]|\d{2,})\s*등급", body):
        f.append("★등급범위밖")
    for p in body.split("\n\n"):
        if len(re.findall(r"실적배당형.{0,80}보장되지\s*않", p)) >= 3:
            f.append("유의문장_과다")
    if re.search(r"보장되지는 않는 상품은 아닙|보장되지 않는 상품은 아닙", body):
        f.append("★이중부정")
    if "아래 참고 문서—" in body or "근거 문서:아래" in body:
        f.append("★근거줄_파일명소실")
    if re.search(r"(?m)^\s*[-•]?\s*(?:증권자?투자신탁|투자신탁)은\(는\)", body):
        f.append("★주어조각")
    for m in re.finditer(r"([^\n.]{0,80})변동성이 큰 편", body):
        if re.search(r"단기채|채권\]|\(채권\)|인덱스12M", m.group(1)):
            f.append("★저위험상품_고위험문장")
    if re.search(r"(\d)\s*등급\s*및\s*\1\s*등급", body):
        f.append("★등급_중복표기")
    if re.search(r"삼성클래식[^\n]{0,40}\[채권\][^\n]{0,60}(?<![\d.])6\s*등급", body) and "인덱스12M" not in body:
        f.append("★채권형_등급오기")
    if re.search(r"이러한\s*원리금\s*보장형\s*상품들?", body) and not re.search(r"예금\s*[:：]|은행\s*(?:정기)?예금", body):
        f.append("★펀드를_원리금보장형으로")
    if re.search(r"고소득자(?:에게|일수록)?\s*(?:더욱?\s*)?유리", body):
        f.append("고소득자유리_단정")
    if "자료에서 확인 필요" in body and "근거 문서:" in body:
        f.append("등급자리표시_잔존")
    return f


Q = [
    ("M2", "좋은 연금상품 하나 추천해주세요.", _blocks_ok),
    ("M2b", "은퇴가 10년 남았는데 안정적인 연금펀드 추천해줘.", _blocks_ok),
    ("G11", "원금 손실 없이 가장 좋은 상품은요?", lambda a: _blocks_ok(a) + ([] if not re.search(r"원금\s*손실이\s*없|손실\s*없이\s*투자할 수 있는 상품(?!은)", a) else ["원금무손실_단정"])),
    ("R1", "연금상품 하나만 골라줘.", _blocks_ok),
    ("R2", "손해 안 나는 걸로 하나 추천해줘.", lambda a: _blocks_ok(a) + ([] if not re.search(r"안정성이\s*높은|손해가?\s*나지\s*않", a) else ["안정성단정"])),
]


def main():
    ft = open("mini24_out.txt", "w", encoding="utf-8"); bad = 0
    for qid, q, chk in Q:
        t0 = time.time()
        try:
            r = requests.get(BASE, params={"question_id": qid, "question": q}, timeout=180).json(); a = r.get("answer", "") or ""; tr = r.get("think_trace", "")
        except Exception as e:
            a = f"(요청실패:{str(e)[:40]})"; tr = ""
        f = chk(a); bad += bool(f)
        print(f"  [{qid:3}] {time.time()-t0:4.1f}s  {'OK' if not f else '확인: ' + ' '.join(f)}  {'렌더러 적용' if '추천 렌더러' in tr else '(렌더러 미적용)'}")
        ft.write(f"\n{'='*70}\n[{qid}] {q}\n판정: {f or 'OK'}\n--- trace ---\n{tr}\n--- 답변 ---\n{a}\n"); time.sleep(0.5)
    ft.close(); print("=" * 50); print("5문항 모두 OK → v13.46 확인 통과" if not bad else f"확인 필요 {bad}문항 → mini24_out.txt")


if __name__ == "__main__":
    main()
