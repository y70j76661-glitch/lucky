# -*- coding: utf-8 -*-
"""
audit_ingest.py — 문서 온보딩 숫자 정합성 검수 (실서비스용, 재사용)

새 문서를 색인(chunks.json)에 넣기 전/후에 돌려, 문서 안의 숫자가 서로
어긋나는 곳을 자동으로 찾아 '사람 검수 리스트'로 뽑아준다. 자동으로
고치지 않는다 — 후보만 제시하고, 최종 판단은 사람이 한다(2차 환각 방지).

검사 4종
  A) 명시적 계산식 검산 : 'A(=B × C)' 처럼 문서가 스스로 쓴 산식을 실제
       계산과 대조.                       예) 148만 5천만원(=900만원 × 16.5%)
  B) 비율×금액 검산     : 한 문장에 'P%'와 '결과 금액', '기준 금액'이 함께
       나오면 기준×P% ≈ 결과 인지 검산.   예) (기준)×30% = 절세액 7만 9,200원
  C) 배분 합계 검산     : '인컴형 60% / 성장형 30% / 안정형 10%' 같은 배분·
       구성 비율의 합이 100%인지.
  D) 한글 단위 이상     : '만' 뒤에 더 큰 단위(천만·백만·억)가 오는 뒤죽박죽
       표기 탐지.                         예) 148만 5천만원, 26만 4천만원
                                          (우리가 수기로 찾은 두 오류가 이 형태)

입력 우선순위
  1) chunks.json  (서버 색인 — 실제 대상)      : [{"source":..., "text":...}, ...]
  2) 없으면 reocr/*.txt (로컬 개발용 폴백)

출력
  - ingest_review.json : 기계용(검수 큐/교정테이블 연동)
  - 콘솔 리포트         : 사람이 바로 읽는 요약 + 상위 항목
  - NUMBER_NOTES 스텁   : 검수 확정 시 main.py 교정테이블에 붙일 초안

사용법
  python3 audit_ingest.py
"""
import glob
import json
import os
import re
import sys

# 오차 허용(비율 검산). 반올림·표기 차이를 흡수.
REL_TOL = 0.01      # 1% 상대오차
ABS_TOL = 1.0       # 절대오차(원 단위)

# ─────────────────────────────────────────────────────────────────────────
# 한글 금액 파서
# ─────────────────────────────────────────────────────────────────────────
_UNIT = {"조": 10 ** 12, "억": 10 ** 8, "만": 10 ** 4,
         "천": 10 ** 3, "백": 10 ** 2, "십": 10}
# 큰 단위부터. '천만/백만/천억' 같은 복합 단위도 인식하기 위해 정렬.
_UNIT_SEQ = ["조", "천억", "백억", "십억", "억", "천만", "백만", "십만",
             "만", "천", "백", "십"]
_UNIT_VAL = {
    "조": 10 ** 12, "천억": 10 ** 11, "백억": 10 ** 10, "십억": 10 ** 9,
    "억": 10 ** 8, "천만": 10 ** 7, "백만": 10 ** 6, "십만": 10 ** 5,
    "만": 10 ** 4, "천": 10 ** 3, "백": 10 ** 2, "십": 10,
}


def _to_num(s):
    """'900만', '148만 5천', '1,485,000', '16.5' → 숫자. 실패 시 None."""
    if s is None:
        return None
    s = s.strip()
    # 순수 아라비아 숫자(콤마 포함)
    if re.fullmatch(r"[\d,]+(?:\.\d+)?", s):
        try:
            return float(s.replace(",", ""))
        except ValueError:
            return None
    # 한글 단위 섞임: '148만 5천', '900만', '3억 5천만'
    total = 0.0
    matched = False
    # '숫자+단위' 토큰을 왼→오로 훑되, 마지막에 단위 없는 숫자는 그대로 더함
    for m in re.finditer(r"([\d,]+(?:\.\d+)?)\s*(조|억|만|천|백|십)?", s):
        digits, unit = m.group(1), m.group(2)
        if digits == "":
            continue
        try:
            v = float(digits.replace(",", ""))
        except ValueError:
            continue
        total += v * (_UNIT.get(unit, 1) if unit else 1)
        matched = True
    return total if matched else None


