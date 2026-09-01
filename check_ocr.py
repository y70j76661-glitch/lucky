# check_ocr.py — OCR로 깨진 청크가 얼마나 되는지 재고, 근거로 쓰이면 위험한 것을 찾는다.
#   실측 계기: doc9.pdf의 '예약주문' 대목이 문장이 뒤섞이고 글자가 깨진 채로 근거가 되어,
#   모델이 없는 인과관계를 지어냈다("8시 30분~9시 29분에 주문하면 미수가 발생하지 않는다").
#   사용법: python3 check_ocr.py [출력할 예시 수]
import json, re, sys, collections

chunks = json.load(open("chunks.json", encoding="utf-8"))

# 깨짐 신호 — 정상 한국어 문장에서는 거의 나오지 않는 것만 센다
_ODD_CHAR = re.compile(r"[『』〔〕｢｣＠＃＄％＆￥∙◇◆■□▲▼¨′″]")
_JAMO = re.compile(r"[ㄱ-ㅎㅏ-ㅣ]")                       # 자모만 남은 글자
# 의미 없이 이어진 긴 숫자 3개 이상 (예: 4 14186 6561 560411465)
_NUMRUN = re.compile(r"(?:(?<=\s)|^)\d{3,}(?:\s+\d{3,}){2,}")
_ASCII_JUNK = re.compile(r"[a-zA-Z]\d{4,}|\d{4,}[a-zA-Z]")
# 정상적으로 홀로 쓰이는 한 음절 (이건 깨짐이 아니다)
_OK1 = set("연년월일시분초총약각및등내외전후중상하대소만원수개건차명색점"
           "그이저것수때곳말일법식형기수액율률비용상한액표주식채권형")
_LONE = re.compile(r"(?<!\S)([가-힣])(?!\S)")


def garble_score(t):
    """0(깨끗)~1(심하게 깨짐). 정상 한국어에서는 거의 0이 나와야 한다."""
    n = max(len(t), 1)
    words = t.split()
    w = max(len(words), 1)
    lone_bad = sum(1 for c in _LONE.findall(t) if c not in _OK1)
    s = 0.0
    s += min(len(_ODD_CHAR.findall(t)) / n * 60, 0.30)
    s += min(len(_JAMO.findall(t)) / n * 80, 0.25)
    s += min(lone_bad / w * 3.0, 0.25)
    s += min(len(_NUMRUN.findall(t)) * 0.12, 0.24)
    s += min(len(_ASCII_JUNK.findall(t)) * 0.04, 0.12)
    return round(min(s, 1.0), 3)


rows = [(garble_score(c["text"]), c["source"], c["chunk_id"], c["text"]) for c in chunks]
rows.sort(key=lambda r: -r[0])

BANDS = [(0.5, "심각"), (0.3, "주의"), (0.15, "경미"), (0.0, "양호")]
band_cnt = collections.Counter()
for sc, *_ in rows:
    for th, name in BANDS:
        if sc >= th:
            band_cnt[name] += 1
            break

print(f"청크 {len(rows):,}개 품질 분포")
for _th, name in BANDS:
    n = band_cnt[name]
    print(f"  {name:4s} : {n:6,}개 ({n*100/len(rows):.1f}%)")

by_src = collections.defaultdict(lambda: [0, 0])
for sc, src, *_ in rows:
    by_src[src][1] += 1
    if sc >= 0.3:
        by_src[src][0] += 1
bad_src = sorted(((b / t, b, t, s) for s, (b, t) in by_src.items() if b),
                 reverse=True)[:15]
print("\n깨진 청크 비율이 높은 문서 (0.3 이상 기준)")
for ratio, b, t, s in bad_src:
    print(f"  {s:28s} {b:4d}/{t:4d}  ({ratio*100:.0f}%)")

k = int(sys.argv[1]) if len(sys.argv) > 1 else 5
print(f"\n가장 심하게 깨진 청크 {k}개")
for sc, src, cid, t in rows[:k]:
    print(f"\n--- {src} #{cid}  점수 {sc}")
    print("   " + re.sub(r"\s+", " ", t)[:300])
