# -*- coding: utf-8 -*-
"""diag_prodgate.py — v13.15 상품명 게이트를 실제 코퍼스 + 실제 답변 문장으로 재현(API 호출 없음)."""
import json, re, sys
d = json.load(open("chunks.json", encoding="utf-8")); it = d if isinstance(d, list) else d.values()
_CORPUS_NORM = "\u0001".join(re.sub(r"\s+", "", (c.get("text", "") if isinstance(c, dict) else str(c))) for c in it)
_NOINFO = re.compile(r"(확인할 수 없|확인되지 않|확인이 어렵|포함되어 있지 않|자료에 없|"
                     r"자료에는 없|찾을 수 없|나와 있지 않|나와있지 않|명시되어 있지 않|"
                     r"제시되어 있지 않|제시되지 않|매기지 않|"
                     r"(?:지정|특정|선정|단정|answer|골라|선택)할 수 없|"
                     r"알려드릴 수 없|확답을 드릴 수 없|말씀드리기 어렵|"
                     r"비교하기 어렵|제공하기 어렵|판단하기 어렵|파악할 수 없|"
                     r"드릴 수 없|알 수 없)")
_PROD_SUFFIX = r"(?:펀드|투자신탁|ETF|ETN|리츠|연금보험|저축보험|변액보험)"
_PROD_PARTICLE = r"(?:와|과|는|은|이|가|을|를|의|도|로|에|에서|이나|나|처럼|같은|등)?"
_PROD_HIT = re.compile(_PROD_SUFFIX + r"(?=" + _PROD_PARTICLE + r"(?![가-힣]))")   # 접미어 뒤 조사만 허용
_PROD_BRAND = re.compile(r"^(?:미래에셋|삼성|KB|신한|한국투자|NH|키움|에셋플러스|한화|교보|하나|우리|IBK|DB|메리츠|"
                         r"피델리티|슈로더|블랙록|AB|TIGER|KODEX|ARIRANG|KBSTAR|HANARO|ACE|SOL|RISE)")
_PROD_UNITWORD = re.compile(r"^\d[\d,.]*(?:등급|년차?|%|만원|만|개|세|일|회|호|억|천)?$")


def _is_marker_word(w):
    """이 단어가 '특정 상품'을 가리키는 표지인가(브랜드·영문 약어·제N호·증권/투자신탁·영숫자 혼합)."""
    if _PROD_BRAND.search(w): return True
    if re.search(r"[A-Z]{2,}", w): return True
    if re.search(r"제\s*\d+\s*호|증권|투자신탁|자산운용", w): return True
    if re.search(r"\d", w) and re.search(r"[A-Za-z가-힣]", w) and not _PROD_UNITWORD.match(w): return True
    return False


