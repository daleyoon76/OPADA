"""정답 세트(tests/answer_set/*.json) 검증기.

정답 세트는 추출 알고리듬을 재는 «자»다. 자가 틀리면 그 위의 측정이 전부 틀린다.
그래서 사람이 쓴 정답을 그대로 믿지 않고, 모든 항목의 근거 인용이 원문에 «글자 그대로» 있는지 대조한다.
작성자의 기억·요약·추론이 정답에 섞이는 경로를 막는 것이 목적이다.

원천은 레포 밖(~/Documents/Dev/.opada-survey)에 있다(공고 HTML 14MB + 첨부 59건).
원천이 없으면 «건너뛰지 않고» 실패한다 — 건너뛰면 원천 없는 기기에서 영원히 초록이다.
npm test 에 넣지 않은 이유가 이것이다. 원천이 있는 기기에서 손으로 돌린다.

    python3 tests/verify_answer_set.py
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANSWERS = ROOT / "answer_set"
SURVEY = Path(os.environ.get("OPADA_SURVEY_DIR", Path.home() / "Documents/Dev/.opada-survey"))

# 표본조사 §6-1 이 고른 10건. 파일 목록에서 파생시키지 않는다 — 파생시키면 파일을 지워도 초록이다.
EXPECTED_IDX = [1, 4, 9, 12, 13, 15, 19, 21, 22, 23]
CONDITIONS = {"개인", "법인", "대리", "공동", "미성년", "외국인", "전원"}
STAGES = {"입찰전", "낙찰후", "계약시", "불명"}
LOCATIONS = {"body", "attachment", "both", "none"}
BODY_SOURCES = {"noticeBodyText", "docsSecText", "docsTableRows", "bidMethodText"}
ATTACH_SOURCE_RE = re.compile(r"^(\d{2})_(\d+)\.txt$")

PLAYED: list[tuple[str, str]] = [
    ("원천 텍스트", "첨부는 .opada-survey/extract_text.py 가 만든 텍스트다. 텍스트화 도구(pdfminer·hwp5html)의 "
     "누락은 이 검증기가 보지 못한다 — 인용이 대조되면 «텍스트에는 있다»까지만 참이다"),
]
AXES: list[tuple[str, str]] = [
    ("V1", "파일이 10건 전부 있고 JSON 으로 읽힌다"),
    ("V2", "스키마 — 필수 키·조건·단계·위치 값이 허용 목록 안"),
    ("V3", "근거 인용이 원문에 글자 그대로 있다(공백 차이만 허용)"),
    ("V4", "위치 판정과 근거 출처가 모순되지 않는다(none 이면 items 0 · body 인데 첨부 근거 없음 등)"),
    ("V5", "검증기 자체 — 지어낸 인용·빈 출처를 잡는다(음성 대조)"),
]

_results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> bool:
    _results.append((name, ok, detail))
    return ok


def squash(text: str) -> str:
    """공백 차이만 허용한다. PDF 추출이 단어 중간에 공백을 넣는 일이 있어 공백을 전부 뺀다."""
    return re.sub(r"\s+", "", text or "")


def load_samples() -> dict[int, dict]:
    return {s["idx"]: s for s in json.loads((SURVEY / "samples.json").read_text())}


def source_text(sample: dict, source: str) -> str | None:
    if source in ("noticeBodyText", "docsSecText", "bidMethodText"):
        return sample.get(source) or ""
    if source == "docsTableRows":
        # 사람이 읽는 순서(행 → 셀)로 잇는다. JSON 문자열로 펼치면 따옴표·쉼표가 끼어
        # 표를 읽은 그대로 인용한 근거가 전부 불일치로 떨어진다(2026-09-11 #09 실측 2건).
        rows = sample.get("docsTableRows") or []
        return " ".join(" ".join(str(cell) for cell in row) for row in rows)
    match = ATTACH_SOURCE_RE.match(source)
    if match:
        if int(match.group(1)) != sample["idx"]:
            return None  # 다른 공고의 첨부를 근거로 댔다
        path = SURVEY / "text" / source
        return path.read_text() if path.exists() else None
    return None


def quote_found(sample: dict, evidence: dict) -> tuple[bool, str]:
    if not isinstance(evidence, dict):
        return False, "evidence 가 객체가 아님"
    source, quote = evidence.get("source", ""), evidence.get("quote", "")
    if len(squash(quote)) < 8:
        return False, f"인용이 너무 짧다({len(squash(quote))}자) — 짧으면 아무 데나 걸린다"
    text = source_text(sample, source)
    if text is None:
        return False, f"출처를 찾을 수 없음: {source}"
    return (squash(quote) in squash(text)), f"{source}: {quote[:40]}"


def verify_one(answer: dict, sample: dict) -> None:
    idx = answer.get("idx")
    tag = f"#{idx:02d}" if isinstance(idx, int) else "#??"
    check(f"V2 {tag} 필수 키", all(k in answer for k in ("idx", "location", "items", "excluded")), str(sorted(answer)))
    location = answer.get("location")
    check(f"V2 {tag} 위치 값", location in LOCATIONS, str(location))

    bad_schema: list[str] = []
    missing_quote: list[str] = []
    item_sources: set[str] = set()
    for n, item in enumerate(answer.get("items", [])):
        cond = str(item.get("condition", ""))
        if not (cond in CONDITIONS or cond.startswith("기타:")):
            bad_schema.append(f"items[{n}].condition={cond}")
        if item.get("stage") not in STAGES:
            bad_schema.append(f"items[{n}].stage={item.get('stage')}")
        if not str(item.get("name", "")).strip():
            bad_schema.append(f"items[{n}].name 비어 있음")
        ok, detail = quote_found(sample, item.get("evidence"))
        if not ok:
            missing_quote.append(f"items[{n}] {item.get('name')} ← {detail}")
        item_sources.add(str((item.get("evidence") or {}).get("source", "")))
    for n, ex in enumerate(answer.get("excluded", [])):
        ok, detail = quote_found(sample, ex.get("evidence"))
        if not ok:
            missing_quote.append(f"excluded[{n}] {ex.get('text')} ← {detail}")

    check(f"V2 {tag} 조건·단계 값", not bad_schema, "; ".join(bad_schema[:4]))
    check(f"V3 {tag} 인용 대조 {len(answer.get('items', [])) + len(answer.get('excluded', []))}건",
          not missing_quote, "; ".join(missing_quote[:3]))

    has_body = bool(item_sources & BODY_SOURCES)
    has_attach = any(ATTACH_SOURCE_RE.match(s) for s in item_sources)
    items = answer.get("items", [])
    consistent = {
        "none": not items,
        "body": bool(items) and has_body and not has_attach,
        "attachment": bool(items) and has_attach and not has_body,
        "both": has_body and has_attach,
    }.get(location, False)
    check(f"V4 {tag} 위치({location}) ↔ 근거 출처", consistent,
          f"본문 근거 {has_body} · 첨부 근거 {has_attach} · items {len(items)}")


def self_test(samples: dict[int, dict]) -> None:
    """검증기가 «잡아야 하는» 입력을 넣어 실제로 잡는지 본다. 이것이 없으면 V3 는 무증명이다."""
    sample = samples[1]
    real = (sample.get("noticeBodyText") or "")[:60]
    ok_real, _ = quote_found(sample, {"source": "noticeBodyText", "quote": real})
    check("V5 음성 대조 기준 — 원문 앞 60자는 대조된다", ok_real, real[:30])
    ok_fake, _ = quote_found(sample, {"source": "noticeBodyText", "quote": "이 문장은 원문에 없는 지어낸 근거 인용입니다 확실히"})
    check("V5 지어낸 인용을 잡는다", not ok_fake)
    ok_other, _ = quote_found(sample, {"source": "04_1.txt", "quote": real})
    check("V5 다른 공고의 첨부를 근거로 대면 잡는다", not ok_other)
    ok_short, _ = quote_found(sample, {"source": "noticeBodyText", "quote": "서류"})
    check("V5 너무 짧은 인용을 잡는다", not ok_short)
    ok_spaced, _ = quote_found(sample, {"source": "noticeBodyText", "quote": " ".join(real)})
    check("V5 붉히면 안 됨 — 공백만 다른 인용은 대조된다", ok_spaced)
    # 표는 행→셀 순서로 이어 대조한다. 그 완화가 지어낸 표 인용까지 통과시키지 않는지 본다.
    rows = sample.get("docsTableRows") or []
    table_real = " ".join(str(c) for c in rows[1]) if len(rows) > 1 else ""
    ok_table, _ = quote_found(sample, {"source": "docsTableRows", "quote": table_real})
    check("V5 붉히면 안 됨 — 표를 셀 순서대로 인용하면 대조된다", ok_table, table_real[:30])
    ok_table_fake, _ = quote_found(sample, {"source": "docsTableRows", "quote": "주민등록초본 법인등기부등본 입찰전 제출"})
    check("V5 지어낸 표 인용을 잡는다", not ok_table_fake)


def main() -> int:
    print(f"PLAYED — 이 검증기가 대신 연기한 것 {len(PLAYED)}개")
    for symbol, note in PLAYED:
        print(f"  · {symbol} — {note}")
    print(f"AXES — 축 {len(AXES)}개")
    for code, name in AXES:
        print(f"  {code} {name}")

    if not (SURVEY / "samples.json").exists():
        print(f"\n🔴 원천 없음: {SURVEY} — 건너뛰지 않고 실패한다")
        return 1
    samples = load_samples()
    self_test(samples)

    for idx in EXPECTED_IDX:
        path = ANSWERS / f"{idx:02d}.json"
        if not check(f"V1 #{idx:02d} 파일 존재", path.exists(), str(path.name)):
            continue
        try:
            answer = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            check(f"V1 #{idx:02d} JSON", False, str(exc))
            continue
        check(f"V1 #{idx:02d} idx 일치", answer.get("idx") == idx, str(answer.get("idx")))
        verify_one(answer, samples[idx])

    passed = sum(1 for _, ok, _ in _results if ok)
    print()
    for name, ok, detail in _results:
        if not ok:
            print(f"FAIL {name} — {detail}")
    covered = {name.split()[0] for name, _, _ in _results}
    uncovered = [code for code, _ in AXES if code not in covered]
    print(f"\n{passed}/{len(_results)} 통과 · 연기 {len(PLAYED)}개 · 축 {len(AXES)}개 중 미실행 {len(uncovered)}개"
          f"{' — ' + ', '.join(uncovered) if uncovered else ''}")
    # 모수 하한 — 10건 × (V1 2 + V2 3 + V3 1 + V4 1) + V5 7 = 77. 파일이 빠지면 줄어든다.
    if len(_results) < 77:
        print(f"🔴 판정 수 {len(_results)} < 77 — 정답 파일이 빠졌다")
        return 1
    return 0 if passed == len(_results) else 1


if __name__ == "__main__":
    sys.exit(main())
