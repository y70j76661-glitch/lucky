# -*- coding: utf-8 -*-
# diag15.py — '문서에 있는 질문인데 자료 없음' 사례를 해부한다.
#   각 건마다: ①질문이 나온 원본 청크를 찾고 ②검색을 다시 돌려
#   그 청크(또는 그 문서)가 몇 등으로 나오는지 잰다.
#   → '검색이 못 찾음(순위권 밖)' / '문서는 찾았는데 다른 청크' /
#      '청크까지 찾았는데 모델이 무시함' 을 가른다. 처방이 서로 다르기 때문이다.
#   비용: 질문당 임베딩 1회 (LLM 생성 없음) — 15건이면 몇십 원 수준.
import json, re, sys

sys.path.insert(0, "/root/app")
import main  # chunks·embeddings 로드 + search()

# 1) 대상 수집: probe.jsonl에서 '문서에 있는 질문인데 자료 없음'이 찍힌 건
targets = []
for ln in open("/root/app/probe.jsonl", encoding="utf-8"):
    d = json.loads(ln)
    if any("문서에 있는 질문인데" in x for x in d.get("soft", [])):
        targets.append(d)
print(f"대상 {len(targets)}건\n")


def flat(t):
    return re.sub(r"\s", "", t)


counts = {"검색이 못 찾음": 0, "문서만 찾음(다른 청크)": 0, "청크 찾았는데 무시": 0,
          "원본 청크 못 찾음(질문 변형)": 0}
for d in targets:
    q, src = d["q"], d.get("src", "")
    # 2) 이 질문이 나온 원본 청크 찾기 (사정붙임 A2는 앞부분 제거)
    body = re.sub(r"^[^.?!]*(?:이에요|예요|입니다|인데요|받았어요|갖고 있어요)\.\s*",
                  "", q).strip()
    key = flat(body)[:24]
    idxs = [i for i, c in enumerate(main.chunks) if key and key in flat(c["text"])]
    # 3) 검색 재실행 — 원본 청크·문서의 순위
    docs, scores, top, _ = main.search(q, top_k=5)
    got_srcs = [c["source"] for c in docs]
    chunk_hit = any(key in flat(c["text"]) for c in docs) if key else False
    if not idxs:
        verdict = "원본 청크 못 찾음(질문 변형)"
    elif chunk_hit:
        verdict = "청크 찾았는데 무시"
    elif src in got_srcs:
        verdict = "문서만 찾음(다른 청크)"
    else:
        verdict = "검색이 못 찾음"
    counts[verdict] += 1
    print(f"[{d['id']}] {verdict}  (최고 유사도 {top:.3f})")
    print(f"    질문: {q[:70]}")
    print(f"    원본: {src} (코퍼스 내 일치 청크 {len(idxs)}개)")
    print(f"    검색 결과: {', '.join(dict.fromkeys(got_srcs))}")

print("\n== 판정 집계 ==")
for k, v in counts.items():
    if v:
        print(f"  {v:3d}  {k}")