def annotate_unknown_products(ans, question=""):
    """문서에 없는 특정 상품명을 찾아 ※주석 병기(삭제 없음). → (답변, 미확인 상품명 목록)
    방법: 상품 접미어(펀드·투자신탁·ETF…) 앞의 단어열(구두점으로 경계, 최대 8단어)에서 '표지 단어'부터 끝까지를
    상품명 후보로 보고, 후보의 어떤 꼬리도 코퍼스에 없으면 미확인. 유형 명칭('채권형 펀드')은 표지가 없어 대상 아님."""
    body = ans.split("[참고 문서]")[0]
    unknown = []
    for m in _PROD_HIT.finditer(body):
        left = body[max(0, m.start() - 60): m.start()]
        left = re.split(r"[.,:;!?()\[\]\n\"'“”‘’※]|" + _PROD_SUFFIX + _PROD_PARTICLE + r"(?![가-힣])", left)[-1]
        words = (left + m.group(0)).split()
        words = words[-8:]
        idx = [i for i, w in enumerate(words) if _is_marker_word(w)]
        if not idx:
            continue
        cand_words = words[idx[0]:]
        if len(cand_words) == 1 and re.fullmatch(_PROD_SUFFIX + _PROD_PARTICLE, cand_words[0]):
            continue                       # 'ETF'·'펀드' 접미어 단독은 유형 표기이지 상품명이 아님
        grounded = False
        for k in range(len(cand_words)):
            tail = re.sub(r"\s+", "", "".join(w + " " for w in cand_words[k:]))
            if len(tail) < 6:
                break
            if tail in _CORPUS_NORM:
                grounded = True
                break
        if not grounded:
            # 축약 표기 보호: 브랜드어·접미어를 뺀 핵심부(4자 이상)가 코퍼스에 있으면 실재 상품의 줄임말로 본다
            #   (예: '미래에셋 또박또박연금펀드' → 핵심 '또박또박연금' ∈ '…또박또박연금받는펀드')
            core_words = [w for w in cand_words if not _PROD_BRAND.fullmatch(w)]
            core = re.sub(_PROD_SUFFIX + r"$", "", re.sub(r"\s+", "", " ".join(core_words)))
            core = re.sub(_PROD_PARTICLE + r"$", "", core)
            if len(core) >= 4 and core in _CORPUS_NORM:
                grounded = True
        if grounded:
            continue
        s0 = body.rfind("\n", 0, m.start()); s1 = body.find("\n", m.end())
        sent = body[s0 + 1: s1 if s1 != -1 else len(body)]
        if _NOINFO.search(sent):
            continue
        # 단어 끝 조사 제거('글로벌TDF2050은' → '글로벌TDF2050') 후 이름 확정, 같은 핵심이면 중복 등록 안 함
        cw = [re.sub(r"(?:은|는|이|가|을|를|의|도)$", "", w) if not _PROD_HIT.search(w) else w for w in cand_words]
        name = " ".join(cw)
        core_key = re.sub(_PROD_SUFFIX + _PROD_PARTICLE + r"$", "", re.sub(r"\s+", "", name))
        if not any(core_key == re.sub(_PROD_SUFFIX + _PROD_PARTICLE + r"$", "", re.sub(r"\s+", "", u)) for u in unknown):
            unknown.append(name)
    if unknown:
        # v13.15: 문서에 없는 상품은 '유사 상품의 속성을 끌어오는' 것 자체가 근거 없음 → 그 이름이 언급된 문장·행·
        #   표 블록(마크다운 '|' 형태와 변환 후 '(… vs …)' 형태 모두)을 제거하고 비교를 중단한다. 실재 상품과
        #   같은 문장에 있으면 문장 단위로만 잘라 실재 정보는 보존. 고지를 맨 앞에 두고 상품 식별 정보를 요청한다.
        keys = [re.sub(r"\s+", "", u) for u in unknown]
        keys += [k for k in (re.sub(_PROD_SUFFIX + _PROD_PARTICLE + r"$", "", x) for x in keys) if len(k) >= 5]   # 핵심부(접미어 제외)로도 대조
        def _has(txt):
            n = re.sub(r"\s+", "", txt)
            return any(k in n for k in keys)
        lines = body.split("\n")
        out, i, dropped = [], 0, 0
        while i < len(lines):
            ln = lines[i]
            if ln.lstrip().startswith("|"):                       # 마크다운 표 블록
                j = i
                while j < len(lines) and lines[j].lstrip().startswith("|"):
                    j += 1
                if _has("".join(lines[i:j])):
                    dropped += j - i
                else:
                    out.extend(lines[i:j])
                i = j
                continue
            if _has(ln) and ln.strip().startswith("(") and ("vs" in ln or "—" in ln):   # 변환된 표 헤더
                i += 1; dropped += 1
                while i < len(lines) and re.match(r"\s*-\s", lines[i]):
                    i += 1; dropped += 1
                continue
            if _has(ln):
                if re.match(r"\s*(?:\d+[.)]|[-*•·])\s", ln) or len(ln.strip()) <= 30:
                    i += 1; dropped += 1                          # 목록 항목·제목 줄은 통째로
                    continue
                sents = re.split(r"(?<=[.!?])(?<!\d\.)\s+", ln)
                keep = [st for st in sents if not _has(st)]
                dropped += len(sents) - len(keep)
                if keep and not (len(keep) == 1 and re.fullmatch(r"\s*\d+[.)]\s*", keep[0])):
                    out.append(" ".join(keep))
                i += 1
                continue
            out.append(ln); i += 1
        # 제거로 고아가 된 짧은 제목 줄('수수료', '등급', '유의사항:' 등) 정리
        out = [ln for ln in out if not (0 < len(ln.strip()) <= 8 and not re.search(r"[.!?]|\d|^\s*[-*•]", ln))]
        body2 = re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()
        if len(re.sub(r"[\s※].*", "", body2)) < 20 and not re.search(r"[가-힣]{10,}", re.sub(r"※[^\n]*", "", body2)):
            body2 = ""                                            # 남은 내용이 사실상 없으면 고지만
        note = ("문의하신 " + ", ".join(f"'{u}'" for u in unknown[:3]) +
                "은(는) 제공된 자료에서 확인되지 않는 상품이므로 보수·위험등급·수익률·전략 등 어떤 속성도 "
                "자료로 확정할 수 없어 해당 상품에 대한 안내와 비교는 하지 않습니다. 정확한 상품명(운용사·상품 유형·"
                "클래스 또는 종목코드)을 알려주시면 제공된 자료 범위에서 다시 확인해 드리겠습니다.")
        if body2:
            note += " 아래는 자료에서 확인되는 범위의 안내입니다."
        tail = ("\n\n[참고 문서]" + ans.split("[참고 문서]", 1)[1]) if "[참고 문서]" in ans else ""
        ans = note + ("\n\n" + body2 if body2 else "") + tail
    return ans, unknown


