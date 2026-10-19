"""공고 36건 덤프로 서류 단계 판정을 다시 재는 계측 스크립트.

덤프(본문 절 · 첨부 텍스트 · 첨부 목록)는 레포 밖에 있다. 파산 공고 등에 개인 이름이 들어 있어서다.

    OPADA_STAGE_FIXTURES=~/Documents/Dev/.opada-stage-fixtures python3 tests/measure_stage_fixtures.py

- `raw/<idx>.json` 을 `server.extract_doc_items` 에 다시 넣는다(네트워크 없음).
- `baseline-measure.json` 은 2026-10-19 18:43 에 같은 공고를 분석한 결과(코드 판 1340f55 와 같은 server.py)다.
- 기대값은 `tests/stage_fixture_expectations.json` 이다(근거 team-reports/2026-10-19-bid-stage-sot/implementation-plan.md §6).

종료 조건(구현 계획 §2 머리)을 코드로 판정한다.
- ⑴ 미분류 합계가 기준선보다 적다.
- ⑵ 기준선에서 「입찰 전」이던 항목이 다른 단계로 바뀌거나 사라진 건수가 0이다(사람이 승인한 예외만 허용).
- ⑶ 기대값 표(stage · mustDisappear · mustStay)가 전부 맞는다.
게이트가 아니라 계측이다. 원자료가 없으면 건너뛰지 않고 실패한다(npm test 에 넣지 않는다).
"""

from __future__ import annotations

import collections
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import server  # noqa: E402

FIXTURES = Path(os.environ.get("OPADA_STAGE_FIXTURES", Path.home() / "Documents/Dev/.opada-stage-fixtures"))
EXPECT = json.loads((ROOT / "tests/stage_fixture_expectations.json").read_text(encoding="utf-8"))
PREBID = "입찰 전"
POSTAWARD = "낙찰 후·계약 시"
# 기준선 「입찰 전」 항목 중 바뀌어도 된다고 사람이 확인한 것: (idx, 서류명, 근거 앞 40자) → 이유
APPROVED_PREBID_CHANGES: dict[tuple[int, str, str], str] = {}


