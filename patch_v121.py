# -*- coding: utf-8 -*-
"""
patch_v121.py — v120(9e8d2c2b) main.py 에 v12.1 1차 패치 3건을 안전하게 in-place 적용.
  P0-1: 이동 절차 기한 질문에 섞인 '사업자·회사 통지/지급 의무' 무관 기한 제거
  P0-2: 인용부호 안 오삽입 볼드 마커 제거 (_final_cleanup A3)
  P1-2: [참고 문서] 근거 상위 5개로 절단

특징: 4개 블록을 정확 문자열로만 치환. 하나라도 못 찾으면 즉시 중단(부분 적용 금지).
      이미 패치돼 있으면(v12.1 마커) 아무것도 하지 않음. 적용 전 자동 백업.
사용: cd /root/app && python3 patch_v121.py           # 기본 대상 main.py
      python3 patch_v121.py /경로/main.py             # 대상 지정
검증: 적용 후 md5 == f9c867e9a4b250d735c5056cb074d779 이면 성공.
"""
import sys, os, time, hashlib, py_compile

TARGET = sys.argv[1] if len(sys.argv) > 1 else "main.py"
EXPECT_BEFORE = "9e8d2c2bcbfecf91130077c318982a8e"
EXPECT_AFTER  = "f9c867e9a4b250d735c5056cb074d779"

EDITS = [
    # (설명, OLD, NEW)
    ("P0-1 패턴",
r'''_DEADLINE_INTENT = re.compile(r"기한|언제|이내|며칠|몇\s*일|몇\s*개월|데드라인|시점|"
                              r"(?:기간|기일)\s*(?:은|이|내|안|까지)?")''',
r'''_DEADLINE_INTENT = re.compile(r"기한|언제|이내|며칠|몇\s*일|몇\s*개월|데드라인|시점|"
                              r"(?:기간|기일)\s*(?:은|이|내|안|까지)?")

# v12.1(P0-1): '내가 하는 절차'(이전·입금 등) 기한 질문에 '사업자·회사의 통지/지급 의무'
#   기한(운용현황 통지 10일, 급여지급 14일 등)이 섞여 붙는 무관 노이즈를 걸러내기 위한 패턴.
#   질문이 이동 절차이고(_MOVE_PAT) 문장이 통지/지급 의무이며(_PROVIDER_DL) 이동 동사가
#   없을 때만(_MOVE_PAT 미매칭) 제거 → 온토픽 기한은 절대 손대지 않는다(3중 조건).
_MOVE_PAT = re.compile(r"옮|이전|이체|입금|납입|전환|넣")
_PROVIDER_DL = re.compile(r"통지|통보|운용\s*현황|지급하도록|지급해야|지급하여야|지급합")'''),

    ("P0-1 게이트",
r'''        _pending = [] if _no_answer else \
            [(n, t) for n, t in forced_pairs if n not in ans.replace(" ", "")]
        miss = _pending if _DEADLINE_INTENT.search(question) else []''',
r'''        _pending = [] if _no_answer else \
            [(n, t) for n, t in forced_pairs if n not in ans.replace(" ", "")]
        # v12.1(P0-1): 이동 절차 기한 질문에 섞인 '사업자·회사의 통지/지급 의무' 기한 제거.
        #   (질문=이동절차) & (문장=통지/지급 의무) & (문장에 이동 동사 없음) 3조건 동시일 때만.
        if _pending and _MOVE_PAT.search(question):
            _pending = [(n, t) for n, t in _pending
                        if not (_PROVIDER_DL.search(t) and not _MOVE_PAT.search(t))]
        miss = _pending if _DEADLINE_INTENT.search(question) else []'''),

    ("P0-2 A3",
r'''    ans = re.sub(r"(\d(?:[.,]\d+)?)\s*\*\*\s*(?=[(（])", r"\1", ans)''',
r'''    ans = re.sub(r"(\d(?:[.,]\d+)?)\s*\*\*\s*(?=[(（])", r"\1", ans)
    # A3) v12.1(P0-2): 인용부호 안에 오삽입된 볼드 마커 제거 — '**보통위험' → '보통위험'.
    #   여는 따옴표 직후 ** + (따옴표/별표 없는 짧은 어구) + 닫는 따옴표 형태만 정확히 매칭
    #   (정상 볼드 '**중요**'는 어구 뒤가 ** 이므로 매칭되지 않아 보호됨). 남은 홀수 **는 E)가 정리.
    ans = re.sub(r"(['\"‘’“”])\*\*([^*'\"‘’“”\n]{1,30})"
                 r"(['\"‘’“”])", r"\1\2\3", ans)'''),

    ("P1-2 근거상한",
r'''        if srcs:
            ans = ans.rstrip() + "\n\n[참고 문서] " + ", ".join(srcs)''',
r'''        if srcs:
            # v12.1(P1-2): 근거 과다(6개+) 방지 — used는 관련도순이므로 상위 5개까지만 표기.
            #   (len≤5이면 무변화 → 3~4개 정상 답변은 손대지 않고 6·7·8개만 5로 절단.)
            ans = ans.rstrip() + "\n\n[참고 문서] " + ", ".join(srcs[:5])'''),
]


def md5(s):
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def main():
    if not os.path.exists(TARGET):
        print(f"[중단] 대상 없음: {TARGET}"); sys.exit(1)
    src = open(TARGET, encoding="utf-8").read()
    before = md5(src)
    print(f"대상: {TARGET}\n적용전 md5: {before}")

    if "v12.1(P0-1)" in src:
        print("[스킵] 이미 v12.1 패치가 적용돼 있음. 변경 없음."); sys.exit(0)
    if before != EXPECT_BEFORE:
        print(f"[경고] 적용전 md5가 예상 v120({EXPECT_BEFORE})과 다름.")
        print("       그래도 4개 블록이 정확히 매칭되면 계속 진행함(문제 시 중단).")

    # 매칭 사전 검증(부분 적용 방지) — 하나라도 없거나 2회 이상이면 중단
    for name, old, new in EDITS:
        c = src.count(old)
        if c != 1:
            print(f"[중단] '{name}' OLD 블록 매칭 {c}회(정확히 1회여야 함). 적용 취소.")
            sys.exit(2)
    # 적용
    out = src
    for name, old, new in EDITS:
        out = out.replace(old, new)
        print(f"  ✓ {name} 적용")

    after = md5(out)
    # 백업 후 기록
    ts = time.strftime("%Y%m%d_%H%M%S")
    bak = f"{TARGET}.bak_v120_{ts}"
    open(bak, "w", encoding="utf-8").write(src)
    open(TARGET, "w", encoding="utf-8").write(out)
    print(f"백업: {bak}")
    print(f"적용후 md5: {after}")
    print(f"기대   md5: {EXPECT_AFTER}  → {'일치 ✅' if after == EXPECT_AFTER else '불일치 ❌'}")

    # 문법 검사
    try:
        py_compile.compile(TARGET, doraise=True)
        print("py_compile: OK")
    except py_compile.PyCompileError as e:
        print(f"[중단] 문법 오류 — 백업 복원 필요: {e}")
        sys.exit(3)

    n = out.count("v12.1(P0") + out.count("v12.1(P1")
    print(f"마커 수: {n} (기대 4)")
    print("\n완료. 이제 uvicorn 재시작 후 스모크 확인.")


if __name__ == "__main__":
    main()
