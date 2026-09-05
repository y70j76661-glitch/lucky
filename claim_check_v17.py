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
  F) 질문 요구 슬롯 충족  G) 잘못된 전제 교정 여부  H) 불필요한 역질문  I) 제외조건 준수
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
# 규칙 원천 공유: 서버(main.py)의 요구 슬롯을 그대로 쓴다(없으면 로컬 사본). 서버와 검사기의 canonical 불일치 방지.
try:
    from main import REQUEST_SLOTS as _SRV_SLOTS   # main import 시 인덱스 로딩(수십 초)
    REQUEST_SLOTS = _SRV_SLOTS
    print("[claim_check] 규칙 원천: main.py (REQUEST_SLOTS 공유)")
except Exception as _e:
    print(f"[claim_check] main.py 규칙 import 실패({type(_e).__name__}) → 로컬 사본 사용")
    REQUEST_SLOTS = [("위험등급", r"위험\s*등급|등급", r"\d\s*등급|(?:높은|낮은|보통)\s*위험|등급"), ("총보수", r"총\s*보수|보수|수수료", r"보수|수수료"),
                     ("수익률", r"수익률", r"수익률"), ("세액공제", r"세액\s*공제|공제액", r"세액공제|공제"), ("한도", r"한도", r"한도|까지")]
_EXCL_NEG = r"(?:빼고|말고|제외하고|제외한\s|넘어가고|됐고|필요\s*없(?:고|으니|어서)|생략하고|건너뛰고|안\s*해도\s*(?:되니|돼서|되고))"
FIELD_WORDS = {"총보수·비용": r"총보수[·ㆍ]비용|총보수비용", "동종유형": r"동종유형", "판매보수": r"판매보수",
               "합성총보수": r"합성총보수", "총보수": r"총보수"}
PROD = re.compile(r"[가-힣A-Za-z0-9()\[\]·\-]{6,}(?:증권자?투자신탁|투자신탁|펀드|ETF)(?:\s*제?\s*\d+\s*호)?(?:\s*\[[가-힣]+\])?")
GENERIC = re.compile(r"^(?:연금저축펀드|주식형펀드|채권형펀드|혼합형펀드|인덱스펀드|국내펀드|해외펀드|연금펀드|공모펀드|TDF펀드|퇴직연금펀드|"
                     r"실적배당형펀드|실적배당형\(펀드\)?|실적배당형상품\(펀드·ETF\)?|원리금보장형|채권형|주식형|혼합형|실적배당형)$")   # v2: 유형 표현은 상품명이 아님
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
            _rng = next(((l, h) for (l, h), r in AGE_TABLE if l <= lo and hi <= h), None)
            exp = next((r for (l, h), r in AGE_TABLE if l <= lo and hi <= h), None)
            if exp is None:
                out.append(f"  A) 세율 주장 '{raw}' — 표준표(55~69/70~79/80+) 구간과 맞지 않음(구간 경계 오류)")
                continue
            if rate != exp:
                out.append(f"  A) 세율 주장 '{raw}' — 표준표는 {exp}% (값 오류)")
                continue
            # v2(T3 실측): 개별 나이('72세')는 그 나이가 속한 표준 구간의 경계('70세')로 출처를 찾는다(구간 포함 검사)
            _l, _h = _rng
            key = f"{_l}세" if _l != 55 else f"{_h + 1}세"     # 문서는 '70세' 경계로 표기
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
        after = body[m.end(): m.end() + 60].split("\n")[0]
        if re.search(r"\bvs\b|;", after):                        # 비교표 머리말('A vs B') 뒤의 등급은 이 상품의 것이 아님
            after = ""
        g = re.search(r"(?<![\d.])(\d)\s*등급", after)
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
    # v13.35: 수익률 문맥의 % 값은 상품명이 있는 출처 청크(없으면 표시 출처 전체)에 실제로 있어야 한다(표 행 오독·환각 탐지)
    for st in sents(body):
        if not re.search(r"수익률", st):
            continue
        for v in re.findall(r"(?<![\d.])(-?\d+\.\d{1,2})\s*%", st):
            if not any(v in t for t in texts):
                out.append(f"  B) 수익률 값 {v}% — 표시 출처 청크에 없음: '{st.strip()[:50]}…'")
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
    # 본문 재언급 정합성(TaxCalculationContract 불변식): 공제 문맥 문장의 세율·공제액·대상액이 요약(계산기)과 모순되면 위반
    ok_amts = {paid, base, credit, round(paid - base, 1), 600.0, 900.0, 1800.0, inc, 5500.0, 4500.0, 300.0}
    acc = (f(ps), f(irp)) if (ps and irp) else None
    if acc is None:
        _qa = re.search(r"연금저축[^\d\n]{0,12}?([\d,]+)\s*만\s*원[^\n]{0,20}?IRP[^\d\n]{0,12}?([\d,]+)\s*만\s*원", QUESTION_HINT[0])
        if _qa:
            acc = (f(_qa.group(1)), f(_qa.group(2)))
    if acc:
        p1 = min(acc[0], 600.0); p2 = base - p1
        ok_amts |= {acc[0], acc[1], p1, p2, round(p1 * rate / 100, 1), round(p2 * rate / 100, 1), round(acc[1] - p2, 1)}
    _after = body.split("계산 결과 요약", 1)[-1]
    _after = _after.split("\n", 1)[1] if "\n" in _after else ""
    for st in sents(_after):
        if not re.search(r"세액공제|공제액|공제\s*대상|공제율|돌려받|환급", st):
            continue
        for r_ in re.findall(r"(?<![\d.])(\d{1,2}(?:\.\d)?)\s*%", st):
            if float(r_) not in (16.5, 13.2, 15.0, 12.0):
                continue
            if abs(float(r_) - rate) > 0.01 and not re.search(r"초과|이하|경우|면\b|라면|구간", st):
                out.append(f"  C) 본문 세율 {r_}% ≠ 요약 {rate}%: '{st.strip()[:60]}…'")
        for m_ in re.finditer(r"(?<![\d.])(\d[\d,]*(?:\.\d)?)\s*만\s*원", st):
            v = float(m_.group(1).replace(",", ""))
            if v < 20 or any(abs(v - o) < 0.11 for o in ok_amts):
                continue
            if re.search(r"(?:한도|납입|추가|초과|중)\s*$", st[max(0, m_.start() - 8):m_.start()]):
                continue
            out.append(f"  C) 본문 금액 {m_.group(1)}만원 — 요약(대상 {int(base):,}·공제액 {credit}·납입 {int(paid):,})과 무관한 공제 문맥 숫자: '{st.strip()[:60]}…'")
    # 한도 근거
    if not any("600만원" in t or "900만원" in t or "600만" in t or "900만" in t for t in texts):
        out.append("  C) 세액공제 한도(600/900만원) — 표시 출처 청크에 한도 수치가 없음")
    return out