# ─────────────────────────────────────────────────────────────────────────
# D) 한글 단위 이상 탐지 — '만' 뒤에 더 큰 단위(천만/백만/억)
# ─────────────────────────────────────────────────────────────────────────
# 예) 148만 5천만원 / 26만 4천만원 / 3만 2억
_UNIT_RANK = {"십": 1, "백": 2, "천": 3, "만": 4, "십만": 5, "백만": 6,
              "천만": 7, "억": 8, "십억": 9, "백억": 10, "천억": 11, "조": 12}
# '만' 다음에 '천만/백만/억' 이상이 오는 구조(단위 단조감소 위배)
_D_MALFORMED = re.compile(
    r"\d+\s*만\s*\d+\s*(?:천만|백만|십만|억|조)\s*원?"
)


def check_unit_malformed(text):
    out = []
    for m in _D_MALFORMED.finditer(text):
        out.append(m.group(0))
    return out


# ─────────────────────────────────────────────────────────────────────────
# 금액 토큰 — '900만원', '148만 5천원'(공백·복수 단위), '1,485,000원' 모두 인식
# ─────────────────────────────────────────────────────────────────────────
_AMT = r"(?:[\d,]+\s*(?:조|억|만|천|백|십)\s*)+[\d,]*\s*원|[\d,]+\s*원"

# ─────────────────────────────────────────────────────────────────────────
# A) 명시적 계산식 검산 — 'A(=B 연산 C ...)'
# ─────────────────────────────────────────────────────────────────────────
# 값 바로 뒤 괄호 안에 산식이 있는 경우. 연산자: ×,x,X,*
_A_FORMULA = re.compile(
    r"(" + _AMT + r")"                            # 결과값 A(원 단위)
    r"\s*[\(（]\s*=?\s*"                           # (  또는 (=
    r"([^)）]+?)"                                  # 산식 본문
    r"\s*[\)）]"
)
_OP_SPLIT = re.compile(r"\s*[×xX*]\s*")


def _eval_simple(expr):
    """'900만원 × 16.5%' → 900만 × 0.165. 곱셈(×)만 안전 계산."""
    parts = _OP_SPLIT.split(expr)
    if len(parts) < 2:
        return None
    acc = 1.0
    got = 0
    for p in parts:
        p = p.strip()
        pct = "%" in p or "퍼센트" in p
        val = _to_num(re.sub(r"[%원퍼센트\s]", "", p))
        if val is None:
            return None
        acc *= (val / 100.0) if pct else val
        got += 1
    return acc if got >= 2 else None


def check_explicit_formula(text):
    out = []
    for m in _A_FORMULA.finditer(text):
        a_raw, expr = m.group(1), m.group(2)
        if not re.search(r"[×xX*]", expr):      # 곱셈식만 대상(가장 신뢰)
            continue
        a_val = _to_num(re.sub(r"[원\s]", "", a_raw))
        calc = _eval_simple(expr)
        if a_val is None or calc is None:
            continue
        if abs(a_val - calc) > max(ABS_TOL, calc * REL_TOL):
            out.append({
                "stated": a_raw.strip(),
                "stated_val": a_val,
                "formula": expr.strip(),
                "calc_val": round(calc, 2),
                "diff": round(abs(a_val - calc), 2),
            })
    return out


# ─────────────────────────────────────────────────────────────────────────
# B) 비율×금액 검산 — '기준금액 (의) P% (인/에 해당하는) 결과금액'이 붙어 있을 때만
#    (느슨하게 '문장에 %와 금액'만 보면 오탐이 폭증 → 명시적 관계 패턴만 잡는다)
# ─────────────────────────────────────────────────────────────────────────
_AMOUNT = re.compile(_AMT)
_PCT = re.compile(r"(\d+(?:\.\d+)?)\s*%")
# 기준금액 … 의/에서 … P% … (인|에 해당하는|상당|는|가) … 결과금액
_B_REL = re.compile(
    r"(" + _AMT + r")"                                  # 1) 기준 금액
    r"\s*(?:의|에서|중)?\s*"
    r"(\d+(?:\.\d+)?)\s*%"                              # 2) 비율
    r"\s*(?:인|에\s*해당(?:하는|되는)?|상당(?:액)?[은는이가]?|는|가|=|:)?\s*"
    r"[^\d\n]{0,12}?"                                   # 결과 라벨(절세액 등) 허용
    r"(" + _AMT + r")"                                  # 3) 결과 금액
)


