# -*- coding: utf-8 -*-
"""
verify_layer.py — 외부 공식기관 '선택적' 교차검증 레이어 (never-block)

역할: 미래에셋 공식 문서(Primary Source)를 최우선 답변 근거로 두고, ETF
  상장폐지·만기·제도 변경처럼 '시간이 지나 달라질 수 있는' 핵심 Claim만
  허용된 공식기관(Verification Source)으로 짧은 시간 안에 교차검증한다.
  외부 검증은 기존 RAG 답변을 절대 대체하거나 막지 않는다.

세 개의 독립 안전장치 중 ③에 해당한다.
  ① 없는 정보 생성 방지     (검색·카드·후처리 — main.py)
  ② 미래에셋 문서 충실       (프롬프트·근거검증 — main.py)
  ③ 공식기관 선택적 최신성 교차검증  ← 이 모듈. 실패해도 ①②는 그대로 동작.

절대 원칙(정직·안전):
  A) 공식·인증 경로만 사용한다. 비공식 라이브러리(pykrx 등), 웹페이지 내부/
     비공개 endpoint scraping, 인증 없이 우회되는 endpoint, 뉴스·블로그·포털
     금융정보 fallback — 전부 사용하지 않는다(코드에 존재하지 않음).
  B) 공식 API가 인증키·사전승인을 요구하면 숨기거나 우회하지 않고 명확히
     'auth_required'로 표시한다. 그런 기관은 adapter/인터페이스만 두고
     connector는 stub 상태로 남긴다(정직한 미연동).
  C) never-block. 연결실패·timeout·인증문제·데이터없음·파싱오류는 모두 답변을
     막지 않고 문서 기준 답변을 유지한다. 실패 이유는 내부 trace에만 남긴다.

호출: main.py가 최종 답변(ans) 확정 직후 1회 호출.
  results = verify_layer.verify_answer(ans, context, question, qtype)
  ans     = verify_layer.apply_verification(ans, results)   # STALE/CONFLICT만 병기
  trace  += verify_layer.verification_trace(results)        # think_trace/log용
기능 전체는 EXTERNAL_VERIFICATION_ENABLED=False면 완전 비활성(기존 동작 그대로).
"""
import concurrent.futures as _cf
import json
import os
import re
import time

try:                                     # 검증 비활성 환경에서도 import는 성공하게
    import requests
except Exception:
    requests = None

# ══════════════════════════════════════════════════════════════════════
# 0. Feature flag & 예산  (환경변수로도 제어 가능 — 예선/실서비스 분리)
# ══════════════════════════════════════════════════════════════════════
def _envbool(k, default):
    v = os.environ.get(k)
    return default if v is None else v.strip().lower() in ("1", "true", "yes", "on")

def _envfloat(k, default):
    try:
        return float(os.environ[k])
    except Exception:
        return default

def _envint(k, default):
    try:
        return int(os.environ[k])
    except Exception:
        return default

# 기본 OFF — 예선 채점 안정성 우선. 켤 때만 True(또는 env=true).
EXTERNAL_VERIFICATION_ENABLED = _envbool("EXTERNAL_VERIFICATION_ENABLED", False)
# 답변당 외부검증 총 시간 상한(초). 초과하면 남은 Claim은 검증하지 않는다.
EXTERNAL_VERIFICATION_TIMEOUT_SECONDS = _envfloat("EXTERNAL_VERIFICATION_TIMEOUT_SECONDS", 3.0)
# 개별 기관 호출 timeout(초).
EXTERNAL_VERIFICATION_PER_CALL_TIMEOUT = _envfloat("EXTERNAL_VERIFICATION_PER_CALL_TIMEOUT", 2.0)
# 답변당 최대 검증 Claim 수(비용·속도 상한).
EXTERNAL_VERIFICATION_MAX_CLAIMS = _envint("EXTERNAL_VERIFICATION_MAX_CLAIMS", 3)
# 동일 Claim 재조회 방지 캐시 TTL(초).
CACHE_TTL_SEC = _envint("EXTERNAL_VERIFICATION_CACHE_TTL", 6 * 3600)
# 데모/시연용 mock fixture 사용 여부(실제 미연동 상태에서 STALE/CONFLICT 동작 시연).
EXTERNAL_VERIFICATION_USE_FIXTURES = _envbool("EXTERNAL_VERIFICATION_USE_FIXTURES", False)
# 미래에셋 공식 웹(securities.miraeasset.com) 실시간 조회 사용 여부(1순위-B 검증소스).
#   기본 OFF — 켜면 실제 네트워크 호출(never-block·timeout·도메인 whitelist 적용).
EXTERNAL_VERIFICATION_LIVE_WEB = _envbool("EXTERNAL_VERIFICATION_LIVE_WEB", False)

# 구버전 호환 별칭(기존 코드가 참조할 수 있어 유지)
VERIFY_ENABLED = EXTERNAL_VERIFICATION_ENABLED

# ══════════════════════════════════════════════════════════════════════
# 1. Source Hierarchy & 공식기관 whitelist
#    Primary(답변 근거) vs Verification(최신성 검증)을 '역할'로 구분.
#    whitelist에 없는 출처는 이 dict에 아예 없음 → 비공식 fallback 구조적 불가.
# ══════════════════════════════════════════════════════════════════════
# ── Source Hierarchy ──────────────────────────────────────────────────
#   1순위-A: 주입된 미래에셋 공식 문서 = 답변 생성의 Primary Source(대체 불가)
#   1순위-B: 미래에셋증권 공식 웹(securities.miraeasset.com) = 최신성·상품상태·
#            제도안내 변화 '검증' 소스(주입 문서를 대체하지 않음). 실시간 조회.
#   2순위  : KRX·금감원·금융위·KSD·금투협·국세청·고용부·법령정보센터(공식기관)
PRIMARY_SOURCE = "미래에셋 공식 제공 문서(주입)"          # 1순위-A

