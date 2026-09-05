# -*- coding: utf-8 -*-
# auto_probe.py — 문서에서 질문을 스스로 만들어 대량으로 던지고, '의심스러운 답변'만 남긴다.
#
#   왜 만드는가
#     사람이 질문을 하나씩 넣어 고치는 방식은 하루에 수십 건이 한계다.
#     오류는 '내가 떠올린 질문'이 아니라 '떠올리지 못한 질문'에서 난다.
#     → 문서가 스스로 던진 질문(FAQ)과 문서의 표제어로 질문을 만들어,
#       근거(그 청크)를 알고 있는 상태로 대량으로 물어본다.
#
#   중요한 원칙
#     여기서 나오는 [오류]는 코드 불변식 위반이라 확실하다.
#     [의심]은 사람이 봐야 하는 후보일 뿐이다. 자동으로 고치지 않는다.
#
#   사용법
#     python3 auto_probe.py --dry 30          질문만 30개 뽑아 눈으로 확인 (API 호출 없음)
#     python3 auto_probe.py --n 1000          1000건 실행 (약 4~5시간)
#     python3 auto_probe.py --n 1000 --resume 중단된 지점부터 이어서
#     결과: probe.jsonl (전체) / probe_flags.txt (걸린 것만)
import argparse, json, os, random, re, subprocess, sys, time

BASE = "http://localhost:8000/answer"
PACE = 1.2                 # 문항 사이 대기(초)
OUT_JSONL = "probe.jsonl"
OUT_FLAGS = "probe_flags.txt"


def _stop_if_concurrent():
    """회귀 테스트와 같이 돌면 429로 허위 실패가 난다 (실측). 코드가 막는다."""
    try:
        out = subprocess.run(["pgrep", "-af", "python3"],
                             capture_output=True, text=True, timeout=10).stdout
    except Exception:
        return
    me = str(os.getpid())
    for ln in out.splitlines():
        pid = ln.split()[0] if ln.split() else ""
        if pid in (me, str(os.getppid())):
            continue
        if "test_regression" in ln or "test_topic" in ln or "hunt_matrix" in ln:
            print("다른 테스트가 돌고 있습니다. 끝난 뒤에 실행하세요:\n  " + ln)
            sys.exit(2)


# ── main.py 가 가진 판정 문구·함수를 그대로 읽어온다 (두 군데서 판단하지 않기) ──
def _from_main(name, default):
    try:
        src = open("main.py", encoding="utf-8").read()
        m = re.search(rf'^{name}\s*=\s*"([^"]+)"', src, re.M)
        return m.group(1) if m else default
    except OSError:
        return default


RISK_CARD_MARK = _from_main("RISK_CARD_MARK", "[위험등급 정리")
RISK_WARN_MARK = _from_main("RISK_WARN_MARK", "[위험등급 원문 대조")


def _load_garble():
    """main.py의 garble_score를 그대로 가져온다 (같은 잣대를 두 번 만들지 않기)."""
    try:
        src = open("main.py", encoding="utf-8").read()
        lines = src.split("\n")
        keep, want = [], ("_ODD_CHAR", "_JAMO", "_NUMRUN", "_ASCII_JUNK",
                          "_OK1", "_LONE1", "GARBLE_WARN", "GARBLE_STRICT")
        i = 0
        while i < len(lines):
            ln = lines[i]
            if ln.startswith(want) or ln.startswith("def garble_score("):
                j = i + 1
                while j < len(lines) and (not lines[j].strip()
                                          or lines[j].startswith((" ", "\t", ")", "]", "}"))):
                    j += 1
                keep.append("\n".join(lines[i:j]))
                i = j
                continue
            i += 1
        ns = {"re": re}
        exec("import re\n" + "\n".join(keep), ns)
        return ns["garble_score"], ns.get("GARBLE_STRICT", 0.15)
    except Exception as e:
        print("garble_score 로드 실패(검사 일부 생략):", e)
        return (lambda t: 0.0), 1.0


garble_score, GARBLE_STRICT = _load_garble()

