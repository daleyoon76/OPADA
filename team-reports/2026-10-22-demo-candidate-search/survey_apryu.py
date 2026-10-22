import gzip, json
from pathlib import Path
from collections import defaultdict
SRC = Path("/Users/user/Documents/Dev/Hometest_op/team-reports/2026-10-22-demo-candidate-search")
cltrs = json.loads(gzip.open(SRC/"raw-cltr-list.json.gz").read())
apryu = [c for c in cltrs if c.get("prptDivNm")=="압류재산"]
alive = [c for c in apryu if str(c.get("cltrBidEndDt") or "")>="202610230000"]
print("압류재산 전체", len(apryu), "마감유효", len(alive))
by_pb = defaultdict(list)
for c in alive: by_pb[str(c["onbidPbancNo"])].append(c)
print("고유 공고 수:", len(by_pb))
for pb, lst in sorted(by_pb.items(), key=lambda x:-len(x[1]))[:40]:
    print(" ", pb, len(lst), lst[0].get("onbidCltrNm","")[:40])
