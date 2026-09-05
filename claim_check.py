# -*- coding: utf-8 -*-
"""claim_check.py — 주장 유형별 구조화 근거 검증기(API 호출 0회). cite_check(존재 검사)의 후속.
답변을 문장으로 나눠 다음 주장 유형을 추출하고, '[참고 문서]'에 적힌 출처 청크 안에서 같은 문맥(±window)에 대상과 값이
함께 있는지 검사한다. 코퍼스 어딘가에 있는 것은 인정하지 않는다(표시 출처 안에서만).
  A) 세율 주장  : (연령 구간, 세율) 쌍 — 출처 청크의 같은 문맥에 '연령 경계'와 '세율'이 함께 있고, 표준표(70세미만 5.5 / 70~79 4.4 /
                  80이상 3.3)와 맞는지. '지방소득세 포함'은 출처에 그 표기가 있을 때만.
  B) 상품 주장  : (상품 핵심부, 위험등급, 보수값·필드명) — 출처의 '한 청크' 안에 상품명과 등급이 함께 있는지, 보수는 값 ±60자 안에
                  답변이 붙인 필드명(총보수/총보수·비용/동종유형/판매보수/합성총보수)이 있는지. 상품마다 따로 판정.
  C) 계산 주장  : '계산 결과 요약' 줄의 (소득유형·소득·세율·납입·대상·공제액)을 독립 재계산해 내부 정합성 검사 + 한도(600/900)가
                  출처에 있는지.
  D) 조건 주장  : 펀드 문맥의 긍정 '원금/수익 보장' 단정(부정 없이) → 위반. ISA 전환금 문장은 출처에 'ISA전환금 포함'·'세액공제' 문맥이 있는지.
  E) 출처명 정규화: 공백·대소문자·경로 제거 후 매칭(불일치 시 후보 제시).
사용: cd /root/app && python3 claim_check.py mini10_out.txt   → claim_check_out.txt"""
import json, re, sys, glob, os

# ---------- 코퍼스 ----------
d = json.load(open("chunks.json", encoding="utf-8"))
chunks = d if isinstance(d, list) else list(d.values())
def nsrc(s):
    return re.sub(r"\s+", "", os.path.basename(str(s))).lower()
def norm(t):
    return re.sub(r"\s+", "", t)
by_src = {}
for c in chunks:
    if isinstance(c, dict):
        by_src.setdefault(nsrc(c.get("source") or c.get("src") or ""), []).append(norm(c.get("text", "")))

AGE_TABLE = [((55, 69), "5.5"), ((70, 79), "4.4"), ((80, 200), "3.3")]
FIELD_WORDS = {"총보수·비용": r"총보수[·ㆍ]비용|총보수비용", "동종유형": r"동종유형", "판매보수": r"판매보수",
               "합성총보수": r"합성총보수", "총보수": r"총보수"}
PROD = re.compile(r"[가-힣A-Za-z0-9()\[\]·\-]{6,}(?:증권자?투자신탁|투자신탁|펀드|ETF)(?:\s*제?\s*\d+\s*호)?(?:\s*\[[가-힣]+\])?")
GENERIC = re.compile(r"^(?:연금저축펀드|주식형펀드|채권형펀드|혼합형펀드|인덱스펀드|국내펀드|해외펀드|연금펀드|공모펀드|TDF펀드|퇴직연금펀드)$")
FUND_CTX = re.compile(r"펀드|ETF|투자신탁|TDF|리츠|\d\s*등급")


def sents(body):
    out = []
    for ln in body.split("\n"):
        out += [x for x in re.split(r"(?<=[.!?])\s+", ln) if x.strip()]
    return out


def find_ctx(texts, a, b, win=160):
    """어떤 청크 안에서 a와 b가 win자 이내에 함께 나오는가"""
    for t in texts:
        for m in re.finditer(re.escape(a), t):
            seg = t[max(0, m.start() - win): m.end() + win]
            if b in seg:
                return True
    return False


# ---------- A) 세율 주장 ----------
AGE_RANGE = re.compile(r"(?:만\s*)?(\d{2})\s*세?\s*(?:이상|부터|에서|[~\-–∼])\s*(?:만\s*)?(\d{2})\s*세\s*(미만|이하)?[^\n%]{0,20}?(?<![\d.])(\d(?:\.\d)?)\s*%")
AGE_SINGLE = re.compile(r"(?:만\s*)?(\d{2})\s*세\s*(미만|이하|이상|초과)?[^\n%]{0,20}?(?<![\d.])(\d(?:\.\d)?)\s*%")


