# -*- coding: utf-8 -*-
"""
audit_crossdoc.py — 문서 간/골든 팩트 정합성 검수 (비수치 오류까지)

audit_ingest(문서 내부 수치 자기모순)로는 못 잡는,
'내부적으론 멀쩡한데 사실이 틀린' 오류(틀린 세율·조항·날짜)를 잡기 위한 도구.
실제 프로덕션의 '골든 팩트 레지스트리(golden fact store)' 패턴:
  검증된 핵심 사실 목록을 두고, 문서가 그와 어긋나면 검수 후보로 올린다.

검사
  ① 골든 팩트 위반 : 검증된 값과 다른 값을 말하는 문서를 잡는다
       (예: 위험자산 한도는 70%인데 어떤 문서가 다른 %로 적음)
  ② 조항 인벤토리 : '제N조' 인용을 법령별로 모아, 같은 맥락에 서로 다른
       조를 인용한 문서를 대조(문서 간 불일치)
  ③ 날짜 대조     : 같은 사건(폐지·개정·시행)에 서로 다른 날짜를 적은 문서

한계(정직): 모든 문서가 똑같이 틀렸으면 못 잡는다. 최종 검증은 외부
  정답(법령DB)·전문가 몫이며, 이 도구는 '검수 후보를 좁혀줄' 뿐이다.
자동 교정은 하지 않는다 — 후보만 제시하고 사람이 확정한다.

입력: chunks.json (없으면 reocr/*.txt)
출력: crossdoc_review.json + 콘솔 리포트
사용법: cd /root/app && python3 audit_crossdoc.py
"""
import glob
import json
import os
import re
import sys


def _norm(s):
    """비교용 정규화: 공백·콤마 제거."""
    return re.sub(r"[\s,]", "", s)


# ── 골든 팩트(검증된 핵심 사실) ─────────────────────────────────────────
#   각 항목: (개념, 개념+값을 잡는 정규식[값은 그룹1], 기대값(정규화), 비고)
#   ※ 값이 하나로 확정되는 안정 사실만 넣는다(연도별로 갈리는 한도 등은 제외).
GOLDEN = [
    ("퇴직연금 위험자산 한도",
     r"위험자산\s*(?:투자\s*)?한도[^%\n]{0,6}?(\d{1,3})\s*%", "70",
     "감독규정상 위험자산 한도는 70%"),
    ("기타소득세율(연금외수령)",
     r"기타소득세[^%\n]{0,6}?(\d{1,2}(?:\.\d)?)\s*%", "16.5",
     "연금외수령·중도해지 기타소득세 16.5%"),
    ("이자·배당소득세율(일반계좌)",
     r"(?:이자소득세|배당소득세|금융소득세)[^%\n]{0,6}?(\d{1,2}(?:\.\d)?)\s*%", "15.4",
     "일반계좌 이자·배당 15.4%"),
    # ※ 세액공제율은 소득구간(16.5/13.2)·지방세 유무(15/16.5)로 여러 형태를
    #   가지므로 '값이 하나로 딱 떨어지는' 골든 팩트에 부적합 → 제외(실측 오탐 8건).
    ("금융소득 종합과세 기준",
     r"금융소득\s*종합과세[^0-9\n]{0,12}?(\d[\d,]*)\s*만\s*원", "2000",
     "금융소득 종합과세 2,000만원"),
    ("해외주식 직접투자 양도세율",
     r"(?:양도소득세|양도세)[^%\n]{0,8}?(\d{2})\s*%", "22",
     "해외주식 양도세 22%(지방세 포함)"),
    ("해외주식 양도세 기본공제",
     r"양도[^.\n]{0,12}?기본공제[^0-9\n]{0,6}?(\d[\d,]*)\s*만\s*원", "250",
     "양도소득 기본공제 250만원"),
    ("예금자보호 한도",
     r"예금자?\s*보호[^0-9\n]{0,20}?(\d[\d,]*)\s*만\s*원", "5000",
     "예금자보호 5천만원(=5000만원)"),
    ("ISA 초과수익 저율과세율",
     r"(?:ISA|아이에스에이)[^%\n]{0,30}?(?:초과|비과세\s*한도\s*초과)[^%\n]{0,10}?(\d(?:\.\d)?)\s*%", "9.9",
     "ISA 비과세 한도 초과분 9.9%"),
    ("연금소득세 최저율(80세 이상)",
     r"80세\s*이상[^%\n]{0,10}?(\d(?:\.\d)?)\s*%", "3.3",
     "80세 이상 연금소득세 3.3%"),
]

# ── 날짜 골든(같은 사건 = 하나의 날짜) ─────────────────────────────────
GOLDEN_DATE = [
    ("집중투자한도 폐지일",
     r"집중투자한도[^\n]{0,20}?(20\d\d)\s*[.\-]\s*(\d{1,2})\s*[.\-]\s*(\d{1,2})",
     ("2023", "7", "3"), "집중투자한도 폐지 2023.07.03"),
]


def load_docs():
    if os.path.exists("chunks.json"):
        data = json.load(open("chunks.json", encoding="utf-8"))
        docs = {}
        for c in data:
            docs.setdefault(c.get("source", "?"), []).append(c.get("text", "") or "")
        return {k: " ".join(v) for k, v in docs.items()}, "chunks.json"
    files = sorted(glob.glob("reocr/*.txt"))
    if files:
        return ({os.path.basename(f): open(f, encoding="utf-8").read()
                 for f in files}, "reocr/*.txt")
    print("chunks.json도 reocr/*.txt도 없습니다.", file=sys.stderr)
    sys.exit(1)


