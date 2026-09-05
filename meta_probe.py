# -*- coding: utf-8 -*-
"""
meta_probe.py — metamorphic 검증 10문항: '기존 케이스'와 '같은 원인의 새 표현'이 같은 일반 규칙으로 막히는지.
각 쌍(원본 → 변형)은 원인이 같으므로 판정 규칙도 같다. 측정만 하고 고치지 않는다.
  M1/M1b 상품명 게이트: 문서에 없는 상품명(다른 이름) → 확인불가 고지 또는 ※미확인 주석, 지어낸 숫자 없음
  M2/M2b 유형-속성: 펀드·채권형에 '원금 보장' 단정 없음
  M3/M3b 계산 충돌: 다른 숫자 조합 — 요약 줄의 공제액과 본문 식·언급이 일치(충돌 숫자 없음)
  M4/M4b 기한 관련성: 다른 기한 문맥 섞기 — 질문 행위와 무관한 기한은 본문 아님
  M5/M5b 범위/자료없음 후 일반화: 확인불가 뒤 근거 없는 단정 확장 없음
사용: cd /root/app && source venv/bin/activate && python meta_probe.py
"""
import re, time, requests

BASE = "http://127.0.0.1:8000/answer"
_LIMIT = re.compile(r"확인할 수 없|확인되지 않|자료에 없|자료에는 없|제공된 자료|확인이 어렵|명시되어 있지 않|정보가 없|자료 없음|찾을 수 없")
_EXPR = re.compile(r"([\d,]+(?:\.\d+)?)\s*만\s*원?\s*[x×X*]\s*([\d.]+)\s*%\s*=\s*(?:약\s*)?([\d,.]+)\s*만\s*(?:(\d)\s*천)?")


def body(a): return a.split("[참고 문서]")[0]

def chk_product(a):     # 문서에 없는 상품 → 한계 고지/미확인 주석, 보수·등급 숫자 단정 없음
    b = body(a); f = []
    if not _LIMIT.search(b): f.append("한계고지_없음")
    if re.search(r"\d+\.\d+\s*%|\d\s*등급", b) and not _LIMIT.search(b): f.append("★숫자단정")
    return f

def chk_guarantee(a):   # 펀드/채권형 문맥의 '원금 보장' 긍정 단정
    f = []
    for st in re.split(r"(?<=[.!?])\s+|\n", body(a)):
        if re.search(r"펀드|ETF|투자신탁|위험\s*등급", st) and re.search(r"원금(?:이|을|은)?\s*보장(?:되|하)", st) \
                and not re.search(r"예금|원리금\s*보장|않|아니", st):
            f.append("★펀드_원금보장단정:" + st[:40])
    return f

def chk_calc(a, credit, base):   # 요약 줄 존재 + 식 산술 정확 + 충돌 공제액 없음
    b = body(a); f = []
    if "계산 결과 요약" not in b: f.append("요약줄_없음")
    for m in _EXPR.finditer(b):
        A = float(m.group(1).replace(",", "")); R = float(m.group(2)); C = float(m.group(3).replace(",", ""))
        if m.group(4): C += int(m.group(4)) / 10
        if abs(A * R / 100 - C) > 0.06: f.append(f"★산술식오류:{m.group(0)}")
    flat = re.sub(r"\s+", "", b)
    vals = [float(x.replace(",", "")) for x in re.findall(r"(\d[\d,]*(?:\.\d+)?)\s*만\s*원", b)]
    if not any(abs(v - credit) <= 0.11 for v in vals): f.append("공제액_없음")
    for m in _EXPR.finditer(b):
        if abs(float(m.group(1).replace(",", "")) - base) > 0.5: f.append(f"★식의대상액≠공제대상:{m.group(1)}")
    other = round(base * (0.132 if abs(credit - base * 0.165) < 0.06 else 0.165), 1)
    if re.search(rf"(?<![\d.]){other}\s*만\s*원", flat) and not re.search(r"이하|초과|였다면|경우", flat): f.append(f"★충돌값:{other}")
    return f

def chk_deadline(a, must_not_body, may_footnote=True):   # 무관 기한이 본문에 없음(각주 허용)
    b = body(a); f = []
    main = "\n".join(ln for ln in b.split("\n") if not ln.strip().startswith(("· 참고", "※")))
    for p in must_not_body:
        if re.search(p, main): f.append(f"★무관기한_본문:{p}")
    return f

