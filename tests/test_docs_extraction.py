"""제출서류 추출·비공개 가격·마감 D-day 게이트.

의존성 없이 `python3 tests/test_docs_extraction.py` 로 돌린다.

연기한 것(`PLAYED`)과 축 표(`AXES`)는 아래 상수에 두고 **실행할 때마다 stdout 에 찍는다.**
docstring 에만 두면 로그를 받은 사람이 무엇이 연기됐는지 알 수 없다.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import server  # noqa: E402

FAILURES: list[str] = []
PASSED = 0

# 이 게이트가 프로덕션 호출부를 대신 «연기»한 심볼. 여기 있는 것은 이 파일이 검증하지 못한다.
PLAYED: tuple[tuple[str, str], ...] = (
    ("fetch_onbid()", "실제 HTTP 대신 이 파일의 픽스처 HTML을 넣는다"),
    (
        "build_notice()",
        "대부분의 축은 전체 조립 대신 build_doc_checklist·build_tasks·local_ai_coach 를 직접 부른다. "
        "단 B11 축은 build_notice 를 실제로 부르며 그때는 fetch_onbid·public_data_service_key 둘만 연기한다",
    ),
    ("화면 렌더", "이 파일은 화면을 연기하지 않는다. 화면 축은 tests/screen.spec.js 다"),
    (
        "urllib.request.urlopen()",
        "C1·C2 배선 축에서만 — 실제 HTTP 대신 픽스처 본문을 돌려주고 요청 URL 을 캡처한다. "
        "게이트웨이의 실제 응답과 실제 인증키는 이 파일이 검증하지 못한다",
    ),
    ("public_data_service_key()", "C1 배선 축에서만 — 실제 인증키 대신 더미 문자열을 넣는다"),
)

# 축 → 케이스 → 킬러 변이 → 커버(Y/N/영구불가)
AXES: tuple[tuple[str, str, str, str, str], ...] = (
    ("A1", "섹션 분리", "입찰방법 도움말 배제", "배제 제거", "Y"),
    ("A2", "서류명 어휘", "긴 이름 우선/열린 이름", "순서 뒤집기", "Y"),
    ("A3", "조건 물림", "ㅇ 머리글 → - 하위 항목 · 비하위항목 경계", "물림 삭제 · 하위항목 제한 삭제", "Y"),
    ("A4", "부정 문맥", "「불허용」 축 제외", "가드 삭제", "Y"),
    ("A5", "제출 동사 요구", "단순 언급 제외 · license 축 제외", "동사 요구 삭제 · license 필터 해제", "Y"),
    ("A6", "부가조건", "원본/유효기간/방법/기한", "파싱 삭제", "Y"),
    ("A7", "A/B/C 사전판정", "재산유형 → 코드", "표 비우기", "Y"),
    ("A8", "첨부 다운로드", "fn_chkPdfRead 5인자 · 빈 파라미터", "인자 무시 · 빈값 가드 해제", "Y"),
    ("A9", "온비드 표", "구분명만/공고문 확인", "generic 끄기", "Y"),
    ("B1", "추출 정직성", "구분명만 → 못 뽑았다 표시(not_found·C형) · 코치 배선", "옛 판정 복원 · headline 교체", "Y"),
    ("B2", "최저입찰가 비공개", "HideDivCd != 0001", "코드 무시", "Y"),
    ("B3", "마감 D-day", "시작 전/진행/임박/마감", "상태 고정", "Y"),
    ("B4", "비용 항목", "원문값만·세율 미계산", "세율 삽입", "Y"),
    ("B5", "공고문 목차", "번호 제목/서술문·파일명", "필터 삭제", "Y"),
    ("B6", "용어 안내", "재산유형·처분방식 뜻", "사전 비우기", "Y"),
    ("B7", "코치 직접제출 배선", "A형 실형태(서류 1건↑ + 항목 method 없음 + 표 직접제출)", "표 보조 근거 삭제 · 항목 가드 삭제", "Y"),
    ("B8", "입찰방법 값 추출", "공동/대리 값 분리 · 값 없음 · 툴팁만", "절 전체 훑기 · 창 경계 삭제", "Y"),
    ("B9", "공동입찰 축 배선", "화면 값 `or` 확장 · 기존 근거 보존", "or → 덮어쓰기 · 화면 값 무시", "Y"),
    ("B10", "명도책임 사실", "매수인 부담 · 없으면 빈 값 · 조건 축 아님", "조건 축에 물리기", "Y"),
    ("B11", "build_notice 배선", "공동/대리 값 갈림 · 값 뒤집기 · 절 없음", "빈 값 고정 · 대리입찰 값 탑재", "Y"),
    ("B11-1", "코치 action 문구", "서류 0건 → 목록 전제 없음 · 서류 근거 → 옛 문장", "분기 삭제(한 문장으로 합치기)", "Y"),
    (
        "C1",
        "물건관리번호 4-4-6",
        "하이픈 없는 14자리 · 이미 하이픈(멱등) · 14자리 아님(원문 통과) · 빈값/None · 요청 URL 배선",
        "하이픈 삽입 삭제 · 자리수 4-6-4 · 슬라이스 소스를 digits→value(멱등 파괴) · 배선 호출 삭제",
        "Y",
    ),
    (
        "C2",
        "게이트웨이 오류 봉투",
        "cmmMsgHeader.returnReasonCode 22 · returnAuthMsg 없으면 errMsg · 정상 봉투 불변 · 봉투는 item 아님",
        "OpenAPI_ServiceResponse 분기 삭제 · returnReasonCode 를 resultCode 로 안 옮기기",
        "Y",
    ),
)


def print_header() -> None:
    print(f"PLAYED — 이 게이트가 대신 연기한 것 {len(PLAYED)}개")
    for symbol, note in PLAYED:
        print(f"  · {symbol} — {note}")
    print(f"AXES — 축 {len(AXES)}개 (축 → 케이스 → 킬러 변이 → 커버)")
    for code, name, case, mutation, covered in AXES:
        print(f"  {code} {name:<14} → {case} → {mutation} → {covered}")
    print()


def check(name: str, condition: bool, detail: str = "") -> None:
    global PASSED
    if condition:
        PASSED += 1
    else:
        FAILURES.append(f"{name}{f' — {detail}' if detail else ''}")


def section(title: str, body: str) -> str:
    return f'<h2 class="tit">{title}</h2>{body}'


# ---------------------------------------------------------------------------
# 픽스처 — 표본조사(docs/90_MVP개발/07_제출서류_표본조사_20260907.md)에서 관측된 형태를
# 최소 크기로 옮긴 것이다. 문구는 표본 01·04·12·19·23의 실제 문장을 줄여 썼다.
# ---------------------------------------------------------------------------

# 온비드 「입찰방법」 절 도움말. 표본 23/23에 똑같이 들어 있고 위임장·대리입찰신청서·
# 공동입찰참가신청서를 포함한다. 서류명 탐색에 들어가면 전건 오탐이 된다.
ONBID_HELP_SECTION = section(
    "입찰방법",
    """
    <div class="tooltip_wrap01"><button class="tooltip"><span>도움말(공동입찰)</span></button>
      <div class="tooltip_box"><div class="tooltip_con"><ul>
        <li>서류제출방식: 공동입찰자 전원이 '공동입찰참가신청서' 등 관련 서류를 제출하는 방식</li>
        <li>대리입찰은 '대리입찰신청서', '위임장' 등 관련 서류를 제출하여야 유효합니다.</li>
      </ul></div></div>
    </div>
    <div class="left_box"><div class="tit_area01"><span class="txt_01">입찰보증금</span></div></div>
    <div class="item_box_cont"><div class="text_box01"><span class="txt01">최저입찰가격 X 10%</span></div></div>
    <div class="left_box"><div class="tit_area01"><span class="txt_01">잔대금 납부방법</span></div></div>
    <div class="item_box_cont"><div class="text_box01"><span class="txt01">일시불</span></div></div>
    """,
)

# 온비드 「제출서류」 표. 서류명 칸이 구분명 그대로인 표본 12건과 같은 모양이다.
GENERIC_DOCS_TABLE = section(
    "제출서류",
    """
    <table><tr><td>구분</td><td>서류명</td><td>제출기한</td><td>제출방법</td></tr>
    <tr><td>공동입찰서류</td><td>공동입찰서류</td><td>입찰마감일시 전까지</td><td>직접제출</td></tr>
    <tr><td>대리입찰서류</td><td>대리입찰서류</td><td>입찰마감일시 전까지</td><td>직접제출</td></tr></table>
    """,
)

# 표본 01(압류재산) 본문 형태 — 번호 조건 블록.
NUMBERED_CONDITION_NOTICE = section(
    "공고문",
    """
    <p>가. 부동산의 표시는 부동산등기사항증명서 기준이며, 수량은 법정계량단위 기준입니다.</p>
    <p>자. 입찰하려는 자가 미성년자이거나 다른 사람을 선임하여 입찰에 참가하려는 경우 또는
       여러 사람이 공동으로 입찰에 참가하려는 경우에는 다음 각 호의 서류를 직접 제출하여야 합니다.</p>
    <p>① 매수신청인이 미성년자인 경우 : 법정대리인의 미성년자 입찰참가 동의서 및 인감증명서(또는 본인서명사실확인서)와 주민등록등본 또는 가족관계증명서</p>
    <p>② 대리인을 선임한 경우 : 대리입찰신청서 및 대리입찰신청인(위임인)의 인감증명서</p>
    <p>③ 여러 사람이 공동으로 입찰에 참가하려는 경우 : 공동입찰참가신청서</p>
    """,
)

# 표본 04(국유재산) 본문 형태 — ㅇ 머리글 + - 하위 항목 + 부가조건 문장.
BULLET_CONDITION_NOTICE = section(
    "공고문",
    """
    <p>ㅇ 공동입찰의 경우 서류제출 방식을 선택할 경우에는 다음의 서류를 제출하여야 합니다.</p>
    <p>- 공동입찰 참가신청서</p>
    <p>- 공동입찰자의 인감증명서 또는 본인서명사실확인서</p>
    <p>ㅇ 대리입찰의 경우에는 다음의 서류를 제출하여야 합니다.</p>
    <p>- 대리입찰 참가신청서</p>
    <p>ㅇ 제출 서류는 원본으로 준비하여, 입찰 기간 마감일 17:00까지 우편으로 제출하여야 합니다.</p>
    """,
)

# 같은 도움말 문구를 툴팁 마크업 없이 둔 것. 「절 배제」와 「툴팁 제거」 두 가드를 각각
# 따로 고정하기 위한 픽스처다 — 하나만 남아도 통과하면 나머지 하나는 무증명이 된다.
NAKED_HELP_SECTION = section(
    "입찰방법",
    "<p>서류제출방식: 공동입찰자 전원이 '공동입찰참가신청서' 등 관련 서류를 제출하는 방식</p>"
    "<p>대리입찰은 '대리입찰신청서', '위임장' 등 관련 서류를 제출하여야 유효합니다.</p>",
)

# 하위 항목에 조건 낱말도 제출 동사도 없는 형태. 머리글의 조건 물림이 유일한 근거다.
CARRY_ONLY_NOTICE = section(
    "공고문",
    "<p>ㅇ 매수신청인이 미성년자인 경우에는 다음의 서류를 제출하여야 합니다.</p><p>- 주민등록등본</p>",
)

ATTACHMENT_HTML = """
<a href="javascript:devUtil.fn_chkPdfRead('17070043','3','','20260813033701195_1.pdf','COGFDOFI');">
  <span class="ico_pdf01"></span><span class="txt01">공유재산 사용수익허가 입찰공고문.pdf</span></a>
