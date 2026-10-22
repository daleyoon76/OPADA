import json, re
from pathlib import Path
from collections import Counter
OUT = Path("/tmp/opada-probe")
cltrs = json.loads((OUT/"raw-cltr-list.json").read_text(encoding="utf-8"))
notices = json.loads((OUT/"raw-notice-list.json").read_text(encoding="utf-8"))

# 중복 제거
seen=set(); uniq=[]
for c in cltrs:
    k=(c.get("onbidCltrno"), c.get("pbctCdtnNo"))
    if k in seen: continue
    seen.add(k); uniq.append(c)
print("물건 고유", len(uniq))

nmap={}
for n in notices:
    nmap.setdefault(str(n.get("onbidPbancNo")), n)
print("공고 고유", len(nmap))

DEADLINE_MIN = "202610230000"
alive=[c for c in uniq if str(c.get("cltrBidEndDt") or "") >= DEADLINE_MIN]
print("마감 2026-10-23 이후", len(alive))

KW = ["제안","운영자","위탁","입주","공모","사업자","모집","선정","평가","수탁","민간","창업","매점","카페","자판기","식당","운영"]
def notice_name(c):
    n = nmap.get(str(c.get("onbidPbancNo")))
    return (n or {}).get("onbidPbancNm") or ""

hits=[]
for c in alive:
    nn = notice_name(c)
    blob = nn + " " + (c.get("onbidCltrNm") or "")
    kws=[k for k in KW if k in blob]
    if kws: hits.append((c, nn, kws))
print("키워드 적중", len(hits))
print("\n재산유형×처분방식 분포 (마감 유효 물건):")
for k,v in Counter((c.get("prptDivNm"), c.get("dspsMthodNm")) for c in alive).most_common():
    print(" ", k, v)
print("\n키워드별 건수:")
for k,v in Counter(kw for _,_,kws in hits for kw in kws).most_common():
    print(" ", k, v)
print("\n적중 상위 25건(공고명):")
for c,nn,kws in sorted(hits, key=lambda x: -len(x[2]))[:25]:
    print(f"  [{c.get('prptDivNm')}/{c.get('dspsMthodNm')}] {nn[:70]} || {(c.get('onbidCltrNm') or '')[:40]} || {kws}")
json.dump([{"cltr":c,"noticeNm":nn,"kws":kws} for c,nn,kws in hits], open(OUT/"hits.json","w"), ensure_ascii=False)
json.dump(alive, open(OUT/"alive.json","w"), ensure_ascii=False)
