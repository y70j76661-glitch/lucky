# test_topic.py — 특정 주제가 문서에 있는지 먼저 확인하고, 그다음 답변을 본다.
#   사용법: 서버 켠 상태에서
#     nohup python3 -u test_topic.py > topic.txt 2>&1 & P=$!; sleep 1; tail -f --pid=$P topic.txt
#
#   왜 코퍼스 확인이 먼저인가
#     문서에 있으면 '제대로 답했나'를, 없으면 '지어내지 않았나'를 봐야 한다.
#     기준이 정반대라, 답변만 읽으면 잘한 건지 못한 건지 판단할 수 없다.
import json, re, time, requests, collections

BASE = "http://localhost:8000/answer"

# 질문 세트 — 실행할 때 이름으로 고른다:  python3 test_topic.py order
QSETS = {
 "fintech": [
    ("미래에셋 디지털 혁신 플랫폼이란 무엇입니까?", ["디지털 혁신", "혁신 플랫폼", "플랫폼"]),
    ("미래에셋 핀테크 허브란 무엇입니까?", ["핀테크", "허브"]),
    ("핀테크 허브로 참여할 수 있는 자격이 따로 있습니까?", ["핀테크", "허브", "자격"]),
    ("핀테크 허브 제휴사로 참여하면 어떤 혜택을 받습니까?", ["핀테크", "제휴사", "혜택"]),
    ("핀테크 허브 제휴사가 되면 해야 할 의무가 있습니까?", ["제휴사", "의무"]),
    ("핀테크 허브 제휴사가 되려면 어떤 절차를 거쳐야 합니까?", ["제휴사", "절차"]),
    ("핀테크 허브 제휴사가 되기 위한 참여 비용이 있습니까?", ["제휴사", "참여 비용"]),
    ("핀테크 파트너십 프로그램이란 어떤 프로그램입니까?", ["파트너십", "프로그램"]),
    ("핀테크 파트너십 프로그램에 어떤 회사가 지원할 수 있습니까?", ["파트너십", "지원"]),
    ("핀테크 파트너십 프로그램에서 주어진 과제가 아닌 사업은 참여가 불가능합니까?",
     ["파트너십", "과제"]),
 ],
 # 주식 주문 — 연금 범위 밖. '수수료'·'체결'처럼 연금 문서에도 있는 단어가 섞여 있어
 # 임계값을 넘기 쉽다. 넘고도 지어내지 않는지를 본다.
 "order": [
    ("거래소 및 코스닥 신규상장 종목의 최초 가격 결정이 어떻게 되나요?", ["신규상장", "코스닥"]),
    ("미수동결계좌 적용되면 신용주문도 안되나요?", ["미수동결", "신용주문"]),
    ("오늘 체결되지 않은 국내주식 주문은 언제까지 유효한가요?", ["체결", "국내주식", "주문"]),
    ("미수발생 없이 현금범위내에서 주문하고 싶습니다. 어떻게 하나요?", ["미수", "현금범위"]),
    ("최근에 신규 상장된 종목을 찾고 싶은데 어디서 확인할 수 있나요?", ["신규 상장", "종목"]),
    ("신주인수권증서 매매는 어디에서 하나요?", ["신주인수권", "매매"]),
    ("주식 매매시 수수료가 어떻게 되나요?", ["매매", "수수료"]),
    ("주문유형 중 IOC, FOK 는 무슨 뜻 인가요?", ["IOC", "FOK"]),
    ("주문시 조건(시장가, 조건부지정가, 최유리 지정가, 최우선 지정가)은 무슨 뜻 인가요?",
     ["시장가", "조건부지정가", "최유리"]),
    ("체결이 되면 문자로 알려주는 서비스가 있나요?", ["체결", "문자"]),
 ],
 # 개인연금 — 범위 '안'이다. 앞의 두 세트와 검사 방향이 반대다.
 #   막으면 실패, 제대로 답해야 통과. 문서에 있는데 '자료 없음'이면 놓친 것이다.
 "pension": [
    ("개인연금계좌에 입금이 안되는데 어떻게 해야 하죠?", ["입금", "연금계좌"]),
    ("보험사에 있는 내 연금, 미래에셋증권으로 가져올 수 있나요?", ["이전", "연금저축"]),
    ("연금저축계좌에서 담보대출이 가능한가요?", ["담보", "연금저축"]),
    ("연금저축계좌에 상품에 투자를 하지 않은 예수금(현금)은 어떻게 운용되나요?",
     ["예수금", "연금저축"]),
    ("연금해지신청 후 전화를 받아야 된다고 하는데 지금 해외라 다른 인증 방법이 있나요?",
     ["해지", "인증"]),
    ("연금저축계좌에서 ETF를 매월 정기적으로 자동 매수를 설정할 수 있나요?",
     ["ETF", "자동", "연금저축"]),
    ("ISA 계좌가 만기되어 해지했는데 연금저축계좌로 이전이 가능한가요?", ["ISA", "이전"]),
    ("'세금우대 약정정보가 없습니다'라는 메시지가 나옵니다.", ["세금우대", "약정"]),
    ("주식계좌에 있는 일부 주식을 연금계좌로 옮기고 싶은데 가능한가요?", ["연금계좌", "주식"]),
    ("연금저축계좌가 여러 개 있는데 나중에 연금개시를 할 때 통합해서 개시할 수 있나요?",
     ["연금개시", "연금저축"]),
    ("연금저축계좌를 해지하면 세금이 많이 나오나요?", ["해지", "기타소득세"]),
    ("연금을 이전한 경우 타사 계좌에서 추가로 발생하는 분배금, 배당 등은 어떻게 처리되나요?",
     ["이전", "분배금"]),
 ],
}