# ---------- M) 의미·범위 검사(v13.74): 숫자 일치가 아니라 조건·범위·요구 충족을 본다 ----------
def check_semantic(q, body):
    out = []
    if re.search(r"매매|사고팔|거래|팔면|배당|분배금", q) and re.search(r"세금|과세|소득세|내나요|내야", q) and re.search(r"IRP|연금저축|연금계좌|퇴직연금", q):
        if not re.search(r"거래\s*시점|즉시|당장|바로", body) or "인출" not in body:
            out.append("  M) 계좌 내 과세 답변에 '거래 시점(즉시 과세 아님)'과 '인출 시 과세'가 분리돼 있지 않음")
        if re.search(r"연금계좌\s+계좌|연금저축\s*\(\s*IRP\s*포함", body):
            out.append("  M) 용어 오류: '연금계좌 계좌' 또는 '연금저축(IRP 포함)'")
    if re.search(r"해지|중도\s*인출|인출", q) and re.search(r"세금|과세|세율", q) and re.search(r"연금저축|IRP|연금계좌", q):
        if "받지 않은" not in body or "받은" not in body:
            out.append("  M) 해지·인출 과세 답변에 '세액공제 받은 재원'과 '받지 않은 재원' 구분이 없음")
        if re.search(r"(?:전체|모든)\s*(?:해지|인출)\s*금액[^\n]{0,10}16\.5", body):
            out.append("  M) '전체 해지금액에 16.5%'로 읽히는 표현")
    if re.search(r"추천|골라|어떤\s*상품|좋은\s*상품", q) and re.search(r"하나|한\s*개|한\s*가지|1개", q):
        if not re.search(r"대표 검토 후보|확정하지 않|확정해 추천하지는|후보로 검토하실 수 있습니다|'하나'로 지정하지 않|조건이 정해지면", body):
            out.append("  M) '하나' 요청인데 확정 보류·대표 후보 표시가 없음")
    for st in sents(body):
        if re.search(r"높은\s*성장\s*가능성을\s*제공|회복(?:할)?\s*가능성이\s*(?:큽|높)|극복할\s*가능성|안전합니다|적합합니다|높은\s*수익을\s*제공", st) and not st.lstrip().startswith("※"):
            out.append(f"  M) 근거 밖 전망·적합성 단정: '{st.strip()[:60]}…'")
            break
    return out