def check_golden(docs):
    """골든 값과 다른 값을 말하는 문서를 찾는다."""
    out = []
    for name, rgx, expected, note in GOLDEN:
        pat = re.compile(rgx)
        for src, text in docs.items():
            for m in pat.finditer(text):
                got = _norm(m.group(1))
                # 만원 단위 표기 흡수: '5천만'→'5000' 등은 정규식이 숫자만 잡으므로 그대로 비교
                if _norm(expected) != got:
                    ctx = text[max(0, m.start() - 20):m.end() + 15]
                    out.append({"type": "골든위반", "concept": name, "source": src,
                                "stated": m.group(1), "expected": expected,
                                "note": note, "context": ctx.strip()[:110]})
    return out


def check_dates(docs):
    out = []
    for name, rgx, exp, note in GOLDEN_DATE:
        pat = re.compile(rgx)
        for src, text in docs.items():
            for m in pat.finditer(text):
                got = (m.group(1), str(int(m.group(2))), str(int(m.group(3))))
                if got != exp:
                    out.append({"type": "날짜불일치", "concept": name, "source": src,
                                "stated": ".".join(m.groups()),
                                "expected": ".".join(exp), "note": note})
    return out


# ── 조항 인벤토리: '제N조'를 법령별로 모아 문서 간 대조 ─────────────────
_LAW = re.compile(r"([가-힣]{2,10}법(?:\s*시행령|\s*시행규칙)?)\s*(?:제)?\s*(\d+)\s*조"
                  r"(?:\s*의\s*(\d+))?")


def _bigrams(s):
    s = re.sub(r"\s", "", s)
    return {s[i:i + 2] for i in range(len(s) - 1)}


def _sim(a, b):
    # Jaccard(합집합 분모): 짧은 맥락이 긴 맥락에 부분포함돼도 과대평가되지 않게
    A, B = _bigrams(a), _bigrams(b)
    return len(A & B) / max(1, len(A | B))


def clause_conflicts(docs):
    """같은 법령을 '거의 같은 맥락'으로 인용했는데 조 번호가 다른 경우만 잡는다.
    (전체 나열이 아니라 '진짜 불일치 후보'만 — 예: 같은 문장에 제20조 vs 제20의3조).
    반환: [(법령, [(조, 대표맥락, 출처들), ...])]"""
    inv = {}
    for src, text in docs.items():
        for m in _LAW.finditer(text):
            law = re.sub(r"\s+", "", m.group(1))
            jo = m.group(2) + ("의" + m.group(3) if m.group(3) else "")
            ctx = re.sub(r"\s+", " ", text[m.end():m.end() + 40]).strip()
            inv.setdefault(law, {}).setdefault(jo, []).append((src, ctx[:40]))
    conflicts = []
    for law, jos in inv.items():
        reps = [(jo, refs[0][1], sorted({s for s, _ in refs})) for jo, refs in jos.items()]
        flagged = []
        for i in range(len(reps)):
            for j in range(i + 1, len(reps)):
                # 조 번호는 다른데 인용 맥락이 거의 같으면(≥0.55) 불일치 후보
                if reps[i][0] != reps[j][0] and _sim(reps[i][1], reps[j][1]) >= 0.55:
                    flagged.extend([reps[i], reps[j]])
        if flagged:
            uniq = {r[0]: r for r in flagged}
            conflicts.append((law, list(uniq.values())))
    return conflicts, sum(len(v) for v in inv.values())


def main():
    docs, srcname = load_docs()
    print(f"검수 대상: {srcname}  |  문서 {len(docs)}개\n")

    g = check_golden(docs)
    d = check_dates(docs)
    findings = g + d
    json.dump(findings, open("crossdoc_review.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    print("=" * 68)
    print(f"① 골든 팩트 위반: {len(g)}건   ② 날짜 불일치: {len(d)}건")
    print("=" * 68)
    for f in findings:
        print(f"\n▶ [{f['type']}] {f['concept']}  ({f['source']})")
        print(f"    문서값: {f['stated']}  ↔  골든: {f['expected']}  ({f['note']})")
        if f.get("context"):
            print(f"    맥락: …{f['context']}…")
    if not findings:
        print("\n골든 팩트·날짜 위반 없음 — 코퍼스가 검증된 사실과 일치.")

    # ③ 조항 불일치: 거의 같은 맥락인데 조 번호가 다른 경우만
    conflicts, total_cites = clause_conflicts(docs)
    print("\n" + "=" * 68)
    print(f"③ 조항 불일치 후보: {len(conflicts)}건  (총 조항 인용 {total_cites}개 중)")
    print("   같은 법을 '거의 같은 맥락'으로 인용했는데 조 번호가 다른 것만 (OCR 오타 등)")
    print("=" * 68)
    for law, reps in conflicts:
        print(f"\n▶ {law}")
        for jo, ctx, srcs in reps:
            print(f"    제{jo}조 ← {', '.join(srcs)}")
            print(f"        맥락: {ctx}")
    if not conflicts:
        print("\n조항 불일치 후보 없음.")

    print(f"\n→ crossdoc_review.json 저장. 뜬 항목은 '검수 후보'이며, "
          f"연도·맥락 차이로 정당할 수 있으니 사람이 확정한다.")


if __name__ == "__main__":
    main()
