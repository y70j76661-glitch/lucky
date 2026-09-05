# -*- coding: utf-8 -*-
"""
test_reco_coverage.py — '추천 전용 처리'가 다양한 표현의 추천 질문에
                        빠짐없이 적용되는지 커버리지 검사.

핵심 판정: 서버 think_trace의 "3) LLM 유형 분류: '추천'" 여부.
  qtype가 '추천'이면 main.py의 `if qtype == "추천"` 블록(단정완화·종결어미
  통일·순서고지·균형캐비엇·과거성과 등)이 전부 걸린 것이므로, 이 한 줄이
  '이 질문에 추천 전용 처리가 적용됐는가'의 결정적 근거다.

보조 확인: clean_note(실제 발동한 후처리)와 답변 속 표식.

목적: 표현이 애매해서 '상품설명/제도'로 잘못 분류되는 추천 질문이 있는지
      찾아내 분류 커버리지의 빈틈을 드러낸다.
"""
import re
import time
import auto_probe as ap

# 다양한 표현·어투·구조의 추천 질문(일부러 애매한 것 포함)
Q = [
    "나한테 맞는 연금 상품 추천해줘",
    "30대 중립형인데 어떤 펀드가 좋을까?",
    "공격형인데 연금으로 담을 ETF 종목 몇 개 골라줘",
    "은퇴 앞둔 60대인데 안정적인 상품 뭐가 있을까 추천 부탁해",
    "IRP에 넣을 만한 상품 추천",
    "적립식으로 굴릴 만한 거 추천해줘, 20대야",
    "위험은 좀 감수할 수 있는데 수익 괜찮은 종목 추천",
    "연금저축으로 뭐 사면 좋아?",              # 애매
    "TDF 중에 나한테 맞는 거 골라줄래?",
    "안정형인데 원리금 보장되는 상품 중에 추천해줘",
    "월 50만원 넣을 건데 뭐가 좋을지 추천",
    "디폴트옵션 뭐로 할지 골라줘",
    "초보인데 연금 처음 시작하면 뭐부터 담아야 해?",   # 애매
    "배당 나오는 ETF 추천해줘",
    "장기투자할 건데 성장형 상품 추천",
    "40대 직장인 연금 포트폴리오 짜줘",
    "노후 대비로 뭐 들면 좋을까?",             # 애매
    "리스크 낮은 걸로 몇 개 추천해줄 수 있어?",
]

_QTYPE = re.compile(r"유형\s*분류:\s*'([^']+)'")

# 추천 전용 후처리의 흔적(clean_note 또는 답변 표식)
MARKERS = {
    "균형캐비엇": (lambda tr, a: "균형 캐비엇" in tr or "적합성을 단정" in a),
    "과거성과": (lambda tr, a: "과거성과" in tr or "미래의 수익을 보장" in a),
    "순서고지": (lambda tr, a: "순서 무순위" in tr or "나열 순서는" in a),
    "단정완화": (lambda tr, a: "검토" in a and "적합합니다" not in a),
}

results = []
for i, q in enumerate(Q):
    if i:
        time.sleep(3)
    a, tr, c = ap.ask(f"COV{i:02d}", q)
    m = _QTYPE.search(tr or "")
    qtype = m.group(1) if m else "(파싱실패)"
    is_reco = (qtype == "추천")
    fired = [k for k, fn in MARKERS.items() if fn(tr or "", a or "")]
    results.append((q, qtype, is_reco, fired))
    print("=" * 66)
    print(f"[{qtype:^6}] {q}")
    print(f"  추천 분류: {'✅' if is_reco else '❌ (' + qtype + '로 분류)'}")
    print(f"  발동 후처리: {', '.join(fired) if fired else '(표식 없음)'}")

# ── 대조군(회귀 방지): 추천이 아니어야 하는 질문. '추천'으로 끌려오면 부작용 ──
CONTROLS = [
    ("상품설명", "TDF가 뭐야?"),
    ("상품설명", "원리금보장형 상품은 어떤 게 있어?"),
    ("상품설명", "이 펀드 수수료 얼마야?"),
    ("제도",   "IRP 가입 자격이 어떻게 돼?"),
    ("세제",   "연금저축 세액공제 한도 얼마야?"),
]
ctrl = []
for i, (exp, q) in enumerate(CONTROLS):
    time.sleep(3)
    a, tr, c = ap.ask(f"CTL{i:02d}", q)
    m = _QTYPE.search(tr or "")
    qtype = m.group(1) if m else "(파싱실패)"
    leaked = (qtype == "추천")        # 추천으로 끌려오면 회귀
    ctrl.append((q, exp, qtype, leaked))
    print("=" * 66)
    print(f"[{qtype:^6}] (대조군, 기대:{exp}) {q}")
    print(f"  추천으로 안 샘: {'❌ 추천으로 끌려옴(회귀!)' if leaked else '✅'}")

# 요약
n = len(results)
reco = sum(1 for _, _, r, _ in results if r)
print("\n" + "#" * 66)
print(f"추천 커버리지: {reco}/{n}")
miss = [q for q, qt, r, _ in results if not r]
if miss:
    print("\n[추천으로 안 잡힌 질문 — 분류 커버리지 빈틈]")
    for q in miss:
        print(f"  - {q}")
else:
    print("모든 추천 표현이 '추천'으로 분류됨 → 추천 전용 처리 전부 적용 ✅")

leaks = [q for q, e, qt, l in ctrl if l]
print(f"\n대조군 회귀: {len(leaks)}/{len(CONTROLS)} 건 추천으로 잘못 끌려옴")
if leaks:
    print("[회귀 발생 — 이 질문들이 추천으로 오분류됨]")
    for q in leaks:
        print(f"  - {q}")
else:
    print("대조군 전부 추천 아님으로 유지 → 부작용 없음 ✅")