# ---------- N) 문장 완결성·출처 줄(v13.78): 잘린 문장, 출처 줄 부재(정상 예외는 따로 판정) ----------
def check_form(q, ans):
    out = []
    body = ans.split("[참고 문서]")[0]
    lines = [l.strip() for l in body.split("\n") if l.strip() and not l.strip().startswith(("※", "[", "(", "|", "-"))]
    if lines:
        last = lines[-1]
        if not re.search(r"[.!?)\]”\"':]$", last) and not re.search(r"[.!?]\s*$", last):
            out.append(f"  N) 문장 완결성: 본문이 문장 부호 없이 끝남 — '…{last[-30:]}'")
    if "[참고 문서]" not in ans:
        out.append("  N) 출처 줄 없음(정상 예외 표기 '[참고 문서] 해당 없음'도 없음)")
    return out

# ---------- D) 조건 주장 ----------
def check_conditions(body, texts):
    out = []
    for st in sents(body):
        if FUND_CTX.search(st) and re.search(r"(?:원금|수익)(?:이|을|은)?\s*보장", st) and not re.search(r"않|아니|아닙|없|되지|비보장|별도로\s*확인", st):
            out.append(f"  D) 펀드 문맥의 보장 단정: '{st.strip()[:70]}…'")
        if "ISA" in st and re.search(r"전환", st):
            if not any(("ISA전환금" in t or "ISA만기" in t or "만기ISA" in t) and ("세액공제" in t or "과세제외" in t or "비과세" in t) for t in texts):
                out.append(f"  D) ISA 전환금 주장 — 표시 출처에 'ISA 전환금 + 세액공제/과세제외' 문맥 없음: '{st.strip()[:60]}…'")
        if re.search(r"(?:마지막|나중)(?:에|으로)\s*인출", st) and "받지 않은" in st and "먼저" not in st:
            out.append(f"  D) 인출 순서 반대 서술: '{st.strip()[:60]}…'")
    return out


# ---------- F) 질문 요구사항(슬롯) 주장 ----------
def check_requirements(q, body):
    out = []
    for name, qpat, apat in REQUEST_SLOTS:
        if not re.search(qpat, q) or re.search(r"(" + qpat + r")[^\n]{0,14}?" + _EXCL_NEG, q):
            continue
        if not re.search(apat, body):
            out.append(f"  F) 질문이 요구한 '{name}'이(가) 답변에 없음(누락)")
    return out


QUESTION_HINT = [""]


# ---------- G) 잘못된 전제 교정 / H) 역질문 적절성 / I) 제외조건 준수 ----------
_PREMISE_Q = re.compile(r"(?:IRP|연금저축|연금계좌|퇴직연금|DC)[^\n]{0,25}?(?:원금[^\n]{0,6}?보장|손해\s*(?:안|없)|손실\s*(?:안|없|이\s*없)|원금\s*(?:손실|손해)\s*(?:없|안)|안전한\s*거|안전하)")
_PREMISE_Q2 = re.compile(r"죠|나요|맞|되나|인가|가요|잖아|아닌가|거\s*아냐|아니야")
_RATE_PREMISE = re.compile(r"(?:연봉|총급여)\s*([\d,]+)\s*(천만|억|만)\s*원[^\n]{0,30}?(16\.5|13\.2)\s*%")
_EXCL_TOPICS = [(r"중도\s*해지|해지", r"중도\s*해지|연금\s*외\s*수령|기타소득세"), (r"중도\s*인출|인출", r"중도\s*인출|인출\s*사유"),
                (r"기한|기간\s*얘기", r"\d+\s*일\s*(?:이내|내에|안에)|기한"), (r"수령\s*나이|나이|연령", r"수령\s*나이|만\s*55\s*세|55\s*세"),
                (r"퇴직금", r"퇴직금|퇴직급여"), (r"ISA", r"ISA"), (r"수수료|보수", r"수수료|보수"), (r"세액공제", r"세액공제"),
                (r"연금소득세", r"연금소득세"), (r"디폴트옵션|디폴트\s*옵션", r"디폴트\s*옵션|사전지정운용")]
