# -*- coding: utf-8 -*-
"""투자설명서 보수표 전수 검산
  ① 상세표 내부: 집합투자업자+판매회사+신탁업자+사무관리 = 총보수 인가
  ② 상세표 내부: 총보수 + 기타비용 = 총보수·비용 인가
  ③ 요약표 ↔ 상세표: 요약표의 총보수 값이 상세표에도 있는가
  어긋난 것만 fee_conflicts.json 에 저장한다.
사용법: python3 audit_fees.py
"""
import glob, json, re, sys, time
import pdfplumber

TOL = 0.0051
FIRST = re.compile(r"\d+\.\d+")
TOK = re.compile(r"\d+(?:\.\d+)?%?|[-–—]")   # v2: 정수 값("1")과 % 표기도 포함
ALL = re.compile(r"\d+\.\d+|\d+|[-–—]")
CLS = re.compile(r"종류\s*([A-Za-z][A-Za-z0-9\-]*)")


def num(t):
    """'1', '0.72', '0.4000%' 를 모두 숫자로. 대시는 None."""
    if t is None:
        return None
    t = str(t).replace("%", "").replace(",", "")
    try:
        return float(t)
    except ValueError:
        return None


def parse_detail(lines):
    """상세표 행 → [(클래스, 구성4, 총보수, 기타비용, 총보수·비용)]"""
    rows = []
    for i, line in enumerate(lines):
        m = FIRST.search(line)
        if not m:
            continue
        t = TOK.findall(line[m.start():])
        if len(t) < 9:
            continue
        t = t[:9]
        parts = [num(x) or 0.0 for x in t[:4]]
        total, etc, totcost = num(t[4]), num(t[5]) or 0.0, num(t[6])
        if total is None or not (0 < total < 10):
            continue
        cls = ""
        for j in range(i, max(-1, i - 4), -1):        # 라벨은 보통 1~3줄 위
            c = CLS.search(lines[j])
            if c:
                cls = c.group(1)
                break
        rows.append((cls, parts, total, etc, totcost))
    return rows


def parse_summary(lines):
    """요약표 행 → [(총보수, 판매보수, 동종유형, 총보수·비용)]"""
    rows = []
    for line in lines:
        t = ALL.findall(line)
        ints = []
        for x in reversed(t):
            v = num(x)
            if v is not None and "." not in x and v >= 50:
                ints.append(x)
                if len(ints) == 5:
                    break
            else:
                break
        if len(ints) < 5:
            continue
        fee = t[:len(t) - 5][-4:]
        if len(fee) < 4:
            continue
        tot = num(fee[0])
        if tot is None or not (0 < tot < 10):
            continue
        rows.append(tuple(fee))
    return rows


def main():
    files = sorted(glob.glob("docs/fund_pdf/**/*.pdf", recursive=True))
    print(f"검산 대상 {len(files)}개 파일\n", flush=True)
    conflicts, stats = [], {"detail_rows": 0, "sum_bad": 0, "cost_bad": 0,
                            "cross_bad": 0, "no_detail": 0, "no_summary": 0}
    t0 = time.time()

    for n, f in enumerate(files, 1):
        det, summ = [], []
        try:
            with pdfplumber.open(f) as pdf:
                for page in pdf.pages[:45]:          # 두 표 모두 앞쪽에 있음
                    txt = page.extract_text() or ""
                    if "보수" not in txt:
                        continue
                    lines = [re.sub(r"\s+", " ", l).strip() for l in txt.split("\n")]
                    if "신탁업자" in txt:            # v2: '종류' 라벨 없는 양식도 포함
                        det += parse_detail(lines)
                    if "투자기간별" in txt or "총비용" in txt:
                        summ += parse_summary(lines)
        except Exception as e:
            print(f"  [읽기 실패] {f}: {e}", flush=True)
            continue

        if not det:
            stats["no_detail"] += 1
        if not summ:
            stats["no_summary"] += 1
        stats["detail_rows"] += len(det)

        for cls, parts, total, etc, totcost in det:
            s = round(sum(parts), 4)
            if abs(s - total) > TOL:
                stats["sum_bad"] += 1
                conflicts.append({"file": f, "type": "구성항목합≠총보수", "class": cls,
                                  "parts": parts, "sum": s, "total": total,
                                  "diff": round(abs(s - total), 4)})
            if totcost is not None and abs(total + etc - totcost) > TOL:
                stats["cost_bad"] += 1
                conflicts.append({"file": f, "type": "총보수+기타비용≠총보수·비용",
                                  "class": cls, "total": total, "etc": etc,
                                  "total_cost": totcost,
                                  "diff": round(abs(total + etc - totcost), 4)})

        if det and summ:
            dtot = {round(t, 4) for _, _, t, _, _ in det}
            for row in summ:
                v = num(row[0])
                if v is None:
                    continue
                if not any(abs(v - d) < TOL for d in dtot):
                    stats["cross_bad"] += 1  # 참고용(파싱 취약)
                    conflicts.append({"file": f, "type": "요약표총보수↔상세표불일치",
                                      "summary_total": v,
                                      "detail_totals": sorted(dtot)})

        if n % 10 == 0:
            print(f"  {n}/{len(files)} 처리 ({time.time()-t0:.0f}초, "
                  f"불일치 {len(conflicts)}건)", flush=True)

    json.dump(conflicts, open("fee_conflicts.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    print("\n" + "=" * 72)
    print(f"파일 {len(files)}개 / 상세표 행 {stats['detail_rows']}개 검산")
    print(f"  상세표 없음: {stats['no_detail']}개 파일 / 요약표 없음: {stats['no_summary']}개 파일")
    print(f"  ① 구성항목 합 ≠ 총보수      : {stats['sum_bad']}건")
    print(f"  ② 총보수+기타 ≠ 총보수·비용 : {stats['cost_bad']}건")
    print(f"  ③ 요약표 ↔ 상세표 불일치    : {stats['cross_bad']}건")
    print(f"\n총 {len(conflicts)}건 → fee_conflicts.json 저장")

    for c in conflicts[:15]:
        print("\n---", c["type"], "|", c["file"].split("/")[-1])
        for k, v in c.items():
            if k not in ("file", "type"):
                print(f"      {k}: {v}")


if __name__ == "__main__":
    main()
