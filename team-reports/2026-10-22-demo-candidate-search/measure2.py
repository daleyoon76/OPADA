"""measure.py 확장판 — 조건별(대리입찰·공동입찰·미성년자) 입찰 전 서류 수를 함께 센다.

- src/server.py 를 importlib 로 불러 쓴다(읽기만). 라이브 서버는 호출하지 않는다.
- 사용법: python3 -I measure2.py <targets.json> <out.json> [시작index] [끝index] [워커수]
"""
import importlib.util, json, sys, time, threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("opada_server", ROOT / "src" / "server.py")
srv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(srv)

PREBID = "입찰 전"
POSTBID = "낙찰 후·계약 시"
UNCLASSIFIED = "미분류"
NEEDS_INQUIRY = "별도 문의 필요"

_lock = threading.Lock()
_gate = threading.Lock()
_last = [0.0]
MIN_GAP = 1.2


def throttle():
    with _gate:
        wait = MIN_GAP - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()


def measure(target):
    throttle()
    row = {k: target.get(k) for k in ("group", "url", "cltrNm", "asset", "disp", "bidEnd", "onbidPbancNo")}
    t0 = time.time()
    try:
        notice = srv.build_notice(target["url"])
    except Exception as exc:
        row.update({"ok": False, "error": f"{type(exc).__name__}: {exc}", "elapsed": round(time.time() - t0, 1)})
        return row
    checklist = notice.get("docChecklist") or {}
    items = checklist.get("items") or []

    def is_prebid(i):
        return str(i.get("stage") or "") == PREBID

    prebid_items = [i for i in items if is_prebid(i)]
    no_cond = [i for i in prebid_items if not i.get("conditions")]
    proxy = [i for i in prebid_items if "대리입찰" in (i.get("conditions") or [])]
    joint = [i for i in prebid_items if "공동입찰" in (i.get("conditions") or [])]
    minor = [i for i in prebid_items if "미성년자" in (i.get("conditions") or [])]
    sot_fallback = [i for i in prebid_items if "준수규칙" in str(i.get("sourceHeading") or "")]

    stages = [str(i.get("stage") or "") for i in items]
    row.update({
        "ok": True,
        "elapsed": round(time.time() - t0, 1),
        "title": notice.get("title"),
        "assetType": notice.get("assetType"),
        "dispositionLabel": notice.get("dispositionLabel"),
        "bidDeadline": notice.get("bidDeadline"),
        "docTotal": len(items),
        "prebidTotal": len(prebid_items),
        "prebidNoCondition": len(no_cond),
        "prebidProxy": len(proxy),
        "prebidJoint": len(joint),
        "prebidMinor": len(minor),
        "prebidViaSotFallback": len(sot_fallback),
        "sotFallbackNames": sorted({i["name"] for i in sot_fallback}),
        "postbid": stages.count(POSTBID),
        "unclassified": stages.count(UNCLASSIFIED),
        "needsInquiry": stages.count(NEEDS_INQUIRY),
        "noConditionNames": sorted({i["name"] for i in no_cond}),
        "proxyNames": sorted({i["name"] for i in proxy}),
        "jointNames": sorted({i["name"] for i in joint}),
        "minorNames": sorted({i["name"] for i in minor}),
        "allItemDump": [
            {"name": i.get("name"), "stage": i.get("stage"), "conditions": i.get("conditions"),
             "sourceHeading": i.get("sourceHeading")}
            for i in items
        ],
    })
    return row


def main():
    targets = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out_path = Path(sys.argv[2])
    start = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    end = int(sys.argv[4]) if len(sys.argv) > 4 else len(targets)
    workers = int(sys.argv[5]) if len(sys.argv) > 5 else 3
    todo = targets[start:end]
    rows = []
    done = [0]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for row in pool.map(measure, todo):
            with _lock:
                rows.append(row)
                done[0] += 1
                mark = "ok" if row.get("ok") else "ERR"
                print(f"[{done[0]}/{len(todo)}] {mark} 전체전{row.get('prebidTotal')}"
                      f"(기본{row.get('prebidNoCondition')}/대리{row.get('prebidProxy')}"
                      f"/공동{row.get('prebidJoint')}/미성년{row.get('prebidMinor')}) "
                      f"후{row.get('postbid')} 미{row.get('unclassified')} "
                      f"{row.get('elapsed')}s {(row.get('cltrNm') or '')[:30]}", flush=True)
    out_path.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print("저장:", out_path, len(rows), "건")


if __name__ == "__main__":
    main()