def check_qrules(q, body):
    out = []
    # G) 잘못된 전제: 'IRP는 원금이 보장되죠?' → 답변이 '실적배당형/원리금보장상품에 따라' 구분을 담아야 하고 '보장됩니다' 수긍이 없어야
    if _PREMISE_Q.search(q) and _PREMISE_Q2.search(q):
        if not re.search(r"실적배당|원리금\s*보장|보장되지\s*않|보장하지\s*않|보장하는\s*것은\s*아니", body):
            out.append("  G) 잘못된 전제(원금 보장) — 답변에 교정(실적배당형/원리금보장 구분·비보장) 없음")
        if re.search(r"(?:IRP|연금저축|연금계좌)[^.\n]{0,15}원금(?:이|을|은)?\s*보장(?:됩니다|되며|되고|돼요)", body):
            out.append("  G) 잘못된 전제 수용 — 'IRP … 원금이 보장됩니다' 단정 잔존")
    m = _RATE_PREMISE.search(q)
    if m:
        v = float(m.group(1).replace(",", "")); unit = m.group(2); v = v * (1000 if unit == "천만" else 10000 if unit == "억" else 1)
        exp = "16.5" if v <= 5500 else "13.2"
        if m.group(3) != exp and exp + "%" not in body.replace(" ", ""):
            out.append(f"  G) 잘못된 세율 전제({m.group(3)}%) — 답변이 올바른 세율 {exp}%를 제시하지 않음")
    # H) 불필요한 역질문: 단순 사실·계산 질문에 나이/투자성향을 되묻는 문장
    if re.search(r"한도|얼마|몇\s*%|세율|기한|나이는|언제", q) and not re.search(r"추천|골라|어떤\s*상품|좋은\s*상품", q) \
            and not (re.search(r"얼마", q) and re.search(r"받|수령|나오", q) and not re.search(r"\d", q)):   # v13.63: 수령액 질문(조건 없음)의 조건 역질문은 정당
        for st in sents(body):
            if re.search(r"(?:나이|연령|투자\s*성향|성향)[^.!?]{0,20}(?:알려주시|말씀해\s*주|여쭤|여쭙)", st):
                out.append(f"  H) 불필요한 역질문(단순 사실 질문에 개인정보 되묻기): '{st.strip()[:50]}…'")
                break
    # I) 제외조건: '<주제> 빼고/말고/제외하고/…'이면 답변에 그 주제 문장이 없어야
    for tq, tpat in _EXCL_TOPICS:
        mm = re.search(r"(" + tq + r")[^\n]{0,14}?" + _EXCL_NEG, q)
        if not mm or re.search(tq, q[mm.end():]):
            continue
        hit = [st for st in sents(body) if re.search(tpat, st)]
        if hit:
            out.append(f"  I) 제외 요청 주제('{hit and re.search(tq, q).group(0)}') 문장 잔존: '{hit[0].strip()[:50]}…'")
    return out


# ---------- J) 비교 관계 모순 / K) 추천 최종 표현 / L) 출처 표기 무결성 (v3) ----------
_REL_J = re.compile(r"(?:등급|위험(?:도|성)?)[^.!?\n]{0,30}?(?:더|보다|가장|상대적으로|비교적)[^.!?\n]{0,15}?(?:낮|높|안전|우위|우열)|"
                    r"(?:더|보다|가장|상대적으로|비교적)[^.!?\n]{0,15}?(?:낮|높|안전)[^.!?\n]{0,20}?(?:등급|위험)|(?:등급|위험)[^.!?\n]{0,20}?(?:우위|우열|낮습니다|높습니다)")


def check_compare_relation(body):
    """비교 답변에서 등급 미확정('대조 불가'·'확정하지 못함'·'확정할 수 없')이 하나라도 있는데 표 밖에 등급·위험 우열 관계 문장이 있으면 위반"""
    out = []
    if not re.search(r"원문 대조 불가|확정하지 못함|확정할 수 없", body):
        return out
    for ln in body.split("\n"):
        if ln.lstrip().startswith(("|", "※", "[", "(", "-")) or "위험등급 우열:" in ln:
            continue
        for st in sents(ln):
            if _REL_J.search(st):
                out.append(f"  J) 비교 관계 모순 — 등급 미확정인데 우열 문장: '{st.strip()[:60]}'")
    return out