# 1순위-B — 미래에셋 공식 웹(검증 소스). 도메인 whitelist로만 접근.
MIRAEASSET_WEB = {
    "key": "MAWEB",
    "name": "미래에셋증권 공식 웹",
    "domains": {"securities.miraeasset.com"},   # 이 호스트만 허용(internal API·서치snippet 금지)
    "role": ("Verification Source(1순위-B) — 주입 문서의 최신성·상품상태·서비스/제도 "
             "안내 변화 여부만 검증. 시장전망·추천·수익률기대 등 해석적 의견은 사용 안 함."),
}

# 검증에 쓰는 '객관 사실' Claim만 매핑 — 공식 공개 가이드 페이지(본문 서버렌더링 확인됨).
#   각 항목: 토픽 -> {url, concept(개념 정규식), value(기대값, 없으면 존재확인),
#                     conflict(개념 근처 다른 값 스캔), label}
#   ※ 근거는 '개념 ↔ 타깃(값/가능표현)'이 같은 의미단위(같은 표 행·문장)로 '연결'된
#     구간만 인정한다. 페이지 어딘가에 각각 따로 존재하는 것만으로는 VERIFIED 안 함.
FACT_PAGES = {
    "위험자산한도": {
        "url": "https://securities.miraeasset.com/hkp/hkp2005/n07.do",
        "concept": r"위험자산",
        "value": "70",                        # 감독규정상 위험자산 한도 70%
        "value_pat": r"70\s*%|70\s*퍼센트|백분의\s*70",
        "connect_window": 24,                 # 위험자산~70%가 이 글자수 안에 함께 있어야 연결로 인정
        # CONFLICT는 '위험자산 (투자)한도 XX%'처럼 개념·한도·값이 '밀접'할 때만.
        #   (표의 다른 행 값 100% 등에 오탐하지 않도록 엄격)
        "conflict_pat": r"위험자산\s*(?:투자\s*)?한도[^\n]{0,10}?(\d{1,3})\s*%",
        "label": "퇴직연금 위험자산 투자한도(70%)",
    },
    "연금ETF매매": {
        "url": "https://securities.miraeasset.com/public/mw/guide/html/orderstock.html",
        "concept": r"ETF|ETN|리츠|상장지수",
        # 제목의 '매매안내'만으로는 부족 — 실제 '가능/거래/주문/매수' 의미가 붙어야 인정
        "avail_pat": (r"매매\s*(?:가능|할\s*수\s*있|하실\s*수\s*있|가능합니다)|"
                      r"거래\s*(?:가능|할\s*수\s*있|하실\s*수\s*있)|주문\s*(?:가능|하실\s*수\s*있)|"
                      r"매수\s*(?:가능|하실\s*수\s*있)|투자할\s*수\s*있|담을\s*수\s*있"),
        "connect_window": 60,                 # ETF~가능표현이 이 글자수 안에 함께 있어야 연결
        "label": "연금계좌 ETF/ETN/리츠 매매 가능",
    },
}

# OFFICIAL_SOURCE_WHITELIST: 허용된 공식기관만(2순위). 뉴스/블로그/커뮤니티/포털 없음.
OFFICIAL_SOURCE_WHITELIST = {
    "KRX":   {"name": "한국거래소",       "for": ["상장여부", "상장폐지", "만기", "종목코드",
                                                "종목명", "시장상태", "ETF공시"]},
    "KSD":   {"name": "한국예탁결제원",   "for": ["증권기본정보", "종목식별정보"]},
    "FSS":   {"name": "금융감독원",       "for": ["금융상품공시", "펀드공시", "투자설명서", "DART"]},
    "FSC":   {"name": "금융위원회",       "for": ["금융정책", "연금제도", "규제변경", "보도자료"]},
    "KOFIA": {"name": "금융투자협회",     "for": ["펀드정보", "상품분류", "금융투자상품공시"]},
    "NTS":   {"name": "국세청",           "for": ["세액공제", "연금소득과세", "ISA세제", "금융상품세금"]},
    "MOEL":  {"name": "고용노동부",       "for": ["퇴직연금제도", "DB", "DC", "IRP"]},
    "LAW":   {"name": "국가법령정보센터", "for": ["법령", "시행령", "법조항유효성"]},
}
AUTHORITIES = OFFICIAL_SOURCE_WHITELIST   # 별칭

# ── 검증 결과 status (semantic) ──────────────────────────────────────
VERIFIED = "VERIFIED"                     # 공식기관이 문서 내용을 확인함
DOCUMENT_PRIMARY = "DOCUMENT_PRIMARY"     # 판정 근거 없음 → 문서 우선(경고 없음)
STALE_SUSPECTED = "STALE_SUSPECTED"       # 문서 작성 후 상태 변경 의심(만기·상폐 등)
CONFLICT = "CONFLICT"                     # 동일사실인데 공식기관과 명확 충돌
UNVERIFIABLE = "UNVERIFIABLE"             # 애초에 공식데이터로 판정 불가(의견·해석)
EXTERNAL_UNAVAILABLE = "EXTERNAL_VERIFICATION_UNAVAILABLE"  # 외부 검증 자체 불가

# ── 검증 시도 결과 reason (내부 trace/log 용) ────────────────────────
R_VERIFIED = "verified"                   # 공식기관 응답을 정상 수신·판정
R_SOURCE_NA = "source_not_available"      # 해당 기관 커넥터 미연동/미가용
R_AUTH = "auth_required"                  # 공식 API가 인증키·사전승인 요구(우회 안 함)
R_TIMEOUT = "timeout"                     # 제한 시간 내 응답 없음
R_NO_RESULT = "no_official_result"        # 연결됐으나 해당 항목 공식결과 없음
R_PARSER = "parser_error"                 # 응답 수신했으나 파싱 실패
R_DISABLED = "disabled"                   # 기능 OFF
R_NOT_REQUIRED = "not_required"           # 검증 대상 아님(시간민감·결정적 아님)
R_MOCK = "mock_fixture_demo"              # 시연/테스트용 mock — 실제 검증 아님

