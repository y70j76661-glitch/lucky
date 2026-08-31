import os, json, requests
import numpy as np
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("CLOVA_API_KEY")
EMB_URL = "https://clovastudio.stream.ntruss.com/v1/api-tools/embedding/v2"
CHAT_URL = "https://clovastudio.stream.ntruss.com/v3/chat-completions/HCX-005"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# ---- 서버 시작 시 딱 1번 로딩 (질문마다 다시 안 읽음) ----
print("검색 인덱스 로딩 중...")
with open("chunks.json", encoding="utf-8") as f:
    chunks = json.load(f)
with open("embeddings.json", encoding="utf-8") as f:
    embs = json.load(f)
idx_list = [e["idx"] for e in embs]
matrix = np.array([e["embedding"] for e in embs])
matrix = matrix / np.linalg.norm(matrix, axis=1, keepdims=True)
print(f"로딩 완료: 청크 {len(idx_list)}개")

app = FastAPI()

# ============================================================
# 라우팅 설정
# ============================================================

# 무관 '즉시 차단' 임계값 (2026-08-18 조정)
# 1차 실험(test_threshold.py): 관련 0.642~0.706 vs 무관 0.427~0.507 → 0.55로 시작
# 추가 테스트에서 겹침 발견: "TDF가 어떤 상품이야?"(관련) 0.469 < "BTS 티켓"(무관) 0.507
# → 임계값만으로는 완벽 분리 불가. 0.45 미만만 '확실한 무관'으로 즉시 차단하고,
#   그 이상의 애매한 구간은 LLM 분류기가 무관 여부까지 판단 (2차 방어)
THRESHOLD = 0.45

LABELS = ["제도", "세제", "상품설명", "추천", "무관"]

CLASSIFY_SYSTEM = (
    "너는 연금 상담 챗봇의 질문 유형 분류기야. 사용자의 질문을 아래 다섯 유형 중 "
    "하나로 분류해서 유형 이름만 정확히 출력해.\n\n"
    "- 제도: 연금·퇴직금 제도의 규정, 가입 조건, 수령 나이, 절차에 대한 질문 "
    "(예: 국민연금 수령 나이, 퇴직금 중간정산 조건, IRP 가입 자격)\n"
    "- 세제: 세금, 세액공제, 과세, 세율에 대한 질문 "
    "(예: 연금저축 세액공제 한도, 연금소득세율, 퇴직소득세 계산)\n"
    "- 상품설명: 특정 금융상품의 내용·구조·수수료·수익률·위험에 대한 질문 "
    "(예: 이 펀드 수수료 얼마야, TDF가 뭐야, 이 상품 위험등급은?)\n"
    "- 추천: 사용자에게 맞는 상품이나 전략을 골라달라는 질문 "
    "(예: 나한테 맞는 연금 상품 추천해줘, IRP랑 연금저축 중 뭐가 나아?)\n"
    "- 무관: 연금·퇴직금·금융과 관련 없는 질문 "
    "(예: 오늘 점심 뭐 먹을까, 콘서트 티켓 예매 방법)\n\n"
    "다른 말은 하지 말고 유형 이름 하나만 출력해."
)

# 유형별 전략: 검색 개수(top_k) + 시스템 프롬프트
BASE_RULES = (
    "- 아래 참고 문서의 내용을 근거로만 답변해.\n"
    "- 문서에 없는 내용은 '제공된 자료에서 확인할 수 없습니다'라고 답해.\n"
    "- 정확한 수치를 인용하고, 간결하고 이해하기 쉽게 설명해."
)

TYPE_CONFIG = {
    "제도": {
        "top_k": 3,
        "system": (
            "너는 미래에셋증권의 연금 전문 상담사야. 지금 질문은 연금·퇴직금 '제도'에 대한 질문이야.\n"
            + BASE_RULES + "\n"
            "- 적용 조건(나이, 근속기간, 기한, 자격 요건)을 빠뜨리지 말고 명확히 설명해.\n"
            "- 조건에 따라 결과가 달라지면 경우를 나눠서 설명해."
        ),
    },
    "세제": {
        "top_k": 3,
        "system": (
            "너는 미래에셋증권의 연금 전문 상담사야. 지금 질문은 연금 관련 '세금·세제'에 대한 질문이야.\n"
            + BASE_RULES + "\n"
            "- 세율·한도·공제액 같은 수치는 문서의 숫자를 정확히 인용해.\n"
            "- 소득 구간이나 납입액 등 조건에 따라 달라지면 구간별로 나눠 설명해.\n"
            "- 가능하면 간단한 계산 예시를 들어서 설명해."
        ),
    },
    "상품설명": {
        "top_k": 3,
        "system": (
            "너는 미래에셋증권의 연금 전문 상담사야. 지금 질문은 특정 '금융상품에 대한 설명' 질문이야.\n"
            + BASE_RULES + "\n"
            "- 상품의 구조, 수수료, 위험등급, 수익 구조를 사실 그대로 설명해.\n"
            "- 장점만 말하지 말고 위험과 유의사항도 함께 설명해.\n"
            "- 여러 상품이 언급되면 항목별로 나눠서 비교해."
        ),
    },
    "추천": {
        "top_k": 5,  # 추천은 여러 상품을 비교해야 하므로 더 많이 검색
        "system": (
            "너는 미래에셋증권의 연금 전문 상담사야. 지금 질문은 상품·전략 '추천' 질문이야.\n"
            + BASE_RULES + "\n"
            "- 특정 상품을 단정적으로 추천하지 마. 대신 문서 근거로 선택 기준"
            "(연령, 투자성향, 세제 혜택, 수수료 등)을 설명해.\n"
            "- 나이, 투자성향, 납입 여력 같은 정보가 있으면 더 정확한 안내가 가능하다는 점을 알려줘.\n"
            "- 투자 판단의 최종 책임은 투자자 본인에게 있다는 점을 자연스럽게 언급해."
        ),
    },
    # 분류 실패 시 폴백: 기존의 범용 프롬프트
    "일반": {
        "top_k": 3,
        "system": (
            "너는 미래에셋증권의 연금 전문 상담사야.\n" + BASE_RULES
        ),
    },
}

