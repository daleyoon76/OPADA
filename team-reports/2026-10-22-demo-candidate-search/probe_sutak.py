import importlib.util, json
from pathlib import Path
ROOT = Path("/Users/user/Documents/Dev/Hometest_op")
spec = importlib.util.spec_from_file_location("opada_server", ROOT / "src" / "server.py")
srv = importlib.util.module_from_spec(spec); spec.loader.exec_module(srv)
u = "https://www.onbid.co.kr/op/cltrpbancinf/pbanc/pbancdtlinf/PbancDtlInqController/mvmnPbancDtl.do?onbidPbancNo=908297&pbctNo=10107437"
n = srv.build_notice(u)
items = n["docChecklist"]["items"]
stages=[i["stage"] for i in items]
pre=[i for i in items if i["stage"]=="입찰 전"]
no_cond=[i for i in pre if i["conditions"]==["공통"]]
proxy=[i for i in pre if "대리입찰" in i["conditions"]]
joint=[i for i in pre if "공동입찰" in i["conditions"]]
out={
  "url": u, "title": n["title"], "pageType": n["pageType"], "bidDeadline": n["bidDeadline"],
  "docTotal": len(items), "prebid": len(pre), "noCond": len(no_cond), "proxy": len(proxy), "joint": len(joint),
  "postbid": stages.count("낙찰 후·계약 시"), "unclassified": stages.count("미분류"), "needsInquiry": stages.count("별도 문의 필요"),
  "items": [{"name":i["name"],"stage":i["stage"],"conditions":i["conditions"],"sourceHeading":i.get("sourceHeading")} for i in items],
}
Path("/Users/user/Documents/Dev/Hometest_op/team-reports/2026-10-22-demo-candidate-search/m-cond-sutak.json").write_text(
    json.dumps([out], ensure_ascii=False, indent=1), encoding="utf-8")
print("기본",len(no_cond),"대리",len(proxy),"공동",len(joint),"전체전",len(pre),"후",stages.count("낙찰 후·계약 시"),"미",stages.count("미분류"))