_REC_K = [(r"추천\s*상품\s*[:：]", "'추천 상품:' 라벨"), (r"적합하다고\s*판단", "'적합하다고 판단' 단정"), (r"안정성을\s*(?:극대화|최대화)", "'안정성을 극대화' 단정"),
          (r"(?:펀드|ETF|투자신탁|\]|\))(?:을|를)\s*추천\s*(?:드립니다|합니다|드릴\s*수)", "상품 단정 추천"), (r"가장\s*좋은\s*(?:상품|펀드)입니다", "'가장 좋은 상품' 단정"),
          (r"수상|최우수|우수상|인정받은|선정된|1위|대표\s*상품", "판촉·경력 주장(상품 귀속 불확실)")]


def check_recommend_wording(q, body, texts=None):
    out = []
    if not re.search(r"추천|골라|좋은\s*(?:상품|펀드)|굴릴|어떤\s*(?:상품|펀드)", q):
        return out
    for pat, nm in _REC_K:
        m = re.search(pat, body)
        if m:
            out.append(f"  K) 추천 표현 계약 위반 — {nm}: '…{body[max(0, m.start()-15):m.end()+15].strip()}…'")
    return out


def check_source_integrity(ans):
    """[참고 문서]와 '(출처: …)'에는 파일명만 — 본문이 섞이면 위반"""
    out = []
    raw = re.findall(r"\[참고 문서\]\s*(.+)$", ans, re.M)
    for s0 in (raw[0].split(",") if raw else []):
        s0 = s0.strip()
        if s0 and not re.fullmatch(r"[\w.\-]+\.(?:pdf|docx|xlsx|xls|txt|csv|hwp|pptx)", s0, re.I):
            out.append(f"  L) 출처 표기 무결성 — 파일명이 아님: '{s0[:60]}'")
    for m in re.finditer(r"\(출처\s*[:：]\s*([^)\n]{0,200})\)?", ans):
        v = m.group(1).strip()
        if not re.fullmatch(r"[\w.\-]+\.(?:pdf|docx|xlsx|xls|txt|csv|hwp|pptx)", v, re.I):
            out.append(f"  L) 출처 표기 무결성 — '(출처:' 안이 파일명이 아님: '{v[:60]}'")
    for m in re.finditer(r"근거 문서:\s*([^\n—]+)", ans):
        for s0 in re.split(r",\s*", m.group(1).strip()):
            if s0 and not re.fullmatch(r"[\w.\-]+\.(?:pdf|docx|xlsx|xls|txt|csv|hwp|pptx)", s0, re.I):
                out.append(f"  L) 출처 표기 무결성 — '근거 문서:' 항목이 파일명이 아님: '{s0[:60]}'")
    return out


def check(qid, q, ans):
    QUESTION_HINT[0] = q
    body = ans.split("[참고 문서]")[0]
    # v2(T16 실측): 대체 답변이 붙인 자료 원문 블록('(출처: doc22.pdf) …')은 답변의 주장이 아니라 인용 → 검사 대상에서 제외
    body = "\n".join(l for l in body.split("\n") if not re.match(r"^\s*\(출처\s*[:：]\s*[^)]+\)", l)
                     and not (l.lstrip().startswith("※") and "제외했습니다" in l))   # 제외 고지에 적힌 이름은 주장이 아님
    raw = re.findall(r"\[참고 문서\]\s*(.+)$", ans, re.M)
    srcs = [x.strip() for x in (raw[0].split(",") if raw else []) if not x.strip().startswith("해당 없음")]   # v13.79: 정상 예외 표기는 출처명이 아님
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
        # v13.78: 실시간·무관·보안 거절처럼 근거 문서가 없는 것이 '정상'인 답변은 정상 예외로 판정(검사 불가가 아님)
        if re.search(r"\[참고 문서\]\s*해당 없음", ans) or re.search(r"범위를 벗어나|실시간 시장 데이터|응해 드릴 수 없|공개할 수 없어", ans):
            _ok = "  정상 예외(근거 문서 없음이 정상: 실시간·무관·보안 거절)" + (" — 단, '[참고 문서] 해당 없음' 표기 누락" if "[참고 문서]" not in ans else "")
            return out + [_ok] + check_form(q, ans) + [x for x in check_semantic(q, body) if "하나" not in x]
        return out + ["  (표시 출처 청크 없음 — 이하 검사 불가)"] + check_compare_relation(body) + check_recommend_wording(q, body) + check_source_integrity(ans) + check_form(q, ans)
    out += check_rates(body, texts) + check_products(body, texts) + check_calc(body, texts) + check_conditions(body, texts) + check_requirements(q, body) + check_qrules(q, body)
    out += check_compare_relation(body) + check_recommend_wording(q, body, texts) + check_source_integrity(ans) + check_semantic(q, body) + check_form(q, ans)
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
