# -*- coding: utf-8 -*-
"""
number_grounding_probe.py — [5단계 사전측정] 답변의 핵심 수치가 근거(retrieved_context)에
실제로 있는지 전수 측정. '삭제/병기'는 하지 않고 '얼마나 미근거로 뜨는지 + 그게 FP인지'만 본다.
  검사 대상 수치: 세율(N%) · 나이(N세) · 위험등급(N등급) · 기간(N일/개월/년)
  계산 맥락(× = 곱 합산) 근처 수치는 파생값일 수 있어 제외.
판정: 미근거로 뜬 수치가 '진짜 근거에 없음'이면 5단계 가치 有 / '사실은 근거에 있는데 표기차/범위/재포맷'이면 FP.
사용: cd /root/app && source venv/bin/activate && python number_grounding_probe.py
"""
import re, time, requests

BASE = "http://127.0.0.1:8000/answer"
Q = [
    ("G01","IRP를 중도해지하면 세금이 어떻게 되나요?"),
    ("G04","연금저축과 IRP 세액공제 한도는 얼마인가요?"),
    ("G05","세액공제 최대 금액만 알려주세요."),
    ("G06","연금 수령 나이는 몇 살인가요?"),
    ("G08","회사가 넣어준 DC 부담금도 공제되나요?"),
    ("N01","IRP로 이전하지 않고 중도해지하면 세금이 어떻게 되나요?"),
    ("F02","세액공제는 납입액 전부를 돌려받는 거죠?"),
    ("P01","또박또박연금펀드의 합성총보수와 위험등급을 알려주세요."),
]
# 수치+단위 추출 (금액 만원/천원은 계산 파생 잦아 제외, 세율·나이·등급·기간만)
_NUM = re.compile(r"(\d+(?:\.\d+)?)\s*(%|세|등급|일|개월|년)")


def norm(s): return re.sub(r"\s+", "", s)


def main():
    print(f"수치 근거 측정 {len(Q)}문항 — {BASE}\n")
    total_ung = 0
    for qid, q in Q:
        try:
            r = requests.get(BASE, params={"question_id": qid, "question": q}, timeout=180)
            j = r.json(); a = j.get("answer", "") or ""; ctx = j.get("retrieved_context", "") or ""
        except Exception as e:
            print(f"  [{qid}] 요청실패 {str(e)[:40]}"); continue
        body = a.split("[참고 문서]")[0]
        nctx = norm(ctx)
        ung = []
        for m in _NUM.finditer(body):
            val, unit = m.group(1), m.group(2)
            # 계산 맥락 제외
            around = body[max(0, m.start()-12):m.end()+12]
            if re.search(r"[×xX=]|곱|합산|공제\s*대상", around):
                continue
            # 근거에 그 숫자(digits)가 있나
            if val.replace(".", "") and val not in nctx and norm(val) not in nctx:
                ung.append(f"{val}{unit}")
        if ung:
            total_ung += len(ung)
            print(f"  [{qid}] 미근거 수치: {ung}")
        else:
            print(f"  [{qid}] 전부 근거확인 OK")
        time.sleep(0.3)
    print("\n" + "=" * 60)
    print(f"미근거 수치 총 {total_ung}건")
    print("→ 각 건이 '진짜 근거에 없음'인지 '표기차·범위·재포맷 FP'인지 원문으로 판단해야 함.")
    print("  FP가 대부분이면 5단계 결정적 병기는 위험 → 채택 안 함이 맞음.")
    print("=" * 60)


if __name__ == "__main__":
    main()
