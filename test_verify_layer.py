# -*- coding: utf-8 -*-
"""
test_verify_layer.py — verify_layer 단위 동작 검증(오프라인, CLOVA 불필요).
6개 status / reason / never-block / mock 데모표시 / 캐시정책을 강제 시나리오로 확인.
사용: cd /root/app && python3 test_verify_layer.py
"""
import time
import verify_layer as V

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
_n_ok = 0
_n_no = 0


def chk(name, cond, extra=""):
    global _n_ok, _n_no
    print(f"  [{PASS if cond else FAIL}] {name}" + (f"  — {extra}" if extra else ""))
    if cond:
        _n_ok += 1
    else:
        _n_no += 1


# 검증 대상 Claim이 잡히도록 시간민감+상품명이 든 표준 답변
DOC_ANS = ("공격형 투자자는 TIGER 미국S&P500과 TIGER 26-04회사채(A+이상)액티브를 "
           "연금 계좌에서 투자할 수 있습니다. 현재 상장되어 거래 가능합니다.\n\n"
           "[참고 문서] doc12, doc41")


def _base_claim(subj="TIGER 미국S&P500"):
    return V.make_claim("C1", f"{subj}의 현재 상장·거래 가능 여부", "상품상태",
                        time_sensitive=True, decision_critical=True,
                        verification_required=True, preferred_authority="KRX",
                        subject=subj)


class _Adapter(V.Verifier):
    """테스트용 — 원하는 (status, reason)을 그대로 돌려주는 어댑터."""
    def __init__(self, authority, status, reason, note="", sleep=0.0, raises=False):
        self.authority = authority; self.available = True
        self._s, self._r, self._note = status, reason, note
        self._sleep, self._raises = sleep, raises

    def check(self, claim):
        if self._raises:
            raise RuntimeError("의도된 예외")
        if self._sleep:
            time.sleep(self._sleep)
        return self._s, self._r, {"authority": self.authority, "note": self._note}


def _run_one(adapter, ans=DOC_ANS):
    """VERIFIERS['KRX']를 교체하고 verify_answer→apply_verification 실행."""
    V.VERIFIERS["KRX"] = adapter
    V._RESULT_CACHE.clear()
    res = V.verify_answer(ans, enabled=True)
    new_ans = V.apply_verification(ans, res)
    return res, new_ans


print("=" * 70)
print("① status 6종 판정")
print("=" * 70)

# VERIFIED — 답변 본문 불변(경고 없음)
res, na = _run_one(_Adapter("KRX", V.VERIFIED, V.R_VERIFIED, "상장 확인"))
chk("VERIFIED status", any(c["verification_status"] == V.VERIFIED for c in res))
chk("VERIFIED → 답변 불변", na == DOC_ANS, "경고 병기 없음")

# STALE_SUSPECTED — 본문 유지 + 경고 병기(삭제 없음)
res, na = _run_one(_Adapter("KRX", V.STALE_SUSPECTED, V.R_VERIFIED, "목록에 없음"))
chk("STALE_SUSPECTED status", any(c["verification_status"] == V.STALE_SUSPECTED for c in res))
chk("STALE → 원문 보존(삭제 없음)", DOC_ANS.split("\n")[0] in na)
chk("STALE → 경고 병기됨", "상태가 변경되었을 가능성" in na)
chk("STALE → [참고 문서] 유지", "[참고 문서]" in na)

# CONFLICT — 본문 유지 + '차이만' 병기(덮어쓰기 없음)
res, na = _run_one(_Adapter("KRX", V.CONFLICT, V.R_VERIFIED, "충돌"))
chk("CONFLICT status", any(c["verification_status"] == V.CONFLICT for c in res))
chk("CONFLICT → 문서 본문 덮어쓰기 안 함", "투자할 수 있습니다" in na)
chk("CONFLICT → '차이' 안내만 추가", "차이가 있어" in na)

# DOCUMENT_PRIMARY — 문서 우선, 경고 없음
res, na = _run_one(_Adapter("KRX", V.DOCUMENT_PRIMARY, V.R_NO_RESULT, "결과 없음"))
chk("DOCUMENT_PRIMARY status", any(c["verification_status"] == V.DOCUMENT_PRIMARY for c in res))
chk("DOCUMENT_PRIMARY → 답변 불변", na == DOC_ANS)

