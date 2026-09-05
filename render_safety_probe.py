# -*- coding: utf-8 -*-
"""
render_safety_probe.py — [갭6] 렌더 안전성 감사.
채점 화면이 마크다운을 렌더하지 않고 raw 텍스트로 보여줄 경우 '글자로 깨지는' 마크다운
구성요소가 답변에 있는지 전수 점검한다. (①②③·※·- 불릿·[참고 문서]·일반숫자는 raw에서도 정상.)
  깨지는 것: **볼드**(이미 제거), | 표 |, # 헤더, `백틱`, [링크](url), > 인용, ~~취소선~~
특히 비교 질문의 마크다운 표(|)가 최대 위험 — 비교 질문도 포함해 던진다.
사용: cd /root/app && source venv/bin/activate && python render_safety_probe.py
"""
import re, time, requests

BASE = "http://127.0.0.1:8000/answer"
Q = [
    ("G01","IRP를 중도해지하면 세금이 어떻게 되나요?"),
    ("G04","연금저축과 IRP 세액공제 한도는 얼마인가요?"),
    ("G05","세액공제 최대 금액만 알려주세요."),
    ("G06","연금 수령 나이는 몇 살인가요?"),
    ("G09","확정급여형(DB)과 확정기여형(DC)의 차이는 무엇인가요?"),
    ("G10","좋은 연금상품 하나 추천해주세요."),
    ("G11","원금 손실 없이 가장 좋은 상품은요?"),
    ("P01","또박또박연금펀드의 합성총보수와 위험등급을 알려주세요."),
    # 비교 질문(표 생성 위험) 3종
    ("CMP1","삼성 주식형과 채권형 상품의 총보수와 위험등급을 비교해줘."),
    ("CMP2","연금저축과 IRP를 세액공제 한도·납입한도 기준으로 비교해줘."),
    ("CMP3","DB형과 DC형을 운용주체·위험부담 기준으로 표로 비교해줘."),
]
# raw에서 깨지는 마크다운
CHECKS = {
    "볼드**": re.compile(r"\*\*"),
    "표|": re.compile(r"(?m)^\s*\|.*\|"),      # 마크다운 표 행
    "헤더#": re.compile(r"(?m)^\s*#{1,6}\s"),
    "백틱`": re.compile(r"`"),
    "링크[](": re.compile(r"\[[^\]]+\]\([^)]+\)"),
    "인용>": re.compile(r"(?m)^\s*>\s"),
    "취소선~~": re.compile(r"~~"),
    "백슬래시\\": re.compile(r"\\"),
}


def main():
    print(f"렌더 안전성 감사 {len(Q)}문항 — {BASE}\n")
    flagged = []
    ft = open("render_out.txt", "w", encoding="utf-8")
    for qid, q in Q:
        try:
            a = requests.get(BASE, params={"question_id": qid, "question": q}, timeout=180).json().get("answer", "") or ""
        except Exception as e:
            a = f"(요청실패:{str(e)[:40]})"
        hit = [name for name, pat in CHECKS.items() if pat.search(a)]
        print(f"  [{qid}] {'OK(raw안전)' if not hit else '깨짐위험: ' + ' '.join(hit)}")
        if hit:
            flagged.append((qid, hit))
            ft.write(f"\n{'='*60}\n[{qid}] {q}\n깨짐:{hit}\n{a}\n")
        time.sleep(0.3)
    ft.close()
    print("\n" + "=" * 60)
    if flagged:
        print(f"raw 렌더 시 깨질 수 있는 문항 {len(flagged)}:")
        for qid, h in flagged:
            print(f"  [{qid}] {h}")
        print("원문: render_out.txt → 그 서식(특히 | 표)만 국소 정리")
    else:
        print("깨지는 마크다운 0 → raw 렌더에서도 안전(갭6 통과)")
    print("=" * 60)


if __name__ == "__main__":
    main()
