# -*- coding: utf-8 -*-
"""
product_neg_probe.py — [미검증 영역 2·3 측정 전용] 상품설명 스트레스 6문항 + 부정·제외 변형 4문항.
측정만 하고 고치지 않는다. 플래그는 '원문 확인 필요' 표시이지 오류 확정이 아니다.
  상품(S): 클래스별 보수 기준 명시 / 유사 이름 상품 등급 뒤바뀜 / 자료 없는 속성의 한계 고지 / 우열 단정
  부정(N): '~는 됐고', '~넘어가고', '~말고', '~빼고' 표현에서 제외 요청한 카드·내용이 안 붙는지
사용: cd /root/app && source venv/bin/activate && python product_neg_probe.py
"""
import re, time, requests

BASE = "http://127.0.0.1:8000/answer"
_LIMIT = re.compile(r"확인할 수 없|확인되지 않|자료에 없|자료에는 없|제공된 자료|확인이 어렵|명시되어 있지 않|정보가 없|자료 없음")
_NUM = re.compile(r"\d+(?:\.\d+)?\s*(?:%|만원|억|원|등급)")


def near(text, a, b, win=40):
    """a 등장 위치 앞뒤 win자 안에 b가 있는지"""
    for m in re.finditer(re.escape(a), text):
        if b in text[max(0, m.start() - win): m.end() + win]:
            return True
    return False


def chk_S1(a):   # 클래스별 총보수: 숫자가 나오면 클래스 표기가 함께 있어야
    f = []
    pct = re.findall(r"\d+\.\d+\s*%", a)
    if pct and not re.search(r"클래스|C-P|C-Pe|A-e|S|종류", a): f.append("보수숫자에_클래스기준없음")
    if not pct and not _LIMIT.search(a): f.append("보수도_한계고지도_없음")
    return f

def chk_S2(a):   # 주식형 2등급 / 채권형 5등급 — 뒤바뀜 감지
    f = []
    if not re.search(r"2\s*등급", a): f.append("주식형2등급_없음")
    if not re.search(r"5\s*등급", a): f.append("채권형5등급_없음")
    def first_grade_after(kw):
        m = re.search(re.escape(kw) + r"[^\n]{0,60}?(\d)\s*등급", a)
        return m.group(1) if m else None
    g_stock, g_bond = first_grade_after("주식"), first_grade_after("채권")
    if g_stock and g_stock != "2": f.append(f"★주식형_바로뒤등급={g_stock}")
    if g_bond and g_bond != "5": f.append(f"★채권형_바로뒤등급={g_bond}")
    return f

def chk_S3(a):   # 인덱스12M 채권: 6등급, 보수는 숫자 또는 한계 고지
    f = []
    if not re.search(r"6\s*등급", a): f.append("6등급_없음")
    if not re.search(r"\d+\.\d+\s*%", a) and not _LIMIT.search(a): f.append("보수_숫자도_한계도_없음")
    return f

def chk_limit_or_grounded(a):   # 문서에 없을 가능성이 큰 속성: 숫자 단정이면 확인 필요
    body = a.split("[참고 문서]")[0]
    nums = _NUM.findall(body)
    if nums and not _LIMIT.search(body): return [f"숫자단정_한계없음{nums[:3]}"]
    return []

def chk_S6(a):   # 우열 단정 금지(같은 기준 근거 없으면)
    f = []
    if re.search(r"더\s*(?:저렴|싸|유리)(?:합니다|하다|함)", a) and not re.search(r"같은\s*(?:기준|클래스)|동일\s*(?:기준|클래스)", a):
        f.append("우열단정_기준없음")
    return f

def chk_N_no(a, pats, must):
    f = []
    for p in pats:
        if re.search(p, a): f.append(f"제외요청내용_포함:{p}")
    for m in must:
        if not re.search(m, a): f.append(f"필수_없음:{m}")
    return f

Q = [
    ("S1", "상품", "또박또박연금펀드의 클래스별 총보수를 알려주세요.", chk_S1),
    ("S2", "상품", "삼성클래식연금 주식형과 채권형의 위험등급은 각각 몇 등급인가요?", chk_S2),
    ("S3", "상품", "삼성퇴직연금인덱스12M 채권 펀드의 위험등급과 총보수를 알려주세요.", chk_S3),
    ("S4", "상품", "미래에셋 TDF 2030과 TDF 2050의 차이점과 각각의 총보수는요?", chk_limit_or_grounded),
    ("S5", "상품", "또박또박연금펀드의 최근 1년 수익률과 설정액은 얼마인가요?", chk_limit_or_grounded),
    ("S6", "상품", "또박또박연금펀드 C-P2와 삼성클래식연금 채권형 중 총보수가 더 싼 건 뭔가요?", chk_S6),
    ("N3", "부정", "IRP 이전 얘기는 됐고, 세액공제 한도만 알려줘.",
     lambda a: chk_N_no(a, [r"60\s*일", r"이전\s*기한"], [r"600", r"900"])),
    ("N4", "부정", "연금 수령 나이는 넘어가고 세액공제만 설명해줘.",
     lambda a: chk_N_no(a, [r"연금수령 요건 — 문서 기준", r"만\s*55세"], [r"세액공제"])),
    ("N5", "부정", "회사 부담금 말고 내가 낸 돈만 기준으로 세액공제 한도 알려줘.",
     lambda a: chk_N_no(a, [], [r"600", r"900"])),
    ("N6", "부정", "중도해지 세금은 빼고, 연금으로 받을 때 세금만 알려줘.",
     lambda a: chk_N_no(a, [r"기타소득세\s*16\.5"], [r"연금소득세|3\.3|5\.5"])),
]


def main():
    print(f"상품설명·부정변형 측정 {len(Q)}문항 — {BASE}\n")
    ft = open("product_neg_out.txt", "w", encoding="utf-8")
    flagged = []
    for qid, grp, q, chk in Q:
        t0 = time.time()
        try:
            a = requests.get(BASE, params={"question_id": qid, "question": q}, timeout=180).json().get("answer", "") or ""
        except Exception as e:
            a = f"(요청실패:{str(e)[:40]})"
        dt = time.time() - t0
        f = chk(a)
        print(f"  [{qid}][{grp}] {dt:4.1f}s  {'OK' if not f else '확인: ' + ' '.join(f)}")
        if f: flagged.append((qid, f))
        ft.write(f"\n{'='*70}\n[{qid}][{grp}] {q}\n판정: {f or 'OK'}\n--- 답변 ---\n{a}\n")
        time.sleep(0.3)
    ft.close()
    print("\n" + "=" * 60)
    if flagged:
        print(f"확인 필요 {len(flagged)}문항 → product_neg_out.txt 원문으로 표기차/실오류 판단 (★는 등급 뒤바뀜 의심)")
    else:
        print("10문항 모두 OK → 상품설명·부정변형 영역 통과")
    print("=" * 60)


if __name__ == "__main__":
    main()
