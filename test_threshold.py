import os, json, requests
import numpy as np
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("CLOVA_API_KEY")
URL = "https://clovastudio.stream.ntruss.com/v1/api-tools/embedding/v2"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

with open("chunks.json", encoding="utf-8") as f:
    chunks = json.load(f)
with open("embeddings.json", encoding="utf-8") as f:
    embs = json.load(f)
idx_list = [e["idx"] for e in embs]
matrix = np.array([e["embedding"] for e in embs])
matrix = matrix / np.linalg.norm(matrix, axis=1, keepdims=True)

def top_score(question):
    res = requests.post(URL, headers=HEADERS, json={"text": question})
    q = np.array(res.json()["result"]["embedding"])
    q = q / np.linalg.norm(q)
    scores = matrix @ q
    best = np.argsort(scores)[::-1][:3]
    print(f"\n질문: {question}")
    for i in best:
        print(f"  {scores[i]:.3f} | {chunks[idx_list[i]]['source']}")

# 문서에 확실히 있는 질문들
top_score("IRP 세액공제 한도가 얼마인가요?")
top_score("개인연금저축 소득공제 한도")        # OCR 문서 확인 겸
# 경계 케이스 테스트
top_score("주택청약 당첨 확률 높이는 법")
top_score("국민연금 수령 나이")
top_score("퇴직금 중간정산 조건")
# 주제만 걸치는 질문
top_score("연금이 뭐야?")

# 문서에 없는 질문들 (임계값 기준용)
top_score("오늘 점심 뭐 먹을까?")
top_score("아이폰이랑 갤럭시 중에 뭐가 나아?")
top_score("BTS 콘서트 티켓 예매 방법")

