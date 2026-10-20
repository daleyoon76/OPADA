import json, re, pathlib
KEYS=["m1_중구_공유임대","m2_마곡_공유임대","m3_부산_기타매각","m4_상암_기타임대"]
TYPES=["압류재산","국유재산","공유재산","기타일반재산","수탁재산","불용품","파산자산"]
def norm(s): return re.sub(r"[\s,·]", "", str(s or ""))
def ans(k):
    p=pathlib.Path(f"/tmp/opada-cmp/{k}.json")
    if p.exists(): return json.loads(p.read_text(encoding="utf-8"))
    o=json.loads(pathlib.Path("/tmp/opada-cmp/out.json").read_text(encoding="utf-8"))
    return {"B":o["B_링크만"],"C":o["C_본문까지"]}
rows=[]
for k in KEYS:
    a=ans(k); t=json.loads(pathlib.Path(f"/tmp/opada-cmp/{k}.truth.json").read_text(encoding="utf-8"))
    true_type=t["assetType"]; 
    org=re.sub(r"^(재단법인|사회복지법인|주식회사|학교법인)\s*","",t["agency"] or "")
    dl=(t.get("bidDeadline") or "")[:10]
    dep=t["costs"].get("입찰보증금","")
    pct=re.search(r"(\d+)\s*%",dep); pct=pct.group(1) if pct else ""
    base="입찰금액" if "입찰금액" in dep else ("최저입찰가격" if "최저입찰" in dep else "")
    for cond in ("B","C"):
        s=a[cond]; ns=norm(s)
        # 재산유형: 다른 유형을 명시했으면 틀림, 아예 안 썼으면 언급없음
        said=[x for x in TYPES if norm(x) in ns]
        if norm(true_type) in ns: ty="맞음"
        elif said: ty="틀림"
        else: ty="언급없음"
        # 공고기관
        og = "맞음" if (org and norm(org) in ns) else "틀림/없음"
        # 마감 날짜
        y,m,d=(dl.split("-")+["",""])[:3] if dl else ("","","")
        pats=[dl,f"{y}.{m}.{d}",f"{y}년{m}월{d}일",f"{int(m)}월{int(d)}일" if m else "",f"{m}월{d}일"] if dl else []
        da="맞음" if any(p and norm(p) in ns for p in pats) else "틀림/없음"
        # 보증금: 기준과 비율이 모두 맞아야 맞음
        dp="맞음" if (pct and base and norm(base) in ns and f"{pct}%" in norm(s)) else "틀림/없음"
        rows.append({"물건":k.split("_",1)[1],"조건":cond,"재산유형":ty,"공고기관":og,
                     "마감":da,"보증금":dp,
                     "근거출처":"있음" if re.search(r"출처\s*[:：]|공고문\s*>\s*\d",s) else "없음",
                     "미확정표시":"있음" if re.search(r"미분류|확정하지 못|별도 문의",s) else "없음",
                     "기한추측":"있음" if re.search(r"보통\s*낙찰|통상|일반적으로\s*\d+\s*일|7~10일|60일\s*이내",s) else "없음"})
pathlib.Path("/tmp/opada-cmp/score2.json").write_text(json.dumps(rows,ensure_ascii=False,indent=1),encoding="utf-8")
hdr=["물건","조건","재산유형","공고기관","마감","보증금","근거출처","미확정표시","기한추측"]
print(" | ".join(hdr))
for r in rows: print(" | ".join(str(r[h]) for h in hdr))
print()
for cond in ("B","C"):
    sub=[r for r in rows if r["조건"]==cond]
    ok=sum(1 for r in sub for f in ("재산유형","공고기관","마감","보증금") if r[f]=="맞음")
    print(f"조건 {cond}: 사실 4항목 × 물건 4건 = 16개 중 맞음 {ok}개")