def age_claims(st):
    """문장 → [(원문, lo, hi, rate)]"""
    out, used = [], []
    for m in AGE_RANGE.finditer(st):
        lo, hi, rel, rate = int(m.group(1)), int(m.group(2)), m.group(3), m.group(4)
        if rel == "미만":
            hi -= 1
        out.append((m.group(0).strip(), lo, hi, rate)); used.append((m.start(), m.end()))
    for m in AGE_SINGLE.finditer(st):
        if any(a <= m.start() < b for a, b in used):
            continue
        a, rel, rate = int(m.group(1)), m.group(2), m.group(3)
        if rel == "미만":
            lo, hi = 55, a - 1
        elif rel == "이하":
            lo, hi = 55, a
        elif rel in ("이상", "초과"):
            lo, hi = a, 200
        else:
            lo, hi = a, a
        out.append((m.group(0).strip(), lo, hi, rate))
    return out


def check_rates(body, texts):
    out = []
    if not re.search(r"연금소득세", body):
        return out
    for st in sents(body):
        for raw, lo, hi, rate in age_claims(st):
            if lo < 55 and not (lo == 55):
                out.append(f"  A) 세율 주장 '{raw}' — 55세 미만 구간은 연금소득세 대상이 아님(구간 오류)")
                continue
            exp = next((r for (l, h), r in AGE_TABLE if l <= lo and hi <= h), None)
            if exp is None:
                out.append(f"  A) 세율 주장 '{raw}' — 표준표(55~69/70~79/80+) 구간과 맞지 않음(구간 경계 오류)")
                continue
            if rate != exp:
                out.append(f"  A) 세율 주장 '{raw}' — 표준표는 {exp}% (값 오류)")
                continue
            key = f"{lo if lo != 55 else (hi + 1)}세"     # 문서는 '70세' 경계로 표기
            if not (find_ctx(texts, key, f"{rate}%") or find_ctx(texts, key, rate)):
                out.append(f"  A) 세율 주장 '{raw}' — 표시 출처의 같은 문맥에 '{key}'와 '{rate}%'가 함께 없음")
    for st in sents(body):
        if re.search(r"연금소득세", st) and re.search(r"지방소득세", st) and not any("지방소득세" in t for t in texts):
            out.append("  A) '지방소득세 포함' 표기 — 표시 출처에 없음")
            break
    return out


# ---------- B) 상품 주장 ----------
def check_products(body, texts):
    out = []
    for m in PROD.finditer(body):
        nm = m.group(0).strip("·-")
        core = norm(re.sub(r"(?:증권자?투자신탁|투자신탁|펀드|ETF).*$", "", nm))
        if len(core) < 4 or GENERIC.match(norm(nm)):
            continue
        host = [t for t in texts if core in t]
        if not host:
            out.append(f"  B) 상품 '{nm}' — 표시 출처 청크에 상품명 없음")
            continue
        after = body[m.end(): m.end() + 60]
        g = re.search(r"(\d)\s*등급", after)
        if g:
            gtxt = f"{g.group(1)}등급"
            if not any(gtxt in t for t in host):
                out.append(f"  B) 상품 '{nm}' 등급 {gtxt} — 상품명이 있는 출처 청크에 그 등급이 없음(다른 상품 등급 혼입 의심)")
        # 보수: 상품명 문단(줄) 안의 '값%' + 필드명
        line = body[body.rfind("\n", 0, m.start()) + 1: (body.find("\n", m.end()) if body.find("\n", m.end()) != -1 else len(body))]
        for fm in re.finditer(r"(0\.\d{2,4})\s*%", line):
            val = fm.group(1)
            pre = line[max(0, fm.start() - 40): fm.start()]
            field = next((f for f, pat in FIELD_WORDS.items() if re.search(pat, pre)), None)
            alts = {val, val.rstrip("0"), val + "0", val + "00"}
            ok_val = any(any(v + "%" in t for v in alts) for t in host)
            if not ok_val:
                out.append(f"  B) 상품 '{nm}' 보수 {val}% — 상품명이 있는 출처 청크에 그 값 없음")
            elif field:
                if not any(re.search(FIELD_WORDS[field] + r".{0,200}?" + re.escape(v) + "%|" + re.escape(v) + r"%.{0,200}?" + FIELD_WORDS[field], t)
                           for v in alts for t in host):
                    out.append(f"  B) 상품 '{nm}' {field} {val}% — 출처 청크에서 값 근처에 필드명 '{field}'가 없음(필드 혼동 의심)")
    return out


