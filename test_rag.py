import os, json, requests
import numpy as np
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("CLOVA_API_KEY")
EMB_URL = "https://clovastudio.stream.ntruss.com/v1/api-tools/embedding/v2"
CHAT_URL = "https://clovastudio.stream.ntruss.com/v3/chat-completions/HCX-005"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

print("데이터 로딩 중...")
with open("chunks.json", encoding="utf-8") as f:
    chunks = json.load(f)
with open("embeddings.json", encoding="utf-8") as f:
    embs = json.load(f)
idx_list = [e["idx"] for e in embs]
matrix = np.array([e["embedding"] for e in embs])
matrix = matrix / np.linalg.norm(matrix, axis=1, keepdims=True)
print(f"로딩 완료: {len(idx_list)}개\n")

def search(question, top_k=3):
    res = requests.post(EMB_URL, headers=HEADERS, json={"text": question})
    q = np.array(res.json()["result"]["embedding"])
    q = q / np.linalg.norm(q)
    scores = matrix @ q
    top = np.argsort(scores)[::-1][:top_k]
    return [chunks[idx_list[i]] for i in top]

def generate_answer(question):
    found = search(question)
    context = "\n\n".join(f"[문서{i+1}] (출처: {c['source']})\n{c['text']}"
                          for i, c in enumerate(found))
    system = (
        "너는 미래에셋증권의 연금 전문 상담사야.\n"
        "- 아래 참고 문서의 내용을 근거로만 답변해.\n"
        "- 문서에 없는 내용은 '제공된 자료에서 확인할 수 없습니다'라고 답해.\n"
        "- 정확한 수치를 인용하고, 간결하고 이해하기 쉽게 설명해."
    )
    user = f"참고 문서:\n{context}\n\n질문: {question}"
    body = {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "maxTokens": 500,
        "temperature": 0.3,
    }
    res = requests.post(CHAT_URL, headers=HEADERS, json=body)
    data = res.json()
    answer = data.get("result", {}).get("message", {}).get("content")
    if not answer:
        print("응답 이상:", json.dumps(data, ensure_ascii=False)[:500])
        return
    print("=" * 60)
    print("질문:", question)
    print("-" * 60)
    print("검색된 근거:", ", ".join(c["source"] for c in found))
    print("-" * 60)
    print("답변:\n", answer)
    print("=" * 60, "\n")

generate_answer("연금저축 세액공제 한도가 얼마야?")
generate_answer("IRP 계좌를 중도 해지하면 불이익이 있나요?")
