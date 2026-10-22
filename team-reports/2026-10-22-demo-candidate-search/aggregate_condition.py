"""m-cond-*.json 을 조건별(기본·대리입찰·공동입찰·미성년자)로 재집계한다.

주의: item["conditions"] 는 조건이 없으면 빈 리스트가 아니라 ["공통"] 으로 채워진다
(src/server.py:1312 `labels = [...] or ["공통"]`). "기본(무조건)" 을 셀 때는
`conditions == ["공통"]` 으로 판정해야 한다. 빈 리스트로 판정하면 전부 0으로 잘못 센다.
"""
import json
from pathlib import Path
from collections import defaultdict

HERE = Path(__file__).resolve().parent
PREBID = "입찰 전"


def recount(r):
    items = r["allItemDump"]
    prebid = [i for i in items if i["stage"] == PREBID]
    no_cond = [i for i in prebid if i["conditions"] == ["공통"]]
    proxy = [i for i in prebid if "대리입찰" in i["conditions"]]
    joint = [i for i in prebid if "공동입찰" in i["conditions"]]
    minor = [i for i in prebid if "미성년자" in i["conditions"]]
    other = [
        i for i in prebid
        if i["conditions"] != ["공통"] and not set(i["conditions"]) & {"대리입찰", "공동입찰", "미성년자"}
    ]
    return {
        "total": len(prebid), "no_cond": len(no_cond), "proxy": len(proxy),
        "joint": len(joint), "minor": len(minor), "other": len(other),
        "otherNames": sorted({i["name"] for i in other}),
        "postbid": r["postbid"], "unclassified": r["unclassified"], "pb": r["onbidPbancNo"],
    }


def main():
    rows = []
    for f in ("m-cond-1.json", "m-cond-gy.json"):
        rows.extend(json.loads((HERE / f).read_text(encoding="utf-8")))

    g = defaultdict(list)
    for r in rows:
        g[r["group"]].append(recount(r))

    print(f"{'유형':<10}{'n':>4}{'공고수':>6}  {'기본':>6}{'대리':>6}{'공동':>6}{'미성년':>6}{'낙찰후':>6}{'미분류':>6}")
    for grp, lst in g.items():
        n = len(lst)
        def avg(k):
            return sum(x[k] for x in lst) / n
        def rng(k):
            return (min(x[k] for x in lst), max(x[k] for x in lst))
        pbs = sorted(set(x["pb"] for x in lst))
        print(f"{grp:<10}{n:>4}{len(pbs):>6}  {avg('no_cond'):>6.1f}{avg('proxy'):>6.1f}"
              f"{avg('joint'):>6.1f}{avg('minor'):>6.1f}{avg('postbid'):>6.1f}{avg('unclassified'):>6.1f}")
        print(f"    범위: 기본{rng('no_cond')} 대리{rng('proxy')} 공동{rng('joint')} "
              f"미성년{rng('minor')} 미분류{rng('unclassified')} | 공고={pbs}")


if __name__ == "__main__":
    main()
