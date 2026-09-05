# -*- coding: utf-8 -*-
"""patch_v1349.py — v1348(cccb88aa) main.py 에 v13.49 적용. (v1348 적용 후 실행)
  [안전성·신뢰성 계약 — 과제소개서 평가항목 '개인정보 노출·부적절한 입출력·프롬프트 공격'] ① 입력의 주민등록번호·전화·카드·계좌번호·이메일을
   검색·생성 전에 가리고(응답 question 필드는 원문 유지) 답변·근거·trace에도 미표시 + 안내문 ② 답변에 프롬프트 내부 카드 문구가 새면 그 줄 제거
   ③ 영문 인젝션(ignore previous instructions / reveal system prompt) 차단. answer()는 래퍼, 기존 본체는 _answer_core().
자동백업·자가검증. 이미 v13.49면 스킵. 검증 md5==5d6986d2a70a45224158427b9ff491d5"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='cccb88aa333f01d44d6e0708364d7a76'
EXPECT_AFTER='5d6986d2a70a45224158427b9ff491d5'
HUNKS=[["    r\"제약\\s*없는\\s*ai|규제\\s*없는\\s*(?:투자|ai|전문가)|개발자\\s*모드|탈옥|jailbreak|\"", "    r\"제약\\s*없는\\s*ai|규제\\s*없는\\s*(?:투자|ai|전문가)|개발자\\s*모드|탈옥|jailbreak|\"\n    r\"ignore\\s+(?:all\\s+)?(?:previous|prior|above|earlier|the)\\s+(?:instructions|rules|prompts?)|reveal\\s+(?:your\\s+)?(?:system\\s+)?(?:prompt|instructions)|\"   # v13.49: 영문 인젝션"], ["@app.get(\"/answer\")\ndef answer(question_id: str, question: str, _retried: bool = False):\n    t_start = time.time()          # v9.27: 응답 시간 예산 기준점", "# v13.49 [안전성 계약 — 개인정보·내부 지시문 유출 방지] (LLM 호출 없음)\n#   입력의 주민등록번호·전화번호·계좌/카드번호·이메일은 검색·생성 전에 가리고(원문은 응답의 question 필드에만 그대로),\n#   답변·근거·trace에 남은 개인정보도 가린다. 답변에 프롬프트 내부 카드 문구가 새면 그 줄을 지운다.\n_PII_PATS = [\n    (re.compile(r\"(?<!\\d)\\d{6}\\s*-\\s*[1-4]\\d{6}(?!\\d)\"), \"주민등록번호\"),\n    (re.compile(r\"(?<!\\d)01[016789]\\s*-?\\s*\\d{3,4}\\s*-?\\s*\\d{4}(?!\\d)\"), \"전화번호\"),\n    (re.compile(r\"(?<!\\d)(?:\\d{4}-){3}\\d{4}(?!\\d)\"), \"카드번호\"),\n    (re.compile(r\"(?<![\\d-])(?!\\d{4}-\\d{2}-\\d{2}(?![\\d-]))(?:\\d{2,6}-){2,3}\\d{2,7}(?![\\d-])\"), \"계좌번호\"),   # 날짜(2026-09-06) 제외\n    (re.compile(r\"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}\"), \"이메일\"),\n]\n_LEAK_PAT = re.compile(r\"너는 미래에셋증권의 연금|\\[상품 사실표|\\[위험등급 —|\\[세액공제율 판정|\\[연금소득세 연령별 세율|이 값만 쓰고 다른|그대로 인용하라|\\[근거 문서에 같은 질문\")\n\n\ndef mask_pii(text):\n    \"\"\"→ (가린 텍스트, 발견한 종류 목록)\"\"\"\n    kinds = []\n    for pat, nm in _PII_PATS:\n        if pat.search(text):\n            text = pat.sub(f\"[{nm} 비공개]\", text)\n            kinds.append(nm)\n    return text, kinds\n\n\n@app.get(\"/answer\")\ndef answer(question_id: str, question: str, _retried: bool = False):\n    q_in, _pii = mask_pii(question or \"\")\n    out = _answer_core(question_id, q_in, _retried)\n    out[\"question\"] = question                                    # 평가 질의 원문은 그대로 돌려준다\n    ans_ = out.get(\"answer\", \"\") or \"\"\n    ans_ = \"\\n\".join(l for l in ans_.split(\"\\n\") if not _LEAK_PAT.search(l))\n    ans_, _pk = mask_pii(ans_)\n    if _pii:\n        ans_ = (\"※ 입력하신 개인정보(\" + \"·\".join(dict.fromkeys(_pii)) + \")는 답변 생성에 사용하지 않았으며 답변에도 표시하지 않습니다. \"\n                \"상담 시 주민등록번호·계좌번호 등 개인정보는 입력하지 마세요.\\n\\n\" + ans_.lstrip())\n        out[\"think_trace\"] = \"0.8) 개인정보(\" + \"·\".join(dict.fromkeys(_pii)) + \") 감지 → 가린 뒤 검색·생성, 답변에 미표시 \" + (out.get(\"think_trace\", \"\") or \"\")\n    out[\"answer\"] = ans_\n    out[\"think_trace\"] = mask_pii(out.get(\"think_trace\", \"\") or \"\")[0]\n    out[\"retrieved_context\"] = mask_pii(out.get(\"retrieved_context\", \"\") or \"\")[0]\n    return out\n\n\ndef _answer_core(question_id: str, question: str, _retried: bool = False):\n    t_start = time.time()          # v9.27: 응답 시간 예산 기준점"], ["            out = answer(question_id=question_id, question=question, _retried=True)", "            out = _answer_core(question_id=question_id, question=question, _retried=True)"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "v13.49 [안전성 계약" in src: print("[스킵] 이미 v13.49 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[경고] 적용전 md5가 예상 v1348과 다름. 훅 매칭되면 계속.")
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v1348_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
