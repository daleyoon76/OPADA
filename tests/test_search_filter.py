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


def test_split_open_bid_items_drops_closed_and_counts() -> None:
    # 2026-10-28 동원님 결정: 입찰 기간이 끝난 물건(수의계약가능 · 입찰마감)은 결과에서 빼고 건수만 알린다.
    now = "202610281600"
    items = [
        make_item(onbidCltrno=1, pbctStatNm="입찰진행중", cltrBidEndDt="202610301600"),
        make_item(onbidCltrno=2, pbctStatNm="입찰준비중", cltrBidEndDt="202611101600"),
        make_item(onbidCltrno=3, pbctStatNm="수의계약가능", cltrBidEndDt="202610221600"),
        make_item(onbidCltrno=4, pbctStatNm="입찰마감", cltrBidEndDt="202610281500"),
        # 상태는 열려 있지만 캐시가 낡아 그 사이 마감된 물건
        make_item(onbidCltrno=5, pbctStatNm="입찰진행중", cltrBidEndDt="202610281559"),
        # 마감이 지금과 같은 분이면 아직 남긴다
        make_item(onbidCltrno=6, pbctStatNm="입찰진행중", cltrBidEndDt="202610281600"),
    ]
    kept, excluded = server.split_open_bid_items(items, now)
    ids = [i["onbidCltrno"] for i in kept]
    check("S28 입찰 가능한 물건만 남김", ids == [1, 2, 6], str(ids))
    check("S29 뺀 건수는 3", excluded == 3, str(excluded))
    check("S30 수의계약가능은 마감일이 미래여도 뺌",
          server.split_open_bid_items([make_item(pbctStatNm="수의계약가능", cltrBidEndDt="202612311600")], now)[1] == 1)
    check("S31 마감일시가 없으면 상태만으로 판정",
          len(server.split_open_bid_items([make_item(pbctStatNm="입찰진행중", cltrBidEndDt=None)], now)[0]) == 1)


def test_search_item_detail_url() -> None:
    item = make_item(onbidCltrno=1147301, pbctCdtnNo=6247576, onbidPbancNo=909691, pbctNo=10110341)
    url = server.search_item_detail_url(item)
    check(
        "S32 물건상세 URL은 네 번호를 모두 담음",
        url == "https://www.onbid.co.kr/op/cltrpbancinf/cltrdtl/CltrDtlController/mvmnCltrDtl.do"
        "?onbidCltrno=1147301&pbctCdtnNo=6247576&onbidPbancNo=909691&pbctNo=10110341",
        url,
    )
    for key in ("onbidCltrno", "pbctCdtnNo", "onbidPbancNo", "pbctNo"):
        ids = {"onbidCltrno": 1147301, "pbctCdtnNo": 6247576, "onbidPbancNo": 909691, "pbctNo": 10110341}
        missing = make_item(**{**ids, key: None})
        check(f"S33 {key} 없으면 빈 문자열", server.search_item_detail_url(missing) == "", server.search_item_detail_url(missing))


def test_refresh_top_items_live_keeps_list_failed_count() -> None:
    # 2026-10-28 실측: 입찰정보 API는 유찰이 19번 넘은 물건에도 usbdNft 0을 줬다. 목록 값을 지킨다.
    # 실제 HTTP 대신 call_public_data 를 이 테스트에서만 바꿔 끼운다(연기).
    calls: list[dict[str, str]] = []

    def fake_call(name: str, params: dict[str, str], key: str) -> dict[str, object]:
        calls.append(params)
        return {"ok": True, "items": [{"usbdNft": 0, "cltrBidBgngDt": "202611200900", "cltrBidEndDt": "202611271700"}]}

    original = server.call_public_data
    server.call_public_data = fake_call
    try:
        items = [make_item(onbidCltrno=i, usbdNft=19, cltrBidEndDt="202611261700") for i in range(3)]
        out = server.refresh_top_items_live(items, "key", limit=2)
    finally:
        server.call_public_data = original
    check("S34 유찰 횟수는 목록 값 그대로", [i["usbdNft"] for i in out] == [19, 19, 19], str([i["usbdNft"] for i in out]))
    check("S35 마감일시는 실시간 값으로", [i["cltrBidEndDt"] for i in out[:2]] == ["202611271700"] * 2, str(out[:2]))
    check("S36 limit 밖은 손대지 않음", out[2]["cltrBidEndDt"] == "202611261700" and "liveRefreshed" not in out[2], str(out[2]))
    check("S37 다시 확인한 물건에 표지", [i.get("liveRefreshed") for i in out[:2]] == [True, True], str(out[:2]))
    check("S38 호출은 limit 만큼", len(calls) == 2, str(calls))


