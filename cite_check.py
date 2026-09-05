# -*- coding: utf-8 -*-
"""cite_check.py — 답변 속 수치·등급·상품이 '[참고 문서]'로 적힌 출처 원문에 실제로 있는지 대조(API 호출 0회).
mini3/4/5_out.txt(및 있으면 golden/other *_out.txt)의 답변마다:
  ① %·등급·연령·연차 값이 출처 청크에 없으면 '출처 불일치 후보'
  ② PRODUCT_FACTS(코퍼스 확인 정답표)의 상품이 답변에 있고 등급/보수가 다르면 '정답표 불일치'
  ③ 답변의 상품명(투자신탁/펀드/ETF 표지)이 출처 청크 어디에도 없으면 '출처에 없는 상품'
계산기 금액(만원)은 코드가 계산한 값이라 제외. 결과: cite_check_out.txt
사용: cd /root/app && python3 cite_check.py mini3_out.txt mini4_out.txt mini5_out.txt"""
import json, re, sys, glob

d = json.load(open("chunks.json", encoding="utf-8"))
chunks = d if isinstance(d, list) else list(d.values())
by_src = {}
for c in chunks:
    if not isinstance(c, dict):
        continue
    src = c.get("source") or c.get("src") or ""
    by_src.setdefault(src, []).append(re.sub(r"\s+", "", c.get("text", "")))
ALL = "".join("".join(v) for v in by_src.values())

FACTS = [
    (r"삼성\s*클래식\s*연금[^\n]{0,30}?(?:주식|\[주식\])|삼성클래식연금증권전환형자투자신탁", "삼성클래식[주식]", "2등급", None),
    (r"삼성\s*클래식\s*연금[^\n]{0,30}?(?:채권|\[채권\])|삼성클래식연금증권전환형투자신탁(?!.*자투자)", "삼성클래식[채권]", "5등급", None),
    (r"인덱스\s*12M|퇴직연금인덱스", "인덱스12M", "6등급", "0.42"),
    (r"또박또박", "또박또박 C-P2", "보통위험", "0.87"),
    (r"미국배당다우존스", "TIGER 미국배당다우존스", "높은위험", "0.08"),
]
PROD = re.compile(r"[가-힣A-Za-z0-9()\[\]·\-]{6,}(?:증권자?투자신탁|투자신탁|펀드|ETF)(?:\s*제?\s*\d+\s*호)?(?:\s*\[[가-힣]+\])?")
GENERIC = re.compile(r"^(?:연금저축펀드|주식형펀드|채권형펀드|혼합형펀드|인덱스펀드|국내펀드|해외펀드|연금펀드|공모펀드|TDF펀드)$")


def norm(s):
    return re.sub(r"\s+", "", s)


def check(qid, q, ans):
    body = ans.split("[참고 문서]")[0]
    srcs = re.findall(r"\[참고 문서\]\s*(.+)$", ans, re.M)
    srcs = [x.strip() for x in (srcs[0].split(",") if srcs else [])]
    texts = [t for s0 in srcs for t in by_src.get(s0, [])]
    if not texts:
        return [f"  (출처 청크 없음: {srcs})"]
    cited = "".join(texts)
    out = []
    # ① 값 대조
    vals = set(re.findall(r"\d+(?:\.\d+)?\s*%", body)) | set(re.findall(r"\d\s*등급", body)) \
        | set(re.findall(r"\d{2}\s*세", body)) | set(re.findall(r"\d+\s*년\s*차", body))
    for v in sorted(vals):
        nv = norm(v)
        # 계산기 세율(16.5/13.2)·연금소득세율은 문서 여러 곳에 있으므로 출처 대신 코퍼스 전체로 확인
        if nv not in cited:
            where = "코퍼스 어딘가엔 있음" if nv in ALL else "코퍼스 전체에도 없음"
            out.append(f"  ① '{v}' 출처({', '.join(srcs)})에 없음 — {where}")
    # ② 정답표 대조
    for key, name, grade, fee in FACTS:
        if re.search(key, body):
            g = re.findall(r"(\d)\s*등급", body)
            gn = grade[0] if grade[0].isdigit() else None
            if gn and g and all(x != gn for x in g):
                out.append(f"  ② {name}: 답변 등급 {sorted(set(g))} ≠ 정답표 {grade}")
            if fee and re.search(r"보수", body) and fee not in body:
                _fv = sorted(set(re.findall(r"0\.\d+", body)))
                out.append(f"  ② {name}: 답변에 정답표 보수 {fee}% 없음 (답변 보수값: {_fv})")
    # ③ 상품명 대조
    for m in PROD.finditer(body):
        nm = m.group(0).strip("·-")
        if GENERIC.match(norm(nm)):
            continue
        core = norm(re.sub(r"(?:증권자?투자신탁|투자신탁|펀드|ETF).*$", "", nm))
        if len(core) < 4:
            continue
        if core not in cited:
            out.append(f"  ③ 상품 '{nm}' 핵심부 '{core}' 출처에 없음 — {'코퍼스엔 있음' if core in ALL else '코퍼스 전체에도 없음'}")
    return out


def main():
    files = sys.argv[1:] or sorted(glob.glob("mini*_out.txt"))
    fo = open("cite_check_out.txt", "w", encoding="utf-8")
    total = 0
    for fn in files:
        try:
            txt = open(fn, encoding="utf-8").read()
        except OSError:
            continue
        for blk in txt.split("=" * 70)[1:]:
            m = re.match(r"\s*\[([^\]]+)\]\s*(.+?)\n", blk)
            if not m:
                continue
            qid, q = m.group(1), m.group(2)
            ans = blk.split("--- 답변 ---", 1)[-1].strip()
            res = check(qid, q, ans)
            line = f"[{fn} {qid}] {q}\n" + ("\n".join(res) if res else "  이상 없음")
            print(line); fo.write(line + "\n")
            total += len(res)
    fo.close()
    print("=" * 50); print(f"불일치 후보 {total}건 → cite_check_out.txt")


if __name__ == "__main__":
    main()
