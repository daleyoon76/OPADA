import gzip, json, random
from pathlib import Path
from collections import defaultdict
SRC = Path("/Users/user/Documents/Dev/Hometest_op/team-reports/2026-10-22-demo-candidate-search")
cltrs = json.loads(gzip.open(SRC/"raw-cltr-list.json.gz").read())
wide = json.loads(gzip.open(SRC/"raw-cltr-wide.json.gz").read())
all_c = cltrs + wide

def url(c):
    return ("https://www.onbid.co.kr/op/cltrpbancinf/cltrdtl/CltrDtlController/mvmnCltrDtl.do"
            f"?onbidCltrno={c['onbidCltrno']}&pbctCdtnNo={c['pbctCdtnNo']}"
            f"&onbidPbancNo={c['onbidPbancNo']}&pbctNo={c['pbctNo']}")

alive = [c for c in all_c if str(c.get("cltrBidEndDt") or "")>="202610230000"]
random.seed(20261022)

targets=[]

# 압류재산: 공고 10개 전부에서 각 3건
apryu_by_pb = defaultdict(list)
for c in alive:
    if c.get("prptDivNm")=="압류재산": apryu_by_pb[str(c["onbidPbancNo"])].append(c)
for pb, lst in apryu_by_pb.items():
    random.shuffle(lst)
    for c in lst[:3]:
        targets.append({"group":"압류재산","url":url(c),"cltrNm":c.get("onbidCltrNm"),
                        "asset":"압류재산","disp":"매각","bidEnd":c.get("cltrBidEndDt"),
                        "onbidPbancNo":pb})
print("압류재산 대상:", sum(1 for t in targets if t["group"]=="압류재산"), "/ 공고", len(apryu_by_pb))

# 수탁재산: pvctTrgtYn 다른 값/물건목록 자체에 없으면 공고목록에서라도 식별자 확보 시도 (아래 별도 점검)

# 공유재산 매각/기타일반재산: 기존 4건 외 소수 추가(각 3건, 서로 다른 공고)
for asset in ("공유재산","기타일반재산"):
    by_pb = defaultdict(list)
    for c in alive:
        if c.get("prptDivNm")==asset and c.get("dspsMthodNm") in ("매각",): by_pb[str(c["onbidPbancNo"])].append(c)
    pbs = list(by_pb.keys()); random.shuffle(pbs)
    n=0
    for pb in pbs:
        c = by_pb[pb][0]
        targets.append({"group":asset,"url":url(c),"cltrNm":c.get("onbidCltrNm"),
                        "asset":asset,"disp":c.get("dspsMthodNm"),"bidEnd":c.get("cltrBidEndDt"),
                        "onbidPbancNo":pb})
        n+=1
        if n>=3: break
    print(asset,"대상 추가:",n)

(SRC/"targets_cond.json").write_text(json.dumps(targets,ensure_ascii=False,indent=1),encoding="utf-8")
print("총 대상:", len(targets))
