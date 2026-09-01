import os, json, time, requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("CLOVA_API_KEY")
URL = "https://clovastudio.stream.ntruss.com/v1/api-tools/embedding/v2"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

with open("chunks.json", encoding="utf-8") as f:
    chunks = json.load(f)
with open("embeddings.json", encoding="utf-8") as f:
    results = json.load(f)

done_idx = {d["idx"] for d in results}
missing = [i for i in range(len(chunks)) if i not in done_idx]
print(f"성공: {len(done_idx)} / 실패(재시도 대상): {len(missing)}")

for n, idx in enumerate(missing):
    ok = False
    for attempt in range(3):
        try:
            res = requests.post(URL, headers=HEADERS,
                                json={"text": chunks[idx]["text"][:2000]}, timeout=30)
            data = res.json() if res.text else None
            emb = (data or {}).get("result", {}).get("embedding") if isinstance(data, dict) else None
            if emb:
                results.append({"idx": idx, "embedding": emb})
                ok = True
                break
            else:
                print(f"[응답이상] idx {idx} (시도{attempt+1}) code={res.status_code} body={res.text[:200]}")
                time.sleep(3)
        except Exception as e:
            print(f"[예외] idx {idx} (시도{attempt+1}): {e}")
            time.sleep(3)
    if not ok:
        print(f"[최종실패] idx {idx}")
    if n % 50 == 0:
        print(f"재시도 진행: {n}/{len(missing)}")
        with open("embeddings.json", "w", encoding="utf-8") as f:
            json.dump(results, f)
    time.sleep(0.3)

with open("embeddings.json", "w", encoding="utf-8") as f:
    json.dump(results, f)
print(f"\n최종: {len(results)}/{len(chunks)} 임베딩 완료")