# ══════════════════════════════════════════════════════════════════
#  1) 질문 만들기 — 문서에서
# ══════════════════════════════════════════════════════════════════
_Q_IN_DOC = re.compile(r"[^\n.!?]{8,70}?(?:나요|까요|습니까|은가요|인가요|될까요)\s*\?")
# 머리표는 줄 맨 앞에만 있지 않다 — 실측: 청크가 한 줄로 뭉쳐 있어 0건이 나왔다
_HEAD = re.compile(r"[■○▶□◆●]\s*([^\n■○▶□◆●|]{4,28}?)\s*(?=[\n■○▶□◆●|]|$)")

# ── 질문에서 표 조각·페이지 머리글·앞 문장 꼬리를 떼어낸다 ──────────────
#   실측(--dry 30): "FAQ | S1,S4 52 | 포트폴리오·부분매도·구성비 | 포트폴리오 안의…",
#   "2 / 4 Mirae Asset Securities ○ 퇴직연금규약을…",
#   "따라서 … 운용지시가 필요합니다 3 [연금] 공제회 퇴직연금 정기예금은…"
#   질문이 깨지면 '답변이 틀린 것'이 아니라 '질문이 나쁜 것'이 걸린다 → 사냥이 무의미해진다.
_CUTS = [
    re.compile(r"^.*Mirae\s+Asset\s+Securities\s*"),      # 페이지 머리글
    re.compile(r"^.*\bFAQ\b\s*"),
    re.compile(r"^.*[|｜／]\s*"),                            # 표 칸 구분자 (마지막 것 기준)
    re.compile(r"^.*\]\s*"),                                # [연금] 같은 말머리
    re.compile(r"^.*(?:습니다|합니다|됩니다|입니다|바랍니다)\s*"),  # 앞 문장 꼬리
    re.compile(r"^.*[■○▶□◆●]\s*"),                          # 머리표
    # 앞 번호 — '55세'의 55를 떼면 안 되므로 구분점이나 공백이 뒤따를 때만
    re.compile(r"^\s*(?:\d{1,3}\s*[.)]|\d{1,3}\s+|[⑴-⒇①-⑳])\s*"),
    re.compile(r"^\s*[/·\-–—*]+\s*"),
]
# ── 재료 품질 문지기 (실측 --dry 20에서 걸러야 했던 것들) ────────────────
#   "KIS중단기지수 1-2Y" "~ 20230630" "매매수수료 0 0 0 주1) 매매회전율"
#   "년 10개월" "신한상대가치종합증권모투자신탁[채권" "ESG & Credit 통합 모니터링 체계"
#   → 이런 조각으로 만든 질문에 '확인할 수 없다'고 답하는 건 오답이 아니라 정답이다.
#     걸러내지 않으면 의심 목록이 쓰레기로 찬다.
_TERM_BAD = re.compile(r"[~\[\]{}<>&|＊*/]|\d{3,}|주\s*\d\s*\)|^\s*\d|"
                       r"^[년월일회호개차]\b|지수|투자신탁|펀드|증권자|모투자")
_JOSA_END = re.compile(r"(?:을|를|이|가|은|는|에|의|와|과|로|으로|및|또는|하여|따른)$")
# 지시어로 시작하는 질문은 앞 문맥이 있어야 답할 수 있다 — 혼자서는 답이 없다
_DEIXIS = re.compile(r"^(?:이것|그것|이거|그거|여기|거기|이런|그런|이때|그때|해당|위의|"
                     r"동\s|상기)|^[이그저]\s")
_QWORD = {"어떻게", "무엇", "언제", "어디", "얼마", "무슨", "어느", "왜", "누가",
          "가능", "해야", "되나요", "있나요", "하나요", "인가요", "합니까", "됩니까",
          "보나요", "건가요", "가요", "때", "것", "수", "제가", "저는"}


