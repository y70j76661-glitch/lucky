# -*- coding: utf-8 -*-
"""
compare_deadline.py — 기한 게이트 '부작용' 실측.
원본(게이트 없음: main_pre_external_verification.py) vs 현재(main.py, v118 게이트)를
같은 '기한 관련' 질문으로 나란히 돌려, 게이트 때문에 '필요한 기한 정보'가 빠졌는지 본다.

판정:
  - 원본에 기한 있고(O) 현재도 있음(O)  → OK (명시 기한질문: 게이트 통과)
  - 원본에 기한 있는데 현재 없음(O→X)   → ★부작용 후보★ (게이트가 유용한 기한 제거)
  - 원본에도 없음                       → 게이트 무관
사용: cd /root/app && source venv/bin/activate && python compare_deadline.py
주의: 원본·현재 두 모듈을 함께 로드(코퍼스 2회) → 초기 로딩 몇 분. CLOVA 2배 호출.
"""
import importlib.util
import re
import time

def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

print("원본/현재 모듈 로딩 중(코퍼스 2회, 수 분 소요)...")
ORIG = _load("/root/app/main_pre_external_verification.py", "orig_main")
CUR = _load("/root/app/main.py", "cur_main")
print("로딩 완료.\n")

# 기한 수치 패턴(며칠/개월/영업일)
_DL = re.compile(r"\d+\s*(?:일|영업일|개월|년)\s*(?:이내|안|까지|이후)?")

# (id, 유형, 질문)  유형: explicit=명시기한 / implicit=기한암시(유용) / control=무관
Q = [
    ("E1", "explicit", "퇴직금은 며칠 이내에 IRP로 옮겨야 하나요?"),
    ("E2", "explicit", "ISA 만기 후 언제까지 연금계좌로 전환해야 하나요?"),
    ("E3", "explicit", "명예퇴직금을 IRP에 입금하는 기한은 언제까지인가요?"),
    ("E4", "explicit", "회사가 미납한 퇴직연금 부담금은 며칠 안에 내야 하나요?"),
    ("I1", "implicit", "퇴직금을 IRP로 이전하면 세금 혜택이 있나요?"),
    ("I2", "implicit", "ISA 만기자금을 연금계좌로 전환하면 세액공제가 되나요?"),
    ("I3", "implicit", "퇴직하면 받은 퇴직금을 어떻게 관리하는 게 좋나요?"),
    ("I4", "implicit", "명예퇴직금도 IRP에 넣을 수 있나요?"),
    ("I5", "implicit", "회사가 낸 DC 부담금도 세액공제 대상인가요?"),
    ("C1", "control", "확정급여형(DB)과 확정기여형(DC)의 차이는?"),
    ("C2", "control", "연금저축 세액공제율은 얼마인가요?"),
    ("C3", "control", "위험자산 투자한도는 몇 퍼센트인가요?"),
]


def deadline_in(ans):
    return bool(_DL.search(ans or ""))


def ask(mod, qid, q):
    try:
        r = mod.answer(qid, q)
        return r.get("answer", "") or ""
    except Exception as e:
        return f"(오류: {str(e)[:60]})"


print(f"{'ID':4} {'유형':9} {'원본기한':6} {'현재기한':6} 판정  | 질문")
print("-" * 78)
side_effects = []
for qid, kind, q in Q:
    ao = ask(ORIG, qid, q)
    ac = ask(CUR, qid, q)
    do, dc = deadline_in(ao), deadline_in(ac)
    if do and not dc:
        verdict = "★빠짐★"
        side_effects.append((qid, kind, q))
    elif do and dc:
        verdict = "유지OK"
    elif not do and dc:
        verdict = "현재만"
    else:
        verdict = "둘다없음"
    print(f"{qid:4} {kind:9} {'O' if do else 'X':6} {'O' if dc else 'X':6} {verdict} | {q[:30]}")
    time.sleep(0.3)

print("\n" + "=" * 70)
if side_effects:
    print(f"★ 게이트 부작용 후보 {len(side_effects)}건 (원본엔 기한 있는데 현재 빠짐):")
    for qid, kind, q in side_effects:
        print(f"   {qid}[{kind}] {q}")
    print("\n→ 이 중 '유용한 기한'이 빠진 게 있으면 게이트를 완화(각주 부활 등) 필요.")
else:
    print("게이트 부작용 후보 0건 → 원본이 붙이던 기한을 현재도 필요한 곳엔 유지 중.")
print("=" * 70)
print("※ explicit(E*)은 반드시 '유지OK'여야 정상. implicit(I*)의 '빠짐'은 판단 대상")
print("  (부차적이라 빼도 되는지 / 유용해서 각주로 살릴지).")
