# -*- coding: utf-8 -*-
"""
test_fixes.py — merge 전 4개 확인(A·B·C·D). 오프라인(CLOVA 불필요).
사용: cd /root/app && python3 test_fixes.py
"""
import verify_layer as V

P, F = "\033[92mPASS\033[0m", "\033[91mFAIL\033[0m"
ok = no = 0
def chk(name, cond, extra=""):
    global ok, no
    print(f"  [{P if cond else F}] {name}" + (f"  — {extra}" if extra else ""))
    ok += bool(cond); no += (not cond)

print("=" * 70)
print("A. '연금저축계좌 연간 납입한도' → verification_required=True 인가")
print("=" * 70)
ansA = "연금저축계좌의 연간 납입한도는 1,800만 원입니다. 이는 제도상 한도입니다.\n\n[참고 문서] doc23.docx"
qA = "연금저축계좌의 연간 납입한도는 얼마인가요?"
clA = V.extract_claims(ansA, question=qA)
limit_claims = [c for c in clA if c["verification_required"] and c["entity_type"] == "regime"]
chk("납입한도 Claim이 verification_required=True로 추출", len(limit_claims) >= 1,
    extra=", ".join(f"{c['subject']}({c['claim_type']}→{V.route_authority(c)})" for c in clA))
chk("needs_verification=True (시간민감 제도 Claim)",
    any(V.needs_verification(c) for c in limit_claims))

print("\n" + "=" * 70)
print("B. generic 'TIGER ETF' → 상품 검증 대상에서 제외되는가")
print("=" * 70)
ansB = ("공격형 투자자는 TIGER ETF를 연금계좌에서 투자할 수 있습니다. "
        "그중 TIGER 인도빌리언컨슈머도 거래 가능합니다.")
clB = V.extract_claims(ansB)
prod = [c for c in clB if c["entity_type"] == "financial_product"]
subs = [c["subject"] for c in prod]
chk("generic 'TIGER ETF'는 상품 Claim 아님", all("인도빌리언컨슈머" in s or s != "TIGER ETF" for s in subs)
    and not any(V._norm_name(s) == V._norm_name("TIGER ETF") for s in subs),
    extra=f"상품Claim={subs}")
chk("is_specific_product=False는 needs_verification=False",
    not V.needs_verification(V.make_claim("x", "t", "상품상태",
        entity_type="financial_product", is_specific_product=False,
        verification_required=True, time_sensitive=True, decision_critical=True)))

print("\n" + "=" * 70)
print("C. 'TIGER 인도빌리언컨슈머 현재 거래 가능해?' → 구체 상품 Claim 검증대상")
print("=" * 70)
ansC = "TIGER 인도빌리언컨슈머는 현재 거래 가능합니다."
qC = "TIGER 인도빌리언컨슈머 현재 거래 가능해?"
clC = V.extract_claims(ansC, question=qC)
spec = [c for c in clC if c["entity_type"] == "financial_product" and c["is_specific_product"]]
chk("구체 상품 Claim 추출(is_specific_product=True)", len(spec) >= 1,
    extra=", ".join(f"{c['subject']}→{V.route_authority(c)}" for c in spec))
chk("KRX로 routing", any(V.route_authority(c) == "KRX" for c in spec))
chk("needs_verification=True", any(V.needs_verification(c) for c in spec))

print("\n" + "=" * 70)
print("D. 최종 답변에 '.pdf' 단독 노출이 없는가 + [참고 문서] 훼손 없음")
print("=" * 70)
# verify_layer가 [참고 문서]를 건드리지 않고, STALE 병기 후에도 출처 온전한지
ansD = ("TIGER 인도빌리언컨슈머는 현재 거래 가능합니다.\n\n"
        "[참고 문서] R2_KR5125450023.pdf, doc41.docx")
V.EXTERNAL_VERIFICATION_USE_FIXTURES = True
V.VERIFY_FIXTURES = {"KRX": {"TIGER 인도빌리언컨슈머": {"status": V.STALE_SUSPECTED, "note": "시연"}}}
V.VERIFIERS = V._build_verifiers()
resD = V.verify_answer(ansD, enabled=True)
outD = V.apply_verification(ansD, resD)
chk("[참고 문서] 줄 온전히 유지", "[참고 문서] R2_KR5125450023.pdf, doc41.docx" in outD)
# '.pdf'가 파일명의 일부가 아니라 '단독'으로 한 줄/토큰으로 뜨는지 검사
import re
standalone_pdf = bool(re.search(r"(^|\n)\s*\.pdf(\s|$)", outD)) or \
                 bool(re.search(r"(?<![\w가-힣_\-])\.pdf(?![\w])", outD))
chk("'.pdf' 단독 노출 없음(파일명 일부로만 존재)", not standalone_pdf)
chk("STALE 병기는 [참고 문서] 뒤에 별도 추가(출처 훼손 없음)", "※" in outD and outD.index("[참고 문서]") < outD.index("※"))
V.EXTERNAL_VERIFICATION_USE_FIXTURES = False
V.VERIFIERS = V._build_verifiers()

print("\n" + "=" * 70)
print(f"결과: {ok} PASS / {no} FAIL")
print("=" * 70)
