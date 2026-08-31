FROM python:3.12-slim

WORKDIR /app

# 의존성 먼저 설치 (레이어 캐시 활용)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 소스 및 인덱스 데이터
#  - chunks.json      : 문서 청크 (build_chunks.py 산출물)
#  - embeddings.json  : 청크 임베딩 (build_embeddings.py 산출물)
COPY main.py .
COPY chunks.json embeddings.json ./

# CLOVA Studio API 키는 이미지에 포함하지 않고 실행 시 주입
#   docker run -e CLOVA_API_KEY=... -p 8000:8000 pension-rag
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
