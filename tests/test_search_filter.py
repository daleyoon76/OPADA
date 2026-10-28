"""AI 자연어 물건 검색 — 필터 정규화·필터링 게이트.

의존성 없이 `python3 tests/test_search_filter.py`로 돌린다.

여기서 검증하는 것은 "자연어 → 필터 JSON" 변환의 순수 함수 둘뿐이다.
LLM 호출(gemini_parse_search_query)과 공공데이터 API 호출(fetch_all_cltr_items·
refresh_top_items_live의 실제 HTTP)은 이 파일이 검증하지 못한다 — 라이브 호출로만
확인했다(핸드오프 참고).

픽스처 필드명은 team-reports/2026-10-22-demo-candidate-search/raw-cltr-list.json.gz의
실제 getRlstCltrList2 응답 스키마를 그대로 썼다.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import server  # noqa: E402

FAILURES: list[str] = []
PASSED = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global PASSED
    if condition:
        PASSED += 1
    else:
        FAILURES.append(f"{name}{f' — {detail}' if detail else ''}")


def make_item(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "onbidCltrno": 1,
        "cltrMngNo": "2026-0300-002152",
        "pbctCdtnNo": 5962095,
        "onbidCltrNm": "서울특별시 중구 어느 상가",
        "prptDivNm": "국유재산",
        "dspsMthodNm": "매각",
        "cltrUsgMclsCtgrNm": "상가용및업무용건물",
        "cltrUsgSclsCtgrNm": "근린생활시설",
        "lctnSdnm": "서울특별시",
        "lctnSggnm": "중구",
        "apslEvlAmt": 120000000,
        "lowstBidPrcIndctCont": "95000000",
        "usbdNft": 2,
    }
    base.update(overrides)
    return base


def test_normalize_drops_values_outside_closed_list() -> None:
    raw = {
        "prptDivNm": ["국유재산", "존재하지않는유형"],
        "dspsMthodNm": ["매각", "증여"],
        "usageCategories": ["근린생활시설", "달나라"],
    }
    out = server.normalize_search_filter(raw)
    check("S1 닫힌 목록 밖 재산유형 제거", out["prptDivNm"] == ["국유재산"], str(out["prptDivNm"]))
    check("S1 닫힌 목록 밖 처분방식 제거", out["dspsMthodNm"] == ["매각"], str(out["dspsMthodNm"]))
    check("S1 닫힌 목록 밖 용도 제거", out["usageCategories"] == ["근린생활시설"], str(out["usageCategories"]))


def test_normalize_clamps_numbers_and_rejects_bool() -> None:
    raw = {
        "maxLowestBidPrice": 100000000,
        "minFailedBidCount": 2,
        "maxFailedBidCount": True,  # bool은 int의 서브클래스라 가드가 없으면 1로 샌다
        "minAppraisalPrice": -5,
    }
    out = server.normalize_search_filter(raw)
    check("S2 가격 상한 보존", out["maxLowestBidPrice"] == 100000000, str(out["maxLowestBidPrice"]))
    check("S2 유찰 하한 보존", out["minFailedBidCount"] == 2, str(out["minFailedBidCount"]))
    check("S2 bool은 숫자로 안 센다", out["maxFailedBidCount"] is None, str(out["maxFailedBidCount"]))
    check("S2 음수 가격 제거", out["minAppraisalPrice"] is None, str(out["minAppraisalPrice"]))


def test_normalize_missing_keys_default_safely() -> None:
    out = server.normalize_search_filter(None)
    check("S3 raw가 None이면 빈 필터", out["sido"] == [] and out["prptDivNm"] == [], str(out))
    check("S3 가격 필드 기본값 None", out["maxLowestBidPrice"] is None, str(out))


def test_parse_search_filter_payload_extracts_json_from_gemini_text() -> None:
    payload = {
        "candidates": [
            {"content": {"parts": [{"text": '{"sido": ["서울특별시"], "maxLowestBidPrice": 100000000}'}]}}
        ]
    }
    parsed = server.parse_search_filter_payload(payload)
    check("S4 gemini 응답에서 JSON 추출", parsed == {"sido": ["서울특별시"], "maxLowestBidPrice": 100000000}, str(parsed))


def test_parse_search_filter_payload_returns_none_without_candidates() -> None:
    check("S5 candidates 없으면 None", server.parse_search_filter_payload({}) is None)
    check("S5 payload가 dict가 아니면 None", server.parse_search_filter_payload("오류") is None)


def test_filter_region_match() -> None:
    items = [make_item(onbidCltrno=1, lctnSdnm="서울특별시"), make_item(onbidCltrno=2, lctnSdnm="부산광역시")]
    filters = server.normalize_search_filter({"sido": ["서울"]})
    out = server.filter_cltr_items(items, filters)
    check("S6 시도 부분일치로 걸러짐", [i["onbidCltrno"] for i in out] == [1], str(out))


def test_filter_prpt_div_and_disposal_exact_match() -> None:
    items = [
        make_item(onbidCltrno=1, prptDivNm="국유재산", dspsMthodNm="매각"),
        make_item(onbidCltrno=2, prptDivNm="공유재산", dspsMthodNm="매각"),
        make_item(onbidCltrno=3, prptDivNm="국유재산", dspsMthodNm="임대"),
    ]
    filters = server.normalize_search_filter({"prptDivNm": ["국유재산"], "dspsMthodNm": ["매각"]})
    out = server.filter_cltr_items(items, filters)
    check("S7 재산유형+처분방식 둘 다 맞는 것만", [i["onbidCltrno"] for i in out] == [1], str(out))


def test_filter_usage_category_matches_either_level() -> None:
    items = [
        make_item(onbidCltrno=1, cltrUsgSclsCtgrNm="근린생활시설", cltrUsgMclsCtgrNm="상가용및업무용건물"),
        make_item(onbidCltrno=2, cltrUsgSclsCtgrNm="아파트", cltrUsgMclsCtgrNm="주거용건물"),
    ]
    filters = server.normalize_search_filter({"usageCategories": ["근린생활시설"]})
    out = server.filter_cltr_items(items, filters)
    check("S8 소분류 일치", [i["onbidCltrno"] for i in out] == [1], str(out))


def test_filter_price_excludes_hidden_price() -> None:
    # 최저입찰가 0은 "비공개"다(known-pitfalls「가격 표시」). 가격 조건이 있으면 제외해야 한다.
    items = [
        make_item(onbidCltrno=1, lowstBidPrcIndctCont="80000000"),
        make_item(onbidCltrno=2, lowstBidPrcIndctCont="0"),
        make_item(onbidCltrno=3, lowstBidPrcIndctCont="150000000"),
    ]
    filters = server.normalize_search_filter({"maxLowestBidPrice": 100000000})
    out = server.filter_cltr_items(items, filters)
    check("S9 상한 이하만 남고 비공개(0)는 제외", [i["onbidCltrno"] for i in out] == [1], str(out))
    # 음성 대조: 가격 조건이 전혀 없으면 비공개 물건도 그대로 통과해야 한다(S9 혼자 가격을 거르는 게 아님을 확인).
    out_no_price_filter = server.filter_cltr_items(items, server.normalize_search_filter({}))
    check("S9 음성대조 — 가격 조건 없으면 비공개도 통과", len(out_no_price_filter) == 3, str(out_no_price_filter))


def test_filter_failed_bid_count_threshold() -> None:
    items = [
        make_item(onbidCltrno=1, usbdNft=0),
        make_item(onbidCltrno=2, usbdNft=2),
        make_item(onbidCltrno=3, usbdNft=5),
    ]
    filters = server.normalize_search_filter({"minFailedBidCount": 2})
    out = server.filter_cltr_items(items, filters)
    check("S10 유찰 2회 이상만", sorted(i["onbidCltrno"] for i in out) == [2, 3], str(out))


def test_filter_keywords_require_all() -> None:
    items = [
        make_item(onbidCltrno=1, onbidCltrNm="서울특별시 중구 명동 근린생활시설"),
        make_item(onbidCltrno=2, onbidCltrNm="부산광역시 해운대구 아파트"),
    ]
    filters = server.normalize_search_filter({"keywords": ["명동"]})
    out = server.filter_cltr_items(items, filters)
    check("S11 키워드 포함 물건만", [i["onbidCltrno"] for i in out] == [1], str(out))


def test_filter_combined_scenario_from_spec() -> None:
    """작업 지시 예시 — "서울에서 1억 아래 상가, 두 번 이상 유찰"을 재현한다."""
    items = [
        make_item(
            onbidCltrno=10,
            lctnSdnm="서울특별시",
            cltrUsgSclsCtgrNm="근린생활시설",
            lowstBidPrcIndctCont="95000000",
            usbdNft=2,
        ),
        # 음성 — 서울이지만 유찰 1회뿐
        make_item(
            onbidCltrno=11,
            lctnSdnm="서울특별시",
            cltrUsgSclsCtgrNm="근린생활시설",
            lowstBidPrcIndctCont="95000000",
            usbdNft=1,
        ),
        # 음성 — 유찰 2회지만 가격이 1억 초과
        make_item(
            onbidCltrno=12,
            lctnSdnm="서울특별시",
            cltrUsgSclsCtgrNm="근린생활시설",
            lowstBidPrcIndctCont="150000000",
            usbdNft=3,
        ),
        # 음성 — 조건 다 맞지만 지역이 다름
        make_item(
            onbidCltrno=13,
            lctnSdnm="부산광역시",
            cltrUsgSclsCtgrNm="근린생활시설",
            lowstBidPrcIndctCont="95000000",
            usbdNft=4,
        ),
    ]
    filters = server.normalize_search_filter({
        "sido": ["서울"],
        "usageCategories": ["근린생활시설"],
        "maxLowestBidPrice": 100000000,
        "minFailedBidCount": 2,
    })
    out = server.filter_cltr_items(items, filters)
    check("S12 네 조건 모두 맞는 1건만 통과", [i["onbidCltrno"] for i in out] == [10], str(out))


def test_filter_empty_filters_returns_all() -> None:
    items = [make_item(onbidCltrno=1), make_item(onbidCltrno=2)]
    out = server.filter_cltr_items(items, server.normalize_search_filter({}))
    check("S13 빈 필터는 전부 통과", len(out) == 2, str(out))


def test_cltr_cache_is_stale() -> None:
    import time

    fresh = {"fetchedAtEpoch": time.time()}
    stale = {"fetchedAtEpoch": time.time() - 2 * 24 * 3600}
    missing = {"fetchedAtEpoch": 0.0}
    check("S14 방금 받은 캐시는 신선함", server.cltr_cache_is_stale(fresh) is False)
    check("S15 24시간 넘은 캐시는 낡음", server.cltr_cache_is_stale(stale) is True)
    check("S16 fetchedAtEpoch 없으면 낡음으로 본다", server.cltr_cache_is_stale(missing) is True)


def test_normalize_accepts_single_string_for_list_fields() -> None:
    # 2026-10-28 라이브: LLM이 "dspsMthodNm": "임대" · "prptDivNm": "압류재산"처럼 문자열 하나를 돌려줬다.
    filters = server.normalize_search_filter(
        {"prptDivNm": "압류재산", "dspsMthodNm": "임대", "usageCategories": "오피스텔", "sido": "부산광역시"}
    )
    check("S17 재산유형 문자열 하나도 받음", filters["prptDivNm"] == ["압류재산"], str(filters))
    check("S18 처분방식 문자열 하나도 받음", filters["dspsMthodNm"] == ["임대"], str(filters))
    check("S19 용도 문자열 하나도 받음", filters["usageCategories"] == ["오피스텔"], str(filters))
    check("S20 시도 문자열 하나도 받음", filters["sido"] == ["부산광역시"], str(filters))
    check("S21 닫힌 목록 밖 문자열은 여전히 버림", server.normalize_search_filter({"dspsMthodNm": "경매"})["dspsMthodNm"] == [])


def test_filter_region_matches_renamed_sido() -> None:
    # 목록 API는 개편된 시도 이름을 쓴다(2026-10-28 캐시 실측).
    items = [
        make_item(onbidCltrno=1, lctnSdnm="강원특별자치도"),
        make_item(onbidCltrno=2, lctnSdnm="전북특별자치도"),
        make_item(onbidCltrno=3, lctnSdnm="전남광주통합특별시"),
        make_item(onbidCltrno=4, lctnSdnm="경상남도"),
        make_item(onbidCltrno=5, lctnSdnm="경상북도"),
    ]

    def ids(sido: list[str]) -> list[object]:
        return [i["onbidCltrno"] for i in server.filter_cltr_items(items, server.normalize_search_filter({"sido": sido}))]

    check("S22 강원도 → 강원특별자치도", ids(["강원도"]) == [1], str(ids(["강원도"])))
    check("S23 전라북도 → 전북특별자치도", ids(["전라북도"]) == [2], str(ids(["전라북도"])))
    check("S24 전라남도 → 전남광주통합특별시", ids(["전라남도"]) == [3], str(ids(["전라남도"])))
    check("S25 광주광역시 → 전남광주통합특별시", ids(["광주광역시"]) == [3], str(ids(["광주광역시"])))
    check("S26 경남은 경상북도를 붙잡지 않음", ids(["경남"]) == [4], str(ids(["경남"])))
    check("S27 표에 없는 이름은 그대로 부분일치", ids(["전남광주통합특별시"]) == [3], str(ids(["전남광주통합특별시"])))


def main() -> int:
    tests = (
        test_normalize_drops_values_outside_closed_list,
        test_normalize_clamps_numbers_and_rejects_bool,
        test_normalize_missing_keys_default_safely,
        test_parse_search_filter_payload_extracts_json_from_gemini_text,
        test_parse_search_filter_payload_returns_none_without_candidates,
        test_filter_region_match,
        test_filter_prpt_div_and_disposal_exact_match,
        test_filter_usage_category_matches_either_level,
        test_filter_price_excludes_hidden_price,
        test_filter_failed_bid_count_threshold,
        test_filter_keywords_require_all,
        test_filter_combined_scenario_from_spec,
        test_filter_empty_filters_returns_all,
        test_cltr_cache_is_stale,
        test_normalize_accepts_single_string_for_list_fields,
        test_filter_region_matches_renamed_sido,
    )
    for test in tests:
        test()
    total = PASSED + len(FAILURES)
    for failure in FAILURES:
        print(f"FAIL {failure}")
    print(f"{PASSED}/{total} 통과")
    print(
        "연기한 것 — gemini_parse_search_query()의 실제 HTTP 호출, fetch_all_cltr_items()·"
        "refresh_top_items_live()의 실제 공공데이터 API 호출. 라이브 호출로만 확인했다."
    )
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
