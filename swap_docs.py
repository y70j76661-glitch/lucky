# -*- coding: utf-8 -*-
# swap_docs.py — 깨진 스캔 문서 3개(doc9, doc22, doc54)의 청크를
#   사람이 다시 읽어 옮겨 적은 텍스트로 교체하고, 새 청크만 재임베딩한다.
#
#   안전장치:
#   - 실행 전 chunks.json / embeddings.json을 타임스탬프 백업
#   - 다른 문서의 청크·임베딩은 단 하나도 건드리지 않는다
#   - 되돌리기: cp chunks.json.bak_XXXX chunks.json (임베딩도 동일) 후 서버 재시작
import json, sys, time, shutil

sys.path.insert(0, "/root/app")
import main                                   # EMB_URL·post_with_retry·인증 재사용

TARGETS = {"doc9.pdf": "doc9.txt", "doc22.pdf": "doc22.txt", "doc54.pdf": "doc54.txt"}
STAMP = time.strftime("%m%d_%H%M")


def chunk_text(text, title):
    """줄 단위로 모아 700~1100자 청크로. 섹션([머리])과 Q항목 경계를 존중한다.
    섹션 이름표는 '청크가 시작될 때'의 섹션을 쓴다(흘러가며 갱신하면 한 칸 밀린다)."""
    import re as _re
    lines = [l.rstrip() for l in text.splitlines()]
    section = ""
    chunks, cur, cur_sec = [], [], ""

    def flush():
        nonlocal cur
        if cur and sum(len(x) for x in cur) > 40:
            body = "\n".join(cur).strip()
            head = title if (cur_sec and body.startswith(cur_sec)) or not cur_sec \
                else f"{title} {cur_sec}"
            chunks.append(body if body.startswith(title) else head + "\n" + body)
        cur = []

    for ln in lines:
        is_sec = bool(_re.fullmatch(r"\[.{2,40}\]", ln.strip()))
        boundary = is_sec or (ln[:1] == "Q" and ln[1:3].strip(". ").isdigit())
        size = sum(len(x) for x in cur)
        if cur and (size > 1100 or (boundary and size > 600)):
            flush()
        if not cur:
            cur_sec = ln.strip() if is_sec else section
        if is_sec:
            section = ln.strip()
        cur.append(ln)
    flush()
    return chunks


chunks = json.load(open("/root/app/chunks.json", encoding="utf-8"))
embs = json.load(open("/root/app/embeddings.json", encoding="utf-8"))
assert len(chunks) == len(embs), f"청크 {len(chunks)} ≠ 임베딩 {len(embs)} — 중단"

old_n = sum(1 for c in chunks if c["source"] in TARGETS)
print(f"교체 대상 기존 청크: {old_n}개 (전체 {len(chunks)}개 중)")

# 1) 백업
for f in ("chunks.json", "embeddings.json"):
    shutil.copy(f"/root/app/{f}", f"/root/app/{f}.bak_{STAMP}")
print(f"백업 완료: *.bak_{STAMP}")

# 2) 기존 청크 제거 (임베딩과 같은 인덱스로)
keep = [(c, e) for c, e in zip(chunks, embs) if c["source"] not in TARGETS]
chunks2 = [c for c, _ in keep]
embs2 = [e for _, e in keep]

# 3) 새 청크 생성 + 임베딩
TITLES = {"doc9.pdf": "[연금저축계좌 주식적립식 서비스]",
          "doc22.pdf": "[IRP 중도인출·계약해지·이체·연금인출 안내]",
          "doc54.pdf": "[퇴직연금 MP 구독 서비스 FAQ]"}
new_total = 0
for src, fn in TARGETS.items():
    text = open(f"/root/app/reocr/{fn}", encoding="utf-8").read()
    parts = chunk_text(text, TITLES[src])
    print(f"{src}: 새 청크 {len(parts)}개 임베딩 중...")
    for p in parts:
        r = main.post_with_retry(main.EMB_URL, {"text": p}, timeout=30)
        emb = r.json()["result"]["embedding"]
        chunks2.append({"text": p, "source": src})
        embs2.append(emb)
        new_total += 1
        time.sleep(0.4)

json.dump(chunks2, open("/root/app/chunks.json", "w", encoding="utf-8"),
          ensure_ascii=False)
json.dump(embs2, open("/root/app/embeddings.json", "w", encoding="utf-8"))
print(f"\n완료: 기존 {old_n}개 제거 → 새 {new_total}개 추가 "
      f"(전체 {len(chunks)} → {len(chunks2)}개)")
print("이제 서버를 재시작해야 새 데이터가 실립니다.")
print(f"되돌리기: cp chunks.json.bak_{STAMP} chunks.json && "
      f"cp embeddings.json.bak_{STAMP} embeddings.json && 서버 재시작")
