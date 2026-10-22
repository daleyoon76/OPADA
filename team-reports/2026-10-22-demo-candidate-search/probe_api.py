"""공공데이터 온비드 API 응답 구조를 확인한다. src/server.py 를 모듈로 불러 쓴다(읽기만)."""
import importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("opada_server", ROOT / "src" / "server.py")
srv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(srv)

key = srv.public_data_service_key()
print("service key 설정됨:", bool(key), "길이:", len(key))

res = srv.call_public_data("notice_list", {"numOfRows": "3", "pageNo": "1"}, key)
print("notice_list ok:", res["ok"], "status:", res["status"], "code:", res["resultCode"], res["resultMsg"])
if res["items"]:
    print(json.dumps(res["items"][0], ensure_ascii=False, indent=1)[:2000])
else:
    print("raw:", res["rawText"][:600])
