# -*- coding: utf-8 -*-
"""patch_v1387.py — v1386(63d34b8e) main.py 에 v13.87 적용. (v1386 적용 후 실행) — 1훅
  [문장 허용 게이트 — 화이트리스트] 전 유형 최종 관문: LLM 산문 문장은 ① 모든 숫자가 근거 문서·질문·코퍼스 상수 안에 있고 ② 우열·추측·법적 단정 표지가 없을 때만 남는다.
  코드 줄(※·[…]·표·판정·후보 블록·코드 문단 유형)은 통과. ③ 근거 접점 낮은 문장은 이번 버전에서는 trace 관측만(다음 버전 보정용).
자동백업·자가검증. 이미 v13.87이면 스킵. 검증 md5==9ec67bdecec6fe9c86baeccfa4574e3d"""








import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='63d34b8e753e08c627567e455e59736d'
EXPECT_AFTER='9ec67bdecec6fe9c86baeccfa4574e3d'
HUNKS=[["        ans = re.sub(r\"([가-힣0-9])([)\\]'\\\"」]*)\\s*은\\(는\\)\", lambda m_: m_.group(1) + m_.group(2) + _josa(m_.group(1)), ans)   # v13.66/67: 조사 정합(따옴표 뒤 포함)\n", "        # ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════\n        # v13.87 [문장 허용 게이트 — 화이트리스트] (전 유형 최종 관문, LLM 호출 없음)\n        #   지금까지의 규칙은 '틀린 표현을 찾아 지우는' 블랙리스트라 LLM이 새 표현을 낼 때마다 구멍이 생겼다. 여기서는 반대로,\n        #   LLM 산문 문장은 아래 조건을 모두 만족할 때만 남긴다(코드가 만든 줄·표·고지·판정은 통과).\n        #   ① 숫자 근거: 문장의 모든 숫자가 사용 근거 문서·질문·코퍼스 확정 상수 안에 있음(근거 밖 수치 = 창작)\n        #   ② 표지 없음: 우열 판단(_VERDICT)·추측(가능성이 큽/보입니다/예상)·법적 성격 단정(의무·벌금·불이익, 질문이 묻지 않은 경우) 없음\n        #   ③ 관측: 내용어의 근거 존재 비율(2자 접두 일치)이 낮은 문장은 이번 버전에서는 '지우지 않고' trace 에 후보로만 기록(다음 버전 보정용)\n        #   답변 전체가 코드 문단인 유형(B4·B5·B7·B10·B12·C4 등)은 게이트를 건너뛴다.\n        _gate_skip = any(k_ in clean_note for k_ in (\"코드 문단만\", \"사실 레코드 답변\", \"정보 한계 답변\", \"한도 구조 문장(\", \"개인 계좌 조회 의도\", \"코드 문장\"))\n        if not _gate_skip and ans.strip():\n            _CONST = {\"600\", \"900\", \"1800\", \"1500\", \"300\", \"5500\", \"4500\", \"16.5\", \"13.2\", \"148.5\", \"118.8\", \"60\", \"55\", \"30\", \"40\", \"50\", \"5.5\", \"4.4\", \"3.3\", \"15.4\", \"16.5\",\n                      \"2024\", \"2023\", \"2022\", \"2013\", \"12\", \"1\", \"2\", \"3\", \"4\", \"5\", \"6\", \"10\", \"11\", \"20\", \"21\", \"70\", \"80\", \"100\", \"12.5\", \"14\", \"1000\", \"148\", \"118\", \"0\"}\n            _evtxt = (\" \".join(c_.get(\"text\", \"\") for c_ in used) + \" \" + question).replace(\",\", \"\")\n            _evnum = set(re.findall(r\"\\d+(?:\\.\\d+)?\", _evtxt)) | _CONST\n            _CODE_SIG = re.compile(r\"근거 문서 기준|위험등급 우열:|계산 결과 요약|세액공제 한도 기준|경과 기간\\(|표현만으로는 60일|제공된 자료|확정하지 못|확정할 수 없|\"\n                                   r\"인출 재원별로|그대로 '반납'하는|과세이연 대상이며|IRP 의무이전|투자설명서 기준으로|연도별 수익률|미래의 수익을 보장|개인정보|시스템 지시문|자료 범위|실시간|\"\n                                   r\"본인 인증|비교 항목에서 제외|자료 없음|후보로 검토하실|조건이 정해지면|성향이면|검토 후보|비교 후보|같은 효과를 얻을 수 있습니다\\(요건|요건을 충족하면\")\n            _SPEC = re.compile(r\"가능성이\\s*(?:큽|높|있)|것으로\\s*(?:보입니다|보이며|예상|추정)|예상됩니다|추정됩니다|전망입니다\")\n            _LEGAL = re.compile(r\"법적\\s*(?:의무|강제)|의무\\s*사항|벌금|불이익\") if not re.search(r\"의무|벌금|불이익|법적\", question) else None\n            _STOP = (\"경우\", \"따라\", \"대해\", \"대한\", \"통해\", \"위해\", \"있습니다\", \"없습니다\", \"됩니다\", \"합니다\", \"입니다\", \"수\", \"및\", \"또는\", \"등의\", \"등을\", \"이는\", \"따라서\", \"다만\", \"또한\", \"그러나\", \"하지만\", \"이때\", \"즉\")\n            _g87, _n87, _obs87, _ex87 = [], 0, 0, \"\"\n            for _ln in ans.split(\"\\n\"):\n                _st = _ln.strip()\n                if not _st or _st.startswith((\"※\", \"[\", \"|\", \"(\")) or \"|\" in _st or _ROW_LABEL.match(_st) or _CODE_SIG.search(_st):\n                    _g87.append(_ln); continue\n                _lead = _PROSE_LEAD.match(_ln).group(0)\n                _ss = re.split(r\"(?<=[.!?])\\s+\", _ln[len(_lead):])\n                _kp = []\n                for s_ in _ss:\n                    if not s_.strip():\n                        continue\n                    _nums = re.findall(r\"\\d+(?:\\.\\d+)?\", s_.replace(\",\", \"\"))\n                    if any(n_ not in _evnum for n_ in _nums):\n                        _n87 += 1; continue                                          # ① 근거 밖 숫자\n                    if _VERDICT.search(s_) or _SPEC.search(s_) or (_LEGAL and _LEGAL.search(s_)):\n                        _n87 += 1; continue                                          # ② 우열·추측·법적 단정\n                    _toks = [t_ for t_ in re.findall(r\"[가-힣]{2,}\", s_) if t_ not in _STOP]\n                    if len(_toks) >= 4 and sum(1 for t_ in _toks if t_[:2] in _evtxt) / len(_toks) < 0.5:\n                        _obs87 += 1; _ex87 = _ex87 or s_[:40]                       # ③ 관측만\n                    _kp.append(s_)\n                if _kp:\n                    _g87.append(_lead + \" \".join(_kp))\n            _body87 = re.sub(r\"\\n{3,}\", \"\\n\\n\", \"\\n\".join(_g87)).strip()\n            if _n87:\n                if not _body87 or not re.search(r\"[가-힣]\", _body87):\n                    _body87 = \"제공된 자료에서 질문에 직접 답하는 근거를 확인하지 못해, 확정할 수 있는 내용만 안내드립니다. 연금 제도·세액공제·상품 위험등급 등 자료 범위의 질문으로 다시 문의해 주세요.\"\n                ans = _body87\n                clean_note += f\" 허용 게이트: 근거 밖·표지 문장 {_n87}건 제외\"\n            if _obs87:\n                clean_note += f\" (허용 게이트 관측: 근거 접점 낮은 문장 {_obs87}건 — 예: '{_ex87}')\"\n        ans = re.sub(r\"([가-힣0-9])([)\\]'\\\"」]*)\\s*은\\(는\\)\", lambda m_: m_.group(1) + m_.group(2) + _josa(m_.group(1)), ans)   # v13.66/67: 조사 정합(따옴표 뒤 포함)\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "v13.87 [문장 허용 게이트 — 화이트리스트]" in src: print("[스킵] 이미 v13.87 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[중단] 적용전 md5가 예상 v1386과 다름 → 서버 파일이 갈라짐. main_v1387_full.py 로 통째 교체하세요."); sys.exit(4)
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v1386_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