import sys as _sys
_SET = _sys.argv[1] if len(_sys.argv) > 1 else "fintech"
if _SET not in QSETS:
    print(f"세트 이름이 잘못됐습니다: {_SET}  (가능: {', '.join(QSETS)})")
    raise SystemExit(2)
QUESTIONS = QSETS[_SET]

# 지어내지 않았다면 나와야 할 표현
# v2: 무관 차단은 '자료 없음'과 다른 문구로 거절한다. 그것도 정답으로 인정해야 한다.
#     (v1에서 8건이 오탐으로 걸렸다 — 실제로는 모두 올바르게 막고 있었다)
# v4: "제공된 자료(출처: X)에 따르면" 처럼 정상 인용에도 들어가서 오탐이 났다
NOINFO = ("확인할 수 없", "확인되지 않", "자료에 없", "제공된 자료에서", "포함되어 있지 않",
          "명시되어 있지 않", "찾을 수 없", "관련 없", "답변드릴 수 없", "안내해 드릴 수 없",
          "다루고 있지 않", "범위를 벗어", "상담사입니다", "상담을 위해",
          "근거로만 답변", "질문해 주시면")
# 지어냈다는 신호 (문서에 없는데 구체적으로 설명하면 위험)
INVENT = ("제휴사는", "다음과 같은 혜택", "신청 절차는", "참가비", "지원 자격은",
          "무료로 제공", "제공합니다", "운영합니다")


def corpus_hits(chunks, kw):
    n = sum(1 for c in chunks if kw in c["text"])
    return n


