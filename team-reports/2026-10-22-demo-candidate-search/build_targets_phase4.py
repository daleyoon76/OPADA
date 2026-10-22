import json
from pathlib import Path
from collections import defaultdict
OUT=Path("/tmp/opada-probe")
got=json.loads((OUT/"raw-cltr-wide.json").read_text(encoding="utf-8"))
alive=[c for c in got if str(c.get("cltrBidEndDt") or "")>="202610230000"]
done_pb={r["onbidPbancNo"] for f in ("m-a.json","m-b.json","m-c.json","m-d.json","m-e.json") for r in json.loads((OUT/f).read_text(encoding="utf-8"))}
def url(c):
    return ("https://www.onbid.co.kr/op/cltrpbancinf/cltrdtl/CltrDtlController/mvmnCltrDtl.do"
            f"?onbidCltrno={c['onbidCltrno']}&pbctCdtnNo={c['pbctCdtnNo']}"
            f"&onbidPbancNo={c['onbidPbancNo']}&pbctNo={c['pbctNo']}")
by_pb=defaultdict(list)
for c in alive: by_pb[(c.get("prptDivNm"),c.get("dspsMthodNm"),str(c["onbidPbancNo"]))].append(c)
targets=[]
quota={"국유재산":4,"기타일반재산":12}
cnt=defaultdict(int)
for (asset,disp,pb),lst in sorted(by_pb.items(), key=lambda x:-len(x[1])):
    if pb in done_pb: continue
    if cnt[asset]>=quota.get(asset,0): continue
    c=lst[0]
    targets.append({"group":"phase4","url":url(c),"noticeNm":"","cltrNm":c.get("onbidCltrNm"),
                    "asset":asset,"disp":disp,"bidEnd":c.get("cltrBidEndDt"),"onbidPbancNo":pb,"kws":[]})
    cnt[asset]+=1
(OUT/"targets4.json").write_text(json.dumps(targets,ensure_ascii=False,indent=1),encoding="utf-8")
print("추가 대상",len(targets),dict(cnt))
