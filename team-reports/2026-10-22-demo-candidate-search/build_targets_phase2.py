import json, random
from pathlib import Path
from collections import defaultdict
OUT=Path("/tmp/opada-probe")
alive=json.loads((OUT/"alive.json").read_text(encoding="utf-8"))
done={r["url"] for f in ("m-a.json","m-b.json","m-c.json") for r in json.loads((OUT/f).read_text(encoding="utf-8"))}
def url(c):
    return ("https://www.onbid.co.kr/op/cltrpbancinf/cltrdtl/CltrDtlController/mvmnCltrDtl.do"
            f"?onbidCltrno={c['onbidCltrno']}&pbctCdtnNo={c['pbctCdtnNo']}"
            f"&onbidPbancNo={c['onbidPbancNo']}&pbctNo={c['pbctNo']}")
QUOTA={("국유재산","임대"):18,("압류재산","매각"):8,("공유재산","매각"):5,("기타일반재산","매각"):5}
buckets=defaultdict(list)
for c in alive: buckets[(c.get("prptDivNm"),c.get("dspsMthodNm"))].append(c)
random.seed(1022)
targets=[]
for k,q in QUOTA.items():
    lst=buckets[k][:]; random.shuffle(lst); n=0
    # 공고가 겹치지 않게 고른다
    seen_pb=set()
    for c in lst:
        u=url(c)
        if u in done: continue
        pb=str(c.get("onbidPbancNo"))
        if pb in seen_pb: continue
        seen_pb.add(pb)
        targets.append({"group":"phase2","url":u,"noticeNm":"","cltrNm":c.get("onbidCltrNm"),
                        "asset":k[0],"disp":k[1],"bidEnd":c.get("cltrBidEndDt"),"onbidPbancNo":pb,"kws":[]})
        n+=1
        if n>=q: break
    print(k,"추가",n)
(OUT/"targets2.json").write_text(json.dumps(targets,ensure_ascii=False,indent=1),encoding="utf-8")
print("추가 대상 총",len(targets))
