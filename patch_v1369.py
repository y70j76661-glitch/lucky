# -*- coding: utf-8 -*-
"""patch_v1369.py — v1368(28c7546d) main.py 에 v13.69 적용. (v1368 적용 후 실행)
  [mini45 리뷰 반영] ① S4: '연 1,500만원 이하로 인출하면 5.5~3.3퍼센트' 일반화 문장에 조건(연금 수령 요건·연금소득 합계·연령별)을 문장 안에 직접 부착
   ② C9: 'IRP의 안정성'·'복리 효과'·'위험 등급 중간 이상 상품 선택' 등 계좌를 자산처럼 서술하는 문장 제거 범위 확대
   ③ 추천 답변 출처 줄 정밀화 일반화: 본문이 인용한 투자설명서 + 비설명서 문서만 표기(인용 안 된 설명서 제외)
   ④ 표기 정리: 마크다운 잔재 홀수 별표 제거, 상품 블록 안 빈 줄·번호 머리 앞 빈 줄 정리(전 유형)
자동백업·자가검증. 이미 v13.69이면 스킵. 검증 md5==c67afd804fdb11dfdca6db7efd222a1f"""
import sys,os,time,hashlib,py_compile
TARGET=sys.argv[1] if len(sys.argv)>1 else "main.py"
EXPECT_BEFORE='28c7546db92068438bb95bf3ccbdd8d0'
EXPECT_AFTER='c67afd804fdb11dfdca6db7efd222a1f'
HUNKS=[["                    if re.search(r\"15\\.4\", s_) and \"15.4\" not in _docs_t:                # v13.68: 금융소득 15.4% 비교는 근거 문서에 있을 때만\n                        _n19 += 1; continue\n", "                    if re.search(r\"15\\.4\", s_) and \"15.4\" not in _docs_t:                # v13.68: 금융소득 15.4% 비교는 근거 문서에 있을 때만\n                        _n19 += 1; continue\n                    if re.search(r\"1,?500\\s*만\\s*원\", s_) and re.search(r\"5\\.5|3\\.3\", s_) and not re.search(r\"요건|연령별|합계\", s_):   # v13.69: 조건 없는 일반화 → 조건 부착\n                        s_ = re.sub(r\"(?:만\\s*55세\\s*이후에?\\s*)?연금(?:으로)?\\s*수령(?:할\\s*때|\\s*시)?\\s*\", \"\", s_, count=1)\n                        s_ = re.sub(r\"(연\\s*1,?500\\s*만\\s*원\\s*이하)(?:로|의\\s*금액에\\s*대해서는|이면|라면)?\\s*(?:인출하면|수령하면)?\\s*(5\\.5\\s*%?\\s*[~∼-]\\s*3\\.3\\s*%)\",\n                                    r\"연금 수령 요건(만 55세 이후, 연금 수령 한도 내)을 갖춰 연금으로 받을 때 연금소득 합계 \\1에 대해 연령별 \\2\", s_)\n                        _n19 += 1\n"], ["                                               or re.search(r\"(?:IRP|연금저축)[^.!?\\n]{0,40}?(?:수익률?\\s*(?:극대화|을\\s*기대|이\\s*높|을\\s*높)|높은\\s*수익|공격적인\\s*포트폴리오|투자\\s*옵션이[^.!?\\n]{0,15}유리|보다\\s*(?:공격적|유리))\", s_))]   # v13.64: 계좌(납입처)를 수익성으로 비교하는 서술은 근거 없음(계좌≠상품)\n", "                                               or re.search(r\"(?:IRP|연금저축)[^.!?\\n]{0,40}?(?:수익률?\\s*(?:극대화|을\\s*기대|이\\s*높|을\\s*높)|높은\\s*수익|공격적인\\s*포트폴리오|투자\\s*옵션이[^.!?\\n]{0,15}유리|보다\\s*(?:공격적|유리))\", s_)\n                                               or re.search(r\"(?:IRP|연금저축)의\\s*(?:안정성|수익성|성장성)|복리\\s*효과를\\s*누리기|위험\\s*등급이\\s*중간\\s*이상\", s_))]   # v13.64/69: 계좌(납입처)를 수익성·안정성으로 서술하는 문장은 근거 없음(계좌≠상품)\n"], ["            if \"구조화 대체 목록\" in _rr and src_tail:                # v13.66(T11): 목록이 인용하지 않은 투자설명서는 출처 줄에서 제외(근거 정밀도)\n                _keep = list(dict.fromkeys(list(_RC_FB_SRCS) + [s for s in _rr_allow if not s.startswith(\"R2_\")]))\n                if _keep:\n                    src_tail = \"[참고 문서] \" + \", \".join(_keep)\n                    clean_note += \" 출처 줄 정밀화\"\n", "            if src_tail:                                              # v13.66/69(T11·M2): 본문이 인용한 투자설명서 + 비(非)설명서 문서만 출처 줄에(근거 정밀도)\n                _cited_r2 = re.findall(r\"근거 문서:\\s*([^\\n—]+)\", ans)\n                _cited_r2 = [x.strip() for grp in _cited_r2 for x in grp.split(\",\") if x.strip().startswith(\"R2_\")]\n                _keep = list(dict.fromkeys(_cited_r2 + list(_RC_FB_SRCS if \"구조화 대체 목록\" in _rr else []) + [s for s in _rr_allow if not s.startswith(\"R2_\")]))\n                _old = re.findall(r\"[\\w.\\-]+\\.(?:pdf|docx|xlsx|xls|txt|csv|hwp|pptx)\", src_tail)\n                if _keep and set(_keep) != set(_old):\n                    src_tail = \"[참고 문서] \" + \", \".join(_keep)\n                    clean_note += \" 출처 줄 정밀화\"\n"], ["        ans = re.sub(r\"([가-힣0-9])([)\\]'\\\"」]*)\\s*은\\(는\\)\", lambda m_: m_.group(1) + m_.group(2) + _josa(m_.group(1)), ans)   # v13.66/67: 조사 정합(따옴표 뒤 포함)\n", "        ans = re.sub(r\"([가-힣0-9])([)\\]'\\\"」]*)\\s*은\\(는\\)\", lambda m_: m_.group(1) + m_.group(2) + _josa(m_.group(1)), ans)   # v13.66/67: 조사 정합(따옴표 뒤 포함)\n        ans = re.sub(r\"(?<!\\*)\\*(?!\\*)\", \"\", ans)                                   # v13.69(C9): 마크다운 잔재 홀수 별표 제거\n        ans = re.sub(r\"\\n[ \\t]*\\n(?=[ \\t]*-\\s*(?:근거 문서|유의)\\s*[:：])\", \"\\n\", ans)   # v13.69(M2): 상품 블록 안 빈 줄 제거\n        ans = re.sub(r\"(?m)(^[ \\t]*-[^\\n]*)\\n(?=\\d+[.)]\\s)\", \"\\\\1\\n\\n\", ans)         # v13.69(M2): 번호 머리 앞 빈 줄\n"]]
def md5(s): return hashlib.md5(s.encode("utf-8")).hexdigest()
def main():
    if not os.path.exists(TARGET): print("[중단] 대상 없음:",TARGET); sys.exit(1)
    src=open(TARGET,encoding="utf-8").read(); before=md5(src)
    print("대상:",TARGET,"\n적용전 md5:",before)
    if "v13.69(C9): 마크다운 잔재" in src: print("[스킵] 이미 v13.69 적용됨."); sys.exit(0)
    if before!=EXPECT_BEFORE: print("[중단] 적용전 md5가 예상 v1368과 다름 → 서버 파일이 갈라짐. main_v1369_full.py 로 통째 교체하세요."); sys.exit(4)
    for k,(O,N) in enumerate(HUNKS):
        c=src.count(O)
        if c!=1: print(f"[중단] 훅{k} OLD 매칭 {c}회(1이어야). 취소."); sys.exit(2)
    out=src
    for O,N in HUNKS: out=out.replace(O,N,1)
    after=md5(out); ts=time.strftime("%Y%m%d_%H%M%S"); bak=TARGET+".bak_v1368_"+ts
    open(bak,"w",encoding="utf-8").write(src); open(TARGET,"w",encoding="utf-8").write(out)
    ok=(after==EXPECT_AFTER)
    print("  ✓ 훅",len(HUNKS),"개 적용","\n백업:",bak,"\n적용후 md5:",after,"\n기대   md5:",EXPECT_AFTER," →","일치 ✅" if ok else "불일치 ❌")
    try: py_compile.compile(TARGET,doraise=True); print("py_compile: OK")
    except py_compile.PyCompileError as e: print("[중단] 문법오류:",e); sys.exit(3)
    print("최종 판정:", "성공 ✅" if ok else "확인 필요 ❌"); print("\n완료. uvicorn 재시작 후 스모크.")
if __name__=="__main__": main()
