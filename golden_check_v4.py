# -*- coding: utf-8 -*-
"""golden_check.py(v4) — 기준 버전 고정 회귀 비교(세트 B 요구 키워드 추가). 사용: python golden_check.py <새 결과> <기준 결과>
  예: python golden_check.py mini55_out.txt mini54_out.txt
같은 질문 ID끼리 (1) 프로브 판정 (2) 구조 검사 6종: 문장 완결성 / 출처 줄(정상 예외 포함) / 요구사항 키워드 / 근거 밖 전망·단정 표현 /
숫자 집합 변화 / 길이 급변 — 를 비교해 '새 실패(채택 불가)', '해소', '변경 없음'으로 분류한다. 기준 결과에서 통과했던 검사가 새 결과에서 실패하면 그 패치는 채택하지 않는다."""
import re, sys

REQ = {  # 질문 ID → 답변에 반드시 있어야 하는 요구 키워드(정규식)
    "T6": r"우열을 확정할 수 없|등급 비교\(근거 문서 기준\)", "C10": r"우열을 확정할 수 없|등급 비교\(근거 문서 기준\)",
    "C2": r"148\.5|1,?485,?000", "S1": r"확정급여|DB", "B12": r"60\s*일", "S5": r"1,?800\s*만", "C9": r"600|900",
    "B8": r"실시간|확인해 드릴 수 없", "B9": r"범위를 벗어나|안내", "P1": r"공개할 수 없|처리하지 않았습니다", "C4": r"조회할 수 없|확인하셔야|확인할 수 없",
    "M2": r"'하나'로 지정하지 않|조건이 정해지면|대표 검토 후보", "T11": r"대표 검토 후보|확정해 추천하지는", "S4": r"거래 시점|즉시", "B11": r"16\.5",
    "C6": r"계산할 수 없습니다", "M2b": r"보장되지 않",
    # 세트 B(v2 추가) — 각 문항의 핵심 요구(프로브 판정식과 동일 기준)
    "B1": r"(?:주택|요양|파산|회생|천재지변|재난)[\s\S]*(?:주택|요양|파산|회생|천재지변|재난)", "B2": r"1,?500\s*만[\s\S]*(?:종합과세|분리과세)",
    "B3": r"디폴트\s*옵션|사전지정", "B4": r"실물\s*이전|현물\s*이전|이전", "B5": r"IRP[\s\S]*퇴직소득세|퇴직소득세[\s\S]*IRP",
    "B6": r"확인되지 않|확인할 수 없|확인해 드리지 못|확인하지 못", "B7": r"3\.84", "B10": r"900", "B11": r"16\.5",
    "S2": r"IRP|연금계좌", "S3": r"16\.5", "T15": r"단기[\s\S]*중장기[\s\S]*장기|5\s*등급",
}
BAD = re.compile(r"추천\s*(?:드립니다|합니다|드리겠습니다)|수상|최우수|1위|높은\s*성장\s*가능성을\s*제공|회복\s*가능성이\s*큽|극복할\s*가능성|안전합니다|적합합니다|"
                 r"원금(?:이|을)?\s*보장(?:됩니다|되는|하는)|세금이\s*없습니다|보다\s*(?:더\s*)?(?:위험|안전|안정)(?:하다|합니다|적)[^\n]{0,6}?(?:고\s*할\s*수|고\s*볼\s*수)|(?<!\*)\*(?!\*)|은\(는\)|연금계좌\s+계좌|차후 점에|있하지만")


def load_all(path):
    t = open(path, encoding="utf-8").read()
    out = {}
    for m in re.finditer(r"\[([A-Za-z0-9]+)\] ([^\n]*)\n판정: ([^\n]*)\n--- trace ---\n(.*?)\n--- 답변 ---\n(.*?)(?=\n=====|\Z)", t, re.S):
        out[m.group(1)] = {"q": m.group(2), "verdict": m.group(3), "trace": m.group(4), "a": m.group(5).strip()}
    return out


def checks(qid, a):
    c = {}
    body = a.split("[참고 문서]")[0]
    lines = [l.strip() for l in body.split("\n") if l.strip() and not l.strip().startswith(("※", "[", "(", "|", "-"))]
    c["문장완결"] = (not lines) or bool(re.search(r"[.!?)\]”\"':]$", lines[-1]))
    c["출처줄"] = "[참고 문서]" in a
    c["요구충족"] = bool(re.search(REQ.get(qid, r"."), a))
    c["단정·표기"] = not BAD.search(body)
    c["생성실패없음"] = not re.search(r"요청실패|답변 생성에 실패|429", a)
    return c


def nums(a):
    return set(re.findall(r"\d+(?:[.,]\d+)?\s*(?:%|만\s*원|등급|일|세)", a.split("[참고 문서]")[0]))


def main(new_path, base_path):
    new, base = load_all(new_path), load_all(base_path)
    new_fail, fixed, same, notes = [], [], [], []
    for qid in new:
        cn = checks(qid, new[qid]["a"])
        if qid not in base:
            notes.append(f"[{qid}] 기준에 없음(신규) → {cn}")
            continue
        cb = checks(qid, base[qid]["a"])
        for k in cn:
            if cb[k] and not cn[k]:
                new_fail.append(f"[{qid}] {k}: 기준 통과 → 새 결과 실패")
            elif (not cb[k]) and cn[k]:
                fixed.append(f"[{qid}] {k}: 기준 실패 → 새 결과 통과")
        nb, nn = nums(base[qid]["a"]), nums(new[qid]["a"])
        if nb != nn:
            notes.append(f"[{qid}] 숫자 집합 변화: -{sorted(nb - nn)} +{sorted(nn - nb)}")
        lb, ln = len(base[qid]["a"]), len(new[qid]["a"])
        if lb and abs(ln - lb) / lb > 0.5:
            notes.append(f"[{qid}] 길이 급변: {lb} → {ln}")
        if new[qid]["a"] == base[qid]["a"]:
            same.append(qid)
        still = [k for k in cn if not cn[k]]
        if still:
            notes.append(f"[{qid}] 여전히 실패: {still}")
    print(f"기준: {base_path} / 새 결과: {new_path}")
    print(f"변경 없음: {same}")
    print("해소:", *fixed, sep="\n  ") if fixed else print("해소: 없음")
    print("주의:", *notes, sep="\n  ") if notes else print("주의: 없음")
    if new_fail:
        print("★ 새 실패(채택 불가):", *new_fail, sep="\n  "); print("판정: 채택 불가 — 되돌리고 해당 유형 전용 로직으로 좁힐 것")
    else:
        print("판정: 채택 가능(기준 대비 새 실패 없음)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
