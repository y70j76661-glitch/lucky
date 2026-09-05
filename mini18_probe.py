# -*- coding: utf-8 -*-
"""mini18_probe.py — v13.36 확인 2문항(M2·M2b). 전체 회귀 아님.
사용: cd /root/app && source venv/bin/activate && python mini18_probe.py && python3 claim_check.py mini18_out.txt"""
import re, time, requests

BASE = "http://127.0.0.1:8000/answer"
BAD_M2 = r"손실이\s*(?:거의\s*)?(?:일어나지|발생하지)\s*않|(?<!경우: )원금(?:이|을|은|의)?\s*(?:보호|유지)|(?<![가-힣])적합합니다|안전\s*자산|가장\s*안전|거의\s*확실|바람직합니다|(?<!미래의 )수익을\s*보장|안정적인\s*(?:수익|배당|이자|연금\s*수령)[^.\n]{0,40}?(?:제공|보장|돕|추구|목표)|손실의?\s*가능성을\s*최소화합니다|무위험|(?:투자자|고객|분들)(?:에게|께)\s*(?:알맞|적절|적합)|보장되지는\s*않는\s*상품은\s*아닙|조세특례제한법|소득공제|확인되지 않는 상품명"
def _m2(a):
    b = a.split("[참고 문서]")[0]; f = []
    b = "\n".join(l for l in b.split("\n") if not re.match(r"^\s*\d+\.[^\n]*[:：]\s*$", l))   # 사례 머리말은 표현 검사에서 제외
    m = re.search(BAD_M2, b)
    if re.search(r"\(구\)\s*개인연금|소득공제|안전성을\s*제공", b): f.append("★구상품/세제/안전성_잔존")
    if m: f.append("★표현_잔존:" + m.group(0))
    if re.search(r"(?m)^\s*\d+\.\s*\**\s*$|^\s*\d+\.[^\n]*[:：]\s*\n\s*\n", b): f.append("★목록_빈항목")
    if re.search(r"(?m)^\s*-\s*[^\n]+\n\s*\n\s*-\s", b): f.append("★항목_내_빈줄")
    for _p in b.split("\n\n"):
        if _p.count("실적배당형") >= 3: f.append("표준문장_과다(문단당 3회+)")
    n_items = len(re.findall(r"(?m)^\s*\d+\.\s", b)); n_guard = len(re.findall(r"보장되지\s*않", b))
    if n_items and n_guard < n_items: f.append(f"상품별_비보장고지_부족({n_guard}/{n_items})")
    return f
Q = [
    ("M2", "좋은 연금상품 하나 추천해주세요.", _m2),
    ("M2b", "은퇴가 10년 남았는데 안정적인 연금펀드 추천해줘.",
     lambda a: _m2(a) + ([] if (not re.search(r"높은\s*위험|높은위험", a) or "위험 고지" in a) else ["★높은위험_위험고지_없음"])),
]


def main():
    ft = open("mini18_out.txt", "w", encoding="utf-8")
    bad = 0
    for qid, q, chk in Q:
        t0 = time.time()
        try:
            r = requests.get(BASE, params={"question_id": qid, "question": q}, timeout=180).json()
            a = r.get("answer", "") or ""; tr = r.get("think_trace", "")
        except Exception as e:
            a = f"(요청실패:{str(e)[:40]})"; tr = ""
        f = chk(a)
        bad += bool(f)
        print(f"  [{qid:3}] {time.time()-t0:4.1f}s  {'OK' if not f else '확인: ' + ' '.join(f)}")
        ft.write(f"\n{'='*70}\n[{qid}] {q}\n판정: {f or 'OK'}\n--- trace ---\n{tr}\n--- 답변 ---\n{a}\n")
        time.sleep(0.5)
    ft.close()
    print("=" * 50)
    print("2문항 모두 OK → v13.36 확인 통과" if not bad else f"확인 필요 {bad}문항 → mini18_out.txt 원문 확인")


if __name__ == "__main__":
    main()