# reason → 답변에 경고를 병기할지(True는 STALE/CONFLICT status에서만 의미)
_FAILURE_REASONS = {R_SOURCE_NA, R_AUTH, R_TIMEOUT, R_PARSER}


# ══════════════════════════════════════════════════════════════════════
# 2. Claim schema
# ══════════════════════════════════════════════════════════════════════
def make_claim(cid, text, ctype, **kw):
    """검증 파이프라인이 다루는 Claim 1건의 표준 구조."""
    return {
        "claim_id": cid,
        "claim_text": text,
        "claim_type": ctype,            # 상품상태 / 제도 / 세제 / 법령 / 상품유형 / 의견 ...
        "time_sensitive": kw.get("time_sensitive", False),
        "decision_critical": kw.get("decision_critical", False),
        "internal_conflict": kw.get("internal_conflict", False),
        "verification_required": kw.get("verification_required", False),
        "entity_type": kw.get("entity_type"),                   # financial_product / regime
        "is_specific_product": kw.get("is_specific_product", False),  # 구체 상품(=검증가능)인가
        "web_topic": kw.get("web_topic"),                       # FACT_PAGES 토픽(1순위-B용)
        "preferred_authority": kw.get("preferred_authority"),
        "subject": kw.get("subject"),
        "document_evidence": kw.get("document_evidence", ""),
        "verification_status": kw.get("verification_status"),   # 위 status
        "verification_reason": kw.get("verification_reason"),   # 위 reason
        "verification_result": kw.get("verification_result"),   # 공식기관 응답 요약
        "authority_used": kw.get("authority_used"),
    }


# ══════════════════════════════════════════════════════════════════════
# 3. Claim 추출  (MVP: 규칙기반 — 추가 LLM 호출 없이 빠름)
#    확장판은 HCX로 문장별 Claim을 뽑되, MVP는 '검증 가치가 가장 큰'
#    상품 상태 Claim(자사 ETF명 + 시간민감 키워드)만 규칙으로 잡는다.
# ══════════════════════════════════════════════════════════════════════
_ETF_NAME = re.compile(r"(?:TIGER|KODEX|KBSTAR|ARIRANG|SOL|ACE|PLUS)\s?[가-힣A-Za-z0-9()&·\-+]+")
_TIME_SENSITIVE = re.compile(
    r"상장|상장폐지|상폐|만기|존속|운용\s*중단|판매\s*(?:중|가능|중단)|"
    r"신규\s*매수|현재\s*투자|투자\s*가능|거래\s*가능")
_DECISION_CRITICAL = re.compile(
    r"위험등급|기초지수|만기일|종목코드|연금계좌\s*투자|위험자산\s*한도|ETF|상장지수")

# ── 구체 상품 판별 (generic 표현은 KRX 상품검증에서 제외) ──────────────
_BRAND = re.compile(r"^(?:TIGER|KODEX|KBSTAR|ARIRANG|SOL|ACE|PLUS)\s*")
_GENERIC_CORE = {"", "ETF", "상품", "펀드", "ETF상품", "상장지수펀드", "상장지수", "지수"}
_CODE6 = re.compile(r"^\d{6}$")


def _is_specific_product(name):
    """'TIGER ETF'·'ETF 상품'처럼 일반 표현이면 False, 실제 식별 가능한
    상품명(또는 6자리 종목코드)이면 True. is_specific_product=True만 KRX로 routing."""
    core = _BRAND.sub("", name).strip()
    core_norm = re.sub(r"\s", "", core)
    if _CODE6.match(core_norm):          # 종목코드 → 검증 가능
        return True
    if core_norm in _GENERIC_CORE:       # 브랜드+ETF/상품 뿐 → 일반 표현
        return False
    return len(core_norm) >= 3           # 실질 상품 설명이 남으면 구체 상품


# ── 시간에 따라 바뀔 수 있는 제도·세제·법령 개념 (상품이 아니어도 검증 후보) ──
#   (개념정규식, 라벨, claim_type, 우선기관)
_REGIME = [
    (re.compile(r"세액공제(?:율|\s*한도)|공제\s*한도|세액공제"), "세액공제 기준", "tax", "NTS"),
    (re.compile(r"(?:연금저축|IRP|연금계좌|퇴직연금)[^.\n]{0,8}납입\s*한도|납입\s*한도"),
     "연금 납입한도", "limit", "NTS"),
    (re.compile(r"집중투자한도|투자\s*한도"), "제도상 투자한도", "pension_rule", "MOEL"),
    (re.compile(r"ISA[^.\n]{0,10}(?:세제|비과세|한도)|금융소득\s*종합과세"), "ISA/금융 세제", "tax", "NTS"),
    (re.compile(r"기타소득세|연금소득세|과세\s*이연|세율"), "연금 과세", "tax", "NTS"),
    (re.compile(r"법\s*제?\d+\s*조|시행령|법령|개정|시행\s*(?:일|예정)"), "관련 법령·제도", "regulation", "LAW"),
]


def _snippet(text, kw, span=40):
    i = text.find(kw)
    if i < 0:
        return ""
    return re.sub(r"\s+", " ", text[max(0, i - span):i + len(kw) + span]).strip()


# ── 1순위-B(미래에셋 공식 웹)로 라이브 검증할 '객관 사실' MVP Claim ──────
#   (개념정규식, 라벨, claim_type, web_topic) — 시장전망·추천·수익률은 제외.
_WEB_CLAIMS = [
    (re.compile(r"위험자산\s*(?:투자\s*)?한도|위험자산[^.\n]{0,10}70"),
     "퇴직연금 위험자산 투자한도", "pension_rule", "위험자산한도"),
    (re.compile(r"(?:연금저축|연금계좌|IRP|DC|퇴직연금)[^.\n]{0,12}ETF[^.\n]{0,12}"
                r"(?:매매|거래|투자|가능)|ETF[^.\n]{0,8}(?:매매|거래)\s*가능"),
     "연금계좌 ETF 매매 가능 여부", "상품상태", "연금ETF매매"),
]


