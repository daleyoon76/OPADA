import importlib.util, json, time
from pathlib import Path
from collections import Counter
ROOT=Path("/Users/user/Documents/Dev/Hometest_op")
spec=importlib.util.spec_from_file_location("opada_server", ROOT/"src"/"server.py")
srv=importlib.util.module_from_spec(spec); spec.loader.exec_module(srv)
key=srv.public_data_service_key()
got=[]
for code in ("0010","0008","0005"):
    for pv in ("N","Y"):
        for page in range(1,7):
            r=srv.call_public_data("real_estate_list",{"prptDivCd":code,"pvctTrgtYn":pv,"numOfRows":"200","pageNo":str(page)},key)
            got.extend(r["items"])
            print(code,pv,page,len(r["items"]),flush=True)
            time.sleep(0.5)
            if len(r["items"])<200: break
Path("/tmp/opada-probe/raw-cltr-wide.json").write_text(json.dumps(got,ensure_ascii=False),encoding="utf-8")
alive=[c for c in got if str(c.get("cltrBidEndDt") or "")>="202610230000"]
print("수집",len(got),"마감유효",len(alive))
print("공고별:", Counter((c.get("prptDivNm"),c.get("dspsMthodNm"),str(c["onbidPbancNo"])) for c in alive).most_common(20))
