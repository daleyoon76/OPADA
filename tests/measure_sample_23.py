"""표본 23건 저장 HTML에 추출기를 실제로 돌려 성공률을 재는 계측 스크립트.

수치를 만드는 도구이지 통과/실패를 판정하는 게이트가 아니다. 게이트는
`tests/test_docs_extraction.py` 다.

원자료는 레포에 없다(총 14MB). 2026-09-07 표본조사가 `/tmp/onbid-survey/html/` 에
`pbanc_01.html` ~ `pbanc_23.html` 로 저장했고, 다른 위치면 환경변수로 준다.

    ONBID_SAMPLE_HTML_DIR=/path/to/html python3 tests/measure_sample_23.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import server  # noqa: E402

SAMPLE_DIR = Path(os.environ.get("ONBID_SAMPLE_HTML_DIR", "/tmp/onbid-survey/html"))
SAMPLE_TOTAL = 23

# 재산유형은 표본조사가 목록 API에서 받아 `samples.json` 에 남긴 `prptDvsnNm` 이 정본이다.
# 공고상세 HTML에는 `scrnCltrPrptDivNm` 이 없어 페이지에서 다시 읽을 수 없다.
# 아래 표는 그 파일이 없을 때 쓰는 사본이며, 2026-09-08 실측으로 23/23 일치를 확인했다.
SAMPLE_ASSET_TYPE = {
    1: "압류재산", 2: "압류재산", 3: "압류재산",
    4: "국유재산", 5: "국유재산", 6: "국유재산", 7: "국유재산", 8: "국유재산",
    9: "공유재산", 10: "공유재산", 11: "공유재산", 12: "공유재산", 13: "공유재산", 14: "공유재산",
    15: "기타일반재산", 16: "기타일반재산", 17: "기타일반재산",
    18: "파산자산", 19: "파산자산",
    20: "기타일반재산", 21: "기타일반재산", 22: "기타일반재산", 23: "기타일반재산",
}
# 표본조사 §2 원문의 유형 배분: 압류 3 · 국유 5 · 공유 6 · 기타일반 6 · 파산 2 · 수탁 1.
SAMPLE_ASSET_TYPE[20] = "수탁재산"


def load_asset_types() -> tuple[dict[int, str], str]:
    """`samples.json` 이 있으면 그 값을 쓰고, 없으면 사본 표를 쓴다."""
    path = SAMPLE_DIR.parent / "samples.json"
    if not path.exists():
        return SAMPLE_ASSET_TYPE, "사본 표(samples.json 없음)"
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return SAMPLE_ASSET_TYPE, "사본 표(samples.json 읽기 실패)"
    observed = {int(row["idx"]): str(row["prptDvsnNm"]) for row in rows if row.get("prptDvsnNm")}
    if not observed:
        return SAMPLE_ASSET_TYPE, "사본 표(prptDvsnNm 없음)"
    mismatch = [idx for idx, value in observed.items() if SAMPLE_ASSET_TYPE.get(idx) != value]
    note = "samples.json 관측값" + (f" · 사본 표와 불일치 {len(mismatch)}건: {mismatch}" if mismatch else " · 사본 표와 일치")
    return observed, note


FAKE_NOTICE_URL = "https://www.onbid.co.kr/op/ppa/pbcpubannc/publicAnnounceDetail.do"


def notice_joint_allowed(html: str) -> str:
    """`build_notice` 를 오프라인으로 불러 조립된 `jointBidAllowed` 를 읽는다.

    표본 축은 여태 `bid_method_flag()` 를 직접 불러 재서, 호출부가 그 값을 실제로
    싣는지는 아무도 보지 않았다. 네트워크 두 곳만 대신 연기해 호출부를 지나게 한다.
    """
    saved_fetch, saved_key = server.fetch_onbid, server.public_data_service_key
    server.fetch_onbid = lambda raw_url: (FAKE_NOTICE_URL, html)
    server.public_data_service_key = lambda: ""
    try:
        return str(server.build_notice(FAKE_NOTICE_URL).get("jointBidAllowed") or "")
    finally:
        server.fetch_onbid, server.public_data_service_key = saved_fetch, saved_key


def main() -> int:
    if not SAMPLE_DIR.is_dir():
        print(f"표본 HTML 디렉터리가 없습니다: {SAMPLE_DIR}")
        print("ONBID_SAMPLE_HTML_DIR 로 경로를 지정하십시오. 측정을 건너뜁니다.")
        return 2

    asset_types, asset_note = load_asset_types()
    print(f"재산유형 출처: {asset_note}")
    by_profile: dict[str, list[int]] = {}
    rows = []
    for index in range(1, SAMPLE_TOTAL + 1):
        path = SAMPLE_DIR / f"pbanc_{index:02d}.html"
        if not path.exists():
            print(f"없음: {path}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        sections = server.split_sections(text)
        asset_type = asset_types[index]
        attachments = server.extract_related_docs(text)
        checklist = server.build_doc_checklist(sections, asset_type, attachments)
        items = checklist["items"]
        profile = checklist["profile"]["code"]
        by_profile.setdefault(profile, []).append(1 if items else 0)
        rows.append(
            {
                "idx": index,
                "asset": asset_type,
                "profile": profile,
                "docs": len(items),
                "names": sorted({str(item["name"]) for item in items}),
                "conditions": sorted({label for item in items for label in item["conditions"]}),
                "attachments": len(attachments),
                "downloadable": sum(1 for att in attachments if att["downloadUrl"]),
                "status": checklist["status"],
                # 조건 축 `joint` 의 두 근거를 나란히 잰다. 합산식은 server.py 의
                # `has_doc_condition or joint_allowed == "가능"` 과 같은 모양이다.
                "docJoint": any("joint" in item["conditionKeys"] for item in items),
                "screenJoint": server.bid_method_flag(sections, "공동입찰"),
                # 호출부 배선 — `build_notice` 가 조립해 내보내는 값. 위 순수 함수 값과
                # 갈리면 배선이 끊겼거나 다른 라벨(`대리입찰`)을 싣고 있다는 뜻이다.
                "noticeJoint": notice_joint_allowed(text),
                "proxyFlag": server.bid_method_flag(sections, "대리입찰"),
                "eviction": server.eviction_responsibility(sections),
            }
        )

    print(f"{'#':>3} {'재산유형':<8} {'형':<3} {'서류':>4} {'첨부':>4} {'링크':>4}  상태")
    for row in rows:
        print(
            f"{row['idx']:>3} {row['asset']:<8} {row['profile']:<3} {row['docs']:>4} "
            f"{row['attachments']:>4} {row['downloadable']:>4}  {row['status']}"
        )
        if row["names"]:
            print(f"      서류: {', '.join(row['names'])}")
            print(f"      조건: {', '.join(row['conditions'])}")

    total = len(rows)
    ok = sum(1 for row in rows if row["docs"])
    # 표본이 일부만 있으면 분모가 조용히 줄어 헤드라인이 「3/3 = 100%」로 읽힌다.
    # 위쪽 「없음:」 줄은 스크롤로 밀리므로 헤드라인 자체에 부분 측정임을 박고 비정상 종료한다.
    partial = "" if total == SAMPLE_TOTAL else f"  ⚠️ 부분 측정 — 표본 {total}/{SAMPLE_TOTAL}만 존재"
    print()
    print(f"구체 서류명 1건 이상 추출: {ok}/{total}{partial}")
    for profile in sorted(by_profile):
        hits = by_profile[profile]
        print(f"  {profile}형: {sum(hits)}/{len(hits)}")
    att_total = sum(row["attachments"] for row in rows)
    att_link = sum(row["downloadable"] for row in rows)
    with_att = sum(1 for row in rows if row["attachments"])
    print(f"첨부 다운로드 파라미터: {att_link}/{att_total} (첨부가 있는 공고 {with_att}건)")

    # 조건 축 `joint` — 서류 근거 / 화면 값 / 합산. 반대 방향 불일치는 「기존 켜짐을 끄는가」다.
    doc_joint = [row["idx"] for row in rows if row["docJoint"]]
    screen_joint = [row["idx"] for row in rows if row["screenJoint"] == "가능"]
    union = sorted(set(doc_joint) | set(screen_joint))
    reverse = [idx for idx in doc_joint if idx not in screen_joint]
    print(f"joint 서류 근거: {len(doc_joint)}/{total} {doc_joint}")
    print(f"joint 화면 값 「가능」: {len(screen_joint)}/{total} {screen_joint}")
    print(f"joint 합산(현행 판정): {len(union)}/{total} · 증분 {sorted(set(union) - set(doc_joint))}")
    print(f"joint 반대 방향(서류 켜짐 · 화면 「불가능」): {len(reverse)}/{total} {reverse}")
    unread = [row["idx"] for row in rows if not row["screenJoint"]]
    print(f"공동입찰 값 못 읽음(화면 「원문 확인」): {len(unread)}/{total} {unread}")

    # 호출부 배선 — `build_notice` 산출값이 순수 함수 값과 같은가.
    # 판별 케이스: 공동과 대리 값이 갈리는 공고. 여기서만 「대리입찰 값을 싣는」 배선이 드러난다.
    wiring_gap = [row["idx"] for row in rows if row["noticeJoint"] != row["screenJoint"]]
    split_rows = [row["idx"] for row in rows if row["screenJoint"] != row["proxyFlag"]]
    print(f"build_notice 배선 일치: {total - len(wiring_gap)}/{total} · 불일치 {wiring_gap}")
    print(f"  판별 케이스(공동≠대리): {len(split_rows)}/{total} {split_rows}")
    for row in rows:
        if row["idx"] in split_rows:
            print(f"    #{row['idx']} 공동={row['screenJoint'] or '없음'} · 대리={row['proxyFlag'] or '없음'} "
                  f"· build_notice={row['noticeJoint'] or '없음'}")
    eviction = [row["idx"] for row in rows if row["eviction"]]
    print(f"명도책임 값: {len(eviction)}/{total} {eviction} · 어휘 {sorted({row['eviction'] for row in rows if row['eviction']})}")
    if partial:
        print(f"표본 {SAMPLE_TOTAL}건 중 {SAMPLE_TOTAL - total}건이 없어 위 수치는 전수가 아닙니다. rc=3")
        return 3
    # 계측 스크립트이지 게이트가 아니지만, 배선 불일치는 수치가 아니라 결함이다.
    if wiring_gap:
        print(f"build_notice 가 조립한 값이 순수 함수 값과 다릅니다: {wiring_gap}. rc=4")
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