# EXTERNAL_UNAVAILABLE (auth_required) — 문서 우선, 경고 없음
res, na = _run_one(_Adapter("KRX", V.EXTERNAL_UNAVAILABLE, V.R_AUTH, "인증 필요"))
chk("EXTERNAL_UNAVAILABLE(auth_required) status",
    any(c["verification_status"] == V.EXTERNAL_UNAVAILABLE for c in res))
chk("auth_required reason", any(c["verification_reason"] == V.R_AUTH for c in res))
chk("auth_required → 답변 불변", na == DOC_ANS)

# UNVERIFIABLE — 검증 대상 아님(시간민감·결정적 아님)
_c = _base_claim(); _c["time_sensitive"] = False; _c["decision_critical"] = False
chk("UNVERIFIABLE 판정(needs_verification=False)", not V.needs_verification(_c))

print("\n" + "=" * 70)
print("② never-block (timeout / exception 나도 답변 실패 금지)")
print("=" * 70)

# per-call timeout: 어댑터가 예산보다 오래 자면 R_TIMEOUT, 답변 불변
_save = V.EXTERNAL_VERIFICATION_PER_CALL_TIMEOUT
V.EXTERNAL_VERIFICATION_PER_CALL_TIMEOUT = 0.3
res, na = _run_one(_Adapter("KRX", V.VERIFIED, V.R_VERIFIED, sleep=1.0))
chk("timeout → reason=timeout", any(c["verification_reason"] == V.R_TIMEOUT for c in res))
chk("timeout → 답변 불변(never-block)", na == DOC_ANS)
V.EXTERNAL_VERIFICATION_PER_CALL_TIMEOUT = _save

# 어댑터 내부 예외 → parser_error 처리, 답변 불변
res, na = _run_one(_Adapter("KRX", V.VERIFIED, V.R_VERIFIED, raises=True))
chk("exception → reason=parser_error", any(c["verification_reason"] == V.R_PARSER for c in res))
chk("exception → 답변 불변(never-block)", na == DOC_ANS)

# 기능 OFF → 아무것도 실행 안 됨(빈 결과), 답변 불변
res = V.verify_answer(DOC_ANS, enabled=False)
chk("ENABLED=False → verify 미실행([])", res == [])
chk("ENABLED=False → 답변 불변", V.apply_verification(DOC_ANS, res) == DOC_ANS)

print("\n" + "=" * 70)
print("③ mock fixture — 데모 표시 / 실제검증 취급 금지 / 캐시 저장 금지")
print("=" * 70)

V.EXTERNAL_VERIFICATION_USE_FIXTURES = True
V.VERIFY_FIXTURES = {"KRX": {
    "TIGER 26-04회사채": {"status": V.STALE_SUSPECTED, "note": "만기 의심"},
    "TIGER 미국S&P500": {"status": V.VERIFIED, "note": "상장 확인"},
}}
V.VERIFIERS = V._build_verifiers()
V._RESULT_CACHE.clear()
res = V.verify_answer(DOC_ANS, enabled=True)
na = V.apply_verification(DOC_ANS, res)
chk("mock → reason=mock_fixture_demo (verified로 취급 안 함)",
    all(c["verification_reason"] == V.R_MOCK for c in res if c["verification_status"] in (V.VERIFIED, V.STALE_SUSPECTED)))
chk("mock → log에 [DEMO/시연] 표시", any("[DEMO" in (c.get("verification_result") or "") for c in res))
chk("mock → 답변 병기 문구에 [데모] 표시", "[데모]" in na)
chk("mock → 실제 결과 캐시에 저장 안 함", len(V._RESULT_CACHE) == 0)
chk("mock STALE 시연 동작", any(c["verification_status"] == V.STALE_SUSPECTED for c in res))
chk("mock VERIFIED 시연 동작", any(c["verification_status"] == V.VERIFIED for c in res))
V.EXTERNAL_VERIFICATION_USE_FIXTURES = False
V.VERIFIERS = V._build_verifiers()

print("\n" + "=" * 70)
print("④ Claim 선별 — 일반 질문엔 외부검증 대상 없음")
print("=" * 70)
plain = "연금저축과 IRP의 세액공제 한도는 각각 얼마인가요? 최종 확인은 공식자료를 참고하세요."
res = V.verify_answer(plain, enabled=True)
chk("일반 질문 → 검증 대상 Claim 없음(불필요한 외부검증 미실행)", res == [])

print("\n" + "=" * 70)
print(f"결과: {_n_ok} PASS / {_n_no} FAIL")
print("=" * 70)