def extract_claims(answer, context="", question="", qtype=""):
    """답변 후보에서 검증 대상 Claim을 뽑는다.
    (w) 미래에셋 공식 웹으로 검증할 객관사실 MVP(위험자산 한도·연금 ETF 매매) → MAWEB
    (a) 구체 상품 상태(ETF, is_specific_product=True) — 일반표현 제외
    (b) 시간민감 제도·세제·법령 개념(tax/limit/pension_rule/regulation)
    검증 가치가 큰 것만 좁게 잡는다 — 전 문장 검색 금지."""
    claims = []
    seen = set()
    hay = answer + " " + (question or "")
    web_hit = set()          # 웹으로 잡은 개념(중복 방지: 아래 (b)에서 제외)

    # (w) 미래에셋 공식 웹 검증 대상(1순위-B) — 최우선
    for rgx, label, ctype, topic in _WEB_CLAIMS:
        if label in seen:
            continue
        mm = rgx.search(hay)
        if mm:
            seen.add(label); web_hit.add(topic)
            claims.append(make_claim(
                f"C{len(claims)+1}", f"{label}(공식 웹 최신 기준 대조)", ctype,
                time_sensitive=True, decision_critical=True, verification_required=True,
                entity_type="regime" if ctype != "상품상태" else "financial_product",
                is_specific_product=(ctype == "상품상태"),
                web_topic=topic, preferred_authority="MAWEB", subject=label,
                document_evidence=_snippet(hay, mm.group(0)[:8])))

    # (a) 구체 상품 상태 Claim — generic('TIGER ETF' 등)은 제외
    if _TIME_SENSITIVE.search(answer) or _DECISION_CRITICAL.search(answer):
        for m in _ETF_NAME.finditer(answer):
            name = re.split(
                r"\s*(?:설정액|총보수|합성총보수|보수|위험|수익|종류|클래스)",
                m.group(0))[0].strip()
            name = re.sub(r"(?:도|를|을|은|는|이|가|에서|에|와|과|의)?[.,)\]]*$", "", name).strip()
            if len(name) < 5 or name in seen:
                continue
            seen.add(name)
            if not _is_specific_product(name):      # 일반 표현 → 상품검증 대상 제외
                continue
            claims.append(make_claim(
                f"C{len(claims)+1}", f"{name}의 현재 상장·거래 가능 여부", "상품상태",
                time_sensitive=True, decision_critical=True, verification_required=True,
                entity_type="financial_product", is_specific_product=True,
                preferred_authority="KRX", subject=name,
                document_evidence=_snippet(answer, name)))

    # (b) 시간민감 제도·세제·법령 개념 Claim (상품 아님 → is_specific_product=False)
    for rgx, label, ctype, auth in _REGIME:
        if label in seen:
            continue
        if label == "제도상 투자한도" and "위험자산한도" in web_hit:
            continue          # 위험자산 한도는 (w)에서 이미 MAWEB로 잡음(중복 방지)
        mm = rgx.search(hay)
        if mm:
            seen.add(label)
            claims.append(make_claim(
                f"C{len(claims)+1}", f"{label}의 현행 기준(개정·한도 변경 가능)", ctype,
                time_sensitive=True, decision_critical=True, verification_required=True,
                entity_type="regime", is_specific_product=False,
                preferred_authority=auth, subject=label,
                document_evidence=_snippet(hay, mm.group(0)[:8])))

    return claims[:EXTERNAL_VERIFICATION_MAX_CLAIMS]


# ══════════════════════════════════════════════════════════════════════
# 4. 검증 필요 판단 + Routing (claim → 기관)
# ══════════════════════════════════════════════════════════════════════
ROUTING = [
    (re.compile(r"상장|상폐|만기|ETF|상장지수|종목코드"), "KRX"),
    (re.compile(r"법령|시행령|법\s*제?\d+조|조항"), "LAW"),
    (re.compile(r"퇴직연금|DB|DC|IRP\b"), "MOEL"),
    (re.compile(r"세액공제|과세|세율|ISA\s*세제|세금"), "NTS"),
    (re.compile(r"금융정책|제도\s*변경|규제"), "FSC"),
    (re.compile(r"펀드\s*공시|투자설명서|상품\s*공시"), "FSS"),
    (re.compile(r"펀드|상품분류"), "KOFIA"),
]


def needs_verification(claim):
    """모든 문장을 검색하지 않는다 — 시간민감 or 결정적 or 내부충돌만.
    또한 상품(financial_product)은 '구체 상품(is_specific_product)'일 때만 검증."""
    if claim.get("entity_type") == "financial_product" and not claim.get("is_specific_product"):
        return False
    return bool(claim.get("verification_required") and
                (claim["time_sensitive"] or claim["decision_critical"]
                 or claim["internal_conflict"]))


def route_authority(claim):
    if claim.get("preferred_authority"):
        return claim["preferred_authority"]
    hay = (claim["claim_text"] + " " + (claim.get("claim_type") or ""))
    for pat, auth in ROUTING:
        if pat.search(hay):
            return auth
    return None


# ══════════════════════════════════════════════════════════════════════
# 5. Verifier(adapter) 인터페이스 + 기관별 구현
#    ─ check(claim) -> (status, reason, evidence_dict)
#    ─ available=True 인 기관만 실제 조회. MVP는 전부 미연동(정직한 stub).
#    ─ 공식 API가 인증키/사전승인을 요구하면 auth_required 로 표시(우회 안 함).
# ══════════════════════════════════════════════════════════════════════
def _norm_name(s):
    return re.sub(r"[\s()·\-+&]", "", s or "")


class Verifier:
    """공식기관 어댑터 인터페이스. 실제 커넥터는 이 클래스를 상속해 구현한다."""
    authority = None
    available = False        # 공식·인증 경로가 실제로 구성됐을 때만 True

    def check(self, claim):
        raise NotImplementedError


