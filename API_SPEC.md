# API 명세서

## 1. End-point

| 항목 | 값 |
|---|---|
| Base URL | `http://<서버 IP>:8000` |
| End-point | `GET /answer` |
| 프로토콜 | HTTP/1.1 |
| 인코딩 | UTF-8 |
| 인증 | 없음 (Public 망 통신) |

> 제출 시 `<서버 IP>` 를 실제 배포 주소로 기재합니다.
> 예: `http://223.130.152.136:8000/answer`

---

## 2. 요청 (Request)

### 2-1. 파라미터 (Query String)

| 이름 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `question_id` | string | O | 질의 식별자. 응답에 그대로 반환됩니다. |
| `question` | string | O | 사용자 질의 원문. URL 인코딩 필요. |

### 2-2. 예시

**cURL**

```bash
curl -G "http://<서버 IP>:8000/answer" \
  --data-urlencode "question_id=Q-001" \
  --data-urlencode "question=연금저축이랑 IRP에 넣으면 세액공제 얼마까지 되나요? 다 합쳐서요."
```

**Python**

```python
import requests

resp = requests.get(
    "http://<서버 IP>:8000/answer",
    params={
        "question_id": "Q-001",
        "question": "연금저축이랑 IRP에 넣으면 세액공제 얼마까지 되나요? 다 합쳐서요.",
    },
    timeout=120,
)
result = resp.json()
```

---

## 3. 응답 (Response)

### 3-1. 스키마

```json
{
  "question_id": "string",
  "question": "string",
  "retrieved_context": "string",
  "think_trace": "string",
  "answer": "string"
}
```

| 필드 | 타입 | 설명 |
|---|---|---|
| `question_id` | string | 요청받은 식별자 그대로 반환 |
| `question` | string | 요청받은 질의 원문 |
| `retrieved_context` | string | 답변 생성에 참고한 검색 문서. `[문서N] (출처: 파일명)` + 원문 형식으로 연결. 무관 질의는 빈 문자열 |
| `think_trace` | string | 사고·추론·도구 사용 과정 (검색 방식, 유사도, 유형 분류, 유형별 행동, 검증 결과, 출처 표기까지 단계별 기록) |
| `answer` | string | 최종 생성 답변. 말미에 `[참고 문서] 파일명…` 이 부착됨 |

### 3-2. 예시

```json
{
  "question_id": "Q-001",
  "question": "연금저축이랑 IRP에 넣으면 세액공제 얼마까지 되나요? 다 합쳐서요.",
  "retrieved_context": "[문서1] (출처: doc41.docx)\n연금계좌 세액공제 한도는…",
  "think_trace": "1) 임베딩+키워드(BM25) 하이브리드 검색으로 12417개 청크 비교 2) 임계값 0.45 통과 (최고 유사도 0.813) 3) LLM 유형 분류: '세제' + 복합 질문 감지(문서 5개, 누락 금지) 4) 상위 5개 문서 검색 (유사도: 0.813, 0.805, 0.700, …) 5) '세제' 전용 프롬프트로 HCX-005 답변 생성 6) 근거 검증: 이상 없음 7) 참고 문서 출처 표기",
  "answer": "연금저축과 IRP 계좌에 합쳐서 납입할 경우, 세액공제 한도는 연 900만원입니다. …\n\n[참고 문서] doc41.docx, doc38.docx"
}
```

---

## 4. 동작 특성

| 항목 | 내용 |
|---|---|
| 응답 시간 | 일반 질의 약 10~25초 (검색 1회 + LLM 3~4회 호출) |
| 무관 질의 | 임계값 미달 시 LLM 호출 없이 즉시 응답 (약 1초) |
| 재시도 | CLOVA API 실패 시 최대 5회 자동 재시도. 속도 제한(429) 시 6→12→18→24초 대기 |
| 오류 처리 | 예외 발생 시에도 HTTP 200과 동일 스키마 반환. `think_trace` 에 오류 내용, `answer` 에 안내 문구 |
| 대화 맥락 | 지시어("그럼", "그거") 또는 직전 되묻기에 대한 응답으로 판단될 때만 직전 대화를 반영 (독립 질의 간 간섭 없음) |

### 오류 응답 예시

```json
{
  "question_id": "Q-001",
  "question": "…",
  "retrieved_context": "",
  "think_trace": "오류 발생: <원인>",
  "answer": "일시적인 오류가 발생했습니다."
}
```

---

## 5. 운영

- 서버 기동 시 BM25 인덱스 구축에 약 60~90초 소요 후 요청 처리 가능
- 5분 주기 헬스체크(`watchdog.sh`)로 프로세스 이상 종료 시 자동 재기동