def _ok_term(t):
    """사람이 물어볼 만한 '주제'인가 — 문장 조각·상품명·표 찌꺼기를 걷어낸다"""
    if not (4 <= len(t) <= 20):
        return False
    if _TERM_BAD.search(t) or _JOSA_END.search(t):
        return False
    if len(re.findall(r"[가-힣]", t)) < 3:
        return False
    return True


def _ok_question(q):
    """혼자 놓고 봐도 답할 수 있는 질문인가"""
    if len(q) < 14 or _DEIXIS.search(q):
        return False
    body = [w for w in re.findall(r"[가-힣A-Za-z]{2,}", q)
            if w not in _QWORD and not any(w.startswith(k) for k in _QWORD)]
    return len(body) >= 2


_QOK = re.compile(r"^[가-힣A-Za-z0-9(][^|｜\]]{6,58}\?$")


def _clean_q(q):
    """표 조각·머리글·앞 문장을 떼고, 사람이 물어볼 만한 문장만 남긴다."""
    q = re.sub(r"\s+", " ", q).strip()
    for c in _CUTS:
        q = c.sub("", q, count=1).strip()
    q = re.sub(r"^\s*(?:\d{1,3}\s*[.)]|\d{1,3}\s+)\s*", "", q).strip()
    return q if (_QOK.match(q) and _ok_question(q)) else ""
# v2: 머리표(■○)만으로는 30개밖에 안 나왔다. 정의문과 제목 기호에서도 뽑는다.
_DEF = re.compile(r"([가-힣A-Za-z][가-힣A-Za-z0-9()·\s]{2,24}?)\s*(?:이란|란)\s+")
_TITLE = re.compile(r"[【<\[]\s*([^】>\]|\n]{4,26}?)\s*[】>\]]")

# 문서 용어에 사용자 사정을 붙인 변형 — 같은 근거를 다른 길로 묻는다.
#   (조건이 붙으면 답이 달라져야 하는데 그대로 나오는 실패를 잡는다)
CONTEXT = [
    "저는 55세이고 IRP를 5년 넘게 갖고 있어요. {q}",
    "회사가 DC형인데요, {q}",
    "올해 퇴직해서 퇴직금을 IRP로 받았어요. {q}",
    "소득이 없는 전업주부입니다. {q}",
    "총급여 5,000만원 직장인이에요. {q}",
]

_FUND = re.compile(r"(미래에셋[가-힣A-Za-z0-9]{2,40}(?:투자신탁|펀드)"
                   r"(?:\s*제?\d+호)?(?:\s*종류[A-Za-z0-9\-]{1,6})?"
                   r"(?:\([가-힣A-Za-z]{1,10}\))?)")
_JUNK = re.compile(r"[『』〔〕｢｣＠＃＄％＆￥∙◇◆■□▲▼¨′″]|[ㄱ-ㅎㅏ-ㅣ]")

TEMPLATES = [
    # 어떤 명사구를 넣어도 말이 되는 형태만 쓴다.
    #   (동사를 붙이는 형태는 '…시 세금 하면 세금은?' 같은 비문을 만들었다)
    "{t}에 대해 알려주세요.",
    "{t}, 자세히 설명해 주세요.",
    "{t} 관련해서 제가 알아야 할 게 뭔가요?",
    "{t}에 대해 조건과 절차를 알려주세요.",
    "{t} 관련해서 수수료나 비용이 드나요?",
    "{t}, 기한이 언제까지인가요?",
    "55세인데 {t}에 대해 알려주세요.",
    "{t}에 세금은 어떻게 붙나요?",
    "{t} 신청 절차가 어떻게 되나요?",
    "{t}에 제가 해당되는지 어떻게 확인하나요?",
]


def _clean(s):
    s = re.sub(r"\s+", " ", s).strip(" ·-–—:：")
    return s


_dup_dropped = [0]


_NEGW = re.compile(r"없|있|불가|가능|되나|안\s|못")


def _negs(q):
    """부정·긍정 표지 — 이게 다르면 답이 반대여야 하는 '다른 질문'이다"""
    return frozenset(_NEGW.findall(q))


