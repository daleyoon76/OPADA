"""후보 물건을 build_notice 로 분석해 서류 단계별 건수를 집계한다.

- src/server.py 를 importlib 로 불러 쓴다. 라이브 서버(포트 18982)는 호출하지 않는다.
- 사용법: python3 -I measure.py <targets.json> <out.json> [시작index] [끝index] [워커수]
"""
import importlib.util, json, sys, time, threading, traceback
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
MIN_GAP = 1.2  # 온비드 요청 간격(초)


def throttle():
    with _gate:
        wait = MIN_GAP - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()


def measure(target):
    throttle()
    row = {k: target.get(k) for k in ("group", "url", "noticeNm", "cltrNm", "asset", "disp", "bidEnd", "onbidPbancNo", "kws")}
    t0 = time.time()
    try:
        notice = srv.build_notice(target["url"])
    except Exception as exc:
        row.update({"ok": False, "error": f"{type(exc).__name__}: {exc}", "elapsed": round(time.time() - t0, 1)})
        return row
    checklist = notice.get("docChecklist") or {}
    items = checklist.get("items") or []
    stages = [str(i.get("stage") or "") for i in items]
    reads = checklist.get("attachmentReads") or []
    row.update({
        "ok": True,
        "elapsed": round(time.time() - t0, 1),
        "title": notice.get("title"),
        "assetType": notice.get("assetType"),
        "dispositionLabel": notice.get("dispositionLabel"),
        "bidMethod": notice.get("bidMethod"),
        "bidPeriod": notice.get("bidPeriod"),
        "bidDeadline": notice.get("bidDeadline"),
        "agency": notice.get("agency"),
        "docTotal": len(items),
        "prebid": stages.count(PREBID),
        "postbid": stages.count(POSTBID),
        "unclassified": stages.count(UNCLASSIFIED),
        "needsInquiry": stages.count(NEEDS_INQUIRY),
        "prebidNames": [str(i.get("name")) for i in items if str(i.get("stage")) == PREBID],
        "docNames": [f"{i.get('name')}|{i.get('stage')}" for i in items],
        "checklistStatus": checklist.get("status"),
        "attachmentTotal": len(notice.get("relatedDocs") or []),
        "attachmentRead": sum(1 for r in reads if r.get("status") == "read"),
        "attachmentUnread": int(checklist.get("attachmentUnread") or 0),
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
                print(f"[{done[0]}/{len(todo)}] {mark} 전{row.get('prebid')} 후{row.get('postbid')} "
                      f"미{row.get('unclassified')} 문{row.get('needsInquiry')} 총{row.get('docTotal')} "
                      f"{row.get('elapsed')}s {(row.get('cltrNm') or '')[:28]}", flush=True)
    out_path.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print("저장:", out_path, len(rows), "건")


if __name__ == "__main__":
    main()
