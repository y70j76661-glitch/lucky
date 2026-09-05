# -*- coding: utf-8 -*-
# diag_new.py — 표적 사냥(probe_new)에서 걸린 질문들의 '검색 단계'를 해부한다.
#   각 질문에 대해 search()가 실제로 가져온 5개 청크를 열어,
#   ① 기대 문서가 잡혔는지 ② 정답 사실(핵심 문자열)이 그 안에 있는지 판정.
#   → "청크 미스"(검색 문제) vs "찾고도 무시"(생성 문제)를 가른다.
#   비용: 질문당 임베딩 1회 (~1원 미만). 답변 생성은 하지 않는다.
import json, re, sys
sys.path.insert(0, "/root/app")
import main

# (질문, 기대 문서, 정답이 들었는지 확인할 핵심 문자열)
CASES = [
    ("구개인연금은 몇 살부터, 얼마나 가입해야 연금으로 받을 수 있나요?", "doc2.pdf", "10년"),
    ("연금저축계좌에 있는 펀드를 담보로 대출받으면 평가금액의 몇 퍼센트까지 가능한가요?", "doc3.pdf", "60"),
    ("연금계좌 증권담보융자의 대출 기간은 얼마나 되나요?", "doc3.pdf", "365"),
    ("6개월 이상 요양이 필요할 때 의료비는 얼마까지 인출할 수 있나요?", "doc5.pdf", "요양"),
    ("M-STOCK으로 산 장외채권을 앱에서 팔 수도 있나요?", "doc7.pdf", "매도"),
    ("퇴직연금에서 회사채에 투자할 때 한도가 있나요?", "doc7.pdf", "40%"),
    ("상장인프라펀드 매매등록 진행중인데 전송 버튼이 활성화되지 않습니다.", "doc8.pdf", "전송 버튼"),
    ("유상청약 시 예약청약 및 입금청약, 초과청약이 가능한가요?", "doc8.pdf", "초과청약"),
    ("신주인수권증서 매수 및 공매도 가능한가요?", "doc8.pdf", "신주인수권"),
    ("적립식 주문단가와 주문수량은 어떻게 설정되나요?", "doc9.pdf", "주문"),
    ("IRP 계좌를 다른 증권사로 옮길 때 보유 상품 그대로 이전되나요?", "doc22.pdf", "실물"),
    ("퇴직연금 계좌로 유상청약할 때 초과청약도 가능한가요?", "doc24.pdf", "초과청약"),
    ("은행용 공동인증서가 있는데, 공동인증서를 추가로 발급해야 하나요?", "doc27.pdf", "은행"),
    ("과학기술발전장려금의 지급대상과 지급기준은 무엇인가요?", "doc27.pdf", "장려금"),
    ("디폴트옵션 상품은 한번 지정하면 변경이나 취소가 불가능한가요?", "doc30.pdf", "취소"),
    ("유선으로도 디폴트옵션 지정이 가능한가요?", "doc32.pdf", "유선"),
    ("디폴트옵션(매도) → 디폴트옵션(매수) 교체매매가 가능한가요?", "doc32.pdf", "교체"),
    ("MP 구독 서비스 신청 대상은 누구인가요?", "doc54.pdf", "구독"),
    ("MP 구독 서비스 신청/취소는 어디에서 하나요?", "doc54.pdf", "구독"),
]

miss = ignore = 0
for q, want_src, key in CASES:
    docs, scores, top, _ = main.search(q, top_k=5)
    srcs = []
    hit_chunk = False
    for d in docs:
        s = d.get("source", "?") if isinstance(d, dict) else "?"
        t = d.get("text", "") if isinstance(d, dict) else str(d)
        mark = ""
        if s == want_src:
            mark = "◁ 대상"
            if key in t:
                mark += "+정답사실"
                hit_chunk = True
        srcs.append(f"{s}{('[' + mark + ']') if mark else ''}")
    if hit_chunk:
        verdict = "찾았는데 무시(생성 문제)"
        ignore += 1
    elif want_src in [s.split("[")[0] for s in srcs]:
        verdict = "문서는 잡았으나 엉뚱한 청크(청크 미스)"
        miss += 1
    else:
        verdict = "문서 자체 미검색(검색 미스)"
        miss += 1
    print(f"\nQ: {q}")
    print(f"  top유사도 {top:.3f} | {verdict}")
    print(f"  검색 5개: {', '.join(srcs)}")

print(f"\n== 요약: 검색 쪽 문제 {miss} / 생성 쪽 문제 {ignore} ==")

# ── doc39류 '글자 겹침' 전수 측정 ──────────────────────────────────
print("\n== 글자 겹침(연연금금…) 청크 전수 조사 ==")
chunks = json.load(open("/root/app/chunks.json", encoding="utf-8"))
pat = re.compile(r"([가-힣])\1([가-힣])\2([가-힣])\3")
bad = {}
for i, c in enumerate(chunks):
    m = pat.search(c["text"])
    if m:
        bad.setdefault(c["source"], []).append(i)
for s, idxs in sorted(bad.items()):
    print(f"  {s}: {len(idxs)}개 청크 {idxs[:8]}")
    ex = chunks[idxs[0]]["text"]
    mm = pat.search(ex)
    print(f"    예: …{ex[max(0, mm.start()-30):mm.end()+30]}…")
if not bad:
    print("  없음")