def check_ratio_amount(text):
    out = []
    for m in _B_REL.finditer(text):
        base = _to_num(re.sub(r"[원\s]", "", m.group(1)))
        p = float(m.group(2)) / 100.0
        result = _to_num(re.sub(r"[원\s]", "", m.group(3)))
        if base is None or result is None or base <= 0:
            continue
        if base == result:                              # 같은 값 반복은 관계식 아님
            continue
        expect = base * p
        # 결과가 기준의 P%라야. 오차 2%(반올림·표기차) 초과면 후보.
        if abs(expect - result) > max(ABS_TOL, expect * 0.02):
            out.append({
                "snippet": m.group(0).strip()[:100],
                "base": base, "pct": m.group(2) + "%",
                "stated_result": result, "expected_result": round(expect, 2),
                "diff": round(abs(expect - result), 2),
            })
    return out


# ─────────────────────────────────────────────────────────────────────────
# C) 배분 합계 검산 — 'A 60% / B 30% / C 10%' 또는 'A 75% + B 25%'
# ─────────────────────────────────────────────────────────────────────────
_ALLOC_LINE = re.compile(r"(비중|배분|포트폴리오|구성|인컴형|성장형|안정형|주식|채권)")
_RANGE = re.compile(r"\d+\s*%\s*[~〜–—-]\s*\d+\s*%")   # '50%~20%' 범위는 제외
# 한도·예시·조건 문맥은 100% 배분표가 아니므로 제외(오탐 억제).
#   v2: 실측(158문서) 오탐 패턴 반영 — 투자설명서 비용예시('연간 수익률 5%로
#   가정… 총보수비용'), 벤치마크(비교지수), 상위 보유종목 비중, 상품 나열은
#   배분표가 아니다.
_ALLOC_SKIP = re.compile(
    r"한도|넘을|넘지|초과|이내|미만|이상|예시|최대|최소|까지|"
    r"수익률|총비용|총보수|수수료|비교지수|투자기간별|재투자|투자신탁|"
    r"출시|누적|연간|가정|보유(?:종목|비중)|상위"
)


def check_alloc_sum(text):
    out = []
    for line in text.split("\n"):
        if not _ALLOC_LINE.search(line):
            continue
        if _RANGE.search(line) or _ALLOC_SKIP.search(line):
            continue
        # 구분자(+ 또는 /)가 있어야 '여러 구성요소 배분'으로 본다
        if not re.search(r"[+/]", line):
            continue
        pcts = [float(x) for x in _PCT.findall(line)]
        if len(pcts) < 2:
            continue
        # 보수·거래비용 등 1% 미만 값이 섞이면 배분표가 아님(오탐 차단)
        if any(p < 1.0 for p in pcts):
            continue
        s = round(sum(pcts), 2)
        # '배분 합계'로 볼 수 있는 범위에서 100%를 벗어난 것만 후보로.
        #   합이 100과 너무 동떨어지면(예: 0.1, 130) 배분표가 아닐 확률이 높아
        #   오탐을 줄이기 위해 80~125% 구간에서 100±0.5%를 벗어난 경우만 잡는다.
        if 99.5 <= s <= 100.5:
            continue
        if not (80.0 <= s <= 125.0):
            continue
        out.append({
            "line": line.strip()[:120],
            "pcts": pcts, "sum": s, "diff": round(abs(s - 100.0), 2),
        })
    return out


