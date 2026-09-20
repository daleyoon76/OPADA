"""5개 규칙기반 첨부추출 프로토타입의 정확도를 10건 표본 정답 세트로 측정한다.

사용법: python3 tests/measure_attachment_extraction.py

첨부 원문 텍스트는 이 저장소 밖(`~/Documents/Dev/.opada-survey/text/`)에 있다
(대용량·원본 데이터라 커밋 대상이 아니다). 경로를 바꾸려면 환경변수
`OPADA_SURVEY_TEXT_DIR`을 지정한다.

이 스크립트는 각 유형의 "헛뽑음"(정답에 없는데 뽑음)과 "누락"(정답에 있는데 못
뽑음)을 구분해서 보고한다. 감정평가 표지값처럼 유형 자체가 없는 idx(재산유형상
감정평가서 미첨부)는 "해당없음 정답 유지"로 따로 센다 — 유형이 없는 idx를 분모에서
빼면 재현율이 부풀려진다.

제출서류는 두 경로를 나란히 잰다(2026-09-20). "1. 제출서류"는 이 디렉터리의
독립 프로토타입(`extract_submission_docs` · 절 앵커+윈도)이고, "1-production"은
실제 서비스에 배선된 `server.extract_doc_items`(줄 단위 · 창 없음)다. 두 경로는
정밀도·재현율 트레이드오프가 달라 같은 줄로 합산하지 않는다.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from attachment_extractors.submission_docs import extract_submission_docs  # noqa: E402
from attachment_extractors.qualification_numbers import extract_qualification_numbers  # noqa: E402
from attachment_extractors.appraisal_cover import extract_appraisal_cover  # noqa: E402
from attachment_extractors.forms import extract_forms  # noqa: E402
from attachment_extractors.clause_boundaries import extract_clause_boundaries  # noqa: E402
import server  # noqa: E402

TEXT_DIR = Path(os.environ.get("OPADA_SURVEY_TEXT_DIR", Path.home() / "Documents/Dev/.opada-survey/text"))
ANSWER_KEY_PATH = REPO_ROOT / "tests/fixtures/attachment_answer_key.json"

TARGET_IDX = ["09", "10", "11", "14", "15", "16", "17", "21", "22", "23"]


def load_idx_texts(idx: str) -> str:
    """한 idx의 첨부 텍스트 전부를 이어 붙여 반환한다(어느 파일에 있는지는 안 가린다).

    실제 서비스라면 첨부별로 따로 돌려야 하지만, 이번 측정은 "idx 단위로 뽑을 수
    있는가"를 보는 것이라 idx 전체를 하나의 검색 대상으로 합쳤다.
    """
    parts = []
    for path in sorted(TEXT_DIR.glob(f"{idx}_*.txt")):
        parts.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parts)


def normalize_set(items: list[str]) -> set[str]:
    """공백 제거 + 끝의 괄호 주석(예: '(법인)', '(위임시)')을 뗀다.

    정답 세트는 '법인등기사항증명서(법인)'처럼 어느 조건에 해당하는지 괄호로
    적어뒀지만, 추출기는 서류명만 뽑고 조건은 보지 않는다. 괄호를 그대로 두고
    비교하면 서류명 자체는 맞혔는데도 문자열이 달라 전부 불일치로 잡힌다 —
    "서류명을 찾았는가"와 "조건까지 구분했는가"는 다른 질문이라 후자는 이번
    측정 범위에서 뺐다.
    """
    cleaned = [re.sub(r"[\(（][^)）]*[\)）]\s*$", "", item).strip() for item in items]
    return {re.sub(r"\s+", "", item) for item in cleaned if item}


def flatten_gt_docs(entry: dict) -> set[str]:
    if "items" in entry:
        return normalize_set(entry["items"])
    names: list[str] = []
    for key, value in entry.items():
        if key.startswith("items") and isinstance(value, list):
            names.extend(value)
        elif key == "items_by_category" and isinstance(value, dict):
            for v in value.values():
                names.extend(v)
    return normalize_set(names)


def score_set(extracted: set[str], truth: set[str]) -> dict:
    tp = extracted & truth
    fp = extracted - truth
    fn = truth - extracted
    precision = len(tp) / len(extracted) if extracted else (1.0 if not truth else 0.0)
    recall = len(tp) / len(truth) if truth else (1.0 if not extracted else 0.0)
    return {
        "tp": sorted(tp), "fp": sorted(fp), "fn": sorted(fn),
        "precision": precision, "recall": recall,
    }


def main() -> None:
    if not TEXT_DIR.exists():
        print(f"첨부 텍스트 디렉터리를 찾을 수 없습니다: {TEXT_DIR}", file=sys.stderr)
        sys.exit(1)

    answer_key = json.loads(ANSWER_KEY_PATH.read_text(encoding="utf-8"))
    results: dict[str, dict] = {t: {} for t in
                                 ["submission_docs", "submission_docs_production",
                                  "qualification_numbers", "appraisal_cover", "forms", "clause_boundaries"]}

    for idx in TARGET_IDX:
        text = load_idx_texts(idx)
        gt = answer_key[idx]

        # 1. 제출서류 — 프로토타입(절 앵커+윈도)
        extracted_docs = normalize_set(extract_submission_docs(text))
        truth_docs = flatten_gt_docs(gt["submission_docs"]) if gt["submission_docs"]["present"] else set()
        results["submission_docs"][idx] = score_set(extracted_docs, truth_docs)

        # 1-production. 제출서류 — 실제 서비스 배선(server.extract_doc_items, 줄 단위 · 창 없음)
        production_items = server.extract_doc_items({}, [(f"첨부:{idx}", text)])
        extracted_production = normalize_set([it["name"] for it in production_items])
        results["submission_docs_production"][idx] = score_set(extracted_production, truth_docs)

        # 2. 자격요건 수치
        extracted_nums = normalize_set(extract_qualification_numbers(text))
        truth_nums = normalize_set([it["value"] for it in gt["qualification_numbers"].get("items", [])]) \
            if gt["qualification_numbers"]["present"] else set()
        results["qualification_numbers"][idx] = score_set(extracted_nums, truth_nums)

        # 3. 감정평가 표지값
        extracted_appraisal = extract_appraisal_cover(text)
        gt_appraisal = gt["appraisal_cover"]
        if gt_appraisal["present"]:
            hit_amount = bool(extracted_appraisal and extracted_appraisal["amount_krw"] == gt_appraisal["amount_krw"])
            hit_date = bool(
                extracted_appraisal
                and extracted_appraisal.get("base_date") == gt_appraisal.get("base_date")
            )
            results["appraisal_cover"][idx] = {
                "applicable": True,
                "extracted": extracted_appraisal,
                "truth_amount": gt_appraisal["amount_krw"],
                "truth_date": gt_appraisal.get("base_date"),
                "hit_amount": hit_amount,
                "hit_date": hit_date,
            }
        else:
            results["appraisal_cover"][idx] = {
                "applicable": False,
                "false_positive": extracted_appraisal is not None,
                "extracted": extracted_appraisal,
            }

        # 4. 서식 존재확인
        extracted_forms = normalize_set(extract_forms(text))
        truth_forms = normalize_set(gt["forms"]["items"]) if gt["forms"]["present"] else set()
        results["forms"][idx] = score_set(extracted_forms, truth_forms)

        # 5. 조 경계탐지
        extracted_clauses = extract_clause_boundaries(text)
        extracted_articles = {c["article"] for c in extracted_clauses if c["sub"] is None}
        cb = gt["clause_boundaries"]
        if cb["present"]:
            truth_articles = set(cb.get("articles_confirmed") or range(cb["min_article"], cb["max_article"] + 1))
        else:
            truth_articles = set()
        results["clause_boundaries"][idx] = score_set(
            {str(a) for a in extracted_articles}, {str(a) for a in truth_articles}
        )

    print_report(results, answer_key)
    out_path = REPO_ROOT / "tests/fixtures/attachment_extraction_results.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n상세 결과 JSON: {out_path.relative_to(REPO_ROOT)}")


def print_report(results: dict, answer_key: dict) -> None:
    print("=" * 70)
    print("첨부추출 규칙기반 프로토타입 정확도 측정 (10건 표본)")
    print("=" * 70)

    for type_name, label in [
        ("submission_docs", "1. 제출서류 (프로토타입 · 절 앵커+윈도)"),
        ("submission_docs_production", "1-production. 제출서류 (실제 서비스 배선 · 줄 단위)"),
        ("qualification_numbers", "2. 자격요건 수치"),
        ("forms", "4. 서식 존재확인"),
    ]:
        print(f"\n## {label}")
        total_tp = total_fp = total_fn = 0
        for idx, r in results[type_name].items():
            total_tp += len(r["tp"])
            total_fp += len(r["fp"])
            total_fn += len(r["fn"])
            flag = "OK" if not r["fp"] and not r["fn"] else ("부분" if r["tp"] else "실패")
            print(f"  idx{idx}: 정답{len(r['tp']) + len(r['fn'])}건 중 적중{len(r['tp'])} "
                  f"헛뽑음{len(r['fp'])} 누락{len(r['fn'])} [{flag}]")
            if r["fp"]:
                print(f"    헛뽑음: {r['fp']}")
            if r["fn"]:
                print(f"    누락: {r['fn']}")
        precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else float("nan")
        recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else float("nan")
        print(f"  => 전체: 정밀도 {precision:.0%} 재현율 {recall:.0%} (TP={total_tp} FP={total_fp} FN={total_fn})")

    print("\n## 3. 감정평가 표지값")
    applicable = [r for r in results["appraisal_cover"].values() if r["applicable"]]
    not_applicable = [r for r in results["appraisal_cover"].values() if not r["applicable"]]
    amount_hits = sum(1 for r in applicable if r["hit_amount"])
    date_hits = sum(1 for r in applicable if r["hit_date"])
    fps = sum(1 for r in not_applicable if r["false_positive"])
    for idx, r in results["appraisal_cover"].items():
        if r["applicable"]:
            status = "OK" if r["hit_amount"] else "실패"
            print(f"  idx{idx}: 금액 정답{r['truth_amount']:,} 추출{r['extracted']['amount_krw'] if r['extracted'] else None} [{status}]"
                  f" / 기준시점 정답{r['truth_date']} 추출{r['extracted'].get('base_date') if r['extracted'] else None}"
                  f" [{'OK' if r['hit_date'] else '실패'}]")
        else:
            status = "헛뽑음(오탐)" if r["false_positive"] else "OK(해당없음 정답 유지)"
            print(f"  idx{idx}: 감정평가서 없음 — 추출결과 {r['extracted']} [{status}]")
    print(f"  => 적용대상 {len(applicable)}건 중 금액 적중 {amount_hits}건, 기준시점 적중 {date_hits}건 / "
          f"비적용 {len(not_applicable)}건 중 오탐 {fps}건")

    print("\n## 5. 조 경계탐지")
    total_tp = total_fp = total_fn = 0
    for idx, r in results["clause_boundaries"].items():
        total_tp += len(r["tp"])
        total_fp += len(r["fp"])
        total_fn += len(r["fn"])
        n_truth = len(r["tp"]) + len(r["fn"])
        print(f"  idx{idx}: 진짜조문{n_truth}개 중 적중{len(r['tp'])} 헛뽑음(법령인용등){len(r['fp'])} 누락{len(r['fn'])}")
    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else float("nan")
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else float("nan")
    print(f"  => 전체: 정밀도 {precision:.0%} 재현율 {recall:.0%} (TP={total_tp} FP={total_fp} FN={total_fn})")


if __name__ == "__main__":
    main()
