# -*- coding: utf-8 -*-
"""
patch_v122.py — v121(f9c867e9) main.py 의 P0-2 A3 규칙을 확장 적용(v12.2).
  원인: HCX가 '**보통위험**'(따옴표 안 볼드)+'**연 0.87%'(미닫힘)을 내면, 기존 A3(한쪽 별표)가
        '**보통위험**'을 못 잡고 E규칙이 별표 하나만 떼어 '**보통위험'이 남았음(P01 글리치).
  수정: A3를 '**X**'·'**X'·'X**' 모두 커버(따옴표 밖 정상 볼드 **16.5%**·**보통위험**는 불변).

특징: A3 블록 정확 문자열 1곳만 치환. 못 찾으면 즉시 중단. 이미 v12.2면 스킵. 자동 백업.
사용: cd /root/app && python3 patch_v122.py
검증: 적용 후 md5 == f44bf0b5caa95ce9ce13892eeb01f3b0 이면 성공.
"""
import sys, os, time, hashlib, py_compile

TARGET = sys.argv[1] if len(sys.argv) > 1 else "main.py"
EXPECT_BEFORE = "f9c867e9a4b250d735c5056cb074d779"
EXPECT_AFTER  = "f44bf0b5caa95ce9ce13892eeb01f3b0"

OLD = (
    "    # A3) v12.1(P0-2): 인용부호 안에 오삽입된 볼드 마커 제거 — '**보통위험' → '보통위험'.\n"
    "    #   여는 따옴표 직후 ** + (따옴표/별표 없는 짧은 어구) + 닫는 따옴표 형태만 정확히 매칭\n"
    "    #   (정상 볼드 '**중요**'는 어구 뒤가 ** 이므로 매칭되지 않아 보호됨). 남은 홀수 **는 E)가 정리.\n"
    "    ans = re.sub(r\"(['\\\"‘’“”])\\*\\*([^*'\\\"‘’“”\\n]{1,30})\"\n"
    "                 r\"(['\\\"‘’“”])\", r\"\\1\\2\\3\", ans)\n"
)
NEW = (
    "    # A3) v12.2(P0-2): 인용부호 안 오삽입 볼드 마커 제거 — '**X**'·'**X'·'X**' 모두 → 'X'.\n"
    "    #   실측: HCX가 '**보통위험**'(따옴표 안 볼드)+'**연 0.87%'(미닫힘)을 냄. both-stars를\n"
    "    #   먼저 처리(안 그러면 one-star 규칙에 안 걸려 남음). 남는 홀수 **(예: **연)은 E)가 정리.\n"
    "    _Q = r\"['\\\"‘’“”]\"\n"
    "    ans = re.sub(rf\"({_Q})\\*\\*([^*'\\\"‘’“”\\n]{{1,30}})\\*\\*({_Q})\", r\"\\1\\2\\3\", ans)  # '**X**'\n"
    "    ans = re.sub(rf\"({_Q})\\*\\*([^*'\\\"‘’“”\\n]{{1,30}})({_Q})\", r\"\\1\\2\\3\", ans)      # '**X'\n"
    "    ans = re.sub(rf\"({_Q})([^*'\\\"‘’“”\\n]{{1,30}})\\*\\*({_Q})\", r\"\\1\\2\\3\", ans)      # 'X**'\n"
)


def md5(s):
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def main():
    if not os.path.exists(TARGET):
        print(f"[중단] 대상 없음: {TARGET}"); sys.exit(1)
    src = open(TARGET, encoding="utf-8").read()
    before = md5(src)
    print(f"대상: {TARGET}\n적용전 md5: {before}")
    if "v12.2(P0-2)" in src:
        print("[스킵] 이미 v12.2 적용됨. 변경 없음."); sys.exit(0)
    if before != EXPECT_BEFORE:
        print(f"[경고] 적용전 md5가 예상 v121({EXPECT_BEFORE})과 다름. 블록 매칭되면 계속.")
    c = src.count(OLD)
    if c != 1:
        print(f"[중단] A3 OLD 블록 매칭 {c}회(1이어야 함). 적용 취소 — 파일 상태 붙여주세요.")
        sys.exit(2)
    out = src.replace(OLD, NEW)
    after = md5(out)
    ts = time.strftime("%Y%m%d_%H%M%S")
    bak = f"{TARGET}.bak_v121_{ts}"
    open(bak, "w", encoding="utf-8").write(src)
    open(TARGET, "w", encoding="utf-8").write(out)
    print(f"  ✓ A3 확장 적용")
    print(f"백업: {bak}")
    print(f"적용후 md5: {after}")
    print(f"기대   md5: {EXPECT_AFTER}  → {'일치 ✅' if after == EXPECT_AFTER else '불일치 ❌'}")
    try:
        py_compile.compile(TARGET, doraise=True)
        print("py_compile: OK")
    except py_compile.PyCompileError as e:
        print(f"[중단] 문법 오류 — 백업 복원: {e}"); sys.exit(3)
    print(f"마커 v12.2: {out.count('v12.2(P0-2)')} (기대 1)")
    print("\n완료. uvicorn 재시작 후 P01 스모크 확인.")


if __name__ == "__main__":
    main()
