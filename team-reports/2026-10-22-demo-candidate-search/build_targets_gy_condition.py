import gzip, json, random
from pathlib import Path
from collections import defaultdict
SRC = Path("/Users/user/Documents/Dev/Hometest_op/team-reports/2026-10-22-demo-candidate-search")
cltrs = json.loads(gzip.open(SRC/"raw-cltr-list.json.gz").read()) + json.loads(gzip.open(SRC/"raw-cltr-wide.json.gz").read())
def url(c):
    return ("https://www.onbid.co.kr/op/cltrpbancinf/cltrdtl/CltrDtlController/mvmnCltrDtl.do"
            f"?onbidCltrno={c['onbidCltrno']}&pbctCdtnNo={c['pbctCdtnNo']}"
            f"&onbidPbancNo={c['onbidPbancNo']}&pbctNo={c['pbctNo']}")
alive = [c for c in cltrs if str(c.get("cltrBidEndDt") or "")>="202610230000"]
gy = [c for c in alive if c.get("prptDivNm")=="국유재산" and c.get("dspsMthodNm")=="임대"]
by_pb = defaultdict(list)
for c in gy: by_pb[str(c["onbidPbancNo"])].append(c)
print("국유재산 임대 고유 공고:", len(by_pb))
random.seed(5)
targets=[]
for pb, lst in by_pb.items():
    random.shuffle(lst)
    for c in lst[:2]:
        targets.append({"group":"국유재산","url":url(c),"cltrNm":c.get("onbidCltrNm"),
                        "asset":"국유재산","disp":"임대","bidEnd":c.get("cltrBidEndDt"),"onbidPbancNo":pb})
(SRC/"targets_gy.json").write_text(json.dumps(targets,ensure_ascii=False,indent=1),encoding="utf-8")
print("대상",len(targets))