# 무관 질문은 LLM 호출 없이 고정 응답 (비용·지연 절약)
OFF_TOPIC_ANSWER = (
    "죄송하지만 저는 미래에셋증권의 연금·퇴직연금 전문 상담사입니다. "
    "연금 제도, 퇴직금, 세제 혜택, 연금 상품에 대해 질문해 주시면 자세히 안내해 드릴게요."
)


def chat(system, user_msg, max_tokens=500, temperature=0.3):
    """HCX-005 호출 공통 함수"""
    body = {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ],
        "maxTokens": max_tokens,
        "temperature": temperature,
    }
    res = requests.post(CHAT_URL, headers=HEADERS, json=body, timeout=60)
    return res.json().get("result", {}).get("message", {}).get("content", "")


def classify(question):
    """질문을 5개 유형 중 하나로 분류. 실패하면 '일반'(폴백)."""
    try:
        text = chat(CLASSIFY_SYSTEM, question, max_tokens=10, temperature=0.1)
        for label in LABELS:
            if label in text:
                return label
    except Exception:
        pass
    return "일반"


def search(question, top_k=5):
    res = requests.post(EMB_URL, headers=HEADERS, json={"text": question}, timeout=30)
    q = np.array(res.json()["result"]["embedding"])
    q = q / np.linalg.norm(q)
    scores = matrix @ q
    top = np.argsort(scores)[::-1][:top_k]
    return [chunks[idx_list[i]] for i in top], [float(scores[i]) for i in top]


@app.get("/answer")
def answer(question_id: str, question: str):
    try:
        # [1단계] 검색: 최대 5개를 미리 검색해두고, 유형에 따라 사용 개수 결정
        #         (임베딩 호출은 여기서 1번만 발생)
        found, scores = search(question, top_k=5)
        top_score = scores[0]

        # [2단계] 임계값 필터: 무관 질문은 LLM 호출 없이 즉시 응답
        if top_score < THRESHOLD:
            trace = (f"1) 질문 임베딩 후 {len(idx_list)}개 청크와 유사도 비교 "
                     f"(최고 유사도 {top_score:.3f}) "
                     f"2) 임계값 {THRESHOLD} 미달 → '무관' 판정 "
                     f"3) 검색·답변 생성 생략 (비용 절약)")
            return {
                "question_id": question_id,
                "question": question,
                "retrieved_context": "",
                "think_trace": trace,
                "answer": OFF_TOPIC_ANSWER,
            }

        # [3단계] LLM 유형 분류 (제도/세제/상품설명/추천, 안전망으로 무관도 포함)
        qtype = classify(question)
        if qtype == "무관":  # 유사도는 높지만 LLM이 무관으로 판단한 경우 (2차 방어)
            trace = (f"1) 질문 임베딩 후 {len(idx_list)}개 청크와 유사도 비교 "
                     f"(최고 유사도 {top_score:.3f}) "
                     f"2) 임계값 통과했으나 LLM 분류 결과 '무관' → 답변 생성 생략")
            return {
                "question_id": question_id,
                "question": question,
                "retrieved_context": "",
                "think_trace": trace,
                "answer": OFF_TOPIC_ANSWER,
            }

        # [4단계] 유형별 전략 적용: 검색 개수 + 전용 프롬프트
        config = TYPE_CONFIG[qtype]
        k = config["top_k"]
        used = found[:k]
        context = "\n\n".join(f"[문서{i+1}] (출처: {c['source']})\n{c['text']}"
                              for i, c in enumerate(used))
        user_msg = f"참고 문서:\n{context}\n\n질문: {question}"

        ans = chat(config["system"], user_msg, max_tokens=500, temperature=0.3)
        if not ans:
            ans = "답변 생성에 실패했습니다."

        trace = (f"1) 질문 임베딩 후 {len(idx_list)}개 청크와 유사도 비교 "
                 f"2) 임계값 {THRESHOLD} 통과 (최고 유사도 {top_score:.3f}) "
                 f"3) LLM 유형 분류: '{qtype}' "
                 f"4) 상위 {k}개 문서 검색 (유사도: {', '.join(f'{s:.3f}' for s in scores[:k])}) "
                 f"5) '{qtype}' 전용 프롬프트로 HCX-005 답변 생성")
        return {
            "question_id": question_id,
            "question": question,
            "retrieved_context": context,
            "think_trace": trace,
            "answer": ans,
        }
    except Exception as e:
        return {
            "question_id": question_id,
            "question": question,
            "retrieved_context": "",
            "think_trace": f"오류 발생: {e}",
            "answer": "일시적인 오류가 발생했습니다.",
        }