# ---------- C) 계산 주장 ----------
def check_calc(body, texts):
    out = []
    m = re.search(r"계산 결과 요약:\s*(총급여|종합소득(?:금액)?)\s*([\d,]+)만원\((?:[^)]*)\)\s*→\s*공제율\s*([\d.]+)%\s*/\s*납입\s*([\d,]+)만원(?:\(연금저축\s*([\d,]+)\s*\+\s*IRP\s*([\d,]+)\))?\s*→\s*공제 대상\s*([\d,]+)만원[^/]*/\s*예상 세액공제액 약\s*([\d.]+)만원", body)
    if not m:
        return out
    kind, inc, rate, paid, ps, irp, base, credit = m.groups()
    f = lambda x: float(x.replace(",", ""))
    inc, rate, paid, base, credit = f(inc), f(rate), f(paid), f(base), f(credit)
    thr = 5500 if kind == "총급여" else 4500
    exp_rate = 16.5 if inc <= thr else 13.2
    if abs(rate - exp_rate) > 0.01:
        out.append(f"  C) 공제율 {rate}% — {kind} {int(inc):,}만원(경계 {thr:,})이면 {exp_rate}% 이어야 함")
    if ps and irp:
        exp_base = min(min(f(ps), 600) + f(irp), 900)
    else:
        exp_base = min(paid, 900 if re.search(r"IRP|합산", body) else 600)
    if abs(base - exp_base) > 0.5 and not (ps is None and abs(base - min(paid, 900)) < 0.5):
        out.append(f"  C) 공제 대상 {int(base):,}만원 — 재계산 {int(exp_base):,}만원과 다름")
    exp_credit = round(base * rate / 100 + 1e-9, 1)
    if abs(credit - exp_credit) > 0.06:
        out.append(f"  C) 공제액 {credit}만원 — {int(base):,}×{rate}% = {exp_credit}만원과 다름")
    # 본문 재언급 정합성
    for v in re.findall(r"(?<![\d.])(\d{2,3}(?:\.\d)?)\s*만\s*원", body.split("계산 결과 요약")[-1]):
        pass
    # 한도 근거
    if not any("600만원" in t or "900만원" in t or "600만" in t or "900만" in t for t in texts):
        out.append("  C) 세액공제 한도(600/900만원) — 표시 출처 청크에 한도 수치가 없음")
    return out


# ---------- D) 조건 주장 ----------
def check_conditions(body, texts):
    out = []
    for st in sents(body):
        if FUND_CTX.search(st) and re.search(r"(?:원금|수익)(?:이|을|은)?\s*보장", st) and not re.search(r"않|아니|없|되지", st):
            out.append(f"  D) 펀드 문맥의 보장 단정: '{st.strip()[:70]}…'")
        if "ISA" in st and re.search(r"전환", st):
            if not any(("ISA전환금" in t or "ISA만기" in t or "만기ISA" in t) and ("세액공제" in t or "과세제외" in t or "비과세" in t) for t in texts):
                out.append(f"  D) ISA 전환금 주장 — 표시 출처에 'ISA 전환금 + 세액공제/과세제외' 문맥 없음: '{st.strip()[:60]}…'")
        if re.search(r"(?:마지막|나중)(?:에|으로)\s*인출", st) and "받지 않은" in st and "먼저" not in st:
            out.append(f"  D) 인출 순서 반대 서술: '{st.strip()[:60]}…'")
    return out


def check(qid, q, ans):
    body = ans.split("[참고 문서]")[0]
    raw = re.findall(r"\[참고 문서\]\s*(.+)$", ans, re.M)
    srcs = [x.strip() for x in (raw[0].split(",") if raw else [])]
    texts, missing = [], []
    for s0 in srcs:
        k = nsrc(s0)
        if k in by_src:
            texts += by_src[k]
        else:
            cand = [x for x in by_src if k.split(".")[0] in x]
            missing.append(f"{s0}(후보: {cand[:2]})")
    out = []
    if missing:
        out.append(f"  E) 출처명 불일치: {missing}")
    if not texts:
        return out + ["  (표시 출처 청크 없음 — 이하 검사 불가)"]
    out += check_rates(body, texts) + check_products(body, texts) + check_calc(body, texts) + check_conditions(body, texts)
    return out


def main():
    files = sys.argv[1:] or sorted(glob.glob("mini*_out.txt"))
    fo = open("claim_check_out.txt", "w", encoding="utf-8")
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
            qid, qq = m.group(1), m.group(2)
            ans = blk.split("--- 답변 ---", 1)[-1].strip()
            res = check(qid, qq, ans)
            line = f"[{fn} {qid}] {qq}\n" + ("\n".join(res) if res else "  이상 없음")
            print(line); fo.write(line + "\n")
            total += len(res)
    fo.close()
    print("=" * 50); print(f"주장 단위 불일치 후보 {total}건 → claim_check_out.txt")


if __name__ == "__main__":
    main()