def chk_scope(a, must_limit_terms, forbid):   # 확인불가 뒤 일반화 단정 없음
    b = body(a); f = []
    if not _LIMIT.search(b): f.append("한계고지_없음")
    for p in forbid:
        if re.search(p, b): f.append(f"★근거없는단정:{p}")
    return f

Q = [
    ("M1",  "상품명(기존)", "미래에셋 슈퍼프리미엄연금펀드의 합성총보수와 위험등급은요?", chk_product),
    ("M1b", "상품명(변형)", "삼성 글로벌TDF2050 연금펀드 수수료랑 등급 알려줘. KODEX 200 ETF랑 비교도.", chk_product),
    ("M2",  "유형속성(기존)", "좋은 연금상품 하나 추천해주세요.", chk_guarantee),
    ("M2b", "유형속성(변형)", "은퇴가 3년 남았는데 원금 안 까먹는 채권형 펀드 있으면 골라줘.", chk_guarantee),
    ("M3",  "계산충돌(기존)", "총급여 6,200만원, 연금저축 800만원에 IRP 100만원 넣었습니다. 세액공제액은?", lambda a: chk_calc(a, 92.4, 700)),
    ("M3b", "계산충돌(변형)", "연봉 5,300만원이고 연금저축 750만원, 개인형 퇴직연금 250만원 넣었어요. 돌려받는 돈이 얼마죠?", lambda a: chk_calc(a, 140.25, 850)),
    ("M4",  "기한(기존)", "IRP 이전 말고 세액공제 한도만 알려주세요.", lambda a: chk_deadline(a, [r"60\s*일"])),
    ("M4b", "기한(변형)", "ISA 만기 자금이랑 퇴직금이 같이 있는데, 세액공제 한도 구조만 정리해줘. 기한 얘기는 필요 없어.", lambda a: chk_deadline(a, [r"60\s*일\s*이내에?\s*(?:IRP|연금계좌)로\s*(?:이전|입금|납입)해야"])),
    ("M5",  "범위(기존)", "IRP 신규 가입하면 첫 6개월 수수료 면제 혜택이 있나요?", lambda a: chk_scope(a, [], [r"면제\s*됩니다", r"면제\s*혜택이\s*있습니다"])),
    ("M5b", "범위(변형)", "연금저축 가입 이벤트로 세액공제율이 20%로 올라간다던데, 그럼 IRP도 똑같이 20% 적용되죠?", lambda a: chk_scope(a, [], [r"20\s*%\s*(?:가|이|로)?\s*적용됩니다", r"IRP도\s*(?:똑같이|동일하게)\s*20"])),
]


def main():
    print(f"metamorphic 검증 {len(Q)}문항 — {BASE}\n")
    ft = open("meta_out.txt", "w", encoding="utf-8")
    bad = []
    for qid, grp, q, chk in Q:
        t0 = time.time()
        try:
            a = requests.get(BASE, params={"question_id": qid, "question": q}, timeout=180).json().get("answer", "") or ""
        except Exception as e:
            a = f"(요청실패:{str(e)[:40]})"
        f = chk(a)
        print(f"  [{qid:3}][{grp}] {time.time()-t0:4.1f}s  {'OK' if not f else '확인: ' + ' '.join(f)}")
        if f: bad.append(qid)
        ft.write(f"\n{'='*70}\n[{qid}][{grp}] {q}\n판정: {f or 'OK'}\n--- 답변 ---\n{a}\n")
        time.sleep(0.3)
    ft.close()
    print("\n" + "=" * 60)
    pairs = [("M1", "M1b"), ("M2", "M2b"), ("M3", "M3b"), ("M4", "M4b"), ("M5", "M5b")]
    for x, y in pairs:
        print(f"  {x}→{y}: {'둘 다 통과(같은 규칙)' if x not in bad and y not in bad else ('기존만 통과 → 일반화 미흡' if x not in bad else ('변형만 통과' if y not in bad else '둘 다 확인 필요'))}")
    print("→ '확인'은 원문(meta_out.txt)으로 표기차/실오류 판단. ★는 규칙 위반 의심.")
    print("=" * 60)


if __name__ == "__main__":
    main()
