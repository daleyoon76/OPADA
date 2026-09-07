"""제출서류 추출·비공개 가격·마감 D-day 게이트.

의존성 없이 `python3 tests/test_docs_extraction.py` 로 돌린다.

PLAYED — 이 게이트가 프로덕션 호출부를 대신 연기한 것
  1. `fetch_onbid()` — 실제 HTTP 대신 이 파일의 픽스처 HTML을 넣는다.
  2. `build_notice()` — 전체 조립 대신 `build_doc_checklist`/`build_tasks`/`local_ai_coach`
     를 직접 부른다. 진짜 `build_notice` 배선은 `tests/measure_sample_23.py`(표본 23건)와
     로컬 서버 실호출로 확인한다.
  3. 화면 렌더 — 이 파일은 화면을 연기하지 않는다. 화면 축은 `tests/screen.spec.js` 다.

AXES — 축 → 케이스 → 킬러 변이 → 커버
  A1 섹션 분리        → 입찰방법 도움말 배제      → 배제 제거      → Y
  A2 서류명 어휘      → 긴 이름 우선/열린 이름    → 순서 뒤집기    → Y
  A3 조건 물림        → ㅇ 머리글 → - 하위 항목   → 물림 삭제      → Y
  A4 부정 문맥        → 「불허용」 축 제외        → 가드 삭제      → Y
  A5 제출 동사 요구   → 단순 언급 제외            → 동사 요구 삭제 → Y
  A6 부가조건         → 원본/유효기간/방법/기한   → 파싱 삭제      → Y
  A7 A/B/C 사전판정   → 재산유형 → 코드           → 표 비우기      → Y
  A8 첨부 다운로드    → fn_chkPdfRead 5인자       → 인자 무시      → Y
  A9 온비드 표        → 구분명만/공고문 확인      → generic 끄기   → Y
  B1 has_docs 정직성  → 구분명만 → 못 뽑았다 표시 → 옛 판정 복원   → Y
  B2 최저입찰가 비공개 → HideDivCd != 0001        → 코드 무시      → Y
  B3 마감 D-day       → 시작 전/진행/임박/마감    → 상태 고정      → Y
  B4 비용 항목        → 원문값만·세율 미계산      → 세율 삽입      → Y (음성)
  B5 공고문 목차      → 번호 제목/서술문·파일명   → 필터 삭제      → Y
  B6 용어 안내        → 재산유형·처분방식 뜻      → 사전 비우기    → Y

킬러 변이 실측(2026-09-08): 22개 변이 전부 붉어짐. 화면 축은 17개 전부 붉어짐.
"""

from __future__ import annotations

import sys
from datetime import datetime
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
    check("A8 음성 앵커 없음", server.extract_related_docs("<a href='#'>공고문.pdf</a>") == [], "")


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


def main() -> int:
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
    ):
        test()
    total = PASSED + len(FAILURES)
    for failure in FAILURES:
        print(f"FAIL {failure}")
    print(f"{PASSED}/{total} 통과 · 연기 3개 · 축 15개 중 미커버 0개")
    print("미커버 없음. 화면 축은 tests/screen.spec.js, 표본 축은 tests/measure_sample_23.py 가 맡는다.")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
