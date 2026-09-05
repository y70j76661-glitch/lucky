# -*- coding: utf-8 -*-
"""s3_check.py — S3(인덱스12M) 보수 숫자와 클래스 연결 + N6 연령-세율 근거 문서 원문 대조(API 호출 0회).
사용: cd /root/app && python3 s3_check.py > s3_check_out.txt"""
import json, re
d = json.load(open("chunks.json", encoding="utf-8")); it = d if isinstance(d, list) else d.values()
ts = [(c.get("text", ""), c.get("source", "")) for c in it if isinstance(c, dict)]
def show(title, pick, must, width=700, n=6):
    print("=" * 90); print(f"## {title}")
    hits = [(t, s) for t, s in ts if pick(s) and all(re.search(m, t) for m in must)]
    print(f"청크 {len(hits)}개")
    for t, s in hits[:n]:
        tt = re.sub(r"\s+", " ", t); m = re.search(must[0], tt); a = max(0, (m.start() if m else 0) - width // 3)
        print(f"  [{s}] {tt[a:a + width]}")
R = lambda s: s == "R2_KR5114420046.pdf"
show("S3 ① 클래스별 총보수 표(C / Ce)", R, [r"총보수", r"Ce|온라인"])
show("S3 ② 0.42 / 0.28 / 0.4313 숫자 주변", R, [r"0\.42|0\.28|0\.4313|0\.532"])
show("S3 ③ 동종유형 총보수 0.40", R, [r"동종\s*유형|동종유형"])
show("S3 ④ 판매보수 항목", R, [r"판매\s*보수|판매보수"])
A = lambda s: True
show("N6 ① 연금소득세 연령 구간 표(70세·80세·5.5·4.4·3.3)", A, [r"연금소득세", r"70\s*세", r"5\.5", r"3\.3"])
show("N6 ② 연령-세율만(연금소득세 단어 없이)", A, [r"70\s*세[^\n]{0,30}5\.5|5\.5[^\n]{0,30}70\s*세"])
print("=" * 90); print("끝")