# v13.13(일반 게이트 1b — 유형-속성 모순): 펀드·ETF·투자신탁(실적배당형)을 언급한 문장에서 '원금 보장'을
#   긍정 단정하면 문서 기준(투자원금 비보장)으로 완화한다. 예금·원리금보장상품 문맥이나 부정문은 불변.
_PB_FUND = re.compile(r"펀드|ETF|투자신탁|TDF|리츠|위험\s*등급")
_PB_SAFE = re.compile(r"예금|원리금\s*보장|원리금보장|보장되지|보장하지|보장이\s*아니|않")
_PB_CLAIM = re.compile(r"(?:거의\s*)?원금(?:이|을|은)?\s*보장(?:되|하|이\s*되)")


def soften_fund_guarantee(ans):
    n = 0
    out = []
    for ln in ans.split("\n"):
        sents = re.split(r"(?<=[.!?])\s+", ln)
        fixed = []
        for st in sents:
            if _PB_FUND.search(st) and _PB_CLAIM.search(st) and not _PB_SAFE.search(st):
                st2 = re.sub(r"거의\s*원금(?:이|을|은)?\s*보장(?:되면서|되고|되며|되어|돼)", "원금 손실 위험이 매우 낮으면서", st)
                st2 = re.sub(r"원금(?:이|을|은)?\s*보장(?:되는|되며|되고|됩니다|된다|돼요|되어)", "원금 손실 위험이 낮은 편이지만 원금이 보장되지는 않는", st2) if st2 == st else st2
                if st2 != st:
                    n += 1
                fixed.append(st2)
            else:
                fixed.append(st)
        out.append(" ".join(fixed))
    return "\n".join(out), n



TESTS = {
 "G10": " - 삼성클래식연금증권전환형자투자신탁 제1호[주식](위험 등급 2등급) 같은 주식형 펀드는 장기적으로 높은 성장 가능성을 목표로 합니다.\n - 삼성클래식연금증권전환형투자신탁 제1호[채권](위험 등급 5등급) 같은 채권형 펀드는 상대적으로 안전한 투자를 추구합니다.\n - 또한 삼성퇴직연금인덱스12M증권자투자신탁 제1호[채권](위험 등급 6등급) 역시 매우 낮은 위험 등급입니다.",
 "S2": "삼성클래식연금증권전환형자투자신탁 제1호[주식]의 위험등급은 2등급이고, 삼성클래식연금증권전환형투자신탁 제1호[채권]의 위험등급은 5등급입니다.",
 "S3": "삼성퇴직연금인덱스12M증권자투자신탁 제1호[채권]은 삼성자산운용주식회사가 운용하는 투자신탁으로 위험등급 6등급입니다.",
 "F01": "IRP(연금계좌) 자체가 원금을 보장하는 것은 아닙니다. 계좌 안에서 예금 등 원리금보장상품을 선택하면 원리금이 보장되지만, 펀드·ETF 등 실적배당형 상품은 투자원금을 보장하지 않아 원금 손실이 발생할 수 있습니다.",
 "P01": "'미래에셋투자하며또박또박연금받는펀드 C-P2'의 합성총보수는 연 0.87%이며, 위험 등급은 '보통위험'입니다.",
}
# 후보 추출 단계별 추적
def trace(body):
    for m in _PROD_HIT.finditer(body):
        left = body[max(0, m.start() - 60): m.start()]
        left = re.split(r"[.,:;!?()\[\]\n\"'“”‘’※]|" + _PROD_SUFFIX + _PROD_PARTICLE + r"(?![가-힣])", left)[-1]
        words = (left + m.group(0)).split()[-8:]
        idx = [i for i, w in enumerate(words) if _is_marker_word(w)]
        if not idx: print("   [후보없음]", words); continue
        cand = words[idx[0]:]
        tails = []
        for k in range(len(cand)):
            t = re.sub(r"\s+", "", " ".join(cand[k:]))
            if len(t) < 6: break
            tails.append((t, t in _CORPUS_NORM))
        print("   후보:", cand, "| 꼬리검사:", tails)
for k, t in TESTS.items():
    print("=" * 30, k)
    trace(t)
    a, u = annotate_unknown_products(t, "")
    print("   → 미확인:", u)