def _sig(q):
    """질문의 바이그램 집합 — 조사·띄어쓰기 차이를 흡수해 '거의 같은 질문'을 재는 자"""
    z = re.sub(r"[\s,.?!'\"()·]", "", q)
    return {z[i:i + 2] for i in range(len(z) - 1)}


def build_questions(chunks, n, seed=20260901):
    rnd = random.Random(seed)
    faq, terms, funds, term_hits = [], [], [], {}
    for c in chunks:
        t = c.get("text") or ""
        src = c.get("source") or ""
        # 머리표(■ ○ ▶ □)는 정상 문서에도 흔하다. 그것만 떼고 깨짐을 본다.
        #   (그러지 않으면 표제어가 있는 '멀쩡한 청크'가 통째로 걸러진다)
        if garble_score(re.sub(r"^\s*[■○▶□◆●·]\s*", "", t, flags=re.M)) >= 0.30:
            continue                      # 깨진 청크에서 만든 질문은 질문 자체가 깨진다
        for m in _Q_IN_DOC.finditer(t):
            q = _clean_q(m.group())
            if q and garble_score(q) < 0.15:
                faq.append((q, src))
        for m in list(_HEAD.finditer(t)) + list(_DEF.finditer(t)) \
                + list(_TITLE.finditer(t)):
            term = _clean(m.group(1))
            term = re.sub(r"^\d+\s*[.)]?\s*", "", term).strip()
            if _ok_term(term) and garble_score(term) < 0.15 \
                    and not term.endswith("?") and "Mirae" not in term:
                terms.append((term, src))
                term_hits[term] = term_hits.get(term, 0) + 1
        for m in _FUND.finditer(t):
            nm = _clean(m.group(1))
            if 8 <= len(nm) <= 45 and "모투자신탁" not in nm:
                funds.append(nm)          # 모투자신탁은 고객이 직접 사는 상품이 아니다

    # 같은 문장이 여러 청크·여러 문서에 나온다. 질문 글자 기준으로 한 번만 쓴다
    #   (안 그러면 똑같은 질문에 토큰을 수십 번 쓴다)
    def _uniq(pairs):
        """글자가 같은 것 + '거의 같은' 것을 뺀다. 재료 단계에서 빼야 변형까지 안 퍼진다.
        (실측: '연금저축을 중도해지하면 세금은?' / '연금저축 중도 해지 시 세금은?'
         — 이건 새 질문이 아니라 같은 질문이다. 토큰만 쓰고 오류는 안 나온다.)"""
        seen, kept, out2 = set(), [], []
        for k, v in pairs:
            key = re.sub(r"\s", "", k)
            if key in seen:
                _dup_dropped[0] += 1
                continue
            g = _sig(k)
            if len(g) < 3:
                continue
            neg = _negs(k)
            near = False
            for g2, n2 in kept:
                # 겹침 계수 — 실측으로 갈랐다: 같은 질문 0.76~1.00 / 다른 질문 0.11~0.45
                if len(g & g2) / max(min(len(g), len(g2)), 1) < 0.65:
                    continue
                if neg != n2:
                    continue      # '없나요?' vs '있나요?' — 답이 반대여야 하는 다른 질문이다
                near = True
                break
            if near:
                _dup_dropped[0] += 1
                continue
            seen.add(key)
            kept.append((g, neg))
            out2.append((k, v))
        return out2

    faq = _uniq(faq)
    # 두 곳 이상에 나온 말만 '주제'로 본다 — 한 번뿐인 것은 대개 문장 조각이다
    terms = _uniq([(t, sc) for t, sc in terms if term_hits.get(t, 0) >= 2])
    funds = list(dict.fromkeys(funds))
    rnd.shuffle(faq); rnd.shuffle(terms); rnd.shuffle(funds)

    out = []
    # (A) 문서가 스스로 던진 질문 — 답이 문서 안에 있다는 것이 보장된다
    for q, src in faq:
        out.append(dict(kind="A", q=q, src=src))
    # (A2) 같은 질문에 사용자 사정을 붙인 변형 — 원 질문 하나당 딱 한 번만.
    #   같은 질문을 여러 번 던지는 것은 사냥이 아니라 토큰 낭비다.
    for i, (q, src) in enumerate(faq):
        out.append(dict(kind="A2", src=src,
                        q=CONTEXT[i % len(CONTEXT)].format(q=q)))
    # (B) 표제어 × 말투 — 용어 하나당 서로 다른 템플릿 2개까지
    for i, (t, src) in enumerate(terms):
        for k in range(2):
            out.append(dict(kind="B", src=src,
                            q=TEMPLATES[(i * 2 + k) % len(TEMPLATES)].format(t=t)))
    # (C) 상품 비교 — 표·위험등급 기계를 자극한다 (과거 결함이 가장 많이 난 자리)
    for i in range(len(funds) - 1):
        out.append(dict(kind="C", src="",
                        q=f"{funds[i]}와 {funds[i+1]}를 비교해서 표로 보여주세요."))

    # 재료 단계에서 유사 질문을 이미 뺐다. 여기서는 글자 완전일치만 정리한다.
    seenq, ded = set(), []
    for x in out:
        k = re.sub(r"\s", "", x["q"])
        if k in seenq:
            _dup_dropped[0] += 1
            continue
        seenq.add(k)
        ded.append(x)
    out = ded
    rnd.shuffle(out)
    # 종류가 골고루 섞이도록: A를 절반, 나머지를 B/C로
    pools = {k: [x for x in out if x["kind"] == k] for k in ("A", "A2", "B", "C")}
    # 문서가 던진 질문을 가장 두껍게 — 답이 문서에 있다는 게 보장되기 때문
    share = [("A", 0.35), ("A2", 0.20), ("B", 0.28), ("C", 0.17)]
    pick = []
    for k, frac in share:
        pick += pools[k][:max(int(n * frac), 1)]
    # 남는 자리는 있는 것으로 채운다
    if len(pick) < n:
        have = {id(x) for x in pick}
        for k, _f in share:
            for x in pools[k]:
                if id(x) not in have:
                    pick.append(x)
                    if len(pick) >= n:
                        break
            if len(pick) >= n:
                break
    rnd.shuffle(pick)
    pick = pick[:n]
    for i, x in enumerate(pick, 1):
        x["id"] = f"P{i:04d}"
    return pick, {k: len(v) for k, v in pools.items()}


