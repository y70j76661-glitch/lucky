import os, requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("CLOVA_API_KEY")

url = "https://clovastudio.stream.ntruss.com/v1/api-tools/embedding/v2"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}
res = requests.post(url, headers=headers, json={"text": "연금저축 세액공제 한도"})
print("상태코드:", res.status_code)
data = res.json()
print("응답 키:", list(data.keys()))
emb = data.get("result", {}).get("embedding")
if emb:
    print(f"임베딩 성공! 벡터 길이: {len(emb)}")
    print("앞 5개 숫자:", emb[:5])
else:
    print("전체 응답:", data)
