# -*- coding: utf-8 -*-
"""gate_diag.py — mini8 M2에서 실재 상품(삼성클래식)이 '확인되지 않는 상품명'으로 표시된 원인 진단(API 호출 0회).
main 을 import 해 실제 _CORPUS_NORM 과 게이트 함수로 대조한다. 사용: cd /root/app && source venv/bin/activate && python gate_diag.py"""
import re, requests
requests.post = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("no api"))
import main
txt = open("mini8_out.txt", encoding="utf-8").read().split("[M2]")[1].split("--- 답변 ---")[1].split("[N6]")[0]
txt = txt.split("※ '삼성")[0]
for nm in ["삼성클래식연금증권전환형자투자신탁", "삼성클래식연금증권전환형투자신탁", "삼성클래식연금증권전환형자투자신탁제1호[주식]", "삼성클래식연금증권전환형자", "삼성클래식연금"]:
    print(f"코퍼스에 '{nm}' 있음? {nm in main._CORPUS_NORM}")
i = main._CORPUS_NORM.find("삼성클래식연금")
print("코퍼스 첫 출현 주변:", repr(main._CORPUS_NORM[max(0, i-20): i+80]))
a, u = main.annotate_unknown_products(txt, "좋은 연금상품 하나 추천해주세요.")
print("게이트 판정 미확인:", u)
for m in re.finditer(r"삼성클래식연금증권전환형자?투자신탁", txt):
    seg = txt[m.start(): m.end()]
    print("답변 이름 코드포인트 이상 여부:", [hex(ord(c)) for c in seg if not (0xAC00 <= ord(c) <= 0xD7A3)])