# ══════════════════════════════════════════════════════════════════
#  2) 자동 검사 — 확실한 [오류]와 사람이 볼 [의심]을 나눈다
# ══════════════════════════════════════════════════════════════════
GLOBAL_NEVER = ["[문서1]", "[문서2]", "[문서3]", "[문서4]", "[문서5]",
                "[문서6]", "[문서7]", "[문서8]", "<br", "<BR", "</p>", "<strong>"]
_NOINFO = re.compile(r"확인할 수 없|확인되지 않|자료에 없|명시되어 있지 않|포함되어 있지 않")
_GUESS = ["예상됨", "가능성 있음", "것으로 보입니다", "추정됩니다", "일 것으로 판단",
          "일반적으로 알려", "통상적으로"]
_INFER = ["간주되기 때문", "판단되기 때문", "해석되기 때문", "시사합니다", "유추할 수 있"]
_NUM = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(원|만원|억|%|퍼센트|년|개월|일|회|등급|배)")
# v11: 세제 프롬프트 규칙이 답변에 넣는 확정 숫자들 — 검색 근거에 없어도 정당하다.
#   (실측: 44건 중 다수가 600/900/16.5% 같은 규칙 숫자였다. 400만원은 구기준
#    금지값이므로 절대 여기 넣지 않는다.)
_RULE_NUMS = {"600만원", "900만원", "1800만원", "5500만원", "4500만원",
              "1500만원", "300만원", "16.5%", "13.2%", "3.3%", "5.5%",
              "15.4%", "10%", "55세", "5년"}
_CODE_LINE = ("[위험등급", "※", "[참고 문서]", "[연금수령 요건",
              "자료 없음'으로 표시된 항목")
