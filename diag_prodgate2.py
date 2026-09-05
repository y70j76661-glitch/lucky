# -*- coding: utf-8 -*-
"""diag_prodgate2.py — v13.16 상품명 게이트를 실제 코퍼스 + 실제 답변 형태(굵게·불릿·따옴표 포함)로 재현. API 호출 없음.
기대: 실재 상품(G10·S2·S3·P01·F01)은 미확인 [] / M1b(질문에 지어낸 상품)는 강한 제거 / 답변에만 나온 지어낸 이름은 ※주석만."""
import json, re
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


_PROD_VERBWORD = re.compile(r"(?:하며|하고|이며|으로|로서|적인|적으로|하는|되는|합니다|입니다|있는|없는|같은|위한|통해|따라|및|또는|"
                            r"그리고|대한|관한|경우|때문|보다|처럼|만큼|"
                            r"에서|이나|에게|부터|까지|마다|조차|라도|은|는|이|가|을|를|과|와|도|의|에)$")
_PROD_GENERIC = re.compile(r"(?:ETF|ETN|펀드|예금|적금|IRP|DC|DB|연금저축|연금저축펀드|퇴직연금|연금보험|보험|채권|주식|투자신탁|리츠|TDF|"
                           r"주식형|채권형|혼합형|인덱스|디폴트옵션|원리금보장상품|연금계좌|연금)")


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
        # v13.16: 게이트 시점엔 마크다운 굵게(**)·따옴표·괄호·가운뎃점이 단어에 붙어 있다 → 벗겨낸 뒤 대조
        #   (실측: '**삼성클래식…투자신탁'이 코퍼스와 불일치 → 실재 상품을 미확인으로 오판·삭제)
        words = [w.strip("*'\"“”‘’·-()[]{}<>,.:;") for w in words]
        words = [w for w in words if w][-8:]
        idx = [i for i, w in enumerate(words) if _is_marker_word(w)]
        if not idx:
            continue
        cand_words = words[idx[0]:]
        # v13.16: 표지 뒤에 서술어('하며·으로·하는·적인·통해…')가 끼면 그 앞까지가 이름이 아니다 → 마지막 서술어
        #   다음 단어부터 후보로 삼되, 그 안에 표지가 없으면 후보 아님(문장 단어를 끌어모아 가짜 이름 생성 방지)
        _cut = [i for i, w in enumerate(cand_words[:-1]) if _PROD_VERBWORD.search(w)]
        if _cut:
            cand_words = cand_words[_cut[-1] + 1:]
            if not any(_is_marker_word(w) for w in cand_words):
                continue
        if len(cand_words) == 1 and (re.fullmatch(_PROD_SUFFIX + _PROD_PARTICLE, cand_words[0])
                                     or _PROD_GENERIC.fullmatch(re.sub(_PROD_PARTICLE + r"$", "", cand_words[0]))):
            continue                       # 'ETF'·'펀드'·'IRP'·'연금저축' 같은 일반명사 단독은 상품명이 아님
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
        if len(re.sub(r"\s+", "", name)) < 6:
            continue                       # '·ETF' 같은 구두점 잔재·짧은 조각은 상품명이 아님
        core_key = re.sub(_PROD_SUFFIX + _PROD_PARTICLE + r"$", "", re.sub(r"\s+", "", name))
        if not any(core_key == re.sub(_PROD_SUFFIX + _PROD_PARTICLE + r"$", "", re.sub(r"\s+", "", u)) for u in unknown):
            unknown.append(name)
    if unknown:
        # v13.16 안전장치: 강한 제거(문장·표 삭제)는 사용자가 질문에서 직접 언급한 미확인 상품에만 적용한다.
        #   답변에만 나온 이름(LLM이 문서에서 가져왔을 가능성이 큼)은 삭제하지 않고 ※주석만 병기 → 대조가
        #   어긋나도 실재 상품 답변이 통째로 사라지는 일은 없다.
        qn = re.sub(r"\s+", "", question or "")
        def _in_q(u):
            ck = re.sub(_PROD_SUFFIX + _PROD_PARTICLE + r"$", "", re.sub(r"\s+", "", u))
            return len(ck) >= 5 and ck in qn
        strong = [u for u in unknown if _in_q(u)]
        soft = [u for u in unknown if not _in_q(u)]
        if soft and not strong:
            note = ("※ " + ", ".join(f"'{u}'" for u in soft[:3]) +
                    "은(는) 제공된 자료에서 확인되지 않는 상품명이므로 실제 상품 정보는 별도 확인이 필요합니다.")
            if "[참고 문서]" in ans:
                head, tail = ans.split("[참고 문서]", 1)
                ans = head.rstrip() + "\n\n" + note + "\n\n[참고 문서]" + tail
            else:
                ans = ans.rstrip() + "\n\n" + note
            return ans, unknown
        unknown = strong
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



