"""정답 세트 대비 «항목 단위» 추출 측정기.

기존 지표(measure_sample_23.py)는 「서류를 1건 이상 뽑았는가」라는 이진값이다. 1건만 맞히고 10건을
놓쳐도 성공으로 센다. 그 이진값이 정확도로 오독되지 않게, 이 측정기는 «다른 줄로» 항목 단위를 센다.

두 경로를 잰다.
- 현행   : 온비드 HTML 본문만 읽는 지금의 build_doc_checklist()
- 첨부모의: 위 + 첨부 텍스트 각 줄에 find_doc_names() 를 그대로 태운 것.
            파서 설계가 정해지기 전의 «가장 순진한» 경로다. 오탐이 얼마나 들어오는지 보려는 것이지
            제품 경로가 아니다. 이름에 «모의»를 박아 둔다.

대조 규칙 (2026-09-11 v2 · v1 은 이름 «정확 일치»라 조건이 이름에 녹은 서술형 정답을 전부 놓쳤다)
- 정답은 「법정대리인의 인감증명서(또는 본인서명사실확인서)」처럼 조건이 이름에 녹은 서술형이다.
  추출기는 「인감증명서」 같은 표준 어휘를 (서류명, 조건, 단계)로 조건마다 낸다.
- 맞힘      : 추출 서류명이 정답 이름 «안에» 들어 있고, 조건도 맞는다.
- 이름만 맞음: 이름은 들어 있는데 조건이 안 맞는다. 맞힘에 넣지 않는다.
- 헛뽑음    : 어떤 정답에도 조건까지 맞게 걸리지 않는 추출. 그중 정답 excluded 에 적힌 것은 «함정»으로 따로 센다.
- 단계 불일치: 맞힘 중 추출 단계와 정답 단계가 다른 것. 입찰 준비물 목록에 계약 서류가 섞이는 부류다.
- 한계: 「이름 안에 들어 있다」는 짧은 표준명(인감증명서)이 긴 정답명에 걸리는 느슨한 규칙이다.
  조건 대조가 그 느슨함을 대부분 막지만, 같은 조건 안의 오귀속은 잡지 못한다.
- 첨부모의 경로는 조건을 모른다(find_doc_names 는 이름만 낸다). 「공통」으로 취급해 어느 조건과도 맞게
  둔다 — 그래서 첨부모의 재현율은 «상한»이다. 조건을 모르고도 맞힌 것으로 센 것이다.

    python3 tests/measure_answer_set.py
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "src"))
import server  # noqa: E402

ANSWERS = ROOT / "answer_set"
SURVEY = Path(os.environ.get("OPADA_SURVEY_DIR", Path.home() / "Documents/Dev/.opada-survey"))
EXPECTED_IDX = [1, 4, 9, 12, 13, 15, 19, 21, 22, 23]


# 같은 서류의 옛 이름 → 새 이름. 2011년 부동산등기법 개정으로 「등기부등본」이 「등기사항증명서」가 됐다.
# 공고는 두 이름을 섞어 쓰고 추출기 어휘는 새 이름이다. 이 쌍이 없으면 네 공고에서 같은 서류가
# 「놓침 1 + 헛뽑음 1」로 두 번 틀린 것으로 세어졌다(2026-09-11 실측 #09·#12·#15·#21).
# 이 표는 «사실로 확인된 개칭»만 담는다. 비슷해 보이는 서류를 여기에 묶으면 자가 휜다.
SYNONYMS = {"등기부등본": "등기사항증명서"}


def norm(name: str) -> str:
    text = re.sub(r"[\s()（）\[\]·,]", "", name or "")
    for old, new in SYNONYMS.items():
        text = text.replace(old, new)
    return text


COND_MAP = {"미성년자": "미성년", "대리입찰": "대리", "공동입찰": "공동", "법인": "법인", "개인": "개인"}


def extract_current(idx: int, asset_type: str) -> list[tuple[str, str, str]]:
    html = (SURVEY / "html" / f"pbanc_{idx:02d}.html").read_text(errors="replace")
    sections = server.split_sections(html)
    attachments = server.extract_related_docs(html)
    checklist = server.build_doc_checklist(sections, asset_type, attachments)
    out: list[tuple[str, str, str]] = []
    for item in checklist.get("items", []):
        stage = re.sub(r"\s+", "", str(item.get("stage", "")))
        for cond in item.get("conditions") or ["공통"]:
            out.append((str(item.get("name", "")), COND_MAP.get(cond, cond), stage))
    return out


def extract_attach_naive(idx: int) -> list[tuple[str, str, str]]:
    names: list[str] = []
    for path in sorted((SURVEY / "text").glob(f"{idx:02d}_*.txt")):
        for line in path.read_text(errors="replace").splitlines():
            for name in server.find_doc_names(line):
                if name not in names:
                    names.append(name)
    return [(name, "공통", "불명") for name in names]


def cond_ok(extracted: str, answer: str) -> bool:
    if extracted == "공통" or answer == "전원":
        return True
    if answer == extracted:
        return True
    return answer.startswith("기타:") and extracted in answer


def score(answer: dict, got: list[tuple[str, str, str]]) -> dict[str, object]:
    items = answer.get("items", [])
    traps = {norm(str(e.get("text", ""))) for e in answer.get("excluded", [])}
    hit, name_only, stage_off = [], [], []
    used: set[int] = set()
    for item in items:
        a_name, a_cond, a_stage = norm(str(item["name"])), str(item["condition"]), str(item["stage"])
        match = [i for i, (n, c, _) in enumerate(got) if norm(n) and norm(n) in a_name and cond_ok(c, a_cond)]
        if match:
            hit.append(item["name"])
            used.update(match)
            if a_stage != "불명" and all(got[i][2] not in (a_stage, "불명") for i in match):
                stage_off.append(f"{item['name'][:18]}(정답 {a_stage} · 추출 {got[match[0]][2]})")
        elif any(norm(n) and norm(n) in a_name for n, _, _ in got):
            name_only.append(item["name"])
    extra = [got[i] for i in range(len(got)) if i not in used]
    extra_names = sorted({n for n, _, _ in extra})
    return {
        "want": len(items),
        "hit": len(hit),
        "name_only": name_only,
        "missed": [i["name"] for i in items if i["name"] not in hit and i["name"] not in name_only],
        "extra": extra_names,
        "extra_trap": [n for n in extra_names if norm(n) in traps],
        "stage_off": stage_off,
    }


def main() -> int:
    if not (SURVEY / "samples.json").exists():
        print(f"🔴 원천 없음: {SURVEY} — 건너뛰지 않고 실패한다")
        return 1
    samples = {s["idx"]: s for s in json.loads((SURVEY / "samples.json").read_text())}

    totals = {"현행": [0, 0, 0, 0, 0, 0], "첨부모의": [0, 0, 0, 0, 0, 0]}  # want hit name_only extra trap stage_off
    any_hit = {"현행": 0, "첨부모의": 0}
    counted = 0
    for idx in EXPECTED_IDX:
        path = ANSWERS / f"{idx:02d}.json"
        if not path.exists():
            print(f"#{idx:02d} 정답 없음 — 건너뛰지 않고 모수에서 뺀 채 끝에 붉힌다")
            continue
        answer = json.loads(path.read_text())
        asset_type = samples[idx]["prptDvsnNm"]
        current = extract_current(idx, asset_type)
        naive = current + [t for t in extract_attach_naive(idx) if t[0] not in {n for n, _, _ in current}]
        counted += 1
        print(f"\n#{idx:02d} {asset_type} · 위치 {answer.get('location')} · 정답 {len(answer.get('items', []))}건")
        for label, got in (("현행", current), ("첨부모의", naive)):
            r = score(answer, got)
            t = totals[label]
            for k, v in enumerate((r["want"], r["hit"], len(r["name_only"]), len(r["extra"]), len(r["extra_trap"]), len(r["stage_off"]))):
                t[k] += v
            any_hit[label] += 1 if got else 0
            print(f"  {label:4} 맞힘 {r['hit']}/{r['want']} · 이름만 {len(r['name_only'])} · "
                  f"헛뽑음 {len(r['extra'])}(함정 {len(r['extra_trap'])}) · 단계 불일치 {len(r['stage_off'])}")
            if r["missed"]:
                print(f"         놓침: {', '.join(m[:22] for m in r['missed'][:6])}{' …' if len(r['missed']) > 6 else ''}")
            if r["extra"]:
                print(f"         헛뽑음: {', '.join(r['extra'][:6])}{' …' if len(r['extra']) > 6 else ''}")
            if r["stage_off"]:
                print(f"         단계 불일치: {', '.join(r['stage_off'][:3])}{' …' if len(r['stage_off']) > 3 else ''}")

    print("\n" + "=" * 60)
    for label, (want, hit, name_only, extra, trap, stage_off) in totals.items():
        recall = hit / want if want else 0.0
        print(f"{label:4} 항목 재현율(이름+조건) {hit}/{want} = {recall:.0%} · 이름만 맞음 {name_only} · "
              f"헛뽑음 {extra}(함정 {trap}) · 단계 불일치 {stage_off}")
    print("-" * 60)
    print("아래는 기존 이진 지표다. 위 줄과 «다른 값»이다 — 섞어 읽지 않는다.")
    for label, hit in any_hit.items():
        print(f"{label:4} 「1건 이상 뽑음」 {hit}/{counted}")
    if counted < len(EXPECTED_IDX):
        print(f"🔴 정답 {counted}/{len(EXPECTED_IDX)}건만 쟀다 — 모수 미달")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
