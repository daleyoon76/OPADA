"""측정 결과(m-*.json)를 집계한다. 보고서의 모든 수치는 이 스크립트 출력에서 옮긴다."""
import json, glob, sys
from pathlib import Path
from collections import Counter, defaultdict

HERE = Path(__file__).resolve().parent
rows = []
for f in sorted(glob.glob(str(HERE / "m-*.json"))):
    rows.extend(json.loads(Path(f).read_text(encoding="utf-8")))

# 같은 URL 중복 제거
seen, uniq = set(), []
for r in rows:
    if r["url"] in seen:
        continue
    seen.add(r["url"])
    uniq.append(r)
rows = uniq
ok = [r for r in rows if r.get("ok")]

print(f"분석 물건 총 {len(rows)}건 · 성공 {len(ok)}건 · 실패 {len(rows)-len(ok)}건")
print(f"고유 공고 {len({r['onbidPbancNo'] for r in ok})}개")

hit = [r for r in ok if r["prebid"] >= 2 and r["unclassified"] == 0 and r["needsInquiry"] == 0]
print(f"\n조건 만족(입찰 전 2건 이상 · 미분류 0 · 별도 문의 0): {len(hit)}건")
print(f"  그중 마감 2026-10-23 이후: {sum(1 for r in hit if str(r['bidEnd'] or '') >= '202610230000')}건")
print(f"  조건 만족 물건의 고유 공고: {sorted({r['onbidPbancNo'] for r in hit})}")

print("\n[입찰 전 2건 이상인 물건 전체]")
for r in sorted((r for r in ok if r["prebid"] >= 2), key=lambda x: (-x["prebid"], x["unclassified"])):
    pass_mark = "만족" if (r["unclassified"] == 0 and r["needsInquiry"] == 0) else f"탈락(미분류{r['unclassified']}·문의{r['needsInquiry']})"
    print(f"  전{r['prebid']:>2} 후{r['postbid']:>2} 미{r['unclassified']:>2} 총{r['docTotal']:>2} "
          f"[{r['assetType']}/{r['dispositionLabel']}] {pass_mark} 공고{r['onbidPbancNo']} {(r['cltrNm'] or '')[:34]}")

print("\n[재산유형 × 처분방식별 집계]")
g = defaultdict(list)
for r in ok:
    g[(r["assetType"] or "?", r["dispositionLabel"] or "?")].append(r)
print(f"{'재산유형/처분방식':<24} {'건수':>4} {'공고':>4} {'전평균':>6} {'후평균':>6} {'미평균':>6} {'전>=2':>6} {'조건만족':>7}")
for k, v in sorted(g.items(), key=lambda x: -sum(r["prebid"] for r in x[1]) / len(x[1])):
    n = len(v)
    pb = len({r["onbidPbancNo"] for r in v})
    print(f"{k[0]+'/'+k[1]:<24} {n:>4} {pb:>4} {sum(r['prebid'] for r in v)/n:>6.1f} "
          f"{sum(r['postbid'] for r in v)/n:>6.1f} {sum(r['unclassified'] for r in v)/n:>6.1f} "
          f"{sum(1 for r in v if r['prebid']>=2):>6} "
          f"{sum(1 for r in v if r['prebid']>=2 and r['unclassified']==0 and r['needsInquiry']==0):>7}")

print("\n[첨부 공고문 읽기 결과]")
print(f"  첨부가 있던 물건: {sum(1 for r in ok if r['attachmentTotal'] > 0)}건")
print(f"  첨부 총 {sum(r['attachmentTotal'] for r in ok)}건 · 읽음 {sum(r['attachmentRead'] for r in ok)}건 "
      f"· 못 읽음 {sum(r['attachmentUnread'] for r in ok)}건")
print(f"  못 읽은 첨부가 1건 이상인 물건: {sum(1 for r in ok if r['attachmentUnread'] > 0)}건")

print("\n[서류 0건 물건]")
print(f"  서류 총건수 0: {sum(1 for r in ok if r['docTotal']==0)}건")

if hit:
    print("\n[조건 만족 물건 상세]")
    for r in sorted(hit, key=lambda x: str(x["bidEnd"] or "")):
        uniq_names = sorted(set(r["prebidNames"]))
        print(f"  - {r['cltrNm']}")
        print(f"    공고 {r['onbidPbancNo']} · {r['assetType']}/{r['dispositionLabel']} · 마감 {r['bidDeadline']}")
        print(f"    입찰 전 {r['prebid']}건(고유 {len(uniq_names)}종) / 낙찰 후 {r['postbid']}건 / 미분류 0")
        print(f"    첨부 {r['attachmentTotal']}건 중 읽음 {r['attachmentRead']} · 못 읽음 {r['attachmentUnread']}")
        print(f"    고유 입찰 전 서류: {', '.join(uniq_names)}")
        print(f"    {r['url']}")