def test_refresh_error_hides_raw_exception() -> None:
    # reviewer r1 P1-1: 목록 갱신 실패 원문(urlopen 오류)이 cacheRefreshError 로 화면에 나가지 않는다.
    import tempfile
    import urllib.error

    def failing_fetch(key: str) -> list[dict[str, object]]:
        raise urllib.error.URLError("nodename nor servname provided")

    original_path, original_fetch, original_key = server.CLTR_CACHE_PATH, server.fetch_all_cltr_items, server.public_data_service_key
    with tempfile.TemporaryDirectory() as tmp:
        server.CLTR_CACHE_PATH = Path(tmp) / "missing.json"
        server.fetch_all_cltr_items = failing_fetch
        server.public_data_service_key = lambda: "key"
        try:
            cache = server.refresh_cltr_cache()
        finally:
            server.CLTR_CACHE_PATH, server.fetch_all_cltr_items, server.public_data_service_key = (
                original_path, original_fetch, original_key,
            )
    error = str(cache.get("refreshError") or "")
    check("S39 갱신 실패를 알림", bool(error), str(cache))
    check("S40 원문을 싣지 않음", "urlopen" not in error and "nodename" not in error, error)
    check("S41 빈 캐시는 fetchedAt 이 빈 값", cache.get("fetchedAt") == "" and cache.get("items") == [], str(cache))
    check("S57 네트워크 실패 이유가 실린다", cache.get("refreshErrorReason") == "network", str(cache))


def test_refresh_error_reason_no_key() -> None:
    # reviewer r2 ③: 인증키가 없으면 화면이 "키 없음"을 "네트워크 실패"와 구분할 수 있는 이유가 실려야 한다.
    import tempfile

    original_path, original_key = server.CLTR_CACHE_PATH, server.public_data_service_key
    with tempfile.TemporaryDirectory() as tmp:
        server.CLTR_CACHE_PATH = Path(tmp) / "missing.json"
        server.public_data_service_key = lambda: ""
        try:
            cache = server.refresh_cltr_cache()
        finally:
            server.CLTR_CACHE_PATH, server.public_data_service_key = original_path, original_key
    check("S58 인증키 없음 이유가 실린다", cache.get("refreshErrorReason") == "no_key", str(cache))


def test_kst_now_digits_ignores_server_timezone() -> None:
    # reviewer r1: 마감일시는 KST 다. 서버 TZ 가 UTC 여도 같은 값을 줘야 한다.
    import os
    import time

    # 프로세스 TZ 를 UTC 로 바꿔야 「localtime 으로 되돌림」 변이가 KST 기계에서도 붉어진다(reviewer r2 ①).
    original_time, original_tz = time.time, os.environ.get("TZ")
    os.environ["TZ"] = "UTC"
    time.tzset()
    time.time = lambda: 0.0  # 1970-01-01 00:00 UTC = 09:00 KST
    try:
        value = server.kst_now_digits()
    finally:
        time.time = original_time
        if original_tz is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = original_tz
        time.tzset()
    check("S42 KST 로 계산", value == "197001010900", value)