# ─────────────────────────────────────────────────────────────────────────
# 로드
# ─────────────────────────────────────────────────────────────────────────
def load_docs():
    if os.path.exists("chunks.json"):
        data = json.load(open("chunks.json", encoding="utf-8"))
        docs = {}
        for c in data:
            docs.setdefault(c.get("source", "?"), []).append(c.get("text", ""))
        return {k: "\n".join(v) for k, v in docs.items()}, "chunks.json"
    files = sorted(glob.glob("reocr/*.txt"))
    if files:
        return ({os.path.basename(f): open(f, encoding="utf-8").read()
                 for f in files}, "reocr/*.txt")
    print("chunks.json도 reocr/*.txt도 없습니다.", file=sys.stderr)
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────────────────────────────────
CHECKS = [
    ("D_단위이상", check_unit_malformed),
    ("A_계산식", check_explicit_formula),
    ("B_비율금액", check_ratio_amount),
    ("C_배분합계", check_alloc_sum),
]
SEVERITY = {"D_단위이상": "높음", "A_계산식": "높음",
            "B_비율금액": "중간(오탐 가능)", "C_배분합계": "중간(오탐 가능)"}


def main():
    docs, src = load_docs()
    print(f"검수 대상: {src}  |  문서 {len(docs)}개\n", flush=True)

    findings = []
    seen = set()          # (source, check, 표기/스니펫) 중복 제거 — 같은 문장이
                          #   여러 청크에 걸쳐 중복 카운트되는 것을 막는다
    for source, text in docs.items():
        for name, fn in CHECKS:
            res = fn(text)
            for r in res:
                key_val = r if isinstance(r, str) else (
                    r.get("stated") or r.get("snippet") or r.get("line") or str(r))
                key = (source, name, key_val)
                if key in seen:
                    continue
                seen.add(key)
                findings.append({"source": source, "check": name,
                                 "severity": SEVERITY[name],
                                 "detail": r})

    json.dump(findings, open("ingest_review.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    # 콘솔 리포트
    from collections import Counter
    by_check = Counter(f["check"] for f in findings)
    print("=" * 72)
    print("검수 후보 요약 (자동 탐지 — 사람 확인 필요)")
    print("=" * 72)
    for name, _ in CHECKS:
        print(f"  [{name}] {by_check.get(name, 0)}건   심각도:{SEVERITY[name]}")
    print(f"\n총 {len(findings)}건 → ingest_review.json 저장")

    # 상위 항목 상세
    order = {"높음": 0, "중간(오탐 가능)": 1}
    findings_sorted = sorted(findings, key=lambda x: order.get(x["severity"], 9))
    print("\n" + "-" * 72)
    print("상세(심각도 높은 순, 최대 40건):")
    for f in findings_sorted[:40]:
        print(f"\n▶ [{f['check']}] {f['source']}  (심각도 {f['severity']})")
        d = f["detail"]
        if isinstance(d, dict):
            for k, v in d.items():
                print(f"    {k}: {v}")
        else:
            print(f"    표기: {d}")

    # NUMBER_NOTES 스텁(단위이상·계산식 등 '높음'만) — 검수 확정 후 main.py에 붙일 초안
    stubs = []
    for f in findings_sorted:
        d = f["detail"]
        if f["check"] == "D_단위이상":
            wrong = d if isinstance(d, str) else d.get("stated", "")
            stubs.append({"src": f["source"], "wrong": wrong,
                          "right": "<검수: 올바른 표기 입력>",
                          "basis": "<검수: 근거 입력(단위 뒤죽박죽 의심)>"})
        elif f["check"] == "A_계산식":
            stubs.append({"src": f["source"], "wrong": d["stated"],
                          "right": f"{int(d['calc_val']):,}원(계산값)",
                          "basis": f"{d['formula']} = {d['calc_val']}"})
    if stubs:
        json.dump(stubs, open("number_notes_stub.json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        print("\n" + "-" * 72)
        print(f"NUMBER_NOTES 스텁 {len(stubs)}건 → number_notes_stub.json")
        print("  (사람 검수로 right/basis 채운 뒤 main.py의 NUMBER_NOTES에 추가)")


if __name__ == "__main__":
    main()