class UnavailableAdapter(Verifier):
    """미연동 기관 — 실제 조회 없이 '연결 불가' 사유만 정직하게 반환.
    답변을 바꾸지 않는다(DOCUMENT_PRIMARY 유지)."""
    def __init__(self, authority, reason=R_SOURCE_NA, note=None):
        self.authority = authority
        self.reason = reason
        self._note = note or "해당 공식기관 커넥터 미연동(로드맵) — 문서 기준 유지"

    def check(self, claim):
        # 연결 자체가 불가하므로 status는 문서 우선, reason으로 이유를 남긴다.
        return EXTERNAL_UNAVAILABLE, self.reason, {
            "authority": self.authority, "note": self._note}


class MockAdapter(Verifier):
    """시연·테스트용 — fixture(정답 대장)로 VERIFIED/STALE/CONFLICT 동작을 재현.
    실제 공식기관 응답을 흉내만 낼 뿐, 절대 답변의 '공식 근거'로 쓰지 않는다.
    (EXTERNAL_VERIFICATION_USE_FIXTURES=True 일 때만 활성)."""
    def __init__(self, authority, fixtures):
        self.authority = authority
        self.available = True
        self.fixtures = fixtures or {}

    def check(self, claim):
        subj = _norm_name(claim.get("subject") or "")
        for key, spec in self.fixtures.items():
            k = _norm_name(key)
            if subj and (k in subj or subj in k):
                st = spec.get("status", DOCUMENT_PRIMARY)
                # reason은 R_MOCK — 절대 '진짜 검증 성공(verified)'으로 취급하지 않는다.
                return st, R_MOCK, {
                    "authority": self.authority, "found": True, "is_mock": True,
                    "note": "[DEMO/시연-실제 공식검증 아님] " + spec.get("note", "")}
        # fixture에 없으면 판정 근거 없음 — 문서 우선(역시 mock 컨텍스트임을 표시)
        return DOCUMENT_PRIMARY, R_MOCK, {
            "authority": self.authority, "found": False, "is_mock": True,
            "note": "[DEMO/시연] fixture 미등록 — 문서 기준 유지"}


# ── KRX 어댑터 (정직한 미연동) ─────────────────────────────────────────
#   한국거래소 공식 KRX OPEN API는 회원가입 → 인증키 신청 → API 활용신청/승인
#   절차가 필요하고, 요청에 AUTH_KEY가 사용된다. 인증키·승인 없이 우회 호출하는
#   비공식 endpoint / pykrx / 웹 internal API 는 사용하지 않는다.
#   따라서 현재는 available=False, reason=auth_required 로 정직하게 표시한다.
#   운영 시 승인된 AUTH_KEY를 환경변수(KRX_AUTH_KEY)로 주입하고 아래 TODO의
#   공식 엔드포인트를 구현하면 실연동으로 승격된다.
class KRXAdapter(Verifier):
    authority = "KRX"

    def __init__(self):
        self.auth_key = os.environ.get("KRX_AUTH_KEY")   # 승인된 인증키가 있을 때만
        self.available = bool(self.auth_key) and requests is not None

    def check(self, claim):
        if not self.available:
            # 인증키·사전승인이 없으므로 우회하지 않고 명확히 알린다.
            return EXTERNAL_UNAVAILABLE, R_AUTH, {
                "authority": "KRX",
                "note": "KRX 공식 OPEN API는 회원가입·인증키 신청·API 활용승인이 "
                        "필요. 승인된 KRX_AUTH_KEY 주입 전까지 미연동(우회 조회 안 함)."}
        # ── 운영(승인 후) 경로 ──────────────────────────────────────────
        try:
            # TODO(운영): KRX 공식 OPEN API 엔드포인트/파라미터를 승인 문서대로 구현.
            #   requests.get(OFFICIAL_URL, params={"AUTH_KEY": self.auth_key, ...},
            #                timeout=EXTERNAL_VERIFICATION_PER_CALL_TIMEOUT)
            #   → 정상 응답이면 상장목록 파싱 후 subject 존재여부로
            #     VERIFIED / STALE_SUSPECTED 판정, reason=R_VERIFIED.
            raise NotImplementedError("KRX official connector not implemented yet")
        except NotImplementedError:
            return EXTERNAL_UNAVAILABLE, R_SOURCE_NA, {
                "authority": "KRX", "note": "공식 커넥터 미구현(승인 후 활성)"}
        except Exception as e:
            return EXTERNAL_UNAVAILABLE, R_PARSER, {
                "authority": "KRX", "error": str(e)[:80]}


# ── fixtures: 시연용 (실제 공식 근거 아님) ─────────────────────────────
#   EXTERNAL_VERIFICATION_USE_FIXTURES=True 일 때 MockAdapter가 사용.
VERIFY_FIXTURES = {
    "KRX": {
        # 예: 문서엔 있으나 만기·상폐된 것으로 가정 → STALE_SUSPECTED 시연
        "TIGER 26-04회사채": {"status": STALE_SUSPECTED,
                              "note": "(시연) 해당 종목이 현재 상장목록에서 확인되지 않음"},
        # 예: 정상 상장 확인 → VERIFIED 시연
        "TIGER 미국S&P500": {"status": VERIFIED,
                            "note": "(시연) 현재 상장 종목으로 확인"},
    },
}


# ── 미래에셋 공식 웹 어댑터(1순위-B) — 실제 live 조회 ────────────────────
#   조건: 공식 공개 페이지 직접 조회 / 도메인 whitelist / internal API·서치 snippet
#   금지 / 페이지 '본문'에서 근거 문장 확인 / timeout·실패 시 never-block /
#   live source 임을 trace 표시. 객관 사실 Claim(FACT_PAGES)만 검증.
from urllib.parse import urlparse as _urlparse

_TAG = re.compile(r"(?is)<(script|style)[^>]*>.*?</\1>")
_TAGS = re.compile(r"(?s)<[^>]+>")
_WS = re.compile(r"\s+")


