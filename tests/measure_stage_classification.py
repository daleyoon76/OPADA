"""입찰 전/낙찰 후 단계 분류의 오분류율·미분류율을 재는 계측 스크립트.

수치를 만드는 도구이지 통과/실패를 판정하는 게이트가 아니다. 게이트는
`tests/test_docs_extraction.py` 다 — `tests/measure_sample_23.py`와 같은 자리다.

정답표는 `team-reports/2026-10-18-bid-doc-timeline/stage-classification-design.md`
§4-3 appendix(160행, 사람이 원문을 읽고 확정)를 그대로 옮겼다. 추출은 그 설계 문서
§4-1과 같은 방식(공고문 섹션 + 첨부 텍스트)으로 재현한다.

원자료(표본 23건 HTML + 첨부 추출 텍스트)는 레포에 없다. 2026-10-18 작업에서
`/Users/user/Documents/Dev/.opada-sample-html/`(HTML)과
`/Users/user/Documents/Dev/.opada-survey/text/`(첨부 텍스트, `index.json` 포함)에서
찾았다. 다른 위치면 환경변수로 준다.

    ONBID_SAMPLE_HTML_DIR=/path/to/html ONBID_SAMPLE_TEXT_DIR=/path/to/text \
        python3 tests/measure_stage_classification.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import server  # noqa: E402

HTML_DIR = Path(os.environ.get("ONBID_SAMPLE_HTML_DIR", "/Users/user/Documents/Dev/.opada-sample-html"))
TEXT_DIR = Path(os.environ.get("ONBID_SAMPLE_TEXT_DIR", "/Users/user/Documents/Dev/.opada-survey/text"))

# 분모에서 빼는 항목 — 설계 문서 §4-2.
EXCLUDED_SAMPLES_NO_STAGE_CONCEPT = {9, 10}  # 수의계약형, 입찰 전/낙찰 후 이분법 미성립
EXCLUDED_NOT_A_REQUEST = {(19, "등기사항증명서")}  # 서류 "요구" 문장이 아님(배경 설명)

# 설계 문서 §4-3 appendix 160행을 그대로 옮긴 정답표.
# (표본, 서류명, 조건, 정답) — 조건은 appendix의 "조건" 칸 그대로(" · " 로 join).
GROUND_TRUTH: tuple[tuple[int, str, str, str], ...] = (
    (4, "본인서명사실확인서", "대리입찰 · 공동입찰", "입찰 전"),
    (4, "인감증명서", "대리입찰 · 공동입찰", "입찰 전"),
    (4, "대리입찰신청서", "대리입찰 · 공동입찰", "입찰 전"),
    (4, "공동입찰참가신청서", "대리입찰 · 공동입찰", "입찰 전"),
    (4, "본인서명사실확인서", "공통", "입찰 전"),
    (4, "인감증명서", "공통", "입찰 전"),
    (4, "주민등록등본", "공통", "입찰 전"),
    (4, "미성년자 입찰참가 동의서", "공통", "입찰 전"),
    (4, "대리입찰신청서", "공통", "입찰 전"),
    (4, "공동입찰참가신청서", "공통", "입찰 전"),
    (5, "본인서명사실확인서", "대리입찰 · 공동입찰", "입찰 전"),
    (5, "인감증명서", "대리입찰 · 공동입찰", "입찰 전"),
    (5, "대리입찰신청서", "대리입찰 · 공동입찰", "입찰 전"),
    (5, "공동입찰참가신청서", "대리입찰 · 공동입찰", "입찰 전"),
    (5, "본인서명사실확인서", "공통", "입찰 전"),
    (5, "인감증명서", "공통", "입찰 전"),
    (5, "주민등록등본", "공통", "입찰 전"),
    (5, "미성년자 입찰참가 동의서", "공통", "입찰 전"),
    (5, "대리입찰신청서", "공통", "입찰 전"),
    (5, "공동입찰참가신청서", "공통", "입찰 전"),
    (6, "본인서명사실확인서", "대리입찰 · 공동입찰", "입찰 전"),
    (6, "인감증명서", "대리입찰 · 공동입찰", "입찰 전"),
    (6, "대리입찰신청서", "대리입찰 · 공동입찰", "입찰 전"),
    (6, "공동입찰참가신청서", "대리입찰 · 공동입찰", "입찰 전"),
    (6, "본인서명사실확인서", "공통", "입찰 전"),
    (6, "인감증명서", "공통", "입찰 전"),
    (6, "주민등록등본", "공통", "입찰 전"),
    (6, "미성년자 입찰참가 동의서", "공통", "입찰 전"),
    (6, "대리입찰신청서", "공통", "입찰 전"),
    (6, "공동입찰참가신청서", "공통", "입찰 전"),
    (7, "본인서명사실확인서", "대리입찰 · 공동입찰", "입찰 전"),
    (7, "인감증명서", "대리입찰 · 공동입찰", "입찰 전"),
    (7, "대리입찰신청서", "대리입찰 · 공동입찰", "입찰 전"),
    (7, "공동입찰참가신청서", "대리입찰 · 공동입찰", "입찰 전"),
    (7, "전자보증서", "대리입찰 · 공동입찰", "입찰 전"),
    (7, "보증보험증권", "대리입찰 · 공동입찰", "입찰 전"),
    (7, "본인서명사실확인서", "공통", "입찰 전"),
    (7, "인감증명서", "공통", "입찰 전"),
    (7, "주민등록등본", "공통", "입찰 전"),
    (7, "미성년자 입찰참가 동의서", "공통", "입찰 전"),
    (7, "대리입찰신청서", "공통", "입찰 전"),
    (7, "공동입찰참가신청서", "공통", "입찰 전"),
    (8, "본인서명사실확인서", "대리입찰 · 공동입찰", "입찰 전"),
    (8, "인감증명서", "대리입찰 · 공동입찰", "입찰 전"),
    (8, "대리입찰신청서", "대리입찰 · 공동입찰", "입찰 전"),
    (8, "공동입찰참가신청서", "대리입찰 · 공동입찰", "입찰 전"),
    (8, "전자보증서", "대리입찰 · 공동입찰", "입찰 전"),
    (8, "보증보험증권", "대리입찰 · 공동입찰", "입찰 전"),
    (8, "본인서명사실확인서", "공통", "입찰 전"),
    (8, "인감증명서", "공통", "입찰 전"),
    (8, "주민등록등본", "공통", "입찰 전"),
    (8, "미성년자 입찰참가 동의서", "공통", "입찰 전"),
    (8, "대리입찰신청서", "공통", "입찰 전"),
    (8, "공동입찰참가신청서", "공통", "입찰 전"),
    (11, "법인인감증명서", "공통", "입찰 전"),
    (11, "법인 등기사항증명서", "공통", "입찰 전"),
    (11, "인감증명서", "공통", "입찰 전"),
    (11, "주민등록등본", "공통", "입찰 전"),
    (11, "사업자등록증", "공통", "입찰 전"),
    (11, "사업계획서", "공통", "입찰 전"),
    (11, "인감도장", "공통", "낙찰 후·계약 시"),
    (11, "청렴계약이행서약서", "공통", "낙찰 후·계약 시"),
    (11, "주민등록증", "공통", "낙찰 후·계약 시"),
    (12, "법인인감증명서", "공통", "낙찰 후·계약 시"),
    (12, "법인 등기사항증명서", "공통", "낙찰 후·계약 시"),
    (12, "인감증명서", "공통", "낙찰 후·계약 시"),
    (12, "인감도장", "공통", "낙찰 후·계약 시"),
    (12, "청렴계약서", "공통", "낙찰 후·계약 시"),
    (12, "신분증", "공통", "낙찰 후·계약 시"),
    (13, "법인인감증명서", "공통", "낙찰 후·계약 시"),
    (13, "법인 등기사항증명서", "공통", "낙찰 후·계약 시"),
    (13, "인감증명서", "공통", "낙찰 후·계약 시"),
    (13, "인감도장", "공통", "낙찰 후·계약 시"),
    (13, "주민등록등본", "공통", "낙찰 후·계약 시"),
    (13, "사업자등록증", "공통", "낙찰 후·계약 시"),
    (13, "국세 및 지방세 완납증명서", "공통", "낙찰 후·계약 시"),
    (13, "영업신고증", "공통", "낙찰 후·계약 시"),
    (13, "청렴계약이행서약서", "공통", "낙찰 후·계약 시"),
    (13, "계약이행보증보험증권", "공통", "낙찰 후·계약 시"),
    (13, "보증보험증권", "공통", "낙찰 후·계약 시"),
    (13, "확약서", "공통", "낙찰 후·계약 시"),
    (13, "운영계획서", "공통", "낙찰 후·계약 시"),
    (13, "공유재산 사용허가 신청서", "공통", "낙찰 후·계약 시"),
    (13, "신분증", "공통", "낙찰 후·계약 시"),
    (13, "주민등록증", "공통", "낙찰 후·계약 시"),
    (13, "운전면허증", "공통", "낙찰 후·계약 시"),
    (14, "사업자등록증", "업종·자격 요건", "입찰 전"),
    (14, "옥외광고업 등록증", "업종·자격 요건", "입찰 전"),
    (14, "옥외광고사업 등록증", "공통", "입찰 전"),
    (15, "법인인감증명서", "공통", "낙찰 후·계약 시"),
    (15, "법인 등기사항증명서", "공통", "낙찰 후·계약 시"),
    (15, "인감증명서", "공통", "낙찰 후·계약 시"),
    (15, "인감도장", "공통", "낙찰 후·계약 시"),
    (15, "주민등록초본", "공통", "낙찰 후·계약 시"),
    (15, "위임장", "공통", "낙찰 후·계약 시"),
    (15, "사업자등록증", "공통", "낙찰 후·계약 시"),
    (15, "신분증", "공통", "낙찰 후·계약 시"),
    (16, "법인인감증명서", "공통", "낙찰 후·계약 시"),
    (16, "법인 등기사항증명서", "공통", "낙찰 후·계약 시"),
    (16, "인감증명서", "공통", "낙찰 후·계약 시"),
    (16, "인감도장", "공통", "낙찰 후·계약 시"),
    (16, "주민등록초본", "공통", "낙찰 후·계약 시"),
    (16, "위임장", "공통", "낙찰 후·계약 시"),
    (16, "사업자등록증", "공통", "낙찰 후·계약 시"),
    (16, "신분증", "공통", "낙찰 후·계약 시"),
    (17, "법인인감증명서", "공통", "낙찰 후·계약 시"),
    (17, "법인 등기사항증명서", "공통", "낙찰 후·계약 시"),
    (17, "인감증명서", "공통", "낙찰 후·계약 시"),
    (17, "인감도장", "공통", "낙찰 후·계약 시"),
    (17, "주민등록초본", "공통", "낙찰 후·계약 시"),
    (17, "위임장", "공통", "낙찰 후·계약 시"),
    (17, "사업자등록증", "공통", "낙찰 후·계약 시"),
    (17, "신분증", "공통", "낙찰 후·계약 시"),
    (20, "인감증명서", "대리입찰 · 공동입찰", "낙찰 후·계약 시"),
    (20, "대리입찰신청서", "대리입찰 · 공동입찰", "입찰 전"),
    (20, "공동입찰참가신청서", "대리입찰 · 공동입찰", "입찰 전"),
    (20, "법인인감증명서", "공통", "낙찰 후·계약 시"),
    (20, "법인 등기사항증명서", "공통", "낙찰 후·계약 시"),
    (20, "위임장", "공통", "낙찰 후·계약 시"),
    (20, "사업자등록증", "공통", "낙찰 후·계약 시"),
    (20, "4대보험 가입확인서", "공통", "낙찰 후·계약 시"),
    (20, "전자보증서", "공통", "낙찰 후·계약 시"),
    (20, "재직증명서", "공통", "낙찰 후·계약 시"),
    (20, "신분증", "공통", "낙찰 후·계약 시"),
    (21, "법인 등기사항증명서", "공통", "입찰 전"),
    (21, "인감증명서", "공통", "입찰 전"),
    (21, "사용인감계", "공통", "입찰 전"),
    (21, "주민등록등본", "공통", "입찰 전"),
    (21, "위임장", "공통", "입찰 전"),
    (21, "컨소시엄 협정서", "공통", "입찰 전"),
    (21, "사업자등록증", "공통", "입찰 전"),
    (21, "사업제안서", "공통", "입찰 전"),
    (21, "제안서", "공통", "입찰 전"),
    (21, "입찰참가신청서", "공통", "입찰 전"),
    (21, "신분증", "공통", "입찰 전"),
    (21, "주민등록증", "공통", "입찰 전"),
    (21, "운전면허증", "공통", "입찰 전"),
    (22, "법인인감증명서", "공통", "낙찰 후·계약 시"),
    (22, "법인 등기사항증명서", "공통", "낙찰 후·계약 시"),
    (22, "인감도장", "공통", "낙찰 후·계약 시"),
    (22, "사용인감계", "공통", "낙찰 후·계약 시"),
    (22, "주민등록등본", "공통", "낙찰 후·계약 시"),
    (22, "위임장", "공통", "낙찰 후·계약 시"),
    (22, "사업자등록증", "공통", "낙찰 후·계약 시"),
    (22, "국세 및 지방세 완납증명서", "공통", "낙찰 후·계약 시"),
    (22, "청렴이행각서", "공통", "낙찰 후·계약 시"),
    (22, "재직증명서", "공통", "낙찰 후·계약 시"),
    (22, "건강보험자격득실확인서", "공통", "낙찰 후·계약 시"),
    (23, "법인 등기사항증명서", "공통", "입찰 전"),
    (23, "사업자등록증", "공통", "입찰 전"),
    (23, "제안서", "공통", "입찰 전"),
    (23, "관광사업등록증", "공통", "입찰 전"),
    (23, "등급인정서", "공통", "입찰 전"),
    (23, "평가결과통보서", "공통", "입찰 전"),
    (23, "부가가치세 과세표준증명서", "공통", "입찰 전"),
    (23, "표준재무제표증명서", "공통", "입찰 전"),
    (23, "전자보증서", "공통", "입찰 전"),
    (23, "사업제안서", "공통", "입찰 전"),
    (23, "재직증명서", "공통", "입찰 전"),
    (23, "신분증", "공통", "입찰 전"),
)


def load_attachment_chunks(idx: int) -> list[tuple[str, str]]:
    index_path = TEXT_DIR / "index.json"
    if not index_path.exists():
        return []
    manifest = json.loads(index_path.read_text(encoding="utf-8"))
    chunks: list[tuple[str, str]] = []
    for key in sorted(manifest):
        entry = manifest[key]
        if int(entry.get("idx", -1)) != idx:
            continue
        text_path = TEXT_DIR / f"{key}.txt"
        if not text_path.exists():
            continue
        text = text_path.read_text(encoding="utf-8", errors="replace")
        if not text.strip():
            continue
        name = str(entry.get("name") or key)
        chunks.append((f"첨부:{name}", text))
    return chunks


def extract_sample(idx: int) -> list[dict[str, object]]:
    html_path = HTML_DIR / f"pbanc_{idx:02d}.html"
    if not html_path.exists():
        return []
    text = html_path.read_text(encoding="utf-8", errors="replace")
    sections = server.split_sections(text)
    attachment_chunks = load_attachment_chunks(idx)
    return server.extract_doc_items(sections, attachment_chunks)


def main() -> int:
    if not HTML_DIR.exists():
        print(f"🔴 원자료 없음 — {HTML_DIR} 를 찾지 못했다. 기준선을 재현하지 못했다.")
        return 1

    total_extracted = 0
    scored = 0
    mismatches: list[tuple[int, str, str, str, str]] = []
    unclassified: list[tuple[int, str, str]] = []
    missing_from_extraction: list[tuple[int, str, str]] = []

    per_sample_items: dict[int, list[dict[str, object]]] = {}
    for idx in range(1, 24):
        items = extract_sample(idx)
        per_sample_items[idx] = items
        total_extracted += len(items)

    # 조건(condition) 축은 이번 작업의 대상이 아니다 — 이름(name)만으로 매칭하고, 같은 이름의
    # 항목이 조건별로 여러 번 뽑혀도 "그중 하나라도 단계가 틀리면" 오분류로 센다(실제 화면에
    # 한 번이라도 잘못된 단계가 노출되면 사용자에게는 그것이 오류이기 때문).
    for sample, name, condition, expected in GROUND_TRUTH:
        if sample in EXCLUDED_SAMPLES_NO_STAGE_CONCEPT:
            continue
        if (sample, name) in EXCLUDED_NOT_A_REQUEST:
            continue
        items = per_sample_items.get(sample, [])
        found = [item for item in items if item["name"] == name]
        if not found:
            missing_from_extraction.append((sample, name, condition))
            continue
        scored += 1
        stages = {str(item["stage"]) for item in found}
        if stages == {expected}:
            continue
        if "미분류" in stages:
            unclassified.append((sample, name, condition))
        else:
            wrong = sorted(stages - {expected})
            mismatches.append((sample, name, condition, expected, "/".join(wrong) or "?"))

    print(f"추출된 전체 항목: {total_extracted}건 (설계 문서 §4-1 재현값 180건과 비교)")
    print(f"정답표(분모 160건) 중 실제로 추출돼 채점된 항목: {scored}건")
    if missing_from_extraction:
        print(f"🔴 정답표에 있는데 이번 추출에 안 걸린 항목 {len(missing_from_extraction)}건: {missing_from_extraction}")
    print(f"오분류: {len(mismatches)}/{scored}건 ({len(mismatches) / scored * 100:.1f}%)" if scored else "scored=0")
    print(f"미분류: {len(unclassified)}/{scored}건 ({len(unclassified) / scored * 100:.1f}%)" if scored else "")
    if mismatches:
        print("\n오분류 목록:")
        for sample, name, condition, expected, actual in mismatches:
            print(f"  #{sample} {name} ({condition}) — 정답 {expected} / 실제 {actual}")
    if unclassified:
        print("\n미분류 목록:")
        for sample, name, condition in unclassified:
            print(f"  #{sample} {name} ({condition})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
