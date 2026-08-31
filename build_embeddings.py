import os, json, time, requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("CLOVA_API_KEY")
URL = "https://clovastudio.stream.ntruss.com/v1/api-tools/embedding/v2"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

with open("chunks.json", encoding="utf-8") as f:
    chunks = json.load(f)

# 이미 한 것 불러오기 (중단됐다 재시작해도 이어서 진행)
done = {}
if os.path.exists("embeddings.json"):
    with open("embeddings.json", encoding="utf-8") as f:
        done = {d["idx"]: d for d in json.load(f)}
    print(f"기존 진행분 {len(done)}개 발견, 이어서 시작")

results = list(done.values())

for idx, ch in enumerate(chunks):
    if idx in done:
        continue
    try:
        res = requests.post(URL, headers=HEADERS,
                            json={"text": ch["text"][:2000]}, timeout=30)
        if res.status_code == 429:          # 속도 제한 걸리면 잠깐 쉬고 재시도
            time.sleep(5)
            res = requests.post(URL, headers=HEADERS,
                                json={"text": ch["text"][:2000]}, timeout=30)
        emb = res.json().get("result", {}).get("embedding")
        if emb:
            results.append({"idx": idx, "embedding": emb})
        else:
            print(f"[실패] idx {idx}: {res.json()}")
    except Exception as e:
        print(f"[에러] idx {idx}: {e}")
    if idx % 100 == 0:
        print(f"진행: {idx}/{len(chunks)}")
        with open("embeddings.json", "w", encoding="utf-8") as f:
            json.dump(results, f)          # 100개마다 중간 저장
    time.sleep(0.1)                         # 속도 제한 예방

with open("embeddings.json", "w", encoding="utf-8") as f:
    json.dump(results, f)
print(f"\n완료! 총 {len(results)}개 임베딩 저장 → embeddings.json")
