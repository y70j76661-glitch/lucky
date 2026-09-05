import json, sys, importlib.util
ids = {"P0160","P0232","P0295","P0574","P0713","E0009","E0046","E0055","E0128","E0190","E0199"}
spec = importlib.util.spec_from_file_location("ap", "/root/app/auto_probe.py")
ap = importlib.util.module_from_spec(spec); sys.argv = ["r"]; spec.loader.exec_module(ap)
qs = {}
for ln in open("/root/app/probe.jsonl", encoding="utf-8"):
    d = json.loads(ln)
    if d["id"] in ids:
        qs[d["id"]] = d
for qid, d in sorted(qs.items()):
    ans, tr, ctx = ap.ask("re-" + qid, d["q"])
    h, so = ap.check({"kind": d.get("kind", "A"), "q": d["q"]}, ans, tr, ctx)
    print(f"[{qid}] {'깨끗함' if not (h or so) else ''} {h or ''} {so or ''}")
