# check_risk.py — 위험등급/변동성 추출 검사 + 배포 전 게이트
#   판정 로직은 main.py에서 그대로 꺼내 쓴다(규칙이 두 군데 있으면 반드시 어긋난다).
#   커버리지가 떨어지거나 교차검증이 깨지면 종료코드 1 → 배포를 멈춘다.
import json, re, sys, collections

MIN_COVER = 99          # 투자설명서 중 등급을 읽어야 하는 최소 비율(%)
src = open("main.py", encoding="utf-8").read()
ns = {"re": re}
exec(src[src.index("# 등급 표기는 운용사마다 다르다"):src.index("def _src_text(")], ns)
_read_grade, _read_vol = ns["_read_grade"], ns["_read_vol"]
_read_name = ns["_read_name"]

HAS_FUND = re.compile(r"집합투자기구\s*명칭")
# v9.47: 상품명이 ':' 같은 쓰레기로 잡히던 문제를 게이트로 잡는다
def _name_ok(n):
    return bool(n) and len(n) >= 4 and any(k in n for k in ("투자신탁", "펀드", "증권"))
HIST = re.compile(r"위험등급\s*변경\s*\[\s*([1-6])등급[^\]]*?→\s*([1-6])등급")
# 독립적인 두 번째 표기 — 읽은 값과 일치해야 한다
CROSS = re.compile(r"6\s*등급\s*중\s*(?:위험도가\s*\S+\s*)?([1-6])\s*등급")

chunks = json.load(open("chunks.json", encoding="utf-8"))
by = collections.defaultdict(list)
for c in chunks:
    by[c["source"]].append(c["text"])

real = ok = vol_ok = same = diff = nocross = name_ok = 0
traps, fails, bad, badname = [], [], [], []
kinds = collections.Counter()
for s, ts in sorted(by.items()):
    t = " ".join(ts)
    if not HAS_FUND.search(t):
        continue
    real += 1
    nm = _read_name(t)
    if _name_ok(nm):
        name_ok += 1
    else:
        badname.append((s, repr(nm)))
    g, lab = _read_grade(t)
    v, k = _read_vol(t)
    if g:
        ok += 1
    else:
        fails.append(s)
    if v is not None:
        vol_ok += 1
        kinds[k] += 1
    h = HIST.search(t)
    if h and g and int(h.group(1)) != g:
        traps.append((s, f"현재 {g}등급({lab}) / 이력 {h.group(1)}→{h.group(2)}"))
    ms = [int(m.group(1)) for m in CROSS.finditer(t)]
    if not ms:
        nocross += 1
    elif g in ms:
        same += 1
    else:
        diff += 1
        bad.append((s, g, lab, ms[:4]))

cover = ok * 100 // max(real, 1)
print(f"투자설명서            : {real}건")
print(f"  상품명 추출         : {name_ok}건 ({name_ok*100//max(real,1)}%)")
print(f"  현재 위험등급 추출  : {ok}건 ({cover}%)")
print(f"  변동성 추출         : {vol_ok}건")
for k, n in kinds.most_common():
    print(f"     └ {k}: {n}건")
print(f"  교차검증            : 가능 {same+diff}건 / 일치 {same} / 불일치 {diff}"
      f" (교차표기 없음 {nocross})")
print(f"\n[이력 함정 — 과거 등급을 현재로 오인하면 틀리는 문서] {len(traps)}건")
for s, m in traps[:20]:
    print("  -", s, "|", m)
if badname:
    print(f"\n[상품명 추출 실패] {len(badname)}건")
    for s2, n2 in badname[:15]:
        print("  -", s2, "|", n2)
if bad:
    print(f"\n[교차검증 불일치] {len(bad)}건")
    for b in bad[:15]:
        print("  X", b[0], "| 읽은값", b[1], b[2], "| 교차표기", b[3])
if fails:
    print(f"\n[등급 추출 실패] {len(fails)}건")
    for s in fails[:25]:
        print("  -", s)

problems = []
if cover < MIN_COVER:
    problems.append(f"커버리지 {cover}% < {MIN_COVER}%")
if diff:
    problems.append(f"교차검증 불일치 {diff}건")
if name_ok * 100 // max(real, 1) < 95:
    problems.append(f"상품명 추출 {name_ok}/{real}")
if problems:
    print("\n=== 배포 중단: " + " / ".join(problems) + " ===")
    sys.exit(1)
print("\n=== 통과 — 배포 가능 ===")