# ── v7: 저장본만으로 찾을 수 있는 결함들 (API 호출 없음 = 크레딧 0원) ──────
#   실측 P0013: "[문서1, 문서2]" 가 그대로 나갔다 — v9.1 정규식이 단독형만 잡았다
_DOCNUM_LIST = re.compile(r"\[\s*문서\s*\d+(?:\s*[,·/및~-]+\s*(?:문서\s*)?\d+)+\s*\]")
#   실측 P0002/P0017: 본문 한가운데 "(출처: doc29.xlsx)" — 사용자가 열 수 없는 이름
_FILENAME = re.compile(r"\b(?:doc\d+|R\d+_[A-Za-z0-9]+)\.(?:pdf|xlsx|docx|hwp|txt)\b",
                       re.I)
#   문장이 끝나지 않고 잘린 답변 (max_tokens 초과) — 사용자에게 그대로 보인다
_END_OK = re.compile(r"(?:[.!?…\]\)]|다|요|음|함|임|됨|것|자료 없음|\||:)\s*$")


def _body_lines(ans):
    """코드가 붙인 카드·출처 줄을 뺀 '모델이 쓴 본문'만"""
    return [l for l in ans.splitlines()
            if l.strip() and not l.strip().startswith(_CODE_LINE)]


def check(item, ans, trace, ctx):
    hard, soft = [], []
    if not ans or "일시적인 오류" in ans:
        hard.append("답변 실패")
        return hard, soft
    for k in GLOBAL_NEVER:
        if k in ans:
            hard.append(f"내부 표기 노출: {k}")
    if "자료 없음 |" in ans and "'자료 없음'으로 표시된 항목" not in ans:
        hard.append("자료 없음 각주 누락")
    if re.search(r"\\[~*_\[\]()#+]", ans):
        hard.append("마크다운 이스케이프 노출")
    if "$$" in ans or "\\times" in ans:
        hard.append("수식 표기 노출")
    _rr = [l for l in ans.splitlines()
           if l.count("|") >= 2 and ("위험등급" in l or "위험 등급" in l)]
    if _rr and len(re.findall(r"[1-6]\s*등급", _rr[0])) >= 2 \
            and RISK_CARD_MARK not in ans and RISK_WARN_MARK not in ans:
        hard.append("위험등급 정리 누락")
    if "[참고 문서]" not in ans and "무관" not in trace:
        hard.append("출처 표기 누락")
    # v7: 내부 순번을 묶어 쓴 형태 (실측 P0013)
    _m = _DOCNUM_LIST.search(ans)
    if _m:
        hard.append(f"내부 순번 목록 노출: {_m.group()}")
    # v7: 본문에 내부 파일명 노출 — [참고 문서] 줄에만 있어야 한다 (실측 P0002)
    for ln in ans.splitlines():
        if ln.strip().startswith("[참고 문서]"):
            continue
        _f = _FILENAME.search(ln)
        if _f:
            hard.append(f"본문에 파일명 노출: {_f.group()}")
            break
    # v7: 문장이 끊긴 채 끝난 답변 (생성 토큰 초과)
    _bl = _body_lines(ans)
    if _bl and len(_bl[-1]) >= 15 and not _END_OK.search(_bl[-1].rstrip()):
        hard.append(f"문장 미완결(잘림): …{_bl[-1][-30:]}")
    # v7: 표의 칸 수가 머리글과 다르면 화면이 깨진다
    _rows = [l for l in ans.splitlines() if l.count("|") >= 2]
    if len(_rows) >= 3:
        _w = _rows[0].count("|")
        _bad = sum(1 for l in _rows[1:] if l.count("|") != _w)
        if _bad:
            hard.append(f"표 칸수 불일치({_bad}행, 머리글 {_w}칸)")
    # v7: 같은 문장을 반복하는 답변
    _sents = [x.strip() for x in
              re.split(r"(?<=[.!?])\s+", " ".join(l for l in _bl if l.count("|") < 2))
              if len(x.strip()) >= 15]
    for _s in set(_sents):
        if _sents.count(_s) >= 2:
            soft.append(f"같은 문장 반복 {_sents.count(_s)}회: {_s[:40]}")
            break

    # 깨진 글자가 사용자에게 그대로 나갔는가
    for ln in ans.splitlines():
        if ln.startswith(_CODE_LINE) or ln.count("|") >= 2:
            continue
        # 홑글자 밀도만으로는 법조문('제 N조')이 걸린다 — 자모·이상기호·숫자나열
        # 같은 확실한 신호가 같이 있을 때만 깨진 것으로 본다 (실측 P0279 오탐)
        if len(ln) >= 20 and garble_score(ln) >= GARBLE_STRICT \
                and re.search(r"[ㄱ-ㅎㅏ-ㅣ『』〔〕｢｣＠＃＄％＆￥∙◇◆■□▲▼]"
                              r"|(?:(?<=\s)|^)\d{3,}(?:\s+\d{3,}){2,}", ln):
            hard.append(f"깨진 원문 노출: {ln[:40]}")
            break

    # ── 여기부터는 [의심] — 사람이 봐야 한다 ──
    for g in _GUESS:
        if g in ans:
            soft.append(f"추측 표현: {g}")
            break
    for g in _INFER:
        if g in ans:
            soft.append(f"지어낸 추론: {g}")
            break
    # (A) 문서가 던진 질문인데 '자료에 없다'고 답한 경우 — 검색이 놓친 것일 수 있다
    if item["kind"] in ("A", "A2") and _NOINFO.search(ans[:120]):
        soft.append("문서에 있는 질문인데 '자료 없음'")
    # 근거에 없는 숫자 — 계산형 답변은 제외(코드가 계산해서 붙인 값이 정당하다)
    #   ctx가 None이면 재채점 중이라 근거를 갖고 있지 않다 → 이 검사만 건너뛴다
    if ctx is not None and not re.search(r"[×xX*]\s*\d|계산하면|검산|=\s*\d", ans):
        flat_ctx = re.sub(r"[,\s]", "", ctx)
        seen = []
        for ln in ans.splitlines():
            if ln.startswith(_CODE_LINE):
                continue
            for num, unit in _NUM.findall(ln):
                raw = num.replace(",", "")
                if len(raw.replace(".", "")) < 2:
                    continue
                _qflat = re.sub(r"[,\s]", "", item["q"])
                if raw in flat_ctx or num in ctx or raw in _qflat:
                    continue
                if f"{raw}{unit}" in _RULE_NUMS:
                    continue          # 프롬프트 규칙 숫자 — 창작이 아니다
                seen.append(f"{num}{unit}")
        seen = list(dict.fromkeys(seen))[:3]
        if seen:
            soft.append("근거에 없는 숫자: " + ", ".join(seen))
    return hard, soft