def _html_to_text(html):
    t = _TAG.sub(" ", html or "")
    t = _TAGS.sub(" ", t)
    t = (t.replace("&nbsp;", " ").replace("&amp;", "&")
           .replace("&lt;", "<").replace("&gt;", ">").replace("&#39;", "'"))
    return _WS.sub(" ", t).strip()


def _domain_ok(url):
    try:
        host = (_urlparse(url).hostname or "").lower()
    except Exception:
        return False
    return host in MIRAEASSET_WEB["domains"]      # 정확히 whitelist host만


class MiraeAssetWebVerifier(Verifier):
    """미래에셋증권 공식 웹(securities.miraeasset.com)에서 '객관 사실'만 라이브 검증.
    주입 문서를 대체하지 않는다 — 최신성·상품상태·서비스/제도 안내 변화만 대조."""
    authority = "MAWEB"

    def __init__(self):
        self.available = EXTERNAL_VERIFICATION_LIVE_WEB and requests is not None

    def _fetch_text(self, url):
        r = requests.get(url, timeout=EXTERNAL_VERIFICATION_PER_CALL_TIMEOUT,
                         headers={"User-Agent": "Mozilla/5.0 (compatible; PensionRAG/1.0)",
                                  "Accept-Language": "ko,en;q=0.8"})
        r.raise_for_status()
        try:
            r.encoding = r.apparent_encoding or r.encoding or "utf-8"
        except Exception:
            pass
        return _html_to_text(r.text)

    def check(self, claim):
        if not self.available:
            # 라이브 웹 조회 비활성(기본) — 우회 없이 문서 기준 유지.
            return EXTERNAL_UNAVAILABLE, R_SOURCE_NA, {
                "authority": "MAWEB", "source_kind": "live_web",
                "note": "미래에셋 공식 웹 라이브 조회 OFF(EXTERNAL_VERIFICATION_LIVE_WEB=false)"}
        topic = claim.get("web_topic")
        page = FACT_PAGES.get(topic)
        if not page or requests is None:
            return DOCUMENT_PRIMARY, R_NO_RESULT, {
                "authority": "MAWEB", "source_kind": "live_web",
                "note": "대응 공식 페이지 없음 — 문서 기준 유지"}
        url = page["url"]
        if not _domain_ok(url):                     # 도메인 whitelist 강제
            return EXTERNAL_UNAVAILABLE, R_SOURCE_NA, {
                "authority": "MAWEB", "source_kind": "live_web",
                "note": "whitelist 외 도메인 — 조회 안 함"}
        try:
            text = self._fetch_text(url)
        except Exception as e:
            return EXTERNAL_UNAVAILABLE, R_PARSER, {
                "authority": "MAWEB", "source_kind": "live_web",
                "url": url, "error": str(e)[:80]}
        if not text or len(text) < 200:             # 본문이 비었으면(JS셸 등) 판정 불가
            return EXTERNAL_UNAVAILABLE, R_PARSER, {
                "authority": "MAWEB", "source_kind": "live_web", "url": url,
                "note": "본문 텍스트 부족(동적 렌더링 의심) — 문서 기준 유지"}
        # 개념이 본문에 있어야 판정 시작
        if not re.search(page["concept"], text):
            return DOCUMENT_PRIMARY, R_NO_RESULT, {
                "authority": "MAWEB", "source_kind": "live_web", "url": url,
                "note": "공식 페이지 본문에서 해당 개념을 확인하지 못함 — 문서 기준 유지"}
        win = page.get("connect_window", 40)

        # (1) 값 검증형(예: 위험자산 70%) — 개념과 값이 '연결'된 구간만 인정
        if page.get("value"):
            quote = _connected_quote(text, page["concept"], page["value_pat"], win)
            if quote and re.search(page["value_pat"], quote):
                return VERIFIED, R_VERIFIED, {
                    "authority": "MAWEB", "source_kind": "live_web", "url": url,
                    "note": f"공식 웹 본문에서 '{page['label']}' 연결 근거 확인",
                    "quote": quote}
            # 개념 근처에 '다른 값'이 연결돼 있으면 CONFLICT(보수적)
            if page.get("conflict_pat"):
                cq = _connected_conflict(text, page["conflict_pat"], page["value"], win)
                if cq:
                    return CONFLICT, R_VERIFIED, {
                        "authority": "MAWEB", "source_kind": "live_web", "url": url,
                        "note": f"공식 웹 본문에서 문서값과 다른 값이 연결됨",
                        "quote": cq}
            # 연결 근거를 못 찾으면 VERIFIED를 억지로 유지하지 않는다 → 문서 우선(보수적)
            return DOCUMENT_PRIMARY, R_NO_RESULT, {
                "authority": "MAWEB", "source_kind": "live_web", "url": url,
                "note": "개념·값이 '연결된 근거'로 확인되지 않음 — VERIFIED 보류, 문서 기준 유지"}

        # (2) 존재 확인형(예: 연금 ETF 매매) — 개념과 '가능 의미'가 연결된 문장만 인정
        quote = _connected_quote(text, page["concept"], page["avail_pat"], win)
        if quote and re.search(page["avail_pat"], quote):
            return VERIFIED, R_VERIFIED, {
                "authority": "MAWEB", "source_kind": "live_web", "url": url,
                "note": f"공식 웹 본문에서 '{page['label']}' 연결 근거 확인", "quote": quote}
        # 제목만 있고 본문 '가능' 근거가 없으면 VERIFIED 안 함 → 문서 우선(보수적)
        return DOCUMENT_PRIMARY, R_NO_RESULT, {
            "authority": "MAWEB", "source_kind": "live_web", "url": url,
            "note": "제목 외 본문에서 '매매 가능' 연결 근거를 확인하지 못함 — 문서 기준 유지"}


