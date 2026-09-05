# -*- coding: utf-8 -*-
"""show_flags.py — 운영과 '동일한 순서'(.env 먼저 로드 → verify_layer import)로
현재 유효 flag 값을 확인. .env 적용 여부와 kill-switch 검증에 사용.
사용: cd /root/app && source venv/bin/activate && python show_flags.py"""

# ── 운영 main_v115.py와 동일한 import 순서 ──────────────────────────────
from dotenv import load_dotenv
_loaded = load_dotenv()          # verify_layer import '전에' .env 로드
import verify_layer as V         # 이 시점에 EXTERNAL_VERIFICATION_* env가 반영됨

print("=" * 60)
print("외부검증 레이어 — 유효 flag (.env 먼저 로드 후)")
print("=" * 60)
print(f"  load_dotenv() 실행 → verify_layer import 순서 : 정상(먼저 로드)")
print(f"  .env 로드 성공 여부                          : {_loaded}")
print("-" * 60)
rows = [
    ("EXTERNAL_VERIFICATION_ENABLED", V.EXTERNAL_VERIFICATION_ENABLED),
    ("EXTERNAL_VERIFICATION_LIVE_WEB", V.EXTERNAL_VERIFICATION_LIVE_WEB),
    ("EXTERNAL_VERIFICATION_USE_FIXTURES(mock)", V.EXTERNAL_VERIFICATION_USE_FIXTURES),
    ("EXTERNAL_VERIFICATION_TIMEOUT_SECONDS", V.EXTERNAL_VERIFICATION_TIMEOUT_SECONDS),
    ("EXTERNAL_VERIFICATION_PER_CALL_TIMEOUT", V.EXTERNAL_VERIFICATION_PER_CALL_TIMEOUT),
    ("EXTERNAL_VERIFICATION_MAX_CLAIMS", V.EXTERNAL_VERIFICATION_MAX_CLAIMS),
    ("CACHE_TTL_SEC", V.CACHE_TTL_SEC),
]
for name, val in rows:
    print(f"  {name:40} = {val}")
print(f"  {'MAWEB domains(whitelist)':40} = {sorted(V.MIRAEASSET_WEB['domains'])}")
print(f"  {'MAWEB verifier available':40} = {V.VERIFIERS['MAWEB'].available}")
print("-" * 60)
print("  코드 기본값(fail-safe): ENABLED=False, LIVE_WEB=False, mock=False")
print("  운영 .env 목표        : ENABLED=true, LIVE_WEB=true, mock=false")
print("=" * 60)
# 요약 판정
prod_ok = (V.EXTERNAL_VERIFICATION_ENABLED and V.EXTERNAL_VERIFICATION_LIVE_WEB
           and not V.EXTERNAL_VERIFICATION_USE_FIXTURES)
print("운영 posture 일치:", "예 (ENABLED·LIVE_WEB ON, mock OFF)" if prod_ok
      else "아니오 — .env 확인 필요(누락 시 fail-safe OFF)")
print("kill-switch 확인법: .env에서 EXTERNAL_VERIFICATION_ENABLED=false 로 바꾸고")
print("  이 스크립트를 다시 실행 → ENABLED=False 로 꺼지면 정상.")
