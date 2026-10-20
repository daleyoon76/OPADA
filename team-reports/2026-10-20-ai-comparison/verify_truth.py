import json, re, urllib.request, html, pathlib
KEYS=["m1_중구_공유임대","m2_마곡_공유임대","m3_부산_기타매각","m4_상암_기타임대"]
def norm(s): return re.sub(r"[\s,·]","",str(s or ""))
def page(url):
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(req,timeout=90) as r: raw=r.read().decode("utf-8","replace")
    t=re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>"," ",raw)
    return html.unescape(re.sub(r"(?s)<[^>]+>"," ",t))
print("참값이 페이지 원문에 실재하는지 (우리 서비스 출력과 독립 대조)")
print("물건 | 재산유형 | 공고기관 | 마감 | 보증금")
tot=ok=0
for k in KEYS:
    t=json.loads(pathlib.Path(f"/tmp/opada-cmp/{k}.truth.json").read_text(encoding="utf-8"))
    u=json.loads(pathlib.Path(f"/tmp/opada-cmp/{k}.json").read_text(encoding="utf-8"))["url"] \
      if pathlib.Path(f"/tmp/opada-cmp/{k}.json").exists() else \
      json.loads(pathlib.Path("/tmp/opada-cmp/out.json").read_text(encoding="utf-8")).get("url") or \
      "https://www.onbid.co.kr/op/cltrpbancinf/cltrdtl/CltrDtlController/mvmnCltrDtl.do?onbidCltrno=1147301&pbctCdtnNo=6247576&onbidPbancNo=909691&pbctNo=10110341"
    p=norm(page(u))
    org=re.sub(r"^(재단법인|사회복지법인|주식회사|학교법인)\s*","",t["agency"] or "")
    dl=(t.get("bidDeadline") or "")[:10]; y,m,d=dl.split("-")
    dep=t["costs"].get("입찰보증금","")
    cells=[]
    for name,cands in [("재산유형",[t["assetType"]]),("공고기관",[t["agency"],org]),
                       ("마감",[dl,f"{y}.{m}.{d}",f"{y}-{m}-{d}",f"{y}{m}{d}"]),
                       ("보증금",[dep,dep.replace(" X ","X"),dep.replace(" X ","×")])]:
        hit=any(c and norm(c) in p for c in cands)
        cells.append("원문있음" if hit else "원문에서 못 찾음"); tot+=1; ok+=1 if hit else 0
    print(f"{k.split('_',1)[1]} | " + " | ".join(cells))
print(f"\n합계: {tot}개 중 {ok}개가 페이지 원문에 그대로 있습니다")
