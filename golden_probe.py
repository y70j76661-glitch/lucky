# -*- coding: utf-8 -*-
"""
golden_probe.py — 골든 질문 세트 + 스트레스 케이스로 '디테일 품질'을 수집·자동플래그.
Design.pdf 평가축: 정확성·근거완전성·요구충족·정보한계대응(역질문)·조건부추천·잘못된전제교정·근거표시.
카드 부착 여부만이 아니라 숫자/조건/근거/형식/어투까지 데이터로 남긴다.

사용: cd /root/app && source venv/bin/activate && python golden_probe.py
출력: golden_out.jsonl(전 필드) + golden_out.txt(읽기용) + 콘솔 요약
"""
import json
import re
import time
import requests

BASE = "http://127.0.0.1:8000/answer"
PACE = 0.4
TIMEOUT = 180

# (id, 카테고리, 질문, 기대요지)
Q = [
    # ── 섹션17 골든 세트 ──────────────────────────────────────────
    ("G01", "세제", "IRP를 중도해지하면 세금이 어떻게 되나요?", "A05: 기타소득세16.5%, 과세제외 예외. 이전기한 X"),
    ("G02", "세제", "퇴직금을 IRP로 이전하면 세금 혜택이 있나요?", "I1: 세금혜택 핵심, 60일 이전기한은 좁은 각주 가능"),
    ("G03", "제도", "퇴직금을 IRP로 옮길 때 언제까지 해야 하나요?", "I1 본문: 60일 기한을 본문으로"),
    ("G04", "세제", "연금저축과 IRP 세액공제 한도는 얼마인가요?", "600/900 구분, 납입한도(1800)와 구분"),
    ("G05", "세제", "세액공제 최대 금액만 알려주세요.", "E01: 최대 148.5만(900×16.5), 대상금액 vs 실제공제 구분"),
    ("G06", "제도", "연금 수령 나이는 몇 살인가요?", "55세, 가입기간5년 요건"),
    ("G07", "세제", "연금수령 나이는 묻지 않고 세액공제만 알려주세요.", "수령요건 카드 미부착, 세액공제만"),
    ("G08", "세제", "회사가 넣어준 DC 부담금도 공제되나요?", "A12: 회사부담금 공제대상 아님. 14일 카드 X"),
    ("G09", "제도", "확정급여형(DB)과 확정기여형(DC)의 차이는 무엇인가요?", "제도 비교, 기한 X"),
    ("G10", "추천", "좋은 연금상품 하나 추천해주세요.", "조건 역질문(투자기간·손실감내)"),
    ("G11", "추천", "원금 손실 없이 가장 좋은 상품은요?", "보장여부 교정 + 조건 확인, 단정 금지"),
    ("G12", "세제", "명예퇴직금을 연금계좌에 넣으면 절세할 수 있나요?", "복합: 세금+이전+조건. 누락 확인"),
    # ── 섹션12 표현 변형(같은 의도 → 같은 처리) ──────────────────
    ("V01", "제도", "퇴직금을 IRP로 옮기면 언제까지 해야 하나요?", "I1 본문(옮기다=이전)"),
    ("V02", "제도", "퇴직금 IRP 입금 기한 알려줘", "I1 본문(구어체·짧은질문)"),
    # ── 섹션13 부정·조건부(오탐 취약) ─────────────────────────────
    ("N01", "세제", "IRP로 이전하지 않고 중도해지하면 세금이 어떻게 되나요?", "이전 오인 금지 → 중도해지 과세 중심"),
    ("N02", "세제", "IRP 이전 말고 세액공제 한도만 알려주세요.", "이전 기한 미부착, 세액공제 한도만"),
    # ── 섹션10 잘못된 전제(유도성) ───────────────────────────────
    ("F01", "세제", "IRP는 원금이 보장되죠?", "전제 교정: 상품에 따라 보장 아님"),
    ("F02", "세제", "세액공제는 납입액 전부를 돌려받는 거죠?", "전제 교정: 대상금액×공제율이지 전액 아님"),
    ("F03", "세제", "60일이 지나면 무조건 혜택을 못 받죠?", "단정 교정: 사유·요건에 따라"),
    # ── 상품 설명 ────────────────────────────────────────────────
    ("P01", "상품", "또박또박연금펀드의 합성총보수와 위험등급을 알려주세요.", "0.87%, 위험등급, 상품유형 정확"),
]