def main() -> int:
    raw_dir = FIXTURES / "raw"
    baseline_path = FIXTURES / "baseline-measure.json"
    if not raw_dir.is_dir() or not baseline_path.exists():
        print(f"덤프가 없습니다: {raw_dir} · {baseline_path}")
        return 2
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    files = sorted(raw_dir.glob("*.json"), key=lambda p: int(p.stem))
    if len(files) < 30:
        print(f"덤프가 {len(files)}건뿐입니다. 30건 미만이면 측정하지 않습니다.")
        return 2

    got: dict[int, list[dict]] = {}
    for path in files:
        idx = int(path.stem)
        data = json.loads(path.read_text(encoding="utf-8"))
        asset = str(baseline[idx].get("assetType") or "")
        got[idx] = server.extract_doc_items(
            data["sections"], [tuple(c) for c in (data.get("chunks") or [])], asset_type=asset
        )

    totals = collections.Counter(str(i["stage"]) for items in got.values() for i in items)
    base_totals = collections.Counter(
        str(i["stage"]) for r in baseline if r.get("ok") for i in r["items"]
    )
    print("기준선", dict(base_totals))
    print("지금  ", dict(totals))

    transitions: collections.Counter = collections.Counter()
    prebid_lost: list[str] = []
    removed: list[str] = []
    added: list[str] = []
    post_changed: list[str] = []
    for idx, items in got.items():
        # 같은 (서류명, 출처)가 근거 문장만 바꿔 남는 경우가 있다(앞 언급이 빠지면 뒤 요구 문장이 대표가 된다).
        # 그래서 사라짐·전이는 (서류명, 출처) 단위로 보고, 단계는 그 쌍이 가진 단계 집합으로 본다.
        before: dict[tuple[str, str], set[str]] = collections.defaultdict(set)
        now: dict[tuple[str, str], set[str]] = collections.defaultdict(set)
        evidence: dict[tuple[str, str], str] = {}
        for i in baseline[idx]["items"]:
            before[(str(i["name"]), str(i["sourceSection"]))].add(str(i["stage"]))
            evidence.setdefault((str(i["name"]), str(i["sourceSection"])), str(i["evidence"])[:40])
        for i in items:
            now[(str(i["name"]), str(i["sourceSection"]))].add(str(i["stage"]))

        def prebid_elsewhere(name: str, now: dict = now) -> bool:
            # 같은 공고의 다른 출처(본문 ↔ 첨부)에서 같은 서류가 「입찰 전」으로 남았으면 잃은 것이 아니다.
            return any(pair[0] == name and PREBID in stages for pair, stages in now.items())
        for pair, stages in before.items():
            approved = (idx, pair[0], evidence[pair]) in APPROVED_PREBID_CHANGES
            if pair not in now:
                removed.append(f"#{idx} {sorted(stages)} {pair[0]} | {pair[1][:20]} | {evidence[pair]}")
                if PREBID in stages and not approved and not prebid_elsewhere(pair[0]):
                    prebid_lost.append(f"#{idx} 사라짐 {pair[0]} | {pair[1][:20]} | {evidence[pair]}")
                continue
            if stages != now[pair]:
                transitions[(" / ".join(sorted(stages)), " / ".join(sorted(now[pair])))] += 1
                if POSTAWARD in stages:
                    # 계획 2단계 ⑶: 맞던 낙찰 후가 바뀐 항목은 사람이 하나씩 확인한다.
                    post_changed.append(f"#{idx} {sorted(stages)}→{sorted(now[pair])} {pair[0]} | {evidence[pair]}")
            if PREBID in stages and PREBID not in now[pair] and not approved and not prebid_elsewhere(pair[0]):
                prebid_lost.append(f"#{idx} {sorted(stages)}→{sorted(now[pair])} {pair[0]} | {evidence[pair]}")
        for pair, stages in now.items():
            if pair not in before:
                added.append(f"#{idx} {sorted(stages)} {pair[0]} | {pair[1][:20]}")
    print("전이", dict(transitions))
    for line in post_changed:
        print("  ~", line)
    print(f"사라진 항목 {len(removed)}건 · 새 항목 {len(added)}건")
    for line in removed:
        print("  -", line)
    for line in added:
        print("  +", line)

    failures: list[str] = []
    unclassified = totals.get("미분류", 0)
    if unclassified >= EXPECT["baseline"]["unclassified"]:
        failures.append(f"⑴ 미분류 {unclassified} ≥ 기준선 {EXPECT['baseline']['unclassified']}")
    for line in prebid_lost:
        failures.append(f"⑵ {line}")

    # 잔여(residual): 이번 규칙으로 못 맞추기로 한 행. 사유를 출력하고, 「입찰 전」 기대 행이 낙찰 후로 가면 그때는 실패로 센다.
    residual = {row["row"]: row["reason"] for row in EXPECT.get("residual", [])}
    residual_lines: list[str] = []
    for row in EXPECT["stage"]:
        items = got.get(row["idx"], [])
        for name in row["names"]:
            hits = [i for i in items if i["name"] == name and str(i["sourceSection"]).startswith(row["section"])]
            stages = [str(i["stage"]) for i in hits]
            if row["row"] in residual:
                if not hits or (row["expected"] == PREBID and POSTAWARD in stages):
                    failures.append(f"⑶ 잔여 {row['row']} #{row['idx']} {name} = {stages or '없음'} (안전한 쪽을 벗어남)")
                else:
                    residual_lines.append(f"{row['row']} #{row['idx']} {name} = {stages}")
            elif not hits:
                failures.append(f"⑶ {row['row']} #{row['idx']} {name} 없음")
            elif row["expected"] not in stages:
                failures.append(f"⑶ {row['row']} #{row['idx']} {name} = {stages} (기대 {row['expected']})")
    for row in EXPECT["mustDisappear"]:
        items = got.get(row["idx"], [])
        if any(i["name"] == row["name"] and row["evidence"] in str(i["evidence"]) for i in items):
            failures.append(f"⑶ 사라져야 함({row['group']}) #{row['idx']} {row['name']} 남음")
    for row in EXPECT["mustStay"]:
        items = got.get(row["idx"], [])
        if not any(i["name"] == row["name"] for i in items):
            failures.append(f"⑶ 남아야 함({row['group']}) #{row['idx']} {row['name']} 사라짐")

    # ⑷ 미분류가 낙찰 후로 가거나(비싼 방향) 미분류·낙찰 후 항목이 사라진 쌍은 사람이 승인한 목록에 있어야 한다
    # (리뷰 d8378b6 r1 검증 장치 결함 · 지금까지는 「입찰 전」 손실만 셌다). 목록은 기대값 파일 approvedChanges 다.
    approved = {
        (row["kind"], row["idx"], row["name"], row["section"]) for row in EXPECT.get("approvedChanges", [])
    }
    for idx, items in got.items():
        before: dict[tuple[str, str], set[str]] = collections.defaultdict(set)
        now_pairs: dict[tuple[str, str], set[str]] = collections.defaultdict(set)
        for i in baseline[idx]["items"]:
            before[(str(i["name"]), str(i["sourceSection"]))].add(str(i["stage"]))
        for i in items:
            now_pairs[(str(i["name"]), str(i["sourceSection"]))].add(str(i["stage"]))
        for (name, section), stages in before.items():
            short = section[:22]
            if (name, section) not in now_pairs:
                if stages - {PREBID} and ("LOST", idx, name, short) not in approved:
                    failures.append(f"⑷ 승인 안 된 사라짐 #{idx} {name} | {short} | {sorted(stages)}")
            elif "미분류" in stages and POSTAWARD in now_pairs[(name, section)] and POSTAWARD not in stages:
                if ("U2P", idx, name, short) not in approved:
                    failures.append(f"⑷ 승인 안 된 미분류→낙찰 후 #{idx} {name} | {short}")

    rows = len(EXPECT["stage"]) + len(EXPECT["mustDisappear"]) + len(EXPECT["mustStay"])
    print(f"\n덤프 {len(files)}건 · 기대값 {rows}행 · 실패 {len(failures)}건 · 잔여 {len(residual_lines)}건")
    for line in residual_lines:
        print("  …", line)
    for row_id, reason in residual.items():
        print(f"  … {row_id} 사유: {reason}")
    for line in failures:
        print("  ✗", line)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
