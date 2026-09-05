# -*- coding: utf-8 -*-
"""patch_v139.py — v138(6d5ae2a2) main.py 에 v13.9 적용.
  [골든 20문항 전수 판독 실결함 4건 — 전부 결정적 후처리, 코퍼스 근거 확인 후 작성]
   ① G11: 최상위 번호 목록이 1부터 연속이 아니면([2], [1,3]) 1부터 재번호. 연속 목록·두 개 목록은 불변.
   ② N02: 한도 카드 지시문을 사용자 안내처럼 옮긴 문장('…잘못 표기하지 않도록 주의') 제거.
   ③ V02: 문서에 없는 '기한 놓치면 이전 불가/계좌 해지해야' 단정 문장 제거(코퍼스: 해당 서술은
      55세 전 중도인출 문맥). ISA '60일 내 이전하지 않으면 혜택 없음'(문서 근거)·55세 중도인출 문장은 보존.
   ④ F01: 'IRP는 원금이 보장되죠?' 전제 교정 문장을 코드로 고정(근거: IRP 원리금보장상품 존재,
      투자신탁은 투자원금 비보장). 답변이 이미 원리금보장/실적배당 구분을 담았으면 불변.
   그 외 경로 불변.
자동백업·자가검증. 이미 v13.9면 스킵. 검증 md5==0bfe0c80b78da76944d67924ac41caa5"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='6d5ae2a25a7bda7f916630eeafb625b1'
EXPECT_AFTER='0bfe0c80b78da76944d67924ac41caa5'
HUNKS=[["            _seen.add(_k)\n        _kept.append(_ln)\n    ans = \"\\n\".join(_kept)\n    return ans.strip()\n\n\n", "            _seen.add(_k)\n        _kept.append(_ln)\n    ans = \"\\n\".join(_kept)\n    # K) v13.9(골든 전수 판독 3건 — 전부 결정적 판정):\n    #    K1 (G11) 최상위 번호 목록이 1부터 연속이 아니면(예: [2], [1,3]) 1부터 재번호.\n    #       앞 항목이 다른 필터에 지워져 '2.'만 남는 고아 번호. 이미 연속([1,2,3] 또는 [1,2,3,1,2] 두 목록)이면 불변.\n    _lines = ans.split(\"\\n\")\n    _idx = [(i, int(m.group(1))) for i, ln in enumerate(_lines)\n            for m in [re.match(r\"^(\\d{1,2})\\.\\s\", ln)] if m]\n    if _idx:\n        _valid, _prev = True, 0\n        for _, _n in _idx:\n            if not (_n == 1 or _n == _prev + 1):\n                _valid = False\n                break\n            _prev = _n\n        if not _valid:\n            _k = 0\n            for i, _n in _idx:\n                _k += 1\n                _lines[i] = re.sub(r\"^\\d{1,2}\\.\", f\"{_k}.\", _lines[i], count=1)\n            ans = \"\\n\".join(_lines)\n    #    K2 (N02) 한도 카드 지시문('…라고 쓰면 안 되고')을 사용자 안내처럼 옮긴 문장 제거:\n    #       '잘못 표기' + '주의/않도록' 조합은 정상 안내문에 없는 지시문 잔재.\n    ans = re.sub(r\"(?m)(?:(?<=[.!?])[ \\t]+|^[ \\t]*)[^.!?\\n]*잘못\\s*표기[^.!?\\n]*(?:주의|않도록)[^.!?\\n]*[.!?]?\", \"\", ans)\n    #    K3 (V02) 문서에 없는 '기한 경과 시 이전 불가/계좌 해지' 단정 제거(코퍼스 확인: 해당 서술은\n    #       55세 전 중도인출 사유 문맥이지 60일 기한 문맥이 아님). 조건문 '…이내에 이전하지 않으면 혜택을\n    #       받을 수 없다'(ISA·문서 근거)는 '이전 자체 불가' 형태가 아니라 보존됨. 뒤따르는 접속 문장도 정리.\n    _out, _dropped = [], False\n    for _ln in ans.split(\"\\n\"):\n        _sents = re.split(r\"(?<=[.!?])\\s+\", _ln)\n        _keep = []\n        for _s in _sents:\n            _bad = (re.search(r\"(?:놓치|놓쳤|지나|경과)[^.!?]*이전(?:이|은|도|은)?\\s*(?:불가능|불가|할\\s*수\\s*없|안\\s*됩)\", _s)\n                    or re.search(r\"계좌를\\s*해지[^.!?]*(?:되찾|기한|기간|60\\s*일)|(?:되찾|기한|기간|60\\s*일)[^.!?]*계좌를\\s*해지\", _s))\n            if _bad:\n                _dropped = True\n                continue\n            if _dropped and re.match(r\"\\s*(?:그러나|하지만|다만|이에|이 경우|또한)\", _s):\n                _dropped = False\n                continue\n            _dropped = False\n            _keep.append(_s)\n        _out.append(\" \".join(k for k in _keep if k.strip()))\n    ans = \"\\n\".join(_out)\n    return ans.strip()\n\n\n"], ["        if _n01n:\n            ans = _n01\n            clean_note += \" 과세제외 범위 명확화\"\n\n        # (1-6b) v9.41: ISA 전환금 질문이면 '대상 총액'을 코드가 계산해 붙인다.\n        #   조건 없이 붙인다 — '이미 썼는지'를 판단하려 들면 그 판단이 또 어긋난다.\n", "        if _n01n:\n            ans = _n01\n            clean_note += \" 과세제외 범위 명확화\"\n        # (1-6c) v13.9(F01): 'IRP는 원금이 보장되죠?' 전제 교정 — 계좌 자체는 원금 보장이 아니며 안에서\n        #   고르는 상품에 따라 다르다(코퍼스 근거: IRP 원리금보장상품 존재(디폴트옵션 FAQ),\n        #   투자신탁은 투자원금을 보장하지 않음(투자설명서)). 답변이 이미 그 구분을 담았으면 불변.\n        if re.search(r\"(?:IRP|연금저축|연금계좌|퇴직연금|DC)[^\\n]{0,25}?원금[^\\n]{0,6}?보장\", question) \\\n                and re.search(r\"죠|나요|맞|되나|인가|가요\", question) \\\n                and not re.search(r\"실적배당|원리금\\s*보장\", ans):\n            _f01 = (\"IRP(연금계좌) 자체가 원금을 보장하는 것은 아닙니다. 계좌 안에서 예금 등 원리금보장상품을 \"\n                    \"선택하면 원리금이 보장되지만, 펀드·ETF 등 실적배당형 상품은 투자원금을 보장하지 않아 \"\n                    \"원금 손실이 발생할 수 있습니다. 즉, 원금 보장 여부는 계좌가 아니라 계좌 안에서 고르는 \"\n                    \"상품에 따라 달라집니다.\")\n            _body = re.sub(r\"^\\s*제공된\\s*자료에서\\s*확인할\\s*수\\s*없습니다\\.?\\s*(?:다만,?\\s*)?\", \"\", ans)\n            ans = _f01 + \"\\n\\n\" + _body.lstrip()\n            clean_note += \" 원금보장 전제 교정\"\n\n        # (1-6b) v9.41: ISA 전환금 질문이면 '대상 총액'을 코드가 계산해 붙인다.\n        #   조건 없이 붙인다 — '이미 썼는지'를 판단하려 들면 그 판단이 또 어긋난다.\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "원금보장 전제 교정" in src: print("[스킵] 이미 v13.9 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[경고] 적용전 md5가 예상 v138과 다름. 훅 매칭되면 계속.")
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v138_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
