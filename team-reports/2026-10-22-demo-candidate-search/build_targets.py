import json, random
from pathlib import Path
from collections import Counter, defaultdict
OUT = Path("/tmp/opada-probe")
hits = json.loads((OUT/"hits.json").read_text(encoding="utf-8"))
alive = json.loads((OUT/"alive.json").read_text(encoding="utf-8"))

def url(c):
    return ("https://www.onbid.co.kr/op/cltrpbancinf/cltrdtl/CltrDtlController/mvmnCltrDtl.do"
            f"?onbidCltrno={c['onbidCltrno']}&pbctCdtnNo={c['pbctCdtnNo']}"
            f"&onbidPbancNo={c['onbidPbancNo']}&pbctNo={c['pbctNo']}")

# 키워드군: 공고 단위로 1건만
by_notice = {}
for h in hits:
    pb = str(h["cltr"]["onbidPbancNo"])
    if pb not in by_notice: by_notice[pb] = h
print("키워드 적중 공고 수:", len(by_notice))

random.seed(20261022)
targets = []
for pb, h in by_notice.items():
    c = h["cltr"]
    targets.append({"group":"keyword","url":url(c),"noticeNm":h["noticeNm"],"cltrNm":c.get("onbidCltrNm"),
                    "asset":c.get("prptDivNm"),"disp":c.get("dspsMthodNm"),"bidEnd":c.get("cltrBidEndDt"),
                    "onbidPbancNo":pb,"kws":h["kws"]})

# 대조군: 재산유형×처분방식별 3건
buckets = defaultdict(list)
kwurls = {t["url"] for t in targets}
for c in alive:
    buckets[(c.get("prptDivNm"), c.get("dspsMthodNm"))].append(c)
for k, lst in buckets.items():
    random.shuffle(lst)
    picked = 0
    for c in lst:
        u = url(c)
        if u in kwurls: continue
        targets.append({"group":"control","url":u,"noticeNm":"","cltrNm":c.get("onbidCltrNm"),
                        "asset":c.get("prptDivNm"),"disp":c.get("dspsMthodNm"),"bidEnd":c.get("cltrBidEndDt"),
                        "onbidPbancNo":str(c.get("onbidPbancNo")),"kws":[]})
        picked += 1
        if picked >= 3: break

print("분석 대상 총:", len(targets), Counter(t["group"] for t in targets))
print("재산유형 분포:", Counter((t["asset"],t["disp"]) for t in targets).most_common())
(OUT/"targets.json").write_text(json.dumps(targets, ensure_ascii=False, indent=1), encoding="utf-8")