# ── 자동 플래그 (섹션18 우선순위) ─────────────────────────────────
_GLITCH = re.compile(r"\d\*\*\s*%|\d\s*\*\*\s*\(|만\s*원\s*원|원원")
_LATEX = re.compile(r"\\frac|\\times|\$\$")
_COND = re.compile(r"다만|단,|경우에 따라|요건|조건|해당(?:하는|되는)|따라 다|수 있습니다|가능할 수")
_ASKBACK = re.compile(r"확인(?:이 필요|해야|해\s*주|하려면)|여쭤|알려주(?:시면|세요)|먼저 파악|어느 정도")
_FIX = re.compile(r"단정하기(?:는)? 어렵|달라질 수 있|경우에 따라|일률적으로|반드시.*것은 아")
_LEAK = re.compile(r"think_trace|retrieved_context|\[4-a|카드\]|_note|clean_note")
_EMPTYBUL = re.compile(r"(?m)^\s*(?:[-*]|\d+[.)])\s*$")


def flags(cat, q, ans, ctx):
    f = []
    if _GLITCH.search(ans): f.append("[오류]숫자/단위글리치")
    if _LATEX.search(ans): f.append("[오류]수식노출")
    if _LEAK.search(ans): f.append("[오류]내부정보노출")
    if _EMPTYBUL.search(ans): f.append("[오류]빈불릿")
    if "[참고 문서]" not in ans and cat != "보안": f.append("[의심]출처없음")
    else:
        _docs = re.findall(r"(?:doc\d+\.\w+|R2_[A-Z0-9]+\.\w+)", ans.split("[참고 문서]")[-1] if "[참고 문서]" in ans else "")
        if len(_docs) >= 6: f.append(f"[의심]근거과다({len(_docs)})")
    # 조건·예외 (세제/제도/추천은 조건표현이 있어야 안전)
    if cat in ("세제", "제도", "추천") and not _COND.search(ans): f.append("[의심]조건/예외부족")
    # 추천 역질문
    if cat == "추천" and not _ASKBACK.search(ans): f.append("[의심]추천_역질문없음")
    # 잘못된 전제 교정 (F*)
    if q.rstrip().endswith(("죠?", "죠")) or "무조건" in q or "전부를" in q:
        if not _FIX.search(ans): f.append("[의심]전제교정없음")
    # 소득 없는데 특정 공제액 단정 (계산 안전)
    if "세액공제" in q and not re.search(r"총급여|연봉|소득", q) \
            and re.search(r"약?\s*\d+(?:\.\d+)?\s*만\s*원.*(?:공제|환급|돌려)", ans) \
            and not re.search(r"소득|구간|이하|초과|경우", ans):
        f.append("[의심]소득미상_공제액단정")
    return f


def main():
    print(f"골든 프로브 {len(Q)}문항 — {BASE}\n")
    flagged = []
    ft = open("golden_out.txt", "w", encoding="utf-8")
    fj = open("golden_out.jsonl", "w", encoding="utf-8")
    for qid, cat, q, expect in Q:
        t0 = time.time()
        try:
            r = requests.get(BASE, params={"question_id": qid, "question": q}, timeout=TIMEOUT)
            j = r.json()
            ans = j.get("answer", "") or ""
            trace = j.get("think_trace", "") or ""
            ctx = j.get("retrieved_context", "") or ""
        except Exception as e:
            ans = f"(요청실패: {str(e)[:60]})"; trace = ""; ctx = ""
        dt = time.time() - t0
        fl = flags(cat, q, ans, ctx)
        docs = re.findall(r"(?:doc\d+\.\w+|R2_[A-Z0-9]+\.\w+)", ans)
        rec = {"id": qid, "category": cat, "question": q, "expect": expect,
               "answer": ans, "trace": trace, "retrieved_context": ctx[:1500],
               "docs_cited": sorted(set(docs)), "elapsed_sec": round(dt, 1), "flags": fl}
        fj.write(json.dumps(rec, ensure_ascii=False) + "\n")
        ft.write(f"\n{'='*74}\n[{qid}][{cat}] {q}\n기대: {expect}\n({dt:.1f}s) flags={fl}\n"
                 f"근거문서: {rec['docs_cited']}\n--- 답변 ---\n{ans}\n")
        print(f"  [{qid}][{cat}] {dt:4.1f}s  {' '.join(fl) if fl else 'OK'}")
        if fl: flagged.append((qid, fl))
        time.sleep(PACE)
    ft.close(); fj.close()
    print("\n" + "=" * 60)
    print(f"플래그 {len(flagged)}/{len(Q)}")
    for qid, fl in flagged:
        print(f"  {qid}: {' '.join(fl)}")
    print("=" * 60)
    print("전체: golden_out.txt / golden_out.jsonl → jsonl 첨부하면 전수 심층검토")


if __name__ == "__main__":
    main()
