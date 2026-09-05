# -*- coding: utf-8 -*-
"""v13.36 recommendation-structure patch.

대상: main.py
목적:
- 추천 답변에서 내용 없는 번호 사례를 통째로 제거하고 재번호
- 상품별 실적배당형/원금·분배금 비보장 고지를 상품 항목에 귀속
- 같은 상품군 문장에서 보장 고지가 다른 상품에 붙는 문제 방지

적용 후 반드시 golden/output-quality/recommendation 회귀를 실행하세요.
"""
import sys, os, re, hashlib, py_compile, shutil, datetime

path = sys.argv[1] if len(sys.argv) > 1 else "main.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

marker = "        # (2) 지우고 남은 이중 공백 정리"
if marker not in text:
    raise SystemExit("삽입 지점을 찾지 못했습니다: final cleanup marker")
if "v13.36 recommendation structure" in text:
    print("이미 v13.36 적용됨")
    raise SystemExit(0)

backup = path + ".bak_v1336_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
shutil.copy2(path, backup)

block = r'''        # v13.36 recommendation structure: 상품 항목 단위 정리
        # 문장 단위 계약이 사례 머리말을 상품 문장으로 오인하거나,
        # 상품별 고지를 전역 중복 제거로 삭제하는 문제를 막는다.
        if qtype == "추천":
            _rec_lines = ans.splitlines()
            _num_re = re.compile(r"^(\s*)(\d+)\.\s*(.*)$")
            _starts = [i for i, _ln in enumerate(_rec_lines)
                       if _num_re.match(_ln)]
            if _starts:
                _blocks = []
                for _j, _st in enumerate(_starts):
                    _en = _starts[_j + 1] if _j + 1 < len(_starts) else len(_rec_lines)
                    _blocks.append((_st, _en, _rec_lines[_st:_en]))

                _prod_re = re.compile(
                    r"(?:삼성|미래에셋|TIGER|KODEX|ACE|KBSTAR|HANARO)[^\n:：]{2,100}"
                    r"(?:증권자?투자신탁|투자신탁|펀드|ETF|예금)(?:[^\n]*)?",
                    re.I)
                _kept = []
                _changed = False
                _new_no = 1
                for _st, _en, _bl in _blocks:
                    _joined = "\n".join(_bl)
                    _first = _bl[0]
                    _heading = _num_re.match(_first).group(3).strip()
                    _has_product = bool(_prod_re.search(_joined))
                    _has_body = any(
                        re.search(r"(?:추천\s*상품|상품\s*예시|근거\s*:|참고\s*:|유의\s*:|투자\s*특징|총보수|위험등급)", _ln)
                        for _ln in _bl[1:]
                    )
                    # 사례 머리말만 있고 상품·본문이 없으면 항목 전체 제거
                    if (re.search(r"(?:경우|때|분들|원하는)\s*[:：]\s*$", _heading)
                            and not (_has_product and _has_body)):
                        _changed = True
                        continue

                    _clean = list(_bl)
                    # 상품명이 있는 항목 안의 공통/잘못 귀속된 비보장 문장은 제거 후
                    # 상품별 고지를 다시 붙인다. 고지 문장은 반드시 해당 상품명과 함께 둔다.
                    _products = []
                    for _m in _prod_re.finditer(_joined):
                        _p = re.sub(r"\s+", " ", _m.group(0)).strip(" -·")
                        _p = re.sub(r"\s+(?:같은|등의?)\s*$", "", _p).strip()
                        if len(_p) >= 8 and _p not in _products:
                            _products.append(_p)
                    if _products:
                        _before = len(_clean)
                        _clean = [
                            _ln for _ln in _clean
                            if not (re.search(r"실적배당형", _ln)
                                    and re.search(r"(?:원금|수익|분배금).*(?:보장되지|보장 안|보장\s*불가)", _ln))
                        ]
                        if len(_clean) != _before:
                            _changed = True
                        # 상품이 여러 개 한 항목에 묶인 경우에도 상품별 고지를 각각 생성
                        for _p in _products:
                            _clean.append(
                                f" - 유의: {_p}은(는) 실적배당형으로, "
                                "투자원금과 수익(분배금)은 보장되지 않습니다."
                            )
                        _changed = True
                    _clean[0] = re.sub(r"^\s*\d+\.", f"{_new_no}.", _clean[0], count=1)
                    _new_no += 1
                    _kept.extend(_clean)

                if _changed:
                    ans = "\n".join(_kept)
                    clean_note += " 추천 항목 단위 정리"

            # 상품명·등급이 없는 세제/일반 사례는 추천 목록으로 남기지 않는다.
            # 단, 질문이 세제혜택을 명시적으로 요구한 경우는 보존한다.
            if not re.search(r"세금|세액|세제|과세|소득세|공제|절세", question):
                _ls = ans.splitlines()
                _drop = []
                _nums = [i for i, _ln in enumerate(_ls) if _num_re.match(_ln)]
                for _j, _st in enumerate(_nums):
                    _en = _nums[_j + 1] if _j + 1 < len(_nums) else len(_ls)
                    _blk = "\n".join(_ls[_st:_en])
                    if re.search(r"(?:세제\s*혜택|소득\s*공제|비과세)", _blk) and not re.search(r"(?:펀드|ETF|투자신탁|예금)", _blk):
                        _drop.extend(range(_st, _en))
                if _drop:
                    ans = "\n".join(_ln for _i, _ln in enumerate(_ls) if _i not in set(_drop))
                    clean_note += " 추천 내 세제 전용 빈 항목 제거"

'''
new_text = text.replace(marker, block + marker, 1)
with open(path, "w", encoding="utf-8") as f:
    f.write(new_text)

py_compile.compile(path, doraise=True)
print("대상:", path)
print("백업:", backup)
print("적용 후 md5:", hashlib.md5(new_text.encode("utf-8")).hexdigest())
print("py_compile: OK")
print("주의: 추천 회귀(M2/M2b/G11), output-quality, golden을 실행하세요.")