def _connected_quote(text, concept_pat, target_pat, window=40):
    """개념(concept)과 타깃(값/가능표현 target)이 window 글자수 안에서 '연결'된
    실제 본문 구간을 찾아 그대로 인용한다. 없으면 None → 호출부가 보수적 처리.
    (페이지 어딘가에 각각 따로 있는 것만으로는 연결로 인정하지 않음)"""
    if not target_pat:
        return None
    for cm in re.finditer(concept_pat, text):
        lo = max(0, cm.start() - window)
        hi = min(len(text), cm.end() + window)
        seg = text[lo:hi]
        tm = re.search(target_pat, seg)
        if tm:
            s = min(cm.start(), lo + tm.start())
            e = max(cm.end(), lo + tm.end())
            return _WS.sub(" ", text[max(0, s - 6):e + 6]).strip()[:180]
    return None


def _connected_conflict(text, conflict_pat, expected, window=40):
    """개념과 '기대값과 다른 값'이 연결된 구간(=CONFLICT 근거)을 찾는다."""
    for m in re.finditer(conflict_pat, text):
        if m.groups() and _norm_name(m.group(1)) != _norm_name(expected):
            s = max(0, m.start() - 6)
            return _WS.sub(" ", text[s:m.end() + 6]).strip()[:180]
    return None


def _build_verifiers():
    """검증소스 어댑터 구성. 1순위-B(MAWEB) + 2순위 8기관.
    fixtures 모드면 8기관은 Mock으로 대체(시연). MAWEB는 LIVE_WEB 플래그로 실동작."""
    reg = {"MAWEB": MiraeAssetWebVerifier()}
    for auth in OFFICIAL_SOURCE_WHITELIST:
        if EXTERNAL_VERIFICATION_USE_FIXTURES:
            reg[auth] = MockAdapter(auth, VERIFY_FIXTURES.get(auth, {}))
        elif auth == "KRX":
            reg[auth] = KRXAdapter()
        else:
            reg[auth] = UnavailableAdapter(auth, reason=R_SOURCE_NA)
    return reg


VERIFIERS = _build_verifiers()


# ══════════════════════════════════════════════════════════════════════
# 6. 캐시 + per-call timeout
# ══════════════════════════════════════════════════════════════════════
_RESULT_CACHE = {}                       # key -> (ts, status, reason, evidence)
_EXECUTOR = _cf.ThreadPoolExecutor(max_workers=2)


def _cache_key(claim, authority):
    return f"{authority}:{_norm_name(claim.get('subject') or claim['claim_text'])}"


def _call_with_timeout(fn, timeout):
    """개별 기관 호출을 timeout으로 감싼다. 초과 시 (…, R_TIMEOUT, …)."""
    fut = _EXECUTOR.submit(fn)
    try:
        return fut.result(timeout=timeout)
    except _cf.TimeoutError:
        fut.cancel()
        return EXTERNAL_UNAVAILABLE, R_TIMEOUT, {"note": "외부 검증 시간 초과"}
    except Exception as e:
        return EXTERNAL_UNAVAILABLE, R_PARSER, {"error": str(e)[:80]}


def _cached_verify(claim, authority):
    key = _cache_key(claim, authority)
    hit = _RESULT_CACHE.get(key)
    if hit and time.time() - hit[0] < CACHE_TTL_SEC:
        return hit[1], hit[2], hit[3]
    v = VERIFIERS.get(authority)
    if v is None:
        return EXTERNAL_UNAVAILABLE, R_SOURCE_NA, {"note": "whitelist 외 기관"}
    status, reason, ev = _call_with_timeout(
        lambda: v.check(claim), EXTERNAL_VERIFICATION_PER_CALL_TIMEOUT)
    # '진짜 공식 응답'만 캐시한다. 일시 실패·mock 시연 결과는 캐시하지 않는다.
    #   (verified/no_official_result만 안정적 사실로 간주)
    if reason in (R_VERIFIED, R_NO_RESULT):
        _RESULT_CACHE[key] = (time.time(), status, reason, ev)
    return status, reason, ev


# ══════════════════════════════════════════════════════════════════════
# 7. 메인 진입점 — 절대 예외를 던지지 않는다(never-block)
#    파이프라인: (main.py가 RAG 답변 생성) → 여기서 핵심 Claim만 제한 시간 내
#    검증 → 성공 결과만 반환. 실패/비활성/예산초과는 답변에 영향 없음([]반환 또는
#    EXTERNAL_UNAVAILABLE status로만 표기).
# ══════════════════════════════════════════════════════════════════════
def verify_answer(answer, context="", question="", qtype="",
                  enabled=None, budget_sec=None):
    """검증이 필요한 Claim만 공식기관으로 교차검증. 실패·비활성 시 안전하게 축소.
    반환: claim 목록(각 verification_status/reason 채워짐). 예외 없음."""
    if enabled is None:
        enabled = EXTERNAL_VERIFICATION_ENABLED
    if not enabled:
        return []
    budget = budget_sec if budget_sec is not None else EXTERNAL_VERIFICATION_TIMEOUT_SECONDS
    t0 = time.time()
    out = []
    try:
        claims = extract_claims(answer, context, question, qtype)
        for claim in claims[:EXTERNAL_VERIFICATION_MAX_CLAIMS]:
            if time.time() - t0 > budget:               # 총 예산 초과 → 중단
                claim["verification_status"] = EXTERNAL_UNAVAILABLE
                claim["verification_reason"] = R_TIMEOUT
                out.append(claim)
                break
            if not needs_verification(claim):
                claim["verification_status"] = UNVERIFIABLE
                claim["verification_reason"] = R_NOT_REQUIRED
                out.append(claim); continue
            auth = route_authority(claim)
            if not auth or auth not in VERIFIERS:
                claim["verification_status"] = DOCUMENT_PRIMARY
                claim["verification_reason"] = R_SOURCE_NA
                out.append(claim); continue
            status, reason, ev = _cached_verify(claim, auth)
            claim["verification_status"] = status
            claim["verification_reason"] = reason
            claim["verification_result"] = ev.get("note")
            claim["authority_used"] = ev.get("authority") or auth
            claim["source_kind"] = ev.get("source_kind")     # live_web 등
            claim["evidence_url"] = ev.get("url")
            claim["evidence_quote"] = ev.get("quote")
            out.append(claim)
    except Exception:
        return out                     # 무슨 일이 있어도 답변을 막지 않는다
    return out


