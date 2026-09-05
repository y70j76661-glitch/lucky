# -*- coding: utf-8 -*-
"""mini2_probe.py — v13.17 런타임 확인 7문항(정독에서 결함이 나온 것만). 전체 회귀 아님.
사용: cd /root/app && source venv/bin/activate && python mini2_probe.py"""
import re, time, requests

BASE = "http://127.0.0.1:8000/answer"
Q = [
    ("E7", "연봉 1억 2천만원, 연금저축 600만원 납입 시 공제액은?",
     lambda a: ([] if not re.search(r"300\s*만\s*원", a) else ["★옛규정_300만_잔존"]) + ([] if not re.search(r"39\.6", a) else ["★39.6_잔존"]) + ([] if "79.2" in a else ["정답_없음"])),
    ("D9", "총급여 5,500만원, 연금저축 500만원과 IRP 500만원 납입하면 공제액은?",
     lambda a: ([] if not re.search(r"149", a) else ["★149_잔존"]) + ([] if not re.search(r"초과하지\s*않", a) else ["★초과하지않_잔존"]) + ([] if "148.5" in a else ["정답_없음"])),
    ("N6", "중도해지 세금은 빼고, 연금으로 받을 때 세금만 알려줘.",
     lambda a: ([] if not re.search(r"년\s*차[^\n]{0,15}(?:5\.5|4\.4|3\.3)\s*%", a) else ["★년차형_잔존"]) + ([] if re.search(r"70\s*세", a) else ["연령구간_없음"])),
    ("M5", "IRP 신규 가입하면 첫 6개월 수수료 면제 혜택이 있나요?",
     lambda a: ([] if "면제" in a else ["★면제_언급없음"]) + ([] if not re.search(r"중도\s*인출", a) else ["딴소리_잔존"])),
    ("M2", "좋은 연금상품 하나 추천해주세요.",
     lambda a: ([] if len(re.findall(r"여쭙|여쭤|알려주시면|말씀해\s*주", a[:700])) <= 2 else ["되묻기_중복의심"])),
    ("B1", "연봉 4,000만원인데 연금저축에 599만원 넣었어요. 세액공제액은?",
     lambda a: ([] if not re.search(r"98\.84|98\.83", a) else ["★소수둘째_잔존"]) + ([] if "98.8" in a else ["정답_없음"])),
    ("G2", "총급여 6,000만원, IRP 900만원 넣었는데 16.5% 적용되는 거 맞죠? 공제액 얼마예요?",
     lambda a: ([] if "십만원" not in a else ["★십만원단위_잔존"]) + ([] if "118.8" in a else ["정답_없음"])),
]


def main():
    ft = open("mini2_out.txt", "w", encoding="utf-8")
    bad = 0
    for qid, q, chk in Q:
        t0 = time.time()
        try:
            a = requests.get(BASE, params={"question_id": qid, "question": q}, timeout=180).json().get("answer", "") or ""
        except Exception as e:
            a = f"(요청실패:{str(e)[:40]})"
        f = chk(a)
        bad += bool(f)
        print(f"  [{qid:3}] {time.time()-t0:4.1f}s  {'OK' if not f else '확인: ' + ' '.join(f)}")
        ft.write(f"\n{'='*70}\n[{qid}] {q}\n판정: {f or 'OK'}\n--- 답변 ---\n{a}\n")
        time.sleep(0.3)
    ft.close()
    print("=" * 50)
    print("7문항 모두 OK → v13.17 런타임 확인 통과" if not bad else f"확인 필요 {bad}문항 → mini2_out.txt 원문 확인")


if __name__ == "__main__":
    main()
