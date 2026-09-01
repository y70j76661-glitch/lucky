import os, json, requests
import numpy as np
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("CLOVA_API_KEY")
URL = "https://clovastudio.stream.ntruss.com/v1/api-tools/embedding/v2"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

print("데이터 로딩 중...")
with open("chunks.json", encoding="utf-8") as f:
    chunks = json.load(f)
with open("embeddings.json", encoding="utf-8") as f:
    embs = json.load(f)

idx_list = [e["idx"] for e in embs]
matrix = np.array([e["embedding"] for e in embs])          # (12217, 1024) 행렬
matrix = matrix / np.linalg.norm(matrix, axis=1, keepdims=True)
print(f"로딩 완료: 청크 {len(idx_list)}개\n")

def search(question, top_k=3):
    res = requests.post(URL, headers=HEADERS, json={"text": question})
    q = np.array(res.json()["result"]["embedding"])
    q = q / np.linalg.norm(q)
    scores = matrix @ q                     # 모든 청크와 유사도 계산
    top = np.argsort(scores)[::-1][:top_k]  # 상위 top_k개
    for rank, i in enumerate(top, 1):
        ch = chunks[idx_list[i]]
        print(f"[{rank}위] 유사도 {scores[i]:.3f} | 출처: {ch['source']} ({ch.get('fund_code','연금문서')})")
        print(ch["text"][:200])
        print("-" * 60)

# 테스트 질문들
search("연금저축 세액공제 한도가 얼마야?")
print("\n" + "=" * 60 + "\n")
search("중도 해지하면 어떻게 되나요?")