def test_order_search_items_marks_name_usage_conflict() -> None:
    # 2026-10-28 동원님 제보: 「서울 아파트 실거주」 결과에 분류가 아파트인 「(유)갈현상가 제818호」가 섞였다.
    items = [
        make_item(onbidCltrno=1, cltrUsgSclsCtgrNm="아파트", onbidCltrNm="서울특별시 은평구 갈현동 548 (유)갈현상가 제8층 제818호"),
        make_item(onbidCltrno=2, cltrUsgSclsCtgrNm="아파트", onbidCltrNm="서울특별시 금천구 독산동 1147 금천롯데캐슬골드파크1차 제102동"),
        make_item(onbidCltrno=3, cltrUsgSclsCtgrNm="근린생활시설", onbidCltrNm="서울특별시 어느 상가 1층"),
        make_item(onbidCltrno=4, cltrUsgSclsCtgrNm="다세대주택", onbidCltrNm="서울특별시 어느 빌라 지하 점포"),
    ]
    out = server.order_search_items(items)
    check("S43 어긋난 물건은 뒤로, 나머지 순서 유지", [i["onbidCltrno"] for i in out] == [2, 3, 1, 4], str([i["onbidCltrno"] for i in out]))
    check("S44 표지는 걸린 낱말", [i["nameUsageConflict"] for i in out] == ["", "", "상가", "점포"], str([i["nameUsageConflict"] for i in out]))
    check("S45 상업용 분류의 상가는 표지 없음", server.search_usage_name_conflict(items[2]) == "")
    check("S46 아무것도 빼지 않음", len(out) == len(items))
    # 낱말 · 주거 소분류마다 리터럴 기대값으로 단정한다. 상수를 순회해 기대값을 만들면 상수와 함께 움직인다(reviewer r3 P2-2).
    for case_id, usage, name, expected in (
        ("S48", "아파트", "어느 아파트 근린생활동 101호", "근린"),
        ("S49", "아파트", "어느 아파트 관리사무실", "사무실"),
        ("S50", "아파트", "어느 아파트 지하 창고", "창고"),
        ("S51", "단독주택", "어느 마을 주택 및 공장", "공장"),
        ("S52", "연립주택", "어느 연립 1층 상가", "상가"),
        ("S53", "도시형생활주택", "어느 도시형 1층 점포", "점포"),
        ("S54", "기타주거용건물", "어느 주거용 건물 1층 상가", "상가"),
        ("S55", "다가구주택", "어느 다가구 1층 점포", "점포"),
        ("S56", "빌라", "어느 빌라 1층 상가", "상가"),
    ):
        got = server.search_usage_name_conflict(make_item(cltrUsgSclsCtgrNm=usage, onbidCltrNm=name))
        check(f"{case_id} {usage} · {expected}", got == expected, got)


def test_search_route_orders_before_live_refresh() -> None:
    # 라우트가 첫 split 뒤 · 실시간 재확인 앞에서 정렬을 한 번 부르는지 본다(reviewer r3 P2-1).
    # 창은 /api/search 블록으로 좁히고 주석은 지운다. 이 검사는 호출 인자는 보지 않는다.
    route = Path(server.__file__).read_text(encoding="utf-8")
    start = route.index('if parsed.path == "/api/search":')
    block = route[start:route.index("self.send_json(404", start)]
    code = "\n".join(line.split("#")[0] for line in block.splitlines())
    pos = [code.find(name) for name in ("split_open_bid_items(", "order_search_items(", "refresh_top_items_live(")]
    # 결과를 matched 에 다시 담는지도 본다. 결과를 버리거나 다른 변수에 담는 변이가 살아남았다(reviewer r4 P2-1).
    assigned = "matched = order_search_items(matched)" in [line.strip() for line in code.splitlines()]
    check("S47 라우트: split → order → 재확인 순서로 한 번", -1 not in pos and pos[0] < pos[1] < pos[2] and code.count("order_search_items(") == 1 and assigned, str(pos))


def test_search_route_hides_exception_text() -> None:
    # reviewer r1 P2-4: /api/search 블록의 400 응답이 예외 원문(str(exc))을 그대로 보내지 않는지 본다.
    # /api/analyze · /api/ask 는 이번 처방 범위 밖이라 str(exc) 가 남아 있어도 된다.
    route = Path(server.__file__).read_text(encoding="utf-8")
    start = route.index('if parsed.path == "/api/search":')
    block = route[start:route.index("self.send_json(404", start)]
    code = "\n".join(line.split("#")[0] for line in block.splitlines())
    check("S59 /api/search 400 은 str(exc) 를 보내지 않음", "self.send_json(400" in code and "str(exc)" not in code, code)


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
        test_split_open_bid_items_drops_closed_and_counts,
        test_search_item_detail_url,
        test_refresh_top_items_live_keeps_list_failed_count,
        test_refresh_error_hides_raw_exception,
        test_refresh_error_reason_no_key,
        test_kst_now_digits_ignores_server_timezone,
        test_order_search_items_marks_name_usage_conflict,
        test_search_route_orders_before_live_refresh,
        test_search_route_hides_exception_text,
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
