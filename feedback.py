# -*- coding: utf-8 -*-
"""
feedback.py — 경량 피드백 루프(검수 큐). 메타층 3: 지속 개선의 순환.

봇(답변 경로)과 완전히 분리된 오프라인 도구 — 검색을 느리게 하지도, 런타임
버그를 늘리지도 않는다. DB 없이 파일(review_queue.jsonl) 하나로 운영한다.

순환:  ① 발견(eval 실패 + audit 발견 + 수동 입력) → ② 큐 적재
       → ③ 사람 검수(resolve로 고정 방법 기록) → ④ 카드/골든/청크에 반영

명령:
  python3 feedback.py pull            # eval·audit 결과에서 실패/후보를 큐로 수집
  python3 feedback.py add "질문" "무엇이 틀렸는지"   # 수동 등록
  python3 feedback.py list            # 미해결 항목 보기
  python3 feedback.py show <id>       # 한 항목 상세
  python3 feedback.py resolve <id> "고정방법(카드/골든/청크 등)"
  python3 feedback.py stats           # 열림/해결 통계
"""
import datetime
import hashlib
import json
import os
import sys

QUEUE = "review_queue.jsonl"


def _now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def _mkid(source, key):
    return source[:2].upper() + hashlib.md5(key.encode("utf-8")).hexdigest()[:8]


def _load():
    if not os.path.exists(QUEUE):
        return []
    out = []
    for line in open(QUEUE, encoding="utf-8"):
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def _save(items):
    with open(QUEUE, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")


def _enqueue(new_items):
    items = _load()
    seen = {i["id"] for i in items}
    added = 0
    for it in new_items:
        if it["id"] in seen:            # 중복(이미 큐에 있음) 방지
            continue
        items.append(it)
        seen.add(it["id"])
        added += 1
    _save(items)
    return added


def _mk(source, key, question, issue, extra=None):
    return {"id": _mkid(source, key), "source": source, "status": "open",
            "created": _now(), "question": question, "issue": issue,
            "fix": "", "resolved": "", **(extra or {})}


def cmd_pull():
    """eval·audit 산출물에서 실패/후보를 읽어 큐에 넣는다."""
    new = []

    # 1) 통합 eval 실패 (eval_latest.json: {results:{id:bool}})
    if os.path.exists("eval_latest.json"):
        ev = json.load(open("eval_latest.json", encoding="utf-8"))
        qmap = {}
        try:
            import test_calc100 as calc
            qmap = {q[0]: (q[2], q[5]) for q in calc.Q}   # id -> (질문, 기대근거)
        except Exception:
            pass
        for qid, ok in ev.get("results", {}).items():
            if ok:
                continue
            ques, memo = qmap.get(qid, (qid, ""))
            new.append(_mk("eval", qid, ques,
                           f"eval 실패(기대: {memo})", {"ref": qid}))

    # 2) 문서 간/골든 검수 (crossdoc_review.json)
    if os.path.exists("crossdoc_review.json"):
        for f in json.load(open("crossdoc_review.json", encoding="utf-8")):
            key = f.get("concept", "") + f.get("source", "") + str(f.get("stated"))
            new.append(_mk("cross", key,
                           f"[{f.get('source')}] {f.get('concept')}",
                           f"{f.get('type')}: 문서값 {f.get('stated')} ↔ "
                           f"기준 {f.get('expected')}", {"doc": f.get("source")}))

    # 3) 문서 내부 수치 검수 (ingest_review.json)
    if os.path.exists("ingest_review.json"):
        for f in json.load(open("ingest_review.json", encoding="utf-8")):
            d = f.get("detail")
            dv = d if isinstance(d, str) else json.dumps(d, ensure_ascii=False)[:60]
            key = f.get("source", "") + f.get("check", "") + dv
            new.append(_mk("ingest", key,
                           f"[{f.get('source')}] {f.get('check')}",
                           f"수치 검수 후보: {dv}", {"doc": f.get("source")}))

    added = _enqueue(new)
    print(f"수집: 후보 {len(new)}개 중 신규 {added}개를 큐에 추가 "
          f"(중복 {len(new)-added}개 제외). → {QUEUE}")


def cmd_add(question, issue):
    added = _enqueue([_mk("manual", question + issue, question, issue)])
    print("등록됨." if added else "이미 큐에 있는 항목입니다.")


def cmd_list():
    items = [i for i in _load() if i["status"] == "open"]
    if not items:
        print("미해결 항목 없음.")
        return
    print(f"미해결 {len(items)}건:")
    by_src = {}
    for i in items:
        by_src.setdefault(i["source"], []).append(i)
    for src, its in sorted(by_src.items()):
        print(f"\n[{src}] {len(its)}건")
        for i in its:
            print(f"  {i['id']}  {i['question'][:40]}")
            print(f"          └ {i['issue'][:70]}")


def cmd_show(qid):
    for i in _load():
        if i["id"] == qid:
            for k, v in i.items():
                print(f"  {k}: {v}")
            return
    print("해당 id 없음:", qid)


def cmd_resolve(qid, fix):
    items = _load()
    for i in items:
        if i["id"] == qid:
            i["status"] = "resolved"
            i["fix"] = fix
            i["resolved"] = _now()
            _save(items)
            print(f"해결 처리: {qid} → {fix}")
            return
    print("해당 id 없음:", qid)


def cmd_stats():
    items = _load()
    o = sum(1 for i in items if i["status"] == "open")
    r = sum(1 for i in items if i["status"] == "resolved")
    print(f"큐 총 {len(items)}건  |  미해결 {o}  |  해결 {r}")
    if items:
        from collections import Counter
        c = Counter(i["source"] for i in items)
        print("  소스별:", dict(c))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1]
    a = sys.argv[2:]
    if cmd == "pull":
        cmd_pull()
    elif cmd == "add" and len(a) >= 2:
        cmd_add(a[0], a[1])
    elif cmd == "list":
        cmd_list()
    elif cmd == "show" and a:
        cmd_show(a[0])
    elif cmd == "resolve" and len(a) >= 2:
        cmd_resolve(a[0], a[1])
    elif cmd == "stats":
        cmd_stats()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
