"""물건 목록·공고 목록을 재산유형별로 수집해 후보 풀을 만든다."""
import importlib.util, time, json
from pathlib import Path
ROOT = Path("/Users/user/Documents/Dev/Hometest_op")
spec = importlib.util.spec_from_file_location("opada_server", ROOT / "src" / "server.py")
srv = importlib.util.module_from_spec(spec); spec.loader.exec_module(srv)
key = srv.public_data_service_key()
OUT = Path("/tmp/opada-probe")

ASSET_CODES = {"0002":"공유재산","0003":"금융권담보재산","0004":"불용품","0005":"기타일반재산","0007":"압류재산","0008":"수탁재산","0010":"국유재산"}

cltrs, notices = [], []
for code, nm in ASSET_CODES.items():
    for pv in ("N","Y"):
        for page in (1,2):
            r = srv.call_public_data("real_estate_list", {"prptDivCd":code,"pvctTrgtYn":pv,"numOfRows":"200","pageNo":str(page)}, key)
            got = r["items"]
            cltrs.extend(got)
            print(f"물건목록 {nm} pv={pv} p{page}: {len(got)}건 code={r['resultCode']}", flush=True)
            time.sleep(0.6)
            if len(got) < 200: break
    for page in (1,2):
        r = srv.call_public_data("notice_list", {"prptDivCd":code,"opbdDtStart":"20261020","opbdDtEnd":"20270630","numOfRows":"200","pageNo":str(page)}, key)
        got = r["items"]
        notices.extend(got)
        print(f"공고목록 {nm} p{page}: {len(got)}건 code={r['resultCode']}", flush=True)
        time.sleep(0.6)
        if len(got) < 200: break

(OUT/"raw-cltr-list.json").write_text(json.dumps(cltrs, ensure_ascii=False), encoding="utf-8")
(OUT/"raw-notice-list.json").write_text(json.dumps(notices, ensure_ascii=False), encoding="utf-8")
print("총 물건", len(cltrs), "총 공고", len(notices))