# ══════════════════════════════════════════════════════════════════════
# 8. 검증 결과를 답변에 '병기' (삭제·덮어쓰기 금지) + trace 생성
# ══════════════════════════════════════════════════════════════════════
def apply_verification(answer, results):
    """STALE_SUSPECTED / CONFLICT 만 안전 문구로 '덧붙인다'(병기).
    핵심 계약: 외부 정보로 미래에셋 문서 내용을 삭제·덮어쓰기하지 않는다.
      CONFLICT 여도 답변 본문은 그대로 두고 '차이가 있다'만 표시한다.
    VERIFIED/DOCUMENT_PRIMARY/UNVERIFIABLE/EXTERNAL_UNAVAILABLE 은 답변 불변."""
    if not results:
        return answer
    notes = []
    for c in results:
        st = c.get("verification_status")
        subj = c.get("subject") or c.get("claim_text")
        who = _source_name(c.get("authority_used"))
        # mock(시연) 결과는 문구에도 데모임을 명시 — 실제 공식 검증으로 오인 금지.
        tag = "[데모] " if c.get("verification_reason") == R_MOCK else ""
        if st == STALE_SUSPECTED:
            notes.append(
                f"※ {tag}제공된 자료에는 '{subj}' 관련 정보가 포함되어 있으나, 현재 "
                f"{who} 기준으로 상품의 상장·만기 등 상태가 변경되었을 가능성이 "
                f"있습니다. 신규 투자 가능 여부는 최신 공식 정보를 추가로 확인해 주세요.")
        elif st == CONFLICT:
            # 덮어쓰기 아님 — 문서 답변은 유지하고 '차이'만 알린다.
            notes.append(
                f"※ {tag}제공된 미래에셋 자료와 현재 {who} 정보 사이에 '{subj}'에 대한 "
                f"차이가 있어, 최신 공식 정보를 추가로 확인할 필요가 있습니다.")
    if not notes:
        return answer
    uniq = []
    for n in notes:
        if n not in answer and n not in uniq:
            uniq.append(n)
    return answer.rstrip() + ("\n\n" + "\n".join(uniq) if uniq else "")


def _source_name(key):
    """검증소스 표시명. 1순위-B(MAWEB) + 2순위 8기관 모두 조회."""
    if key == "MAWEB":
        return MIRAEASSET_WEB["name"]
    return OFFICIAL_SOURCE_WHITELIST.get(key, {}).get("name", "공식기관")


def verification_trace(results):
    """think_trace/log에 넣을 한 줄 요약. reason과 live 소스 여부까지 남긴다.
    반환 예: ' 6.5) 외부검증(live): 위험자산…=VERIFIED(verified/MAWEB·live)'"""
    if not results:
        return ""
    parts = []
    any_live = False
    for c in results:
        subj = (c.get("subject") or c.get("claim_text") or "")[:16]
        st = c.get("verification_status")
        rs = c.get("verification_reason")
        au = c.get("authority_used") or "-"
        live = "·live" if c.get("source_kind") == "live_web" else ""
        if live:
            any_live = True
        parts.append(f"{subj}={st}({rs}/{au}{live})")
    head = " 6.5) 외부검증" + ("(live 포함)" if any_live else "") + ": "
    return head + "; ".join(parts)


def verification_log(results):
    """구조화 로그(JSON 직렬화 가능). 파일 로깅·분석용. live 근거(url·quote) 포함."""
    return [{
        "claim_id": c.get("claim_id"),
        "subject": c.get("subject"),
        "status": c.get("verification_status"),
        "reason": c.get("verification_reason"),
        "authority": c.get("authority_used"),
        "source_kind": c.get("source_kind"),
        "evidence_url": c.get("evidence_url"),
        "evidence_quote": c.get("evidence_quote"),
        "result": c.get("verification_result"),
    } for c in (results or [])]


# ── 오프라인 점검용 CLI ────────────────────────────────────────────────
if __name__ == "__main__":
    sample = ("공격형 투자자가 검토할 수 있는 상품으로 TIGER 26-04회사채(A+이상)"
              "액티브를 연금 계좌에서 투자할 수 있습니다. 현재 상장되어 거래 가능합니다. "
              "TIGER 미국S&P500도 연금계좌에서 투자 가능합니다.")
    print("── 1) Claim 추출 ─────────────────────────")
    cl = extract_claims(sample)
    for c in cl:
        print(f"  {c['claim_id']} subject={c['subject']} "
              f"route={route_authority(c)} need={needs_verification(c)}")

    print("\n── 2) 기본(미연동) — never-block, 답변 불변 ─")
    res = verify_answer(sample, enabled=True)
    print("  trace:", verification_trace(res))
    print("  log  :", json.dumps(verification_log(res), ensure_ascii=False))
    print("  답변 변경 여부:", "변경됨" if apply_verification(sample, res) != sample else "불변(문서 우선)")

    print("\n── 3) fixtures 모드 — STALE/VERIFIED 시연 ─")
    EXTERNAL_VERIFICATION_USE_FIXTURES = True
    VERIFIERS = _build_verifiers()
    res2 = verify_answer(sample, enabled=True)
    print("  trace:", verification_trace(res2))
    print("  log  :", json.dumps(verification_log(res2), ensure_ascii=False))
    print("\n── 4) fixtures 모드 답변 병기 결과 ─────────")
    print(apply_verification(sample, res2))
    print("\n(실서비스: EXTERNAL_VERIFICATION_ENABLED=true, 승인된 KRX_AUTH_KEY 주입 시 실연동)")
