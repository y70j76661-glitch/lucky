# -*- coding: utf-8 -*-
"""mini32_probe.py — v13.54 재확인 3문항(T6·T11·M2).
사용: python mini32_probe.py && python claim_check.py mini32_out.txt && python cite_check.py mini32_out.txt"""
import re, time, requests
BASE = "http://127.0.0.1:8000/answer"


def _common(a):
    f = []
    if re.search(r"요청실패|답변 생성에 실패|429", a):
        f.append("★생성실패")
    if re.search(r"보장되지는 않는 상품은 아닙|보장되지 않는 상품은 아닙", a):
        f.append("★이중부정")
    if re.search(r"(?<![\d.])(?:[07-9]|\d{2,})\s*등급", a.split("[참고 문서]")[0]):
        f.append("★등급범위밖")
    if "자료에서 확인 필요" in a and "근거 문서:" in a:
        f.append("등급자리표시")
    body = a.split("[참고 문서]")[0]
    for m in re.finditer(r"근거 문서:\s*([^\n—]+)", body):
        for s in re.split(r",\s*", m.group(1).strip()):
            if s and s not in a.split("[참고 문서]")[-1]:
                f.append(f"★출처불일치:{s}")
    if "[참고 문서]" not in a:
        f.append("출처줄_없음")
    return f


def _entity_mix(a):
    """번호 항목 머리말의 상품명과 그 블록 안 '유의:'/'상품 예시:' 줄의 상품명이 다르면 True"""
    for blk in re.split(r"\n\s*\n", a.split("[참고 문서]")[0]):
        ls = blk.split("\n")
        m = re.match(r"^\s*\d+[.)]\s*(.+?)(?:\s*\([^)]*위험\))?\s*$", ls[0]) if ls else None
        if not m:
            continue
        head = re.sub(r"\s+", "", m.group(1))[:8]
        for l in ls[1:]:
            mm = re.match(r"^\s*-\s*(?:유의|상품 예시)\s*[:：]\s*(.+?)(?:은\(는\)|$)", l)
            if mm and head and re.sub(r"\s+", "", mm.group(1))[:8] != head and head not in re.sub(r"\s+", "", l):
                return True
    return False


def _order_ok(a):
    i1 = re.search(r"세액공제를?\s*받지\s*않은|공제받지\s*않은|세액공제\s*미적용", a)
    i2 = re.search(r"퇴직(?:금|소득|급여)", a)
    i3 = re.search(r"세액공제를?\s*받은|운용\s*수익|운용수익", a)
    if not (i1 and i2 and i3):
        return ["인출순서_요소누락"]
    return [] if i1.start() < i2.start() < i3.start() else ["★인출순서_오류"]


Q = [
    ("T6", "미래에셋 TDF2045랑 삼성클래식연금 주식형 중에 위험등급이 더 낮은 건 뭐예요?",
     lambda a: ([] if re.search(r"[1-6]\s*등급", a) else ["등급_누락"]) + ([] if "대조 불가" not in a else ["대조불가_고지"]) + ([] if re.search(r"삼성클래식[^\n]{0,40}2\s*등급|2\s*등급[^\n]{0,40}삼성클래식|주식[^\n]{0,30}2\s*등급", a) else ["삼성주식2등급_누락"]) + ([] if "0.47" not in a else ["★창작수치0.47"]) + ([] if not (re.search(r"2\s*등급[^\n]{0,60}보다\s*(?:더\s*)?높", a) and len(re.findall(r"2\s*등급", a.split("핵심 차이")[0])) >= 2) else ["★동일등급_우열단정"]) + ([] if not re.search(r"등급\)\s*/\s*\(", a) else ["★상충셀_잔존"]) + ([] if not re.search(r"TDF2045[^\n]{0,80}\d\s*등급", a.split("핵심 차이")[-1].split("[위험등급")[0]) else ["★TDF등급_요약단정"]) + ([] if re.search(r"등급 비교\(근거 문서 기준\)|검증 불가|위험등급이 같으므로", a) or "보다" not in a else ["우열_미확정문장"])),
    ("T11", "30대 직장인인데 공격적으로 굴릴 연금펀드 하나 추천해줘",
     lambda a: ([] if "근거 문서:" in a else ["근거문서줄_없음"]) + ([] if re.search(r"보장되지\s*않", a) else ["★비보장고지_누락"]) + ([] if "우선순위" in a or not re.search(r"(?m)^\s*2[.)]\s", a) else ["무순위고지_누락"]) + ([] if not re.match(r"^\s*-\s", a) else ["★머리말없는_항목"]) + ([] if not re.search(r"적합하다고\s*판단|추천드릴\s*수\s*있습니다|추천드립니다", a) else ["단정추천_잔존"]) + ([] if not re.search(r"수상|인정받", a) else ["판촉주장_잔존"]) + ([] if not re.search(r"상품 예시:\s*TIGER[^\n]*은\(는\)\s*$", a, re.M) else ["★상품예시_꼬리"]) + (["★엔티티혼입"] if _entity_mix(a) else [])),
    ("M2", "좋은 연금상품 하나 추천해주세요.",
     lambda a: ([] if "근거 문서:" in a else ["근거문서줄_없음"]) + ([] if re.search(r"보장되지\s*않", a) else ["★비보장고지_누락"]) + (["★엔티티혼입"] if _entity_mix(a) else []) + ([] if not re.search(r"(?m)^\s*-\s", a.split("\n\n")[0]) else ["머리말없는_항목"]) + ([] if not re.search(r"(?m)^\s*\d+[.)][^\n]*(?:세제|절세)", a) else ["세제블록_잔존"]) + ([] if not re.search(r"[\]\)]\s*(?:\([^)]*\))?\s*(?:이나|과|와)\s*(?:기타\s*)?원리금\s*보장형", a) else ["★유형혼합"]) + ([] if not re.search(r"원리금\s*보장형[^\n.]{0,20}안정적인\s*수익을\s*제공", a) else ["안정수익단정"])),
]


def main():
    ft = open("mini32_out.txt", "w", encoding="utf-8"); bad = 0
    for qid, q, chk in Q:
        t0 = time.time()
        try:
            r = requests.get(BASE, params={"question_id": qid, "question": q}, timeout=180).json(); a = r.get("answer", "") or ""; tr = r.get("think_trace", "")
        except Exception as e:
            a = f"(요청실패:{str(e)[:40]})"; tr = ""
        f = _common(a) + chk(a); bad += bool(f)
        print(f"  [{qid:3}] {time.time()-t0:4.1f}s  {'OK' if not f else '확인: ' + ' '.join(f)}")
        ft.write(f"\n{'='*70}\n[{qid}] {q}\n판정: {f or 'OK'}\n--- trace ---\n{tr}\n--- 답변 ---\n{a}\n"); time.sleep(0.5)
    ft.close(); print("=" * 50); print("3문항 모두 OK" if not bad else f"확인 필요 {bad}문항 → mini32_out.txt (판정 표시는 후보일 뿐, 원문 확인 필요)")


if __name__ == "__main__":
    main()
