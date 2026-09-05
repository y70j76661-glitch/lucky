# -*- coding: utf-8 -*-
"""corpus_facts.py — PRODUCT_FACTS 정답표를 위한 코퍼스 근거 추출(API 호출 없음).
빈출 상품별로 위험등급·총보수·합성총보수·클래스·기간별 비용 표 주변 원문을 찍는다. 값을 코드에 고정하기 전 근거 확인용.
사용: cd /root/app && python3 corpus_facts.py > corpus_facts_out.txt ; 그 파일을 첨부."""
import json, re

d = json.load(open("chunks.json", encoding="utf-8")); it = d if isinstance(d, list) else d.values()
ts = [(c.get("text", "") if isinstance(c, dict) else str(c), (c.get("source") or c.get("src") or c.get("doc") or c.get("file") or "") if isinstance(c, dict) else "") for c in it]

def show(title, must, extra=None, n=4, width=420):
    print("=" * 90); print(f"## {title}")
    hits = [(t, s) for t, s in ts if all(re.search(m, t) for m in must)]
    print(f"청크 {len(hits)}개")
    for t, s in hits[:n]:
        tt = re.sub(r"\s+", " ", t)
        if extra:
            m = re.search(extra, tt)
            if m:
                a = max(0, m.start() - width // 2); tt = tt[a:a + width]
            else:
                tt = tt[:width]
        else:
            tt = tt[:width]
        print(f"  [{s}] {tt}")

# S1: 또박또박 클래스별 총보수 / 합성총보수
show("또박또박 — 총보수·합성총보수·클래스", [r"또박또박"], r"총보수|합성", n=6)
show("또박또박 — C-P2 / A / C-P 클래스 표", [r"또박또박", r"C-P"], r"C-P", n=6)
# S3: 인덱스12M 기간별 숫자의 표 헤더
show("인덱스12M — 위험등급", [r"인덱스\s*12M", r"등급"], r"등급", n=3)
show("인덱스12M — 총보수/기간별 비용 표", [r"인덱스\s*12M|퇴직연금인덱스"], r"총보수|1년|3년|5년|10년|비용", n=6, width=600)
show("인덱스12M — 0.42/0.28 숫자 주변", [r"0\.42|0\.28|0\.4313|0\.532"], r"0\.42|0\.28|0\.4313|0\.532", n=4, width=600)
# S4: TDF 2030 / 2050
show("TDF2030 — 상품명·등급·보수", [r"TDF\s*2030|2030"], r"TDF|2030", n=6, width=500)
show("TDF2050 — 상품명·등급·보수", [r"TDF\s*2050|2050"], r"TDF|2050", n=6, width=500)
show("전략배분 TDF — 총보수 0.88", [r"0\.88"], r"0\.88", n=4, width=500)
# 빈출 상품 등급 확인
show("삼성클래식 주식형 — 등급", [r"삼성클래식", r"주식"], r"등급", n=3)
show("삼성클래식 채권형 — 등급", [r"삼성클래식", r"채권"], r"등급", n=3)
show("TIGER 미국배당다우존스 — 보수·등급", [r"미국배당다우존스"], r"보수|등급|위험", n=4)
show("우리은행 예금 — 원리금보장", [r"우리은행"], r"예금|원리금", n=3)
print("=" * 90); print("끝")