<a href="javascript:devUtil.fn_chkPdfRead('17070043','3','','20260813033701195_1.pdf','COGFDOFI');" class="file_link01">
  <span class="txt01">공유재산 사용수익허가 입찰공고문.pdf</span></a>
<a href="javascript:devUtil.fn_chkPdfRead('17070043','4','','20260813033701200_2.pdf','COGFDOFI');">
  <span class="txt01">사용허가 조건.pdf</span></a>
"""


def bid_method_item(label: str, value_html: str) -> str:
    """온비드 「입찰방법」 절 항목 박스 하나. 라벨과 값 사이에 실제와 같은 툴팁을 끼운다."""
    return f"""
    <li class="item pos"><div class="item_box01"><div class="item_box_tit">
      <div class="left_box"><div class="tit_area01">
        <span class="txt_01">{label}</span>
        <div class="tooltip_wrap01"><button class="tooltip"><span>도움말({label})</span></button>
          <div class="tooltip_box"><div class="tooltip_con"><ul>
            <li>서류제출방식: 공동입찰자 전원이 '공동입찰참가신청서' 등 관련 서류를 제출하는 방식</li>
          </ul></div></div>
        </div>
      </div></div>
      {value_html}
    </div></div></li>
    """


ICO_VALUE = '<div class="right_box"><div class="ico_box01"><span class="ico"></span><span class="txt_01">{}</span></div></div>'

# 표본 17의 형태 — 공동입찰과 대리입찰의 값이 갈린다. 두 축을 하나로 묶으면 안 되는 근거다.
BID_METHOD_SPLIT = section(
    "입찰방법",
    bid_method_item("공동입찰", ICO_VALUE.format("가능"))
    + bid_method_item("대리입찰", ICO_VALUE.format("불가능")),
)

# 라벨은 있고 값 박스가 없는 항목. 다음 항목(대리입찰)에는 값이 있으므로,
# 창을 다음 `tit_area01` 에서 끊지 않으면 옆 항목의 「가능」을 훔쳐온다.
BID_METHOD_NO_VALUE = section(
    "입찰방법",
    bid_method_item("공동입찰", "")
    + bid_method_item("대리입찰", ICO_VALUE.format("가능")),
)

# B11 음성 대조용. 두 라벨의 값을 서로 바꾼 것 — 표본 22 의 형태다.
# `build_notice` 가 「대리입찰」 값을 실어 나르면 여기서 「가능」이 나와 붉어진다.
BID_METHOD_SPLIT_REVERSED = section(
    "입찰방법",
    bid_method_item("공동입찰", ICO_VALUE.format("불가능"))
    + bid_method_item("대리입찰", ICO_VALUE.format("가능")),
)

# 🔴 킬러 변이용 음성 픽스처. 「공동입찰」 라벨 항목이 **없고** 툴팁 본문에만
# 「공동입찰참가신청서」가 있으며, 다른 항목(입찰보증금)이 값 「가능」을 갖는다.
# 절 전체를 훑어 문자열 존재만 보는 구현은 여기서 「가능」을 집어 붉어진다.
BID_METHOD_TOOLTIP_ONLY = section(
    "입찰방법",
    bid_method_item("입찰보증금", ICO_VALUE.format("가능")),
)

# 압류재산 공고문의 명도책임 문장. 표본 01·02·03 의 실제 두 줄을 그대로 줄여 썼다.
EVICTION_NOTICE = section(
    "공고문",
    "<p>다. 공매재산의 인도 및 명도책임</p>"
    "<p>- 부동산 명도책임은 매수인 부담이며, 동산은 보관중인 소재지에서 현 상태로 인도합니다.</p>",
)


# ---------------------------------------------------------------------------
# A1. 섹션 분리 — 입찰방법 도움말이 서류명으로 새지 않는가
# ---------------------------------------------------------------------------
def test_sections() -> None:
    sections = server.split_sections(ONBID_HELP_SECTION + GENERIC_DOCS_TABLE + NUMBERED_CONDITION_NOTICE)
    check("A1 절 제목 3개", set(sections) == {"입찰방법", "제출서류", "공고문"}, str(sorted(sections)))

    items = server.extract_doc_items(sections)
    names = {item["name"] for item in items}
    # 양성: 공고문 절의 조건별 서류는 잡힌다.
    check("A1 양성 미성년자 동의서", "미성년자 입찰참가 동의서" in names, str(sorted(names)))
    check("A1 양성 대리입찰신청서", "대리입찰신청서" in names, str(sorted(names)))
    # 음성 대조 1: 입찰방법 도움말에만 있는 「위임장」은 잡히면 안 된다.
    check("A1 음성 위임장 미검출", "위임장" not in names, str(sorted(names)))
    # 음성 대조 2: 도움말 문장이 근거로 인용되면 안 된다.
    check(
        "A1 음성 도움말 근거 미사용",
        all("서류제출방식" not in str(item["evidence"]) for item in items),
        "도움말 문장이 근거로 잡혔다",
    )
    # 음성 대조 3: 제출 동사도 조건도 없는 단순 언급은 잡히면 안 된다.
    check("A1 음성 단순 언급 제외", "등기사항증명서" not in names, str(sorted(names)))

    # 가드 ①: 절 배제. 툴팁 마크업이 없어도 입찰방법 절은 탐색 대상이 아니어야 한다.
    naked = server.extract_doc_items(server.split_sections(NAKED_HELP_SECTION))
    check("A1 가드① 절 배제", naked == [], str(naked))
    check("A1 가드① 목록 고정", "입찰방법" not in server.DOC_SEARCH_SECTIONS, str(server.DOC_SEARCH_SECTIONS))

    # 가드 ②: 툴팁 제거. 같은 절 안에 있어도 도움말 블록은 본문에서 지워져야 한다.
    stripped = server.strip_tooltips(ONBID_HELP_SECTION)
    check("A1 가드② 도움말 제거", "공동입찰참가신청서" not in stripped, stripped[:120])
    check("A1 가드② 본문은 보존", "최저입찰가격 X 10%" in stripped, stripped[:120])


# ---------------------------------------------------------------------------
# A2. 서류명 어휘 — 긴 이름 우선, 열린 이름은 원문 그대로
# ---------------------------------------------------------------------------
def test_doc_names() -> None:
    names = server.find_doc_names("법인 등기사항증명서 및 법인 인감증명서를 제출")
    check("A2 법인인감증명서", "법인인감증명서" in names, str(names))
    check("A2 법인 등기사항증명서", "법인 등기사항증명서" in names, str(names))
    # 음성 대조: 「법인 인감증명서」가 「인감증명서」로도 중복 계상되면 안 된다.
    check("A2 음성 인감증명서 중복 없음", "인감증명서" not in names, str(names))

    # 음성 대조(A5 license 축 제외): `등록증`·`면허` 는 서류명 토큰이라 「업종·자격 요건」 축에
    # 걸리지만, 그것만으로는 제출 요구를 증명하지 못한다. 제출 동사도 다른 조건도 없는 줄에서
    # 서류가 뽑히면 안 된다. 이 단언이 `extract_doc_items` 의 `authorizing` 필터를 고정한다.
    license_only = server.extract_doc_items(
        server.split_sections(
            section("공고문", "<p>본 시설은 옥외광고업 등록증을 보유한 업체만 사용할 수 있습니다.</p>")
        )
    )
    check("A5 음성 license 축만으로는 미추출", license_only == [], str(license_only))
    # 같은 문장에 제출 동사가 붙으면 뽑혀야 한다 — 위 단언이 영구 초록이 아님을 보인다.
    license_asked = server.extract_doc_items(
        server.split_sections(section("공고문", "<p>옥외광고업 등록증 사본 1부를 제출하여야 합니다.</p>"))
    )
    check("A5 양성 제출 동사 있으면 추출", [str(i["name"]) for i in license_asked] == ["옥외광고업 등록증"], str(license_asked))

    open_names = server.find_doc_names("옥외광고업 등록증 및 사업자등록증 사본을 제출")
    check("A2 열린 이름 원문 보존", "옥외광고업 등록증" in open_names, str(open_names))
    check("A2 사업자등록증", "사업자등록증" in open_names, str(open_names))
    # 음성 대조: 서류명이 없는 문장에서 아무것도 뽑히면 안 된다.
    check("A2 음성 빈 문장", server.find_doc_names("입찰보증금은 최저입찰가격의 10%입니다.") == [], "")


# ---------------------------------------------------------------------------
# A3. 조건 물림 — ㅇ 머리글의 조건을 - 하위 항목에 물린다
# ---------------------------------------------------------------------------
def test_condition_carry() -> None:
    sections = server.split_sections(BULLET_CONDITION_NOTICE)
    items = server.extract_doc_items(sections)
    joint = [item for item in items if "공동입찰" in item["conditions"]]
    proxy = [item for item in items if "대리입찰" in item["conditions"]]
    check("A3 공동입찰 물림", {str(item["name"]) for item in joint} >= {"공동입찰참가신청서"}, str(joint))
    check("A3 대리입찰 물림", {str(item["name"]) for item in proxy} >= {"대리입찰신청서"}, str(proxy))
    # 음성 대조: 대리 절의 서류가 공동 조건으로 새면 안 된다.
    check(
        "A3 음성 조건 누수 없음",
        all("공동입찰" not in item["conditions"] for item in items if item["name"] == "대리입찰신청서"),
        str(proxy),
    )

    numbered = server.extract_doc_items(server.split_sections(NUMBERED_CONDITION_NOTICE))
    minor = {str(item["name"]) for item in numbered if "미성년자" in item["conditions"]}
    check("A3 번호 조건 블록", minor >= {"미성년자 입찰참가 동의서", "주민등록등본"}, str(sorted(minor)))

    # 물림이 유일한 근거인 경우 — 하위 항목에 조건 낱말도 제출 동사도 없다.
    carry_only = server.extract_doc_items(server.split_sections(CARRY_ONLY_NOTICE))
    check("A3 물림만으로 추출", [str(item["name"]) for item in carry_only] == ["주민등록등본"], str(carry_only))
    check("A3 물림 조건 부여", carry_only and carry_only[0]["conditions"] == ["미성년자"], str(carry_only))

    # 음성 대조(물림 경계): 하위 항목 표식이 없는 줄은 물림 대상이 아니다.
    # 이 제한이 없으면 머리글 조건이 절 끝까지 새어 무관한 서류에 「미성년자」가 붙는다.
    # 위 `A3 음성 조건 누수 없음` 은 모든 줄이 하위 항목인 픽스처라 이 경계에 닿지 못한다.
    boundary = server.extract_doc_items(
        server.split_sections(
            section(
                "공고문",
                "<p>ㅇ 매수신청인이 미성년자인 경우에는 다음의 서류를 제출하여야 합니다.</p>"
                "<p>- 주민등록등본</p>"
                "<p>모든 입찰자는 인감증명서를 제출하여야 합니다.</p>",
            )
        )
    )
    labels = {str(item["name"]): list(item["conditions"]) for item in boundary}
    check("A3 경계 하위항목은 물림", labels.get("주민등록등본") == ["미성년자"], str(labels))
    check("A3 경계 음성 비하위항목은 미물림", labels.get("인감증명서") == ["공통"], str(labels))


# ---------------------------------------------------------------------------
# A4. 부정 문맥 — 「불허용」이면 그 축은 서류 분기가 아니다
# ---------------------------------------------------------------------------
def test_negative_condition() -> None:
    positive = server.find_conditions("여러 사람이 공동으로 입찰에 참가하려는 경우")
    check("A4 양성 공동입찰 축", any(item["key"] == "joint" and not item["negative"] for item in positive), str(positive))
    negative = server.find_conditions("공동입찰허용여부 [ 허용 / ■ 불허용 ]")
    check("A4 음성 불허용 표시", all(item["negative"] for item in negative), str(negative))

    blocked = server.split_sections(section("공고문", "<p>공동입찰 불허용이므로 공동입찰참가신청서는 받지 않습니다.</p>"))
    items = server.extract_doc_items(blocked)
    check(
        "A4 음성 불허용 문장은 공동 조건이 아님",
        all("공동입찰" not in item["conditions"] for item in items),
        str(items),
    )


# ---------------------------------------------------------------------------
# A5·A6. 제출 동사 요구와 부가조건
# ---------------------------------------------------------------------------
def test_extras() -> None:
    extras = server.doc_extras("- 제출 서류는 원본으로 준비하여, 입찰 기간 마감일 17:00까지 우편으로 제출")
    check("A6 원본", extras.get("copy") == "원본", str(extras))
    check("A6 제출방법 우편", extras.get("method") == "우편", str(extras))
    check("A6 기한", "17:00까지" in str(extras.get("due")), str(extras))

    validity = server.doc_extras("각종 증명서는 최근 1개월 이내 발급한 서류여야 합니다. 1부 제출")
    check("A6 유효기간", "1개월" in str(validity.get("validity")), str(validity))
    check("A6 부수", validity.get("count") == "1부", str(validity))

    # 음성 대조: 부가조건이 없는 문장에서 값을 지어내면 안 된다.
    plain = server.doc_extras("- 공동입찰 참가신청서")
    check("A6 음성 빈 부가조건", plain == {}, str(plain))

    # 음성 대조: 서류마다 기한이 다를 수 있다 — 같은 절의 두 항목이 다른 기한을 갖는다.
    staged = server.extract_doc_items(
        server.split_sections(
            section(
                "공고문",
                "<p>1) 공동입찰참가신청서 1부. 입찰마감일시 전까지 제출</p>"
                "<p>2) 사업자등록증 1부. 사용개시일 이전까지 제출</p>",
            )
        )
    )
    dues = {str(item["name"]): str(item["due"]) for item in staged}
    check("A6 서류별 기한 분리", dues.get("공동입찰참가신청서") != dues.get("사업자등록증"), str(dues))


# ---------------------------------------------------------------------------
# A7. 재산유형 → A/B/C 사전 판정
# ---------------------------------------------------------------------------
def test_profile() -> None:
    cases = {
        "압류재산": "A",
        "국유재산": "A",
        "공유재산": "B",
        "기타일반재산": "B",
        "수탁재산": "B",
        "파산자산": "C",
    }
    for asset_type, code in cases.items():
        check(f"A7 {asset_type}", server.doc_source_profile(asset_type)["code"] == code, asset_type)
    # 음성 대조: 모르는 값을 A나 B로 단정하면 안 된다.
    check("A7 음성 미상", server.doc_source_profile("재산유형 확인")["code"] == "unknown", "")
    check("A7 음성 빈값", server.doc_source_profile("")["code"] == "unknown", "")


# ---------------------------------------------------------------------------
# A8. 첨부 다운로드 파라미터
# ---------------------------------------------------------------------------
def test_attachments() -> None:
    docs = server.extract_related_docs(ATTACHMENT_HTML, "https://www.onbid.co.kr/op/x.do?a=1")
    check("A8 중복 제거", len(docs) == 2, str(docs))
    check("A8 파일명", docs[0]["name"] == "공유재산 사용수익허가 입찰공고문.pdf", str(docs))
    url = docs[0]["downloadUrl"]
    check("A8 경로", server.ATTACHMENT_DOWNLOAD_PATH in url, url)
    check("A8 atchFileLstNo", "atchFileLstNo=17070043" in url, url)
    check("A8 atchSn", "atchSn=3" in url, url)
    check("A8 hashCrpsNo", "hashCrpsNo=COGFDOFI" in url, url)
    check("A8 오리진", url.startswith("https://www.onbid.co.kr/"), url)
    # 음성 대조: 앵커가 없으면 빈 목록이며 가짜 URL을 만들지 않는다.
    # 주의 — 이 입력은 `ATTACHMENT_ANCHOR_RE` 에 매칭되지 않아 정규식 앞에서 걸러진다.
    # 빈 파라미터 가드(`not file_list_no or not hash_no`) 분기에는 도달하지 못하므로 아래를 따로 둔다.
    check("A8 음성 앵커 없음", server.extract_related_docs("<a href='#'>공고문.pdf</a>") == [], "")

    # 음성 대조(빈 파라미터 가드): 5인자 형태는 갖췄으나 atchFileLstNo·hashCrpsNo 가 비어 있다.
    # 이대로 URL을 만들면 `atchFileLstNo=&hashCrpsNo=` 인 깨진 링크를 정상 내려받기처럼 노출한다.
    empty_anchor = (
        "<a href=\"javascript:devUtil.fn_chkPdfRead('','3','','x.pdf','');\">"
        "<span class=\"txt01\">공고문.pdf</span></a>"
    )
    check("A8 음성 빈 atchFileLstNo", server.extract_related_docs(empty_anchor) == [], str(server.extract_related_docs(empty_anchor)))
    empty_hash = (
        "<a href=\"javascript:devUtil.fn_chkPdfRead('17070043','3','','x.pdf','');\">"
        "<span class=\"txt01\">공고문.pdf</span></a>"
    )
    check("A8 음성 빈 hashCrpsNo", server.extract_related_docs(empty_hash) == [], str(server.extract_related_docs(empty_hash)))
    # 도달 증거: 같은 형태에서 두 인자를 채우면 뽑힌다. 위 둘이 정규식 미매칭으로 통과한 게 아님을 보인다.
    filled = server.extract_related_docs(
        "<a href=\"javascript:devUtil.fn_chkPdfRead('17070043','3','','x.pdf','COGFDOFI');\">"
        "<span class=\"txt01\">공고문.pdf</span></a>"
    )
    check("A8 도달 증거 채우면 추출", len(filled) == 1 and "hashCrpsNo=COGFDOFI" in filled[0]["downloadUrl"], str(filled))


# ---------------------------------------------------------------------------
# A9·B1. 온비드 표의 구분명만 있는 상태를 추출 성공으로 세지 않는다
# ---------------------------------------------------------------------------
def test_generic_table_is_not_success() -> None:
    sections = server.split_sections(ONBID_HELP_SECTION + GENERIC_DOCS_TABLE)
    rows = server.extract_docs_table(sections)
    check("A9 표 2행", len(rows) == 2, str(rows))
    check("A9 구분명 판정", all(row["generic"] for row in rows), str(rows))

    checklist = server.build_doc_checklist(sections, "압류재산", [])
    check("B1 서류 0건", checklist["items"] == [], str(checklist["items"]))
    check("B1 상태", checklist["status"] == "not_found", str(checklist["status"]))
    check("B1 표는 보존", len(checklist["tableRows"]) == 2, "")
    check("B1 못 뽑았다고 말한다", "찾지 못했습니다" in str(checklist["headline"]), str(checklist["headline"]))

    # 배선: AI 코치가 이 상태에서 「원문에 공동/대리입찰 서류가 보인다」로 통과시키면 안 된다.
    notice = {"assetType": "압류재산", "dispositionLabel": "매각", "docChecklist": checklist}
    coach = server.local_ai_coach(notice, [])
    titles = [item["title"] for item in coach["unresolvedChecks"]]
    check("B1 배선 최우선 경고", titles and "뽑지 못했습니다" in titles[0], str(titles))
    check(
        "B1 배선 음성 — 허위 성공 문구 없음",
        all("공동/대리입찰 서류가 나에게 필요한지" != title for title in titles),
        str(titles),
    )
    # 배선 음성: 서류 0건인데 「직접제출 서류」의 존재를 전제하면 안 된다.
    # 온비드 표(`tableRows`)의 제출방법 칸은 구분명 행에 붙은 값이라 근거가 될 수 없다.
    check(
        "B1 배선 음성 — 직접제출 서류 전제 없음",
        all("직접제출 서류" not in title for title in titles),
        str(titles),
    )
    check("B1 배선 음성 전제 — 표에는 제출방법 값이 있다", any(row["method"] for row in checklist["tableRows"]), str(checklist["tableRows"]))

    # 배선 양성: 추출된 서류가 제출방법을 실제로 갖고 있으면 그 항목은 떠야 한다.
    submit_checklist = server.build_doc_checklist(
        server.split_sections(
            section("공고문", "<p>ㅇ 대리입찰의 경우 대리입찰신청서 1부를 직접제출 하여야 합니다.</p>")
        ),
        "압류재산",
        [],
    )
    submit_titles = [
        item["title"]
        for item in server.local_ai_coach(
            {"assetType": "압류재산", "dispositionLabel": "매각", "docChecklist": submit_checklist}, ["대리입찰신청서"]
        )["unresolvedChecks"]
    ]
    check("B1 배선 양성 — 직접제출", any("직접제출 서류" in title for title in submit_titles), str(submit_titles))

    # B7 배선 양성(표 보조 근거) — 표본 01~08(A형)의 실제 형태다.
    # 서류는 8건 뽑혔는데 항목 단위 `method` 는 전건 비어 있고, 온비드 표에만 「직접제출」이 있다.
    # 이 형태를 재는 검사가 없어서 2차 반영의 회귀(정당한 안내 3건 소실)가 초록으로 통과했다.
    a_type = server.build_doc_checklist(
        server.split_sections(NUMBERED_CONDITION_NOTICE + GENERIC_DOCS_TABLE), "압류재산", []
    )
    # 도달 증거 — 이 픽스처가 실제로 「항목 0건」도 「항목에 method 있음」도 아니어야
    # 아래 단언이 표 보조 근거 경로를 잰다. 셋 다 무너지면 단언은 영구 초록이 된다.
    check("B7 도달 증거 — 서류 1건 이상", len(a_type["items"]) >= 1, str(len(a_type["items"])))
    check("B7 도달 증거 — 항목 method 전건 없음", not any(item["method"] for item in a_type["items"]), str([item["method"] for item in a_type["items"]]))
    check("B7 도달 증거 — 표에는 제출방법 있음", any(row["method"] for row in a_type["tableRows"]), str(a_type["tableRows"]))
    a_titles = [
        item["title"]
        for item in server.local_ai_coach(
            {"assetType": "압류재산", "dispositionLabel": "매각", "docChecklist": a_type},
            [str(item["name"]) for item in a_type["items"]],
        )["unresolvedChecks"]
    ]
    check("B7 배선 양성 — 서류 1건 이상 + 표 직접제출", any("직접제출 서류" in title for title in a_titles), str(a_titles))
    # B7 음성 대조 — 같은 표를 그대로 두고 항목만 0건으로 만들면 False 여야 한다.
    # 「표에 제출방법이 있다」만으로는 절대 켜지지 않는다는 뜻이다.
    a_type_empty = {**a_type, "items": []}
    empty_titles = [
        item["title"]
        for item in server.local_ai_coach(
            {"assetType": "압류재산", "dispositionLabel": "매각", "docChecklist": a_type_empty}, []
        )["unresolvedChecks"]
    ]
    check("B7 배선 음성 — 서류 0건이면 표가 있어도 안 뜬다", all("직접제출 서류" not in title for title in empty_titles), str(empty_titles))

    # 배선: 체크리스트 항목이 실제로 있을 때는 조건 축을 근거로 공동/대리 항목이 붙는다.
    real = server.build_doc_checklist(server.split_sections(NUMBERED_CONDITION_NOTICE), "압류재산", [])
    real_notice = {"assetType": "압류재산", "dispositionLabel": "매각", "docChecklist": real}
    real_coach = server.local_ai_coach(real_notice, [str(item["name"]) for item in real["items"]])
    real_titles = [item["title"] for item in real_coach["unresolvedChecks"]]
    check("B1 배선 양성", any("공동/대리입찰" in title for title in real_titles), str(real_titles))

    # 배선: 준비 보드 항목이 「못 뽑았다」를 그대로 옮긴다.
    tasks = server.build_tasks({**notice, "sourceUrl": "https://www.onbid.co.kr/"}, [])
    documents = next(task for task in tasks if task["id"] == "documents")
    check("B1 배선 체크리스트 문구", "찾지 못했습니다" in str(documents["action"]), str(documents["action"]))
    check("B1 배선 참고용 문구", "막지 않습니다" in str(documents["detail"]), str(documents["detail"]))


def test_checklist_states() -> None:
    attachments = [{"name": "공고문.pdf", "downloadUrl": "https://www.onbid.co.kr/x"}]
    empty = server.split_sections(section("공고문", "<p>자세한 내용은 첨부파일 참고바랍니다.</p>"))
    b_type = server.build_doc_checklist(empty, "공유재산", attachments)
    check("B1 B형 첨부 안내", b_type["status"] == "attachment_only", str(b_type["status"]))
    c_type = server.build_doc_checklist(empty, "파산자산", attachments)
    check("B1 C형 원문 없음", c_type["status"] == "not_in_notice", str(c_type["status"]))
    # C형에서도 「못 뽑으면 못 뽑았다고 말한다」가 지켜져야 한다. 표본 18·19(파산자산)가 이 분기를 탄다.
    # `not_found` 분기의 같은 단언과 별개다 — 상태 코드만 보면 문구가 바뀌어도 초록이 된다.
    check("B1 C형 못 뽑았다고 말한다", "찾지 못했습니다" in str(c_type["headline"]), str(c_type["headline"]))
    check(
        "B1 C형 음성 — 준비를 단정하지 않음",
        "준비를 진행" not in str(c_type["headline"]),
        str(c_type["headline"]),
    )
    extracted = server.build_doc_checklist(server.split_sections(BULLET_CONDITION_NOTICE), "국유재산", [])
    check("B1 A형 추출됨", extracted["status"] == "extracted", str(extracted["status"]))
    # 음성 대조: 어떤 상태에서도 참고용 문구가 빠지면 안 된다.
    for name, checklist in (("B형", b_type), ("C형", c_type), ("A형", extracted)):
        check(f"B1 {name} 참고용 문구", "참고용" in str(checklist["reference"]), name)
        check(f"B1 {name} 진행 안 막음", "막지 않으며" in str(checklist["reference"]), name)


# ---------------------------------------------------------------------------
# B2. 최저입찰가격 비공개
# ---------------------------------------------------------------------------
def test_minimum_bid() -> None:
    check("B2 비공개 코드", server.minimum_bid_value({"lowstBidPrcHideDivCd": "0002"}, "0") == "비공개", "")
    check("B2 비공개 코드(값 있어도)", server.minimum_bid_value({"lowstBidPrcHideDivCd": "0003"}, "1,000") == "비공개", "")
    check("B2 0원 방어", server.minimum_bid_value({}, "0") == "비공개", "")
    check("B2 0원 방어(콤마)", server.minimum_bid_value({}, "0원") == "비공개", "")
    # 음성 대조: 공개 코드와 정상 금액은 그대로 남아야 한다.
    check("B2 음성 공개 코드", server.minimum_bid_value({"lowstBidPrcHideDivCd": "0001"}, "450,000,000") == "450,000,000", "")
    check("B2 음성 코드 없음", server.minimum_bid_value({}, "63,053,628") == "63,053,628", "")
    check("B2 음성 빈값", server.minimum_bid_value({}, "") == "", "")


# ---------------------------------------------------------------------------
# B3. 마감 D-day (알림 발송 아님)
# ---------------------------------------------------------------------------
def test_countdown() -> None:
    now = datetime(2026, 9, 7, 12, 0)
    closed = server.bid_countdown("2026-08-01 10:00 ~ 2026-09-01 17:00", "", now)
    check("B3 마감", closed["state"] == "closed", str(closed))
    before = server.bid_countdown("2026-10-01 14:00 ~ 2026-10-01 16:00", "", now)
    check("B3 시작 전", before["state"] == "before" and before["daysLeft"] == 24, str(before))
    urgent = server.bid_countdown("2026-09-01 10:00 ~ 2026-09-09 17:00", "", now)
    check("B3 임박", urgent["state"] == "urgent" and urgent["label"] == "마감 D-2", str(urgent))
    same_day = server.bid_countdown("2026-09-01 10:00 ~ 2026-09-07 17:00", "", now)
    check("B3 당일", same_day["label"] == "마감 당일", str(same_day))
    open_state = server.bid_countdown("2026-09-01 10:00 ~ 2026-09-30 18:00", "", now)
    check("B3 진행", open_state["state"] == "open", str(open_state))
    # 음성 대조: 날짜를 못 읽으면 상태를 만들지 않는다.
    check("B3 음성 파싱 불가", server.bid_countdown("입찰기간 원문 확인", "", now)["state"] == "unknown", "")
    check("B3 음성 빈값", server.bid_countdown("", "", now)["label"] == "", "")


# ---------------------------------------------------------------------------
# B4. 비용 — 원문값만 쓰고 세율은 계산하지 않는다
# ---------------------------------------------------------------------------
def test_costs() -> None:
    sections = server.split_sections(ONBID_HELP_SECTION)
    terms = server.extract_cost_terms(sections, "비공개")
    titles = {str(term["title"]) for term in terms}
    check("B4 입찰보증금", "입찰보증금" in titles, str(titles))
    deposit = next(term for term in terms if term["title"] == "입찰보증금")
    check("B4 원문값", deposit["value"] == "최저입찰가격 X 10%", str(deposit))
    check("B4 기준가 표기", "비공개" in str(deposit["note"]), str(deposit))
    check("B4 잔대금 납부방법", "잔대금 납부방법" in titles, str(titles))
    tax = next(term for term in terms if "세금" in str(term["title"]))
    check("B4 세금은 값 없음", "사용자 확인" in str(tax["value"]), str(tax))
    # 음성 대조: 어떤 항목에도 요율 숫자를 지어내면 안 된다(원문에 있는 10%는 예외).
    invented = [term for term in terms if "%" in str(term["value"]) and term["title"] != "입찰보증금"]
    check("B4 음성 요율 미생성", invented == [], str(invented))
    # 음성 대조: 입찰방법 절이 없으면 원문값 항목을 만들지 않는다.
    bare = server.extract_cost_terms({}, "")
    check("B4 음성 절 없음", [term["title"] for term in bare] == ["낙찰 후 세금·부대비용"], str(bare))


# ---------------------------------------------------------------------------
# 용어 안내 — 온비드 값은 그대로 두고 뜻만 붙인다
# ---------------------------------------------------------------------------
def test_notice_outline() -> None:
    sections = server.split_sections(
        section(
            "공고문",
            "<p>1. 입찰방법</p><p>온비드를 이용한 인터넷 공매입니다.</p>"
            "<p>라. 온비드의 장애로 입찰이 연기될 수 있습니다.</p>"
            "<p>2. 대금 납부</p>"
            "<p>1. 임대차 공고문_비타민스테이션.hwp</p>"
            "<p>1. 입찰방법</p>",
        )
    )
    outline = server.extract_notice_outline(sections)
    titles = [entry["title"] for entry in outline]
    check("목차 번호 제목", titles == ["1. 입찰방법", "2. 대금 납부"], str(titles))
    check("목차 본문 연결", outline[0]["body"] == "온비드를 이용한 인터넷 공매입니다.", str(outline[0]))
    # 음성 대조 3종: 서술문·첨부 파일명·중복은 목차가 아니다.
    check("목차 음성 서술문", all("연기될 수 있습니다" not in title for title in titles), str(titles))
    check("목차 음성 첨부 파일명", all(".hwp" not in title for title in titles), str(titles))
    check("목차 음성 중복 제거", len(titles) == len(set(titles)), str(titles))
    check("목차 음성 절 없음", server.extract_notice_outline({}) == [], "")


def test_glossary() -> None:
    entries = server.build_glossary("압류재산", "매각", "2026년 제010차 압류재산 공매공고")
    terms = [entry["term"] for entry in entries]
    check("용어 압류재산", "압류재산" in terms, str(terms))
    check("용어 매각", "매각" in terms, str(terms))
    check("용어 중복 없음", len(terms) == len(set(terms)), str(terms))
    check("용어 음성 미상", server.build_glossary("재산유형 확인", "처분방식 확인", "") == [], "")

    # 음성 대조: 용어 안내는 «뜻»만 적는다. 처분방식 사이의 금액·보증금 비교를 담으면
    # 임대(사용료)와 매각(매매대금)의 금액 규모를 같게 오해시킨다.
    lease = server.build_glossary("국유재산", "임대", "") + server.build_glossary("국유재산", "대부", "")
    meanings = {str(entry["term"]): str(entry["meaning"]) for entry in lease}
    check("B6 음성 임대 설명에 매각 비교 없음", "매각" not in meanings.get("임대", ""), str(meanings.get("임대")))
    check("B6 음성 대부 설명에 구조 단정 없음", "구조" not in meanings.get("대부", ""), str(meanings.get("대부")))
    check(
        "B6 음성 사전 전체에 보증금 비교 없음",
        all("보증금" not in meaning for meaning in server.TERM_GLOSSARY.values()),
        str([t for t, m in server.TERM_GLOSSARY.items() if "보증금" in m]),
    )


# ---------------------------------------------------------------------------
# B8. 「입찰방법」 절의 가능/불가능 값 — 툴팁을 값으로 읽지 않는가
# ---------------------------------------------------------------------------
def test_bid_method_flag() -> None:
    split = server.split_sections(BID_METHOD_SPLIT)
    # 도달 증거 — 픽스처가 실제로 툴팁을 품고 있어야 아래 음성 단언이 무언가를 잰다.
    check("B8 도달 증거 — 절에 툴팁 문구 있음", "공동입찰참가신청서" in split["입찰방법"], "")
    # 양성 1·2: 같은 절에서 두 축의 값이 서로 다르게 읽힌다(표본 17 형태).
    check("B8 양성 공동입찰", server.bid_method_flag(split, "공동입찰") == "가능", server.bid_method_flag(split, "공동입찰"))
    check("B8 양성 대리입찰", server.bid_method_flag(split, "대리입찰") == "불가능", server.bid_method_flag(split, "대리입찰"))

    # 음성 1: 「입찰방법」 절이 없으면 빈 문자열이다. 「불가능」으로 접지 않는다.
    check("B8 음성 절 없음", server.bid_method_flag(server.split_sections(GENERIC_DOCS_TABLE), "공동입찰") == "", "")
    check(
        "B8 음성 절 없음은 불가능이 아니다",
        server.bid_method_flag({}, "공동입찰") not in ("가능", "불가능"),
        server.bid_method_flag({}, "공동입찰"),
    )

    # 음성 2: 라벨은 있고 값 박스가 없으면 옆 항목의 값을 훔쳐오지 않는다.
    no_value = server.split_sections(BID_METHOD_NO_VALUE)
    check("B8 음성 값 없음", server.bid_method_flag(no_value, "공동입찰") == "", server.bid_method_flag(no_value, "공동입찰"))
    check("B8 도달 증거 — 옆 항목에는 값이 있다", server.bid_method_flag(no_value, "대리입찰") == "가능", "")

    # 🔴 음성 3(킬러). 툴팁의 「공동입찰참가신청서」를 값으로 읽으면 안 된다.
    # 절 전체를 훑는 구현으로 되돌리면 이 단언이 붉어진다.
    tooltip_only = server.split_sections(BID_METHOD_TOOLTIP_ONLY)
    check("B8 음성 툴팁을 값으로 읽지 않음", server.bid_method_flag(tooltip_only, "공동입찰") == "", server.bid_method_flag(tooltip_only, "공동입찰"))
    check("B8 도달 증거 — 그 절에 값 「가능」이 존재한다", server.bid_method_flag(tooltip_only, "입찰보증금") == "가능", "")


# ---------------------------------------------------------------------------
# B9. 공동입찰 조건 축 — 서류 근거를 덮지 않고 `or` 로 더하는가
# ---------------------------------------------------------------------------
JOINT_TITLE = "공동/대리입찰 서류가 나에게 필요한지"


def coach_checks(notice_extra: dict, checklist: dict, docs: list[str]) -> list[dict]:
    notice = {"assetType": "압류재산", "dispositionLabel": "매각", "docChecklist": checklist, **notice_extra}
    return list(server.local_ai_coach(notice, docs)["unresolvedChecks"])


def joint_check(notice_extra: dict, checklist: dict, docs: list[str]) -> dict:
    """공동/대리입찰 항목 하나. 없으면 빈 dict — 변이가 항목을 지웠을 때 예외 대신 FAIL 로 떨어뜨린다."""
    for entry in coach_checks(notice_extra, checklist, docs):
        if entry["title"] == JOINT_TITLE:
            return entry
    return {}


def test_joint_axis_wiring() -> None:
    empty = server.build_doc_checklist(server.split_sections(GENERIC_DOCS_TABLE), "파산자산", [])
    doc_based = server.build_doc_checklist(server.split_sections(NUMBERED_CONDITION_NOTICE), "압류재산", [])
    doc_names = [str(item["name"]) for item in doc_based["items"]]
    # 도달 증거 — 두 픽스처가 실제로 「서류 근거 없음」과 「서류 근거 있음」이어야 한다.
    check("B9 도달 증거 — 서류 0건 픽스처", empty["items"] == [], str(empty["items"]))
    check(
        "B9 도달 증거 — 서류 근거 픽스처에 joint/proxy 축",
        bool({"proxy", "joint"} & {key for item in doc_based["items"] for key in item["conditionKeys"]}),
        str(doc_names),
    )

    # 양성: 서류를 0건 뽑아도 화면 값이 「가능」이면 축이 켜진다(표본 17·18·21 형태).
    titles = [item["title"] for item in coach_checks({"jointBidAllowed": "가능"}, empty, [])]
    check("B9 양성 화면 값만으로 켜짐", JOINT_TITLE in titles, str(titles))
    item = joint_check({"jointBidAllowed": "가능"}, empty, [])
    check("B9 근거 표기 — 입찰방법", item.get("source") == "온비드 입찰방법", str(item.get("source")))
    # 서류를 못 뽑은 공고에서 「원문에는 …가 보이지만」이라고 쓰면 없는 목록을 전제한다.
    check("B9 음성 — 없는 서류 목록을 전제하지 않음", "제출서류 표 확인" not in item.get("reason", ""), str(item.get("reason")))

    # 음성 1: 값이 없으면 켜지지 않는다(옛 동작 그대로).
    check("B9 음성 값 없음", JOINT_TITLE not in [i["title"] for i in coach_checks({}, empty, [])], "")
    # 음성 2: 값이 「불가능」이면 화면 값만으로는 켜지지 않는다.
    check("B9 음성 불가능", JOINT_TITLE not in [i["title"] for i in coach_checks({"jointBidAllowed": "불가능"}, empty, [])], "")

    # 🔴 순수 증분 — 값이 「불가능」이어도 서류 근거로 켜진 축을 **끄지 않는다**.
    off_titles = [i["title"] for i in coach_checks({"jointBidAllowed": "불가능"}, doc_based, doc_names)]
    check("B9 음성 기존 근거를 덮지 않음", JOINT_TITLE in off_titles, str(off_titles))
    # 서류 근거가 있으면 문구도 옛것을 그대로 쓴다(덮어쓰기가 아니라 확장임을 잰다).
    doc_item = joint_check({"jointBidAllowed": "가능"}, doc_based, doc_names)
    check("B9 서류 근거 우선", doc_item.get("source") == "제출서류 표", str(doc_item.get("source")))


# ---------------------------------------------------------------------------
# B11-1. 코치 action 문구 — 서류 0건 경로가 없는 목록을 전제하지 않는가
# reason 만 갈라 놓고 action 을 옛 문장으로 두면 「남길 목록」이 화면에 없다.
# ---------------------------------------------------------------------------
LIST_PRESUMING_VERB = "필요한 서류만 남깁니다"


def test_joint_action_wording() -> None:
    empty = server.build_doc_checklist(server.split_sections(GENERIC_DOCS_TABLE), "파산자산", [])
    doc_based = server.build_doc_checklist(server.split_sections(NUMBERED_CONDITION_NOTICE), "압류재산", [])
    doc_names = [str(item["name"]) for item in doc_based["items"]]
    # 도달 증거 — 두 경로가 실제로 같은 항목을 만들어 냈어야 비교가 성립한다.
    screen_only = joint_check({"jointBidAllowed": "가능"}, empty, [])
    with_docs = joint_check({"jointBidAllowed": "가능"}, doc_based, doc_names)
    check("B11-1 도달 증거 — 서류 0건 경로에도 항목이 뜬다", bool(screen_only), str(screen_only))
    check("B11-1 도달 증거 — 서류 근거 경로에도 항목이 뜬다", bool(with_docs), str(with_docs))
    # 🔴 양성(음의 단정) — 서류 0건이면 목록 전제 동사를 쓰지 않는다.
    check(
        "B11-1 서류 0건 action 이 목록을 전제하지 않음",
        LIST_PRESUMING_VERB not in str(screen_only.get("action", "")),
        str(screen_only.get("action")),
    )
    check(
        "B11-1 서류 0건 action 이 원문 확인으로 돌린다",
        "원문" in str(screen_only.get("action", "")),
        str(screen_only.get("action")),
    )
    # 음성 대조 — 서류를 뽑은 경로의 옛 문장은 그대로여야 한다. 두 경로를 한 문장으로
    # 합치는 변이(분기 삭제)는 여기서 붉어진다.
    check(
        "B11-1 음성 대조 — 서류 근거 경로는 옛 문장 유지",
        LIST_PRESUMING_VERB in str(with_docs.get("action", "")),
        str(with_docs.get("action")),
    )
    check(
        "B11-1 음성 대조 — 두 경로의 action 이 실제로 다르다",
        screen_only.get("action") != with_docs.get("action"),
        str(screen_only.get("action")),
    )


# ---------------------------------------------------------------------------
# B11. `build_notice` 호출부 배선 — `jointBidAllowed` 가 「공동입찰」 값을 싣는가
# 이 게이트는 build_notice 를 PLAYED 로 두지만, 이 축만은 실제로 부른다.
# 대신 연기하는 것은 네트워크 두 개뿐이다 — fetch_onbid, public_data_service_key.
# ---------------------------------------------------------------------------
FAKE_NOTICE_URL = "https://www.onbid.co.kr/op/ppa/pbcpubannc/publicAnnounceDetail.do"


def notice_from_html(html: str) -> dict:
    """`build_notice` 를 오프라인으로 부른다. 네트워크 두 곳만 대신 연기한다."""
    saved_fetch, saved_key = server.fetch_onbid, server.public_data_service_key
    server.fetch_onbid = lambda raw_url: (FAKE_NOTICE_URL, html)
    server.public_data_service_key = lambda: ""
    try:
        return server.build_notice(FAKE_NOTICE_URL)
    finally:
        server.fetch_onbid, server.public_data_service_key = saved_fetch, saved_key


def test_build_notice_joint_wiring() -> None:
    split = server.split_sections(BID_METHOD_SPLIT)
    # 도달 증거 — 이 픽스처가 실제로 두 라벨을 가르는 판별 케이스여야 한다.
    check(
        "B11 도달 증거 — 공동/대리 값이 갈린다",
        (server.bid_method_flag(split, "공동입찰"), server.bid_method_flag(split, "대리입찰")) == ("가능", "불가능"),
        str((server.bid_method_flag(split, "공동입찰"), server.bid_method_flag(split, "대리입찰"))),
    )
    # 🔴 양성 — 빈 값 고정 변이와 「대리입찰」 값 탑재 변이를 둘 다 가른다.
    notice = notice_from_html(BID_METHOD_SPLIT)
    check("B11 양성 공동입찰 값을 싣는다", notice.get("jointBidAllowed") == "가능", str(notice.get("jointBidAllowed")))
    check(
        "B11 양성 순수 함수 값과 일치",
        notice.get("jointBidAllowed") == server.bid_method_flag(split, "공동입찰"),
        str(notice.get("jointBidAllowed")),
    )
    # 🔴 음성 대조 1 — 값을 뒤집은 픽스처. 「가능」 하드코딩과 대리입찰 탑재가 여기서 붉어진다.
    reversed_notice = notice_from_html(BID_METHOD_SPLIT_REVERSED)
    check(
        "B11 음성 대조 값 뒤집기",
        reversed_notice.get("jointBidAllowed") == "불가능",
        str(reversed_notice.get("jointBidAllowed")),
    )
    # 음성 대조 2 — 「입찰방법」 절이 없으면 빈 문자열이다. 「불가능」으로 접지 않는다.
    no_section = notice_from_html(GENERIC_DOCS_TABLE)
    check(
        "B11 음성 대조 절 없음은 빈 값",
        no_section.get("jointBidAllowed") == "",
        str(no_section.get("jointBidAllowed")),
    )
    # 명도책임도 같은 조립 지점을 지난다 — 배선을 함께 고정한다.
    check(
        "B11 음성 대조 명도책임 값은 지어내지 않는다",
        no_section.get("evictionResponsibility") == "",
        str(no_section.get("evictionResponsibility")),
    )


# ---------------------------------------------------------------------------
# B10. 명도책임 — 사실 한 줄, 조건 축이 아니다
# ---------------------------------------------------------------------------
def test_eviction_responsibility() -> None:
    sections = server.split_sections(EVICTION_NOTICE)
    check("B10 양성 매수인", server.eviction_responsibility(sections) == "매수인", server.eviction_responsibility(sections))
    # 음성: 문장이 없으면 빈 문자열이다. 「해당없음」을 지어내지 않는다.
    check("B10 음성 없음", server.eviction_responsibility(server.split_sections(GENERIC_DOCS_TABLE)) == "", "")
    # 음성: 조건 축이 아니다 — 명도/인도 어휘가 CONDITION_AXES 에 들어가면 안 된다.
    check(
        "B10 음성 조건 축 아님",
        all("명도" not in pattern and "인도" not in pattern for _key, _label, pattern in server.CONDITION_AXES),
        str([axis[0] for axis in server.CONDITION_AXES]),
    )
    check("B10 축 수 고정", len(server.CONDITION_AXES) == 10, str(len(server.CONDITION_AXES)))


# ---------------------------------------------------------------------------
# C 계열. 공공데이터 API 경로 — 이 세 축은 네트워크를 연기한다.
# 연기하는 것은 urlopen 과 인증키 둘뿐이고, 요청 URL 조립과 응답 해석은 실제 코드가 한다.
# ---------------------------------------------------------------------------
OK_BODY = json.dumps(
    {
        "response": {
            "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE."},
            "body": {"items": {"item": {"cltrMngNo": "2026-0800-045167"}}},
        }
    }
)
# 게이트웨이 오류 봉투. 개발계정 한도(일 1,000건) 초과가 이 형태로 HTTP 200 에 실려 온다.
GATEWAY_LIMIT_BODY = json.dumps(
    {
        "OpenAPI_ServiceResponse": {
            "cmmMsgHeader": {
                "errMsg": "SERVICE ERROR",
                "returnAuthMsg": "LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR",
                "returnReasonCode": "22",
            }
        }
    }
)


class PlayedHeaders:
    def get_content_charset(self) -> str:
        return "utf-8"


class PlayedResponse:
    """urlopen 이 돌려주는 것 중 `call_public_data` 가 실제로 쓰는 면만 흉내낸다."""

    def __init__(self, body: str, status: int = 200) -> None:
        self._body = body.encode("utf-8")
        self.status = status
        self.headers = PlayedHeaders()

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "PlayedResponse":
        return self

    def __exit__(self, *exc: object) -> bool:
        return False


def with_played_urlopen(body: str, action, status: int = 200) -> tuple[object, list[str]]:
    """`action()` 을 도는 동안 urlopen 을 픽스처로 갈아끼우고, 실제 요청 URL 을 모아 돌려준다."""
    urls: list[str] = []
    saved = server.urllib.request.urlopen

    def played(request, timeout=None):  # noqa: ANN001
        urls.append(request.full_url)
        return PlayedResponse(body, status)

    server.urllib.request.urlopen = played
    try:
        return action(), urls
    finally:
        server.urllib.request.urlopen = saved


def bundle_request_urls(ids: dict, body: str = OK_BODY) -> list[str]:
    """`fetch_public_data_bundle` 이 실제로 만드는 요청 URL. 인증키만 더미로 연기한다."""
    saved_key = server.public_data_service_key
    server.public_data_service_key = lambda: "DUMMY-KEY"
    try:
        _bundle, urls = with_played_urlopen(body, lambda: server.fetch_public_data_bundle(ids))
        return urls
    finally:
        server.public_data_service_key = saved_key


# ---------------------------------------------------------------------------
# C1. 물건관리번호 4-4-6 재조립 — 하이픈이 없으면 API 는 200 + NODATA_ERROR 를 돌려준다.
# 순수 함수와 호출부 배선을 따로 단정한다. 함수가 초록이어도 호출부가 안 부르면 소용없다.
# ---------------------------------------------------------------------------
RAW_CLTR_MNG_NO = "20260800045167"  # 온비드 hidden input 이 주는 형태
API_CLTR_MNG_NO = "2026-0800-045167"  # API 가 인정하는 형태


def test_api_cltr_mng_no() -> None:
    # 도달 증거 — 이 픽스처가 실제로 하이픈 삽입 분기를 지난다(입력과 출력이 달라야 한다).
    check(
        "C1 도달 증거 — 하이픈 삽입 분기를 지난다",
        server.api_cltr_mng_no(RAW_CLTR_MNG_NO) != RAW_CLTR_MNG_NO,
        server.api_cltr_mng_no(RAW_CLTR_MNG_NO),
    )
    # 🔴 양성 1 — 하이픈 없는 14자리를 4-4-6 으로 만든다.
    check(
        "C1 양성 하이픈 없는 14자리",
        server.api_cltr_mng_no(RAW_CLTR_MNG_NO) == API_CLTR_MNG_NO,
        server.api_cltr_mng_no(RAW_CLTR_MNG_NO),
    )
    # 자리수를 4-4-6 이 아닌 것으로 바꾼 변이는 여기서 붉어진다. 마디를 따로 센다.
    parts = server.api_cltr_mng_no(RAW_CLTR_MNG_NO).split("-")
    check(
        "C1 양성 마디 길이가 4-4-6",
        [len(part) for part in parts] == [4, 4, 6],
        str([len(part) for part in parts]),
    )
    # 🔴 양성 2 — 구분자가 섞인 14자리도 정규화한다(슬라이스 소스를 value 로 바꾼 변이를 가른다).
    check(
        "C1 양성 구분자 섞인 14자리",
        server.api_cltr_mng_no("2026 0800 045167") == API_CLTR_MNG_NO,
        server.api_cltr_mng_no("2026 0800 045167"),
    )
    # 🔴 양성 3 — 멱등. 이미 하이픈이 있는 값은 그대로다. f(f(x)) == f(x).
    check(
        "C1 양성 멱등 — 이미 하이픈",
        server.api_cltr_mng_no(API_CLTR_MNG_NO) == API_CLTR_MNG_NO,
        server.api_cltr_mng_no(API_CLTR_MNG_NO),
    )
    check(
        "C1 양성 멱등 — 두 번 적용해도 같다",
        server.api_cltr_mng_no(server.api_cltr_mng_no(RAW_CLTR_MNG_NO)) == API_CLTR_MNG_NO,
        server.api_cltr_mng_no(server.api_cltr_mng_no(RAW_CLTR_MNG_NO)),
    )
    # 🔴 양성 4 — 빈 값과 None 은 빈 문자열이다. 하이픈만 남은 값을 만들지 않는다.
    check("C1 양성 빈 문자열", server.api_cltr_mng_no("") == "", repr(server.api_cltr_mng_no("")))
    check("C1 양성 None", server.api_cltr_mng_no(None) == "", repr(server.api_cltr_mng_no(None)))

    # ---- 붉히면 안 되는 입력 4개(양성 축과 같은 수) -------------------------
    # 음성 1 — `pbctCdtnNo`(공매조건번호)는 NUMBER(22) 로 하이픈이 없다. 같은 규칙을 적용하면 안 된다.
    check(
        "C1 음성 pbctCdtnNo 류 숫자는 원문 통과",
        server.api_cltr_mng_no("12345678") == "12345678",
        server.api_cltr_mng_no("12345678"),
    )
    # 음성 2 — `pbancMngNo` 는 6-5-2(숫자 13자리)다. 14자리가 아니므로 재조립하지 않는다.
    check(
        "C1 음성 pbancMngNo 는 재조립하지 않는다",
        server.api_cltr_mng_no("202406-21411-00") == "202406-21411-00",
        server.api_cltr_mng_no("202406-21411-00"),
    )
    # 음성 3 — 14자리에서 하나 모자라거나 하나 넘치는 값은 원문 그대로다.
    check(
        "C1 음성 13자리 원문 통과",
        server.api_cltr_mng_no("2026080004516") == "2026080004516",
        server.api_cltr_mng_no("2026080004516"),
    )
    check(
        "C1 음성 15자리 원문 통과",
        server.api_cltr_mng_no("202608000451678") == "202608000451678",
        server.api_cltr_mng_no("202608000451678"),
    )
    # 음성 4 — 원문 통과 경로에는 하이픈이 새로 생기지 않는다.
    check(
        "C1 음성 원문 통과에 하이픈을 만들지 않는다",
        "-" not in server.api_cltr_mng_no("12345678901234567890"),
        server.api_cltr_mng_no("12345678901234567890"),
    )


def test_api_cltr_mng_no_wiring() -> None:
    """순수 함수가 초록인 것과 호출부가 그것을 부르는 것은 다른 사실이다."""
    urls = bundle_request_urls({"cltrMngNo": RAW_CLTR_MNG_NO})
    check("C1 배선 도달 증거 — 요청이 1건 이상 나갔다", len(urls) >= 1, str(len(urls)))
    joined = " ".join(urls)
    # 🔴 양성 — 하이픈 있는 값이 실제 요청 URL 에 실린다.
    check(f"C1 배선 요청 URL 에 {API_CLTR_MNG_NO}", f"cltrMngNo={API_CLTR_MNG_NO}" in joined, joined[:200])
    # 🔴 음성 대조 — 하이픈 없는 원본은 URL 에 남아 있으면 안 된다. 배선 삭제 변이가 여기서 붉어진다.
    check(f"C1 배선 음성 — {RAW_CLTR_MNG_NO} 가 나가지 않는다", f"cltrMngNo={RAW_CLTR_MNG_NO}" not in joined, joined[:200])
    # 음성 대조 — pbctCdtnNo 는 넘긴 값 그대로 나간다(4-4-6 규칙을 물리지 않는다).
    with_cdtn = " ".join(bundle_request_urls({"cltrMngNo": RAW_CLTR_MNG_NO, "pbctCdtnNo": "12345678"}))
    check("C1 배선 음성 pbctCdtnNo 원문", "pbctCdtnNo=12345678" in with_cdtn, with_cdtn[:200])


# ---------------------------------------------------------------------------
# C2. 게이트웨이 오류 봉투 — HTTP 200 에 실려 오는 사유 코드를 상태에 싣는가
# ---------------------------------------------------------------------------
def test_gateway_error_envelope() -> None:
    gateway_payload = json.loads(GATEWAY_LIMIT_BODY)
    # 도달 증거 — 원래 봉투에는 resultCode 키가 없다. 있으면 이 축은 통과해도 무증명이다.
    check(
        "C2 도달 증거 — 봉투에 resultCode 키가 없다",
        "resultCode" not in gateway_payload["OpenAPI_ServiceResponse"]["cmmMsgHeader"],
        str(gateway_payload["OpenAPI_ServiceResponse"]["cmmMsgHeader"].keys()),
    )
    header = server.api_header(gateway_payload)
    # 🔴 양성 — 사유 코드 22 를 resultCode 로 읽는다.
    check("C2 양성 returnReasonCode → resultCode", header.get("resultCode") == "22", str(header.get("resultCode")))
    check(
        "C2 양성 사유 메시지를 싣는다",
        "LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR" in str(header.get("resultMsg")),
        str(header.get("resultMsg")),
    )
    # 🔴 양성 — returnAuthMsg 가 없으면 errMsg 로 대체한다. 빈 메시지를 내지 않는다.
    only_err = server.api_header({"OpenAPI_ServiceResponse": {"cmmMsgHeader": {"errMsg": "SERVICE ERROR", "returnReasonCode": "30"}}})
    check("C2 양성 errMsg 대체", only_err.get("resultMsg") == "SERVICE ERROR", str(only_err.get("resultMsg")))
    check("C2 양성 코드 30 도 읽는다", only_err.get("resultCode") == "30", str(only_err.get("resultCode")))
    # 🔴 음성 대조 — 게이트웨이 봉투는 데이터가 아니다. item 으로 세면 안 된다.
    check("C2 음성 봉투는 item 이 아니다", server.api_items(gateway_payload) == [], str(server.api_items(gateway_payload)))

    # ---- 붉히면 안 되는 입력 — 기존 세 봉투 형태의 동작이 그대로여야 한다 ----
    normal = server.api_header(json.loads(OK_BODY))
    check("C2 음성 정상 봉투 resultCode 불변", normal.get("resultCode") == "00", str(normal.get("resultCode")))
    check("C2 음성 정상 봉투 resultMsg 불변", normal.get("resultMsg") == "NORMAL SERVICE.", str(normal.get("resultMsg")))
    check(
        "C2 음성 result 형태 불변",
        server.api_header({"result": {"resultCode": "11"}}).get("resultCode") == "11",
        str(server.api_header({"result": {"resultCode": "11"}})),
    )
    check(
        "C2 음성 header 형태 불변",
        server.api_header({"header": {"resultCode": "12"}}).get("resultCode") == "12",
        str(server.api_header({"header": {"resultCode": "12"}})),
    )
    check("C2 음성 dict 아님은 {}", server.api_header("문자열") == {}, str(server.api_header("문자열")))
    check("C2 음성 빈 dict 는 {}", server.api_header({}) == {}, str(server.api_header({})))


def test_gateway_error_envelope_wiring() -> None:
    """HTTP 200 에 실린 오류가 상태·사유로 내려오는가. 상태코드만 보면 이 축은 잡히지 않는다."""
    limited, urls = with_played_urlopen(
        GATEWAY_LIMIT_BODY,
        lambda: server.call_public_data("real_estate_detail", {"cltrMngNo": API_CLTR_MNG_NO}, "DUMMY-KEY"),
    )
    check("C2 배선 도달 증거 — 요청 1건", len(urls) == 1, str(len(urls)))
    # 도달 증거 — 이 축의 핵심 조건은 HTTP 가 200 이라는 것이다.
    check("C2 배선 도달 증거 — HTTP 200 이다", limited.get("status") == 200, str(limited.get("status")))
    # 🔴 양성 — 200 이어도 ok 가 아니고, 사유 코드와 메시지가 실린다.
    check("C2 배선 ok 아님", limited.get("ok") is False, str(limited.get("ok")))
    check("C2 배선 resultCode 22", limited.get("resultCode") == "22", str(limited.get("resultCode")))
    check("C2 배선 사유 메시지 비어 있지 않음", bool(limited.get("resultMsg")), str(limited.get("resultMsg")))
    check("C2 배선 오류 봉투는 items 0건", limited.get("items") == [], str(limited.get("items")))
    # 🔴 음성 대조 — 정상 응답 경로는 그대로 ok 다. 이 축이 정상 경로를 죽이지 않았다.
    normal, _ = with_played_urlopen(
        OK_BODY,
        lambda: server.call_public_data("real_estate_detail", {"cltrMngNo": API_CLTR_MNG_NO}, "DUMMY-KEY"),
    )
    check("C2 배선 음성 정상 응답은 ok", normal.get("ok") is True, str(normal.get("ok")))
    check("C2 배선 음성 정상 resultCode 00", normal.get("resultCode") == "00", str(normal.get("resultCode")))
    check("C2 배선 음성 정상 items 1건", len(normal.get("items", [])) == 1, str(normal.get("items")))


def main() -> int:
    print_header()
    for test in (
        test_sections,
        test_doc_names,
        test_condition_carry,
        test_negative_condition,
        test_extras,
        test_profile,
        test_attachments,
        test_generic_table_is_not_success,
        test_checklist_states,
        test_minimum_bid,
        test_countdown,
        test_costs,
        test_notice_outline,
        test_glossary,
        test_bid_method_flag,
        test_joint_axis_wiring,
        test_joint_action_wording,
        test_build_notice_joint_wiring,
        test_eviction_responsibility,
        test_api_cltr_mng_no,
        test_api_cltr_mng_no_wiring,
        test_gateway_error_envelope,
        test_gateway_error_envelope_wiring,
    ):
        test()
    total = PASSED + len(FAILURES)
    for failure in FAILURES:
        print(f"FAIL {failure}")
    uncovered = [f"{code} {name}" for code, name, _case, _mut, covered in AXES if covered != "Y"]
    print(
        f"{PASSED}/{total} 통과 · 연기 {len(PLAYED)}개 · 축 {len(AXES)}개 중 미커버 {len(uncovered)}개"
    )
    print(f"미커버 축: {', '.join(uncovered) if uncovered else '없음'}. "
          "화면 축은 tests/screen.spec.js, 표본 축은 tests/measure_sample_23.py 가 맡는다.")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
