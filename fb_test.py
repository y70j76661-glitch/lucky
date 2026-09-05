# -*- coding: utf-8 -*-
"""fb_test.py — v13.20 429 안전망 오프라인 검증(API 호출 0회, 크레딧 소모 없음).
requests.post 를 가짜 429 응답으로 바꾼 뒤 main.answer() 를 직접 호출한다(서버 재시작 불필요, 실행 중 서버와 무관).
사용: cd /root/app && source venv/bin/activate && python fb_test.py"""
import time, requests
class _R:
    status_code = 429
    text = "fake rate limit"
    def json(self): return {}
requests.post = lambda *a, **k: _R()        # 모든 CLOVA 호출을 429로
import main
main._429_COOLDOWN = 120.0
Q = [("FB1", "총급여 5,500만원, 연금저축 500만원과 IRP 500만원 납입하면 공제액은?"),
     ("FB2", "또박또박연금펀드의 클래스별 총보수를 알려주세요."),
     ("FB3", "연금 수령 나이는 몇 살인가요?")]
bad = 0
for qid, q in Q:
    t = time.time()
    r = main.answer(qid, q)
    a = r.get("answer", "")
    ok = ("일시적인 오류" not in a) and len(a) > 60 and "[참고 문서]" in a
    if qid == "FB1": ok = ok and "148.5" in a
    bad += (not ok)
    print(f"[{qid}] {time.time()-t:4.0f}s {'OK' if ok else '★실패'} | trace: {r.get('think_trace','')[:160]}")
    print("   ", a[:400].replace("\n", " / "))
print("=" * 50)
print("429 안전망 3/3 OK" if not bad else f"확인 필요 {bad}건")
