import json, random
from pathlib import Path
from collections import Counter
OUT=Path("/tmp/opada-probe")
alive=json.loads((OUT/"alive.json").read_text(encoding="utf-8"))
gy=[c for c in alive if c.get("prptDivNm")=="국유재산" and c.get("dspsMthodNm")=="임대"]
print("국유재산 임대 마감유효 물건:", len(gy), "고유 공고:", len({str(c['onbidPbancNo']) for c in gy}))
print("마감일 분포:", Counter(str(c.get("cltrBidEndDt"))[:8] for c in gy).most_common(8))
done={r["url"] for f in ("m-a.json","m-b.json","m-c.json","m-d.json") for r in json.loads((OUT/f).read_text(encoding="utf-8"))}
def url(c):
    return ("https://www.onbid.co.kr/op/cltrpbancinf/cltrdtl/CltrDtlController/mvmnCltrDtl.do"
            f"?onbidCltrno={c['onbidCltrno']}&pbctCdtnNo={c['pbctCdtnNo']}"
            f"&onbidPbancNo={c['onbidPbancNo']}&pbctNo={c['pbctNo']}")
random.seed(777)
pool=[c for c in gy if url(c) not in done]
random.shuffle(pool)
targets=[{"group":"phase3","url":url(c),"noticeNm":"","cltrNm":c.get("onbidCltrNm"),
          "asset":"국유재산","disp":"임대","bidEnd":c.get("cltrBidEndDt"),
          "onbidPbancNo":str(c.get("onbidPbancNo")),"kws":[]} for c in pool[:16]]
(OUT/"targets3.json").write_text(json.dumps(targets,ensure_ascii=False,indent=1),encoding="utf-8")
print("추가 대상", len(targets))