# ══════════════════════════════════════════════════════════════════
def ask(qid, q):
    import requests
    wait = 4
    for attempt in range(4):
        try:
            r = requests.get(BASE, params={"question_id": qid, "question": q},
                             timeout=300)
            if r.status_code == 429:
                time.sleep(wait); wait *= 2
                continue
            d = r.json()
            return d.get("answer", ""), d.get("think_trace", ""), \
                d.get("retrieved_context", "")
        except Exception as e:
            if attempt == 3:
                return "", f"요청 실패: {e}", ""
            time.sleep(wait); wait *= 2
    return "", "429 반복", ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--dry", type=int, default=0)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--extra", default="",
                    help="한 줄에 하나씩 적은 질문 파일 — 그대로 추가로 던진다")
    a = ap.parse_args()

    with open("chunks.json", encoding="utf-8") as f:
        chunks = json.load(f)
    _dup_dropped[0] = 0
    qs, stat = build_questions(chunks, max(a.n, a.dry))
    if a.extra and os.path.exists(a.extra):
        ex = [l.strip() for l in open(a.extra, encoding="utf-8")
              if l.strip() and not l.startswith("#")]
        # v10: 외부 질문도 같은 잣대 — 본체와 겹치거나 서로 비슷하면 버린다.
        #   (같은 질문을 다르게 적은 것은 새 질문이 아니다)
        def _near(g1, n1, g2, n2):
            return n1 == n2 and \
                len(g1 & g2) / max(min(len(g1), len(g2)), 1) >= 0.65
        _seen = [(_sig(x["q"]), _negs(x["q"])) for x in qs]
        _seenk = {re.sub(r"\s", "", x["q"]) for x in qs}
        kept = []
        for q in ex:
            k = re.sub(r"\s", "", q)
            g, ng = _sig(q), _negs(q)
            if k in _seenk or len(g) < 3:
                continue
            if any(_near(g, ng, g2, n2) for g2, n2 in _seen):
                continue
            _seenk.add(k)
            _seen.append((g, ng))
            kept.append(q)
        for i, q in enumerate(kept, 1):
            qs.append(dict(kind="E", q=q, src="", id=f"E{i:04d}"))
        print(f"외부 질문 {len(kept)}건 추가 "
              f"(중복·유사 {len(ex) - len(kept)}건 제외, --extra {a.extra})")
    print(f"질문 재료: 문서질문 {stat['A']} / 사정붙임 {stat['A2']} / "
          f"용어템플릿 {stat['B']} / 상품비교 {stat['C']}"
          f"  (중복·유사 {_dup_dropped[0]}건 제외)  → 실행 {len(qs)}건")

    if a.dry:
        for x in qs[:a.dry]:
            print(f"  [{x['kind']}] {x['q']}")
        return

    _stop_if_concurrent()
    done = set()
    if a.resume and os.path.exists(OUT_JSONL):
        for ln in open(OUT_JSONL, encoding="utf-8"):
            try:
                done.add(json.loads(ln)["id"])
            except Exception:
                pass
        print(f"이어서 실행: 이미 끝난 {len(done)}건 건너뜀")

    fj = open(OUT_JSONL, "a", encoding="utf-8")
    ff = open(OUT_FLAGS, "a", encoding="utf-8")
    ff.write(f"\n===== {time.strftime('%Y-%m-%d %H:%M')} 시작 =====\n")
    t0, n_hard, n_soft = time.time(), 0, 0
    todo = [x for x in qs if x["id"] not in done]
    for i, x in enumerate(todo, 1):
        time.sleep(PACE)
        ans, trace, ctx = ask(x["id"], x["q"])
        hard, soft = check(x, ans, trace, ctx)
        fj.write(json.dumps(dict(id=x["id"], kind=x["kind"], q=x["q"], src=x["src"],
                                 hard=hard, soft=soft, answer=ans, trace=trace,
                                 ctx=ctx[:6000]),
                            ensure_ascii=False) + "\n")
        fj.flush()
        if hard or soft:
            n_hard += bool(hard); n_soft += bool(soft and not hard)
            ff.write(f"\n[{x['id']}] ({x['kind']}) {x['q']}\n")
            if x["src"]:
                ff.write(f"  근거 문서: {x['src']}\n")
            for h in hard:
                ff.write(f"  [오류] {h}\n")
            for s in soft:
                ff.write(f"  [의심] {s}\n")
            ff.write("  답변: " + re.sub(r"\s+", " ", ans)[:300] + "\n")
            ff.flush()
        if i % 10 == 0 or i == len(todo):
            el = time.time() - t0
            eta = el / i * (len(todo) - i)
            print(f"[{i}/{len(todo)}] 오류 {n_hard} / 의심 {n_soft} "
                  f"(경과 {el/60:.0f}분, 남은 예상 {eta/60:.0f}분)", flush=True)
    fj.close()
    print(f"\n끝. 오류 {n_hard}건 / 의심 {n_soft}건 → {OUT_FLAGS} 를 보세요.")
    ff.write(f"===== 끝: 오류 {n_hard} / 의심 {n_soft} / 전체 {len(todo)} =====\n")
    ff.close()


if __name__ == "__main__":
    main()
