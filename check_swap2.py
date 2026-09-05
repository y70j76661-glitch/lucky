# -*- coding: utf-8 -*-
# check_swap2.py — 재추출한 10개 문서가 검색에 실제로 실렸는지 표적 질문으로 확인.
#   각 질문은 새 전사본에만 있는 사실을 겨냥한다. 키워드가 빠지면 [확인 필요]로 표시.
#   (판정은 참고용 — 답 전문을 보고 사람이 최종 확인)
import requests, time

BASE = "http://localhost:8000/answer"

PROBES = [
    ("doc2",  "연금수령한도 계산 공식이 어떻게 되나요?",
     ["120"]),
    ("doc3",  "연금저축계좌에 있는 펀드를 담보로 대출을 받을 수 있나요? 한도는 얼마나 되나요?",
     ["60"]),
    ("doc5",  "연금 받을 때 나이에 따라서 연금소득세율이 어떻게 달라지나요?",
     ["5.5", "3.3"]),
    ("doc7",  "퇴직연금 계좌에서 장외채권은 몇 시까지 매수할 수 있나요?",
     ["15"]),
    ("doc8",  "연금저축계좌 상장인프라펀드 매매등록은 해지할 수 있나요?",
     ["불가"]),
    ("doc24", "퇴직연금 유상청약은 청약 마감일에 몇 시까지 신청할 수 있나요?",
     ["15"]),
    ("doc30", "퇴직연금 예금이 만기되면 예전처럼 자동으로 재예치되나요?",
     ["재예치"]),
    ("doc31", "디폴트옵션은 상품 만기 후 몇 주 지나면 적용되나요?",
     ["6주"]),
    ("doc32", "디폴트옵션을 지정한 후에 취소할 수 있나요?",
     ["불가"]),
    ("doc37", "연금 인출기에는 자산을 어떻게 운용하는 게 좋은가요?",
     []),
]

ok = warn = 0
for i, (doc, q, must) in enumerate(PROBES, 1):
    try:
        r = requests.get(BASE, params={"question_id": f"S{i:02d}", "question": q},
                         timeout=90)
        ans = r.json().get("answer", "")
    except Exception as e:
        print(f"[{doc}] 서버 오류: {e}")
        warn += 1
        continue
    missing = [m for m in must if m not in ans]
    tag = "정상" if not missing else f"확인 필요(누락: {', '.join(missing)})"
    if missing: warn += 1
    else: ok += 1
    print(f"\n===== [{doc}] {tag} =====")
    print(f"Q: {q}")
    print(ans[:700])
    time.sleep(1.0)

print(f"\n표적 {len(PROBES)}건: 정상 {ok} / 확인 필요 {warn}")
