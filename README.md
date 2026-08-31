# 미래에셋증권 연금 상담 RAG 챗봇

제10회 2026 미래에셋증권 AI Festival 예선 제출작.
제공된 연금·퇴직연금 문서(12,417 청크)를 근거로 답변하는 **질문 유형 라우팅 기반 RAG 상담 시스템**입니다.

---

## 1. 핵심 구조

일반적인 RAG(검색 → 생성)와 달리, **질문 유형을 먼저 판별해 유형마다 다른 검색·프롬프트·행동을 적용**합니다.

```
질문
 └─[1] 하이브리드 검색  임베딩(의미) 0.6 + BM25(정확 용어) 0.4
 └─[2] 임계값 필터      최고 유사도 < 0.45 → 무관 즉시 차단 (LLM 호출 없이 응답)
 └─[3] LLM 유형 분류    제도 / 세제 / 상품설명 / 추천 / 무관   ← 무관 2차 방어
 └─[4] 유형별 행동
        ├ 세제      → 질문에서 소득·납입액 추출 → 파이썬 세액공제 계산기 실행
        ├ 추천      → 나이·성향 없으면 되묻기(역질문) / 있으면 맞춤 + 상품 검색 보강
        │              성향 표현이 모순되면(안정+공격) 실제 배분 기준으로 교정
        ├ 상품설명  → 비교 질문 감지 시 마크다운 비교표 생성
        └ 복합 질문 → 여러 요구사항 감지 시 문서 확대 + 누락 금지 지시
 └─[5] 답변 생성        유형 전용 시스템 프롬프트 (HCX-005)
 └─[6] 근거 검증 레이어 판정(JSON) → 불일치 시에만 교정
        · 문서에 없는 수치·상품명 차단  · 계산 방향/단위 검산  · 구기준(400만원) 차단
 └─[7] 출처 자동 표기   답변 말미에 [참고 문서] 파일명 (코드가 부착, 누락 불가)
```

모든 단계는 응답의 `think_trace` 필드에 기록되어 추론 과정을 외부에서 검증할 수 있습니다.

---

## 2. 환경 구성

### 2-1. 요구 사항
- Python 3.12
- CLOVA Studio API Key (임베딩 v2 / HCX-005)

### 2-2. 설치

```bash
git clone <repository-url>
cd <repository>

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2-3. 환경 변수

프로젝트 루트에 `.env` 파일을 생성합니다. (저장소에 포함되지 않음)

```
CLOVA_API_KEY=<발급받은 키>
```

### 2-4. 인덱스 생성

대용량 산출물(`chunks.json`, `embeddings.json`)은 저장소에 포함되지 않으며 아래로 재생성합니다.

```bash
python3 ocr_scan_docs.py      # 문서 텍스트 추출 (스캔 PDF는 OCR)
python3 build_chunks.py       # 청크 분할       → chunks.json
python3 build_embeddings.py   # 임베딩 생성     → embeddings.json
```

### 2-5. 실행

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

기동 시 BM25 키워드 인덱스를 구축하므로 **최초 준비까지 약 60~90초**가 소요됩니다.
로그에 `Application startup complete` 가 출력되면 요청을 받을 수 있습니다.

무중단 운영(백그라운드 실행 + 자동 복구):

```bash
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &

# 5분 주기 헬스체크 및 자동 재시작
crontab -e   # */5 * * * * /bin/bash /root/app/watchdog.sh
```

### 2-6. Docker 실행

```bash
docker build -t pension-rag .
docker run -d -p 8000:8000 -e CLOVA_API_KEY=<발급받은 키> pension-rag
```

---

## 3. API

`GET /answer` — 상세 명세는 [API_SPEC.md](./API_SPEC.md) 참조.

```bash
curl -G "http://<host>:8000/answer" \
  --data-urlencode "question_id=Q-001" \
  --data-urlencode "question=연금저축이랑 IRP에 넣으면 세액공제 얼마까지 되나요?"
```

---

## 4. 검증

| 검증 항목 | 스크립트 | 결과 |
|---|---|---|
| 무관 판정 임계값 실험 | `test_threshold.py` | 임계값 0.45 도출 |
| 라우팅 분류 정확도 (25문항) | `test_routing.py` | **25/25 (100%)** |
| 문서 FAQ 전수 시험 (237문항) | `mock_exam_full.py` | 호출 오류 0 / 검색 실패 0 |
| 공식 참고 질의 (5문항) | `test_official.py` | 전 문항 통과 |
| 답변 일관성 (5문항 × 3회) | `test_consistency.py` | 유형 일관성 5/5 |
| 문서 전체 키워드 검색 | `search_docs.py` | 근거 역추적용 도구 |

```bash
python3 test_routing.py        # 서버 기동 상태에서 실행
```

---

## 5. 파일 구성

```
main.py                 API 서버 본체 (라우팅·검증·출처 표기 전 과정)
ocr_scan_docs.py        문서 텍스트 추출 / OCR
build_chunks.py         청크 분할
build_embeddings.py     임베딩 생성
watchdog.sh             5분 주기 헬스체크 및 자동 재시작
test_*.py, mock_*.py    검증 스크립트
requirements.txt        의존성
Dockerfile              컨테이너 정의
```

---

## 6. 설계 원칙

1. **문서 기반 폐쇄형** — 외부 인터넷을 조회하지 않고 제공 데이터만 근거로 사용합니다.
   문서 내 개정 전후 수치가 충돌할 경우 적용 시점이 명시된 최신 기준을 우선합니다.
2. **모르는 것은 모른다고 답한다** — 문서에서 확인되지 않는 수치·상품명은 생성하지 않고
   한계를 고지하거나, 판단에 필요한 정보를 역질문합니다.
3. **모든 답변은 추적 가능하다** — 출처 파일명을 코드가 부착하며, `retrieved_context` 로
   답변의 근거 원문을 확인할 수 있습니다.
