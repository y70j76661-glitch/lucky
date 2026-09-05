# -*- coding: utf-8 -*-
"""ret_probe.py — B7 원문 대조(API 호출 없음): 삼성퇴직연금인덱스12M 투자설명서 청크에서 3년 수익률 후보(4.63/4.02/3.41/3.43)와 클래스 표기를 뽑아 보여준다.
사용: python ret_probe.py"""
import re, main
hits = [c for c in main.chunks if "5114420046" in str(c.get("source", ""))]
print("R2_KR5114420046 청크:", len(hits))
for c in hits:
    t = c["text"]
    for m in re.finditer(r"4\.63|4\.02|3\.41|3\.43", t):
        s, e = max(0, m.start() - 160), min(len(t), m.end() + 120)
        print("----", m.group(0), "| 클래스 표기:", sorted(set(re.findall(r"(?:종류|클래스)\s*[A-Za-z]-?[A-Za-z0-9]{0,3}|퇴직연금\(?[A-Za-z]?\)?|[A-Z]-P2?|C-e|A-e", t)))[:8])
        print(t[s:e].replace("\n", " "))
print("==== '3년' 문맥 ====")
for c in hits:
    t = c["text"]
    for m in re.finditer(r"최근\s*3\s*년|3년", t):
        s, e = max(0, m.start() - 80), min(len(t), m.end() + 160)
        seg = t[s:e].replace("\n", " ")
        if re.search(r"\d+\.\d+", seg):
            print("·", seg)
