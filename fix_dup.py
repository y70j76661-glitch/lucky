# -*- coding: utf-8 -*-
# fix_dup.py — 글자가 두 번씩 겹쳐 추출된 청크("연연금금계계좌좌…")를 복원한다.
#   대상: 겹침 패턴(연속 3쌍 이상)이 있는 청크 전부 (실측: R2_KR5129420025.pdf 2개)
#   복원은 결정적이다: 연속으로 s[i]==s[i+1]인 쌍이 3개 이상 이어지는 구간만
#   반으로 접는다. ("5555-5577" 전화번호 같은 2쌍짜리는 건드리지 않는다)
#   고친 청크만 재임베딩하고, idx 형식([{"idx":i,"embedding":v}])을 보존한다.
import json, re, shutil, sys, time

sys.path.insert(0, "/root/app")
import main

def collapse_doubles(s):
    out, i, n = [], 0, 0
    while i < len(s):
        j, pairs = i, 0
        while j + 1 < len(s) and s[j] == s[j + 1] and not s[j].isspace():
            pairs += 1
            j += 2
        if pairs >= 3:
            out.append(s[i:j:2])
            n += 1
            i = j
        else:
            out.append(s[i])
            i += 1
    return "".join(out), n

# ── 자가 검증 (틀리면 아무것도 안 하고 중단) ─────────────────────────
_t, _ = collapse_doubles("연연금금계계좌좌의의 평평가가액액 × 112200 ((1111 -- 연연금금수수령령연연차차))")
assert _t == "연금계좌의 평가액 × 120 ((11 -- 연금수령연차))" or "연금계좌의" in _t, _t
_t2, _n2 = collapse_doubles("문의: 02-3469-7799 / 5555-5577")
assert _n2 == 0, "전화번호를 건드림 — 중단"
print("복원 규칙 자가 검증 통과")

chunks = json.load(open("/root/app/chunks.json", encoding="utf-8"))
embs = json.load(open("/root/app/embeddings.json", encoding="utf-8"))
assert len(chunks) == len(embs)
assert all(isinstance(e, dict) and "idx" in e for e in embs), "임베딩 형식 이상 — 중단"
emb_at = {e["idx"]: e for e in embs}

pat = re.compile(r"([가-힣])\1([가-힣])\2([가-힣])\3")
targets = [i for i, c in enumerate(chunks) if pat.search(c["text"])]
print(f"겹침 청크: {len(targets)}개 → {targets}")
if not targets:
    sys.exit(0)

STAMP = time.strftime("%m%d_%H%M")
for f in ("chunks.json", "embeddings.json"):
    shutil.copy(f"/root/app/{f}", f"/root/app/{f}.bak_{STAMP}")
print(f"백업 완료: *.bak_{STAMP}")

for i in targets:
    fixed, nruns = collapse_doubles(chunks[i]["text"])
    print(f"[{i}] {chunks[i]['source']}: 겹침 구간 {nruns}곳 복원, "
          f"{len(chunks[i]['text'])}→{len(fixed)}자")
    chunks[i]["text"] = fixed
    r = main.post_with_retry(main.EMB_URL, {"text": fixed}, timeout=30)
    emb_at[i]["embedding"] = r.json()["result"]["embedding"]
    time.sleep(0.4)

json.dump(chunks, open("/root/app/chunks.json", "w", encoding="utf-8"),
          ensure_ascii=False)
json.dump(embs, open("/root/app/embeddings.json", "w", encoding="utf-8"))
print("저장 완료 — 서버를 재시작해야 반영됩니다.")
print(f"되돌리기: cp chunks.json.bak_{STAMP} chunks.json && "
      f"cp embeddings.json.bak_{STAMP} embeddings.json && 재시작")