def main():
    _stop_if_concurrent()
    chunks = json.load(open("chunks.json", encoding="utf-8"))
    print(f"질문 세트: {_SET}  ({len(QUESTIONS)}문항) / 코퍼스 청크 {len(chunks):,}개\n")

    print("=" * 78)
    print("[1단계] 이 주제가 문서에 있는가")
    print("=" * 78)
    allkw = []
    for _q, kws in QUESTIONS:
        allkw += kws
    for kw in sorted(set(allkw)):
        n = corpus_hits(chunks, kw)
        print(f"  '{kw}' → {n}개 청크")
    print()

    print("=" * 78)
    print("[2단계] 실제 답변")
    print("=" * 78)
    flagged = []
    for i, (q, kws) in enumerate(QUESTIONS, 1):
        hits = {k: corpus_hits(chunks, k) for k in kws}
        in_corpus = all(v > 0 for v in hits.values())
        print(f"\n[{i:2d}/{len(QUESTIONS)}] {q}")
        print(f"   키워드 청크 수: {hits}  → 문서에 {'있음' if in_corpus else '없음/부분'}")
        try:
            d = requests.get(BASE, params={"question_id": f"T{i:02d}", "question": q},
                             timeout=300).json()
            ans, trace = d.get("answer", ""), d.get("think_trace", "")
        except Exception as e:
            ans, trace = f"[호출 실패: {e}]", ""
        # 무관으로 차단된 것도 올바른 처리다 (trace로 판정)
        blocked = "무관" in trace
        said_noinfo = blocked or any(k in ans for k in NOINFO)
        looks_invented = any(k in ans for k in INVENT)
        verdict = []
        if not in_corpus and not said_noinfo:
            verdict.append("문서에 없는 주제인데 '자료 없음'을 밝히지 않음")
        if not in_corpus and looks_invented and not said_noinfo:
            verdict.append("문서에 없는 내용을 구체적으로 설명함(지어냄 의심)")
        # v3: 범위 '안'인 질문은 검사 방향이 반대다 — 막거나 못 답하면 그게 실패다
        if in_corpus and blocked:
            verdict.append("문서에 있는 주제인데 '무관'으로 차단함")
        if in_corpus and said_noinfo and not blocked and len(ans) < 200:
            verdict.append("문서에 있는 주제인데 '자료 없음'으로 끝냄(놓쳤을 가능성)")
        if "[참고 문서]" not in ans and "무관" not in trace:
            verdict.append("출처 표기 누락")
        # 공통 — 어느 세트에서든 나오면 안 되는 것
        for k in ("[문서1]", "[문서2]", "[문서3]", "<br", "</p>"):
            if k in ans:
                verdict.append(f"내부/HTML 노출: {k}")
        if re.search(r"(?<!\[)문서\s*[1-9]\s*(?:에|의|에서|를|은|는)", ans):
            verdict.append("내부 순번 노출(문서N)")
        if re.search(r"\\[~*_\[\]()#+]", ans):
            verdict.append("마크다운 이스케이프 노출")
        if re.search(r"(?:간주|판단|해석|추정)\s*(?:되|하)[가-힣]*\s*때문", ans):
            verdict.append("지어낸 이유(추론 동사 + 때문)")
        if re.search(r"doc\d+\.(?:pdf|docx|xlsx)\s*(?:에서|에|를)\s*(?:직접\s*)?(?:확인|참고|참조)", ans):
            verdict.append("내부 파일명을 안내처럼 씀")
        if verdict:
            flagged.append((i, q, verdict))
            print("   ### 걸림:")
            for v in verdict:
                print(f"       - {v}")
        print(f"[trace] {trace}")
        print(f"[answer]\n{ans}")
        time.sleep(1.0)

    print("\n" + "=" * 78)
    print(f"===== 결과: {len(QUESTIONS)}건 중 걸림 {len(flagged)}건 =====")
    for i, q, v in flagged:
        print(f"  [{i}] {q[:44]}…")
        for x in v:
            print(f"      └ {x}")



def _stop_if_concurrent():
    """다른 테스트가 동시에 돌면 API 호출이 겹쳐 '허위 실패'가 난다.
    실측: 회귀와 주제시험을 같이 돌렸더니 표 생성 항목 5건이 무더기로 실패했다.
    사람이 기억해야 하는 규칙은 언젠가 어긋나므로 코드가 막는다."""
    import os, subprocess, sys as _s
    try:
        out = subprocess.run(["pgrep", "-af", "python3"],
                             capture_output=True, text=True, timeout=10).stdout
    except Exception:
        return
    me = str(os.getpid())
    others = []
    for line in out.splitlines():
        pid = line.split(" ", 1)[0]
        if pid == me:
            continue
        if any(k in line for k in ("test_regression", "hunt_matrix", "test_topic",
                                   "mock_exam", "test_hunt", "test_consistency")):
            others.append(line)
    if others:
        print("!! 다른 테스트가 이미 돌고 있습니다. 동시에 돌리면 API 호출이 겹쳐")
        print("!! 표 생성 같은 무거운 항목이 허위로 실패합니다. 중단합니다.")
        for l in others:
            print("   ", l)
        print("!! 끝난 뒤 다시 실행하세요:  pgrep -af 'test_|hunt_'")
        _s.exit(2)


if __name__ == "__main__":
    main()
