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


def main() -> int:
    if not SAMPLE_DIR.is_dir():
        print(f"표본 HTML 디렉터리가 없습니다: {SAMPLE_DIR}")
        print("ONBID_SAMPLE_HTML_DIR 로 경로를 지정하십시오. 측정을 건너뜁니다.")
        return 2

    asset_types, asset_note = load_asset_types()
    print(f"재산유형 출처: {asset_note}")
    by_profile: dict[str, list[int]] = {}
    rows = []
    for index in range(1, 24):
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
    print()
    print(f"구체 서류명 1건 이상 추출: {ok}/{total}")
    for profile in sorted(by_profile):
        hits = by_profile[profile]
        print(f"  {profile}형: {sum(hits)}/{len(hits)}")
    att_total = sum(row["attachments"] for row in rows)
    att_link = sum(row["downloadable"] for row in rows)
    with_att = sum(1 for row in rows if row["attachments"])
    print(f"첨부 다운로드 파라미터: {att_link}/{att_total} (첨부가 있는 공고 {with_att}건)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
