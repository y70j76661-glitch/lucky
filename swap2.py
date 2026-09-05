# -*- coding: utf-8 -*-
# swap2.py — 깨진 스캔 문서 10개(doc2,3,5,7,8,24,30,31,32,37)의 청크를
#   사람이 다시 읽어 옮겨 적은 텍스트로 교체하고, 새 청크만 재임베딩한다.
#
#   ★ 1차 swap_docs.py와의 차이 (그때의 사고 재발 방지):
#   - embeddings.json은 [{"idx": 청크위치, "embedding": [...]}] 형식이다.
#     짝 맞추기는 반드시 idx 필드로 하고, 저장할 때도 idx를 새 위치로 다시 매긴다.
#   - 실행 전 형식을 검증하고, 어긋나면 아무것도 건드리지 않고 중단한다.
#
#   안전장치:
#   - 실행 전 chunks.json / embeddings.json을 타임스탬프 백업
#   - 다른 문서의 청크·임베딩은 단 하나도 건드리지 않는다
#   - 되돌리기: cp chunks.json.bak_XXXX chunks.json (임베딩도 동일) 후 서버 재시작
import json, sys, time, shutil

sys.path.insert(0, "/root/app")
import main                                   # EMB_URL·post_with_retry·인증 재사용

TARGETS = {
    "doc2.pdf":  ("doc2.txt",  "[퇴직연금·개인연금 연금지급업무 안내]"),
    "doc3.pdf":  ("doc3.txt",  "[연금계좌 증권담보융자(담보대출) 안내]"),
    "doc5.pdf":  ("doc5.txt",  "[연금저축계좌 중도인출·계좌해지 안내]"),
    "doc7.pdf":  ("doc7.txt",  "[퇴직연금 장외채권 매수 모바일 신청 가이드]"),
    "doc8.pdf":  ("doc8.txt",  "[연금저축계좌 상장인프라펀드 매매 FAQ]"),
    "doc24.pdf": ("doc24.txt", "[퇴직연금 모바일 유상청약 가이드]"),
    "doc30.pdf": ("doc30.txt", "[디폴트옵션 자주 묻는 질문 TOP7]"),
    "doc31.pdf": ("doc31.txt", "[디폴트옵션 가입자 안내]"),
    "doc32.pdf": ("doc32.txt", "[디폴트옵션 FAQ 가입자 안내용]"),
    "doc37.pdf": ("doc37.txt", "[연금 인출 가이드]"),
}
STAMP = time.strftime("%m%d_%H%M")


def chunk_text(text, title):
    """줄 단위로 모아 700~1100자 청크로. 섹션([머리] 또는 == 머리 ==)과
    Q항목(Q1. / Q4-1. / Q-3) 경계를 존중한다.
    섹션 이름표는 '청크가 시작될 때'의 섹션을 쓴다."""
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
        s = ln.strip()
        is_sec = bool(_re.fullmatch(r"\[.{2,40}\]", s)) or \
                 bool(_re.fullmatch(r"==\s*.{2,40}?\s*==", s))
        boundary = is_sec or bool(_re.match(r"^Q\s*-?\d", s))
        size = sum(len(x) for x in cur)
        if cur and (size > 1100 or (boundary and size > 600)):
            flush()
        if not cur:
            cur_sec = s if is_sec else section
        if is_sec:
            section = s
        cur.append(ln)
    flush()
    return chunks


chunks = json.load(open("/root/app/chunks.json", encoding="utf-8"))
embs = json.load(open("/root/app/embeddings.json", encoding="utf-8"))

# 0) 형식 검증 — 어긋나면 손대지 않고 중단
assert len(chunks) == len(embs), f"청크 {len(chunks)} ≠ 임베딩 {len(embs)} — 중단"
assert all(isinstance(e, dict) and "idx" in e and "embedding" in e for e in embs), \
    "embeddings.json 항목이 {'idx':…, 'embedding':…} 형식이 아님 — 중단"
idx_set = {e["idx"] for e in embs}
assert idx_set == set(range(len(chunks))), \
    f"idx 필드가 0..{len(chunks)-1} 전체와 일치하지 않음 — 중단"
emb_by_idx = {e["idx"]: e["embedding"] for e in embs}

old_n = sum(1 for c in chunks if c["source"] in TARGETS)
print(f"교체 대상 기존 청크: {old_n}개 (전체 {len(chunks)}개 중)")
assert old_n > 0, "교체 대상 청크가 하나도 없음 — source 이름 확인 필요, 중단"

# 1) 백업
for f in ("chunks.json", "embeddings.json"):
    shutil.copy(f"/root/app/{f}", f"/root/app/{f}.bak_{STAMP}")
print(f"백업 완료: *.bak_{STAMP}")

# 2) 기존 청크 제거 — 반드시 idx 필드로 짝을 맞춰서
keep_pairs = [(c, emb_by_idx[i]) for i, c in enumerate(chunks)
              if c["source"] not in TARGETS]
chunks2 = [c for c, _ in keep_pairs]
vecs2 = [v for _, v in keep_pairs]

# 3) 새 청크 생성 + 임베딩
new_total = 0
for src, (fn, title) in TARGETS.items():
    text = open(f"/root/app/reocr/{fn}", encoding="utf-8").read()
    parts = chunk_text(text, title)
    print(f"{src}: 새 청크 {len(parts)}개 임베딩 중...")
    for p in parts:
        r = main.post_with_retry(main.EMB_URL, {"text": p}, timeout=30)
        emb = r.json()["result"]["embedding"]
        chunks2.append({"text": p, "source": src})
        vecs2.append(emb)
        new_total += 1
        time.sleep(0.4)

# 4) 저장 — idx는 새 위치로 다시 매긴다
assert len(chunks2) == len(vecs2)
embs2 = [{"idx": i, "embedding": v} for i, v in enumerate(vecs2)]
json.dump(chunks2, open("/root/app/chunks.json", "w", encoding="utf-8"),
          ensure_ascii=False)
json.dump(embs2, open("/root/app/embeddings.json", "w", encoding="utf-8"))
print(f"\n완료: 기존 {old_n}개 제거 → 새 {new_total}개 추가 "
      f"(전체 {len(chunks)} → {len(chunks2)}개)")
print("이제 서버를 재시작해야 새 데이터가 실립니다.")
print(f"되돌리기: cp chunks.json.bak_{STAMP} chunks.json && "
      f"cp embeddings.json.bak_{STAMP} embeddings.json && 서버 재시작")
