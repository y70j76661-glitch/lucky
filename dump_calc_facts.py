# -*- coding: utf-8 -*-
"""
dump_calc_facts.py — chunks.json에서 '계산에 쓰이는 사실'만 추출해 파일로 저장.
  세율·한도·보수·수수료·과세·연도별 값 등, 숫자가 들어간 문장만 문서별로 모은다.
  → calc_facts.txt 생성. 이 파일을 근거로 100문제 계산 배터리의 기대값을 박는다.

사용법: cd /root/app && python3 dump_calc_facts.py
"""
import json
import re

# 계산·수치 사실을 담은 문장을 고르는 키워드
KW = re.compile(
    r"세액공제|세율|과세|소득세|퇴직소득|연금소득|기타소득|금융소득|종합과세|"
    r"공제\s*한도|납입\s*한도|한도|공제|절세|환급|중도\s*해지|중도\s*인출|"
    r"총보수|합성총보수|보수|수수료|증권거래비용|비용|위험자산|편입\s*한도|"
    r"세금|원천징수|비과세|과세이연|저율|분리과세"
)
# 숫자(원·%·만원·억·연도)가 있어야 계산 사실
NUM = re.compile(r"\d")
YEAR = re.compile(r"20\d\d\s*년")

data = json.load(open("chunks.json", encoding="utf-8"))
by_src = {}
for c in data:
    src = c.get("source", "?")
    txt = c.get("text", "") or ""
    for ln in re.split(r"(?<=[.。!?])\s+|\n", txt):
        ln = re.sub(r"\s+", " ", ln).strip()
        if len(ln) < 8 or not NUM.search(ln):
            continue
        if not KW.search(ln):
            continue
        by_src.setdefault(src, [])
        if ln not in by_src[src]:            # 문서 내 중복 제거
            by_src[src].append(ln)

with open("calc_facts.txt", "w", encoding="utf-8") as f:
    total = 0
    for src in sorted(by_src):
        lines = by_src[src]
        # 연도 언급 문장을 앞쪽에 오게(연도별 변천이 중요)
        lines.sort(key=lambda x: (0 if YEAR.search(x) else 1))
        f.write(f"\n===== {src} ({len(lines)}문장) =====\n")
        for ln in lines[:40]:                # 문서당 상한(과다 방지)
            f.write(f"- {ln[:300]}\n")
            total += 1
    f.write(f"\n[총 {total}문장 / {len(by_src)}문서]\n")

print(f"calc_facts.txt 저장 완료: {len(by_src)}문서, "
      f"{sum(min(len(v),40) for v in by_src.values())}문장")
print("이 파일을 채팅에 첨부해서 보내주세요.")