TESTS = [
 ("G10-bold", "좋은 연금상품 하나 추천해주세요.", " - 상품 예시: '**삼성클래식연금증권전환형자투자신탁 제1호[주식]**' 같은 고위험 상품이 적합합니다.\n - **삼성클래식연금증권전환형투자신탁 제1호[채권]**(위험 등급 5등급) 같은 채권형 펀드는 안전합니다.\n - 또한 **삼성퇴직연금인덱스12M증권자투자신탁 제1호[채권]**(위험 등급 6등급) 역시 매우 낮은 위험 등급입니다."),
 ("S2", "삼성클래식연금 주식형과 채권형의 위험등급은 각각 몇 등급인가요?", "**삼성클래식연금증권전환형자투자신탁 제1호[주식]**의 위험등급은 2등급이고, 삼성클래식연금증권전환형투자신탁 제1호[채권]의 위험등급은 5등급입니다."),
 ("S3", "삼성퇴직연금인덱스12M 채권 펀드의 위험등급과 총보수를 알려주세요.", "- **삼성퇴직연금인덱스12M증권자투자신탁 제1호[채권]**은 삼성자산운용주식회사가 운용하는 투자신탁으로 위험등급 6등급입니다."),
 ("F01", "IRP는 원금이 보장되죠?", "IRP(연금계좌) 자체가 원금을 보장하는 것은 아닙니다. 계좌 안에서 예금 등 원리금보장상품을 선택하면 원리금이 보장되지만, 펀드·ETF 등 실적배당형 상품은 투자원금을 보장하지 않아 원금 손실이 발생할 수 있습니다."),
 ("P01", "또박또박연금펀드의 합성총보수와 위험등급을 알려주세요.", "'**미래에셋투자하며또박또박연금받는펀드 C-P2**'의 합성총보수는 연 0.87%이며, 위험 등급은 '보통위험'입니다."),
 ("G11", "원금 손실 없이 가장 좋은 상품은요?", "1. **우리은행 예금**: 퇴직연금 원리금보장상품으로서 운용됩니다."),
 ("M1b", "삼성 글로벌TDF2050 연금펀드 수수료랑 등급 알려줘. KODEX 200 ETF랑 비교도.", "**삼성 글로벌TDF2050 연금펀드**의 합성총보수는 0.88%입니다.\n| 항목 | 삼성 글로벌TDF2050 연금펀드 | KODEX 200 ETF |\n| 보수 | 0.88% | 0.15% |\n각 상품에 대한 상세 정보는 문서에서 확인 가능합니다.\n[참고 문서] doc37.pdf"),
 ("환각-answer-only", "좋은 연금상품 하나 추천해주세요.", "추천드릴 만한 상품으로는 **미래에셋 슈퍼프리미엄연금펀드**(총보수 0.5%)와 TIGER 미국배당다우존스 ETF가 있습니다.\n[참고 문서] doc1.pdf"),
]
ok = True
for name, q, t in TESTS:
    a, u = annotate_unknown_products(t, q)
    expect_unknown = name in ("M1b", "환각-answer-only")
    good = (bool(u) == expect_unknown)
    ok &= good
    print(("OK " if good else "★ ") + f"[{name}] 미확인={u}")
    if name in ("M1b", "환각-answer-only"):
        print("   ->", a.replace("\n", " | ")[:260])
print("=" * 60); print("전부 기대대로" if ok else "★ 기대와 다른 항목 있음 — 패치 올리지 말 것")
