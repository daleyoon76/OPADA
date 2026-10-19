"""제출서류 추출·비공개 가격·마감 D-day 게이트.

의존성 없이 `python3 tests/test_docs_extraction.py` 로 돌린다.

연기한 것(`PLAYED`)과 축 표(`AXES`)는 아래 상수에 두고 **실행할 때마다 stdout 에 찍는다.**
docstring 에만 두면 로그를 받은 사람이 무엇이 연기됐는지 알 수 없다.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import attachment_parser  # noqa: E402
import server  # noqa: E402

FAILURES: list[str] = []
PASSED = 0
# 실행된 모든 단정의 이름. 축 커버리지를 «선언»이 아니라 여기서 센다.
CHECK_NAMES: list[str] = []

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
        "C1·C2·C3·D2 축에서만 — 실제 HTTP 대신 픽스처 본문(D2 는 정해 둔 HTTP 429/500)을 돌려주고 요청 URL 을 캡처한다. "
        "D2 는 time.sleep 도 기록만 하고 실제로 기다리지 않는다. "
        "게이트웨이의 실제 응답과 실제 인증키는 이 파일이 검증하지 못한다",
    ),
    ("public_data_service_key()", "C1 배선 축에서만 — 실제 인증키 대신 더미 문자열을 넣는다"),
    (
        "vertex_answer_question()·gemini_answer_question()",
        "D1 배선 축에서만 — 실제 모델 호출 대신 받은 인자를 캡처하고 정해 둔 응답을 돌려준다. "
        "모델이 board 를 실제로 읽고 순서대로 안내하는지는 이 파일이 검증하지 못한다(수동 라이브 시험으로만 확인)",
    ),
    (
        "fetch_attachment_bytes()·attachment_text()·subprocess(venv)",
        "A10 축에서만 — 실제 다운로드·venv subprocess 호출 대신 attachment_chunks 를 직접 만들어 "
        "extract_doc_items·build_doc_checklist 에 넣는다. src/attachment_parser.py 의 실제 PDF·HWP·HWPX "
        "파싱은 이 파일도 tests/measure_answer_set.py 도 자동으로 검증하지 않는다 — 2026-09-12 표본 59건 "
        "수동 스모크 테스트(성공 52 · 스캔본 등 빈 텍스트 7 · 크래시 0)로만 확인했다. 자동화는 다음 과제.",
    ),
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
    (
        "A10",
        "첨부 텍스트 배선",
        "게이트 우회·1200자 상한 해제·조건 무시(공통)·단계 물림·headline 출처 구분 — 모두 본문은 그대로임을 함께 확인",
        "is_attachment 가드 삭제 · 상한 원복 · 조건 우회 삭제 · current_heading 삭제 · headline 분기 삭제",
        "Y",
    ),
    (
        "A11",
        "문장 단위 단계 판정",
        "조항 표제 사전 매칭 → 문장 결정적 문구 → 미분류(추측 금지) · 멀리 떨어진 줄의 낙찰자/계약 신호가 안 번짐",
        "HEADING_STAGE_RULES 매칭 삭제 · SENTENCE_STAGE_RULES 매칭 삭제 · resolve_doc_stage 기본값을 미분류 대신 입찰 전으로 되돌리기",
        "Y",
    ),
    (
        "A12",
        "서식명 사전 우선 판정",
        "공동입찰참가신청서·대리입찰신청서·미성년자 입찰참가 동의서가 조항 표제·문장 판정과 무관하게 입찰 전으로 고정",
        "FORM_NAME_STAGE_RULES 매칭 삭제",
        "Y",
    ),
    (
        "A13",
        "조항 표제 사전 10종",
        "사전 크기 최소 10종 · appendix 인용 표제 3종(표본12·13·15~17) 직접 대조",
        "표제 2종으로 축소(구비서류/낙찰자 제출/낙찰일만 남김) → '계약체결 시 지참 서류' 미분류로 떨어짐",
        "Y",
    ),
    (
        "A14",
        "별도 문의 필요 상태",
        "NO_GENERAL_BASIS_DOC_NAMES 서류는 미분류 대신 별도 문의 필요 · 일반 서류는 그대로 미분류 · 표제 확정 시엔 표제를 따름(최종 폴백일 뿐)",
        "NO_GENERAL_BASIS_DOC_NAMES 비우기",
        "Y",
    ),
    (
        "A15",
        "서식명 사전 완성도·오염 방지",
        "표준 이름 3종 전부 등재 · 기관명 접두어 변형 12종 전부 입찰 전으로 뽑힘 · 범용 서류(인감증명서 등) 미등재",
        "표준 이름 하나 삭제 · 범용 서류를 사전에 섞기",
        "Y",
    ),
    (
        "A16",
        "조항 번호 층별 표제",
        "「10.」 표제 아래 「가.」 항목 · 「바.」 표제 아래 「1).」 항목이 상위 표제를 따름 · 같은 층 번호가 오면 끊김 · 「낙찰자의 제출서류」 변형",
        "같은 층 걷어내기 삭제 · 가장 안쪽 표제만 보기(옛 동작) · 「의?」 삭제 · 「1)」 층 규칙 삭제 · 미커버: ※ 문단에 서류명이 있거나 결정 문구 목록 밖 표현이면 물림을 끊지 못함(리뷰 r2 G3)",
        "Y",
    ),
    (
        "E1",
        "API 플래그 거르기",
        "collbBidPsblYn=N 인데 기한 값이 남은 실제 응답 · Y 인 응답(음성 대조)",
        "플래그 검사 삭제",
        "Y",
    ),
    ("E2", "쓸 수 없는 값", "bidPtctAplyTermNm=「~」 · Y/N 아닌 값", "EMPTY_API_TERM_VALUES 에서 「~」 제거", "Y"),
    ("E3", "제한조건 판정", "지역 제한 있음 · 「없음(…)」 · 「없음」이 섞인 실제 제한", "완전일치를 부분일치로 바꾸기", "Y"),
    ("E4", "식별자 보충 배선", "cltrInfVO.pbctCdtnNo → 공공데이터 호출 · 서비스별 응답 분리", "보충 줄 삭제 · 호출 인자 원복", "Y"),
    ("B1", "추출 정직성", "구분명만 → 못 뽑았다 표시(not_found·C형) · 코치 배선", "옛 판정 복원 · headline 교체", "Y"),
    ("B2", "최저입찰가 비공개", "HideDivCd != 0001", "코드 무시", "Y"),
    ("B3", "마감 D-day", "시작 전/진행/임박/마감", "상태 고정", "Y"),
    ("B4", "비용 항목", "원문값만·세율 미계산", "세율 삽입", "Y"),
    ("B5", "공고문 목차", "번호 제목/서술문·파일명", "필터 삭제", "Y"),
    ("B6", "용어 안내", "재산유형·처분방식 뜻", "사전 비우기", "Y"),
    ("B6-1", "용어 안내 확장", "온비드 자료실 136건 병합 · 2글자 소음어 제외 · 실제 매칭", "확장 사전 병합 삭제", "Y"),
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
    (
        "C3",
        "API 스킴 https",
        "엔드포인트 6종 상수 · 6종 각각의 실제 요청 URL",
        "한 줄이라도 http 로 되돌리기",
        "Y",
    ),
    ("C4", "물건상세 링크 확신 낮춤", "pbctCdtnNo 없음 → itemDetailUncertain · 있으면 없음", "플래그 조건 삭제", "Y"),
    (
        "D1",
        "질문 하네스 보드 상태",
        "개수·길이 상한 · 진행률 재계산 · 프롬프트에 board 탑재 · 보드 없이 board 답변 거부 · 옛 스키마 · 배선",
        "board 가드 삭제 · 재계산 대신 화면 숫자 사용 · 프롬프트 board 키 삭제 · 라우트 전달 삭제",
        "Y",
    ),
    (
        "D3",
        "질문 답변의 온비드 용어 근거",
        "사전 용어·출처 · 띄어쓰기 · 질문 속 순서 · 2글자 사전 용어 제외 · 겹침 · 상한 · 프롬프트 탑재·schema general · "
        "모델 none·미연결에도 references 배선 · 절차 용어 금지표현",
        "minLength 무시 · 겹침 검사 삭제 · 프롬프트 키 삭제 · references 줄 삭제",
        "Y",
    ),
    (
        "D2",
        "Vertex 429 재시도",
        "429 1회 후 성공 · 429 연속이면 포기 · 500 은 즉시 포기 · 질문·코치 호출부 배선",
        "429 분기 삭제 · 재시도 횟수 0 · 질문 호출부를 urlopen 직접 호출로 되돌리기",
        "Y",
    ),
    ("C5", "재산유형 공고상세", "메뉴 문구 차단 · 배지 type01 · hidden input 우선 · C형까지 흐름", "배지 호출 삭제 · 가드 삭제", "Y"),
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
    CHECK_NAMES.append(name)
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
# A10. 첨부 텍스트 배선 — 첨부는 본문과 게이트가 다르다(제출 동사 없어도·1200자 넘어도
# 잡되, 조건은 안 붙인다). 본문 축(A1·A5)은 그대로임을 같은 테스트에서 다시 확인한다.
# ---------------------------------------------------------------------------
def test_heading_layers() -> None:
    # A16. 항목 줄도 「가.」·「1).」처럼 조항 번호 모양이라, 표제를 마지막 번호 줄 하나로만 들고 가면
    # 항목 줄이 상위 표제를 덮어써 사전에 있는 표제 아래 서류가 전부 미분류로 떨어졌다.
    # 픽스처는 2026-10-19 실공고 두 건의 문장을 줄여 썼다(909445 수원 · 909691 서울 중구).
    check("A16 층 판별 1).", server.heading_kind("1). 주민등록등본 1부") == "paren", server.heading_kind("1). 주민등록등본 1부"))
    check("A16 층 판별 10.", server.heading_kind("10. 최종낙찰자 제출서류") == "number", server.heading_kind("10. 최종낙찰자 제출서류"))
    check("A16 층 판별 가.", server.heading_kind("가. 사업자등록증") == "hangul", server.heading_kind("가. 사업자등록증"))

    # 판정 함수 직접 호출 — 같은 층이 다시 오면 그 층과 안쪽 층을 걷어내고, 처음 보는 층은 안쪽으로 쌓는다.
    stack: list[tuple[str, str]] = []
    for line in ("10. 최종낙찰자 제출서류", "가. 사업자등록증 1부", "나. 법인인감증명서 1부"):
        server.push_heading(stack, line)
    check("A16 쌓기 — 형제 항목은 서로 바뀌고 상위는 남음", [kind for kind, _ in stack] == ["number", "hangul"] and stack[-1][1].startswith("나."), str(stack))
    check("A16 안쪽부터 사전 표제 찾기", server.stage_heading_from_stack(stack) == "10. 최종낙찰자 제출서류", server.stage_heading_from_stack(stack))
    server.push_heading(stack, "11. 기타사항")
    check("A16 같은 층 번호가 오면 안쪽까지 걷어냄", stack == [("number", "11. 기타사항")], str(stack))
    # 바깥과 안쪽이 둘 다 사전 표제면 더 구체적인 안쪽이 이긴다. 바깥부터 찾으면 입찰 전으로 뒤집힌다.
    nested = [("number", "2. 입찰참가자격"), ("hangul", "가. 계약체결 시 구비서류")]
    check("A16 안쪽 표제가 바깥 표제를 이김", server.stage_heading_from_stack(nested) == "가. 계약체결 시 구비서류", server.stage_heading_from_stack(nested))

    # 양성 ⑴ — 「10.」 표제 아래 「가.」·「나.」 항목.
    numbered = "10. 최종낙찰자 제출서류\n가. 사업자등록증 및 법인등기부등본 각1부\n나. 법인인감증명서 1부\n"
    numbered_stages = {item["name"]: item["stage"] for item in server.extract_doc_items({}, [("첨부:공고문.pdf", numbered)])}
    check(
        "A16 양성 「10.」 아래 「가.」 항목이 표제를 따름",
        all(numbered_stages.get(name) == "낙찰 후·계약 시" for name in ("사업자등록증", "법인 등기사항증명서", "법인인감증명서")),
        str(numbered_stages),
    )
    # 양성 ⑵ — 「바.」 표제 아래 「1).」 항목 + 조사 「의」가 붙은 표제.
    paren = "바. 낙찰자의 제출서류\n1). 주민등록등본(법인의 경우 법인등기부등본) 1부\n4). 국세 및 지방세 완납증명서 각 1부.\n"
    paren_stages = {item["name"]: item["stage"] for item in server.extract_doc_items({}, [("첨부:공고문.hwp", paren)])}
    check(
        "A16 양성 「바.」 아래 「1).」 항목 · 「낙찰자의 제출서류」",
        paren_stages.get("주민등록등본") == "낙찰 후·계약 시" and paren_stages.get("국세 및 지방세 완납증명서") == "낙찰 후·계약 시",
        str(paren_stages),
    )
    # 음성 ⑴ — 같은 층의 새 조항(「11.」)이 오면 앞 표제를 물려받지 않는다. 「같은 층 걷어내기」를
    # 지우면 「10.」이 스택에 남아 사업자등록증이 낙찰 후로 끌려간다.
    sibling = "10. 최종낙찰자 제출서류\n가. 법인인감증명서 1부\n11. 기타사항\n가. 사업자등록증 지참\n"
    sibling_stages = {item["name"]: item["stage"] for item in server.extract_doc_items({}, [("첨부:공고문.pdf", sibling)])}
    check("A16 음성 같은 층 새 조항은 앞 표제를 안 물려받음", sibling_stages.get("사업자등록증") == "미분류", str(sibling_stages))
    # 음성 ⑵ — 「낙찰자」만 있고 「제출서류」가 없는 표제는 「의?」 변형이 걸리지 않는다.
    selection = "바. 낙찰자 선정 기준\n1). 주민등록등본 1부\n"
    selection_stage = next((i["stage"] for i in server.extract_doc_items({}, [("첨부:공고문.pdf", selection)]) if i["name"] == "주민등록등본"), None)
    check("A16 음성 「낙찰자 선정 기준」은 낙찰 후로 안 감", selection_stage == "미분류", str(selection_stage))

    # 리뷰 r1(2026-10-19) 재현 입력 — 바깥 낙찰 후 표제를 물려받아 입찰 전 서류가 4단계로만 가면 안 된다.
    # 각 입력은 4b292c9(옛 동작)에서 낙찰 후가 아니었고, 60b000a 에서 낙찰 후로 옮겨졌던 것이다.
    def stage_of(text: str, name: str) -> object:
        return next((i["stage"] for i in server.extract_doc_items({}, [("첨부:공고문.pdf", text)]) if i["name"] == name), None)

    t1 = "8. 낙찰자 제출서류\n가. 주민등록등본 1부\n■ 공동입찰 시 유의사항\n공동입찰자는 입찰 마감일까지 인감증명서를 제출하여야 합니다.\n"
    check("A16 음성 T1 기호 형제 아래 입찰 전 문장", stage_of(t1, "인감증명서") == "입찰 전", str(stage_of(t1, "인감증명서")))
    # 직접 호출 — 목록 항목 판정. 소제목·문단은 항목이 아니다.
    check("A16 물림 판정 목록 항목 「1). 주민등록등본 1부」", server.can_inherit_outer_heading("1). 주민등록등본 1부"), "")
    check("A16 물림 판정 소제목 「가. 입찰 참가 신청」", server.can_inherit_outer_heading("가. 입찰 참가 신청"), "")
    check("A16 물림 판정 음성 문단 「가. 입찰 시 유의사항 … 사업자등록증」", not server.can_inherit_outer_heading("가. 입찰 시 유의사항 안내 사업자등록증 사본 1부"), "")
    check("A16 물림 판정 음성 긴 줄", not server.can_inherit_outer_heading("가. " + "나" * 120), "")
    # 표본 21 구조 — 서류명 없는 소제목을 지나 바깥 「입찰참가 등록서류」를 물려받는다.
    nested = "4. 입찰참가 등록서류\n가. 입찰 참가 신청\nㅇ 사업자등록증 1부\n"
    check("A16 양성 소제목을 지나 바깥 표제를 물려받음", stage_of(nested, "사업자등록증") == "입찰 전", str(stage_of(nested, "사업자등록증")))
    t2 = "10. 최종낙찰자 제출서류\n가. 개인\n1) 주민등록등본 1부\n※ 입찰 참가 시에는 아래 서류를 입찰 마감일까지 제출\n1) 사업자등록증 1부\n"
    check("A16 음성 T2 결정 문구 문단 뒤 목록은 물려받지 않음", stage_of(t2, "사업자등록증") != "낙찰 후·계약 시", str(stage_of(t2, "사업자등록증")))
    check("A16 양성 T2 같은 입력의 앞 목록은 그대로 낙찰 후", stage_of(t2, "주민등록등본") == "낙찰 후·계약 시", str(stage_of(t2, "주민등록등본")))
    t3 = "가. 낙찰자는 낙찰일로부터 5일 이내에 계약을 체결하여야 합니다.\n1) 입찰 참가 시 사업자등록증을 입찰 마감일까지 제출\n"
    check("A16 음성 T3 같은 줄 입찰 전 문구가 있으면 낙찰 후 확정 안 함", stage_of(t3, "사업자등록증") != "낙찰 후·계약 시", str(stage_of(t3, "사업자등록증")))
    t5 = "9. 계약체결 및 대금납부방법 " + "가" * 50 + " 잔대금은 60일 이내 납부\n가. 입찰 시 유의사항 " + "나" * 60 + " 사업자등록증 사본 1부\n"
    check("A16 음성 T5 긴 줄은 바깥 표제를 물려받지 않음", stage_of(t5, "사업자등록증") != "낙찰 후·계약 시", str(stage_of(t5, "사업자등록증")))
    farm = "9. 계약체결 및 대금납부방법\n라. 농지법 등 관계 법령에 의하여 농지취득자격증명이 필요한 경우 등 취득이 제한되는 사\n항은 매수자가 갖추어야 할 요건이므로 사전확인 후 응찰하시기 바랍니다.\n"
    check("A16 음성 표본 07 형태 「사전확인 후 응찰」은 입찰 전", stage_of(farm, "농지취득자격증명") == "미분류", str(stage_of(farm, "농지취득자격증명")))
    # 「응찰」 낱말 줄 — G2 낱말 검사와 충돌 검사가 겹쳐 막는다. 하나만 빼면 이 픽스처는 잡지 못한다(리뷰 r3 m2·m3).
    # 대안별 단독 픽스처는 아래 「리뷰 r3 R1」 묶음이 맡는다.
    farm_item = "9. 계약체결 및 대금납부방법\n라. 농지취득자격증명은 사전확인 후 응찰하시기 바랍니다.\n"
    check("A16 음성 「사전확인 후 응찰」 항목 줄은 미분류", stage_of(farm_item, "농지취득자격증명") == "미분류", str(stage_of(farm_item, "농지취득자격증명")))
    # 줄 넘김 — 항목 줄에는 입찰 전 낱말이 없고 다음 줄(이어지는 문장)에 「사전확인 후 입찰」이 있다. 충돌 검사만 잡는다.
    farm_wrap = "9. 계약체결 및 대금납부방법\n라. 농지취득자격증명 1부\n(취득 요건은 사전확인 후 입찰하시기 바랍니다.)\n"
    check("A16 음성 줄 넘김 「사전확인 후 입찰」도 낙찰 후로 확정하지 않음", stage_of(farm_wrap, "농지취득자격증명") == "미분류", str(stage_of(farm_wrap, "농지취득자격증명")))
    # 리뷰 r2 G2 — 넓은 낙찰 후 표제(「입찰 및 계약체결 일정」)가 그 아래 입찰 전 소제목·항목까지 끌고 가면 안 된다.
    h1 = "10. 최종낙찰자 제출서류\n가. 사업자등록증 1부\n■ 입찰참가 신청 시\n- 인감증명서 1부\n"
    check("A16 음성 H1 입찰참가 소제목은 낙찰 후 표제를 물려받지 않음", stage_of(h1, "인감증명서") != "낙찰 후·계약 시", str(stage_of(h1, "인감증명서")))
    check("A16 양성 H1 같은 입력의 앞 항목은 그대로 낙찰 후", stage_of(h1, "사업자등록증") == "낙찰 후·계약 시", str(stage_of(h1, "사업자등록증")))
    h4 = "3. 입찰 및 계약체결 일정\n가. 입찰참가 신청\nㅇ 사업자등록증 사본 1부\n"
    check("A16 음성 H4 넓은 표제 아래 입찰참가 소제목", stage_of(h4, "사업자등록증") != "낙찰 후·계약 시", str(stage_of(h4, "사업자등록증")))
    h4b = "3. 입찰 및 계약체결 일정\n가. 사업자등록증 사본 1부(입찰참가 신청 시)\n"
    check("A16 음성 H4b 넓은 표제 아래 입찰참가 항목", stage_of(h4b, "사업자등록증") != "낙찰 후·계약 시", str(stage_of(h4b, "사업자등록증")))
    # 리뷰 r3 R1 — 정규식 대안마다 그 대안 하나로만 막히는 픽스처. 대안을 지우면 해당 픽스처가 낙찰 후로 뒤집힌다.
    r3_cases = {
        "낱말 응찰": ("9. 계약체결 및 대금납부방법\n라. 농지취득자격증명 1부(응찰 전 확인)\n", "농지취득자격증명"),
        "충돌 응찰 줄넘김": ("9. 계약체결 및 대금납부방법\n라. 농지취득자격증명 1부\n(취득 요건은 사전확인 후 응찰하시기 바랍니다.)\n", "농지취득자격증명"),
        "낱말 입찰 시": ("3. 입찰 및 계약체결 일정\n가. 입찰 시 제출\nㅇ 사업자등록증 사본 1부\n", "사업자등록증"),
        "낱말 입찰 전": ("3. 입찰 및 계약체결 일정\n가. 입찰 전 준비\nㅇ 사업자등록증 사본 1부\n", "사업자등록증"),
    }
    for label, (text, name) in r3_cases.items():
        check(f"A16 음성 r3 {label}", stage_of(text, name) == "미분류", str(stage_of(text, name)))


def test_attachment_wiring() -> None:
    # attachment_parser.detect_kind() — 배선 단정과 별개로 판정 함수 자체를 직접 부른다.
    check("A10 detect_kind pdf", attachment_parser.detect_kind(b"%PDF-1.4 ...") == "pdf", "")
    check("A10 detect_kind zip(hwpx)", attachment_parser.detect_kind(b"PK\x03\x04...") == "zip", "")
    check("A10 detect_kind hwp(ole2)", attachment_parser.detect_kind(b"\xd0\xcf\x11\xe0...") == "hwp", "")
    try:
        attachment_parser.detect_kind(b"random-garbage")
        check("A10 detect_kind 미확인 형식 예외", False, "예외가 안 났다")
    except ValueError:
        check("A10 detect_kind 미확인 형식 예외", True, "")

    # 게이트 우회: 제출 동사도 조건도 없는 줄이지만 첨부라서 뽑혀야 한다.
    # 같은 줄을 본문(공고문 절)에 넣으면 A1·A5 가 이미 세운 「단순 언급 제외」 그대로 안 뽑혀야 한다.
    # 「사업자등록증」 자체가 license 축(`등록증`)에 걸리지만 A5 규칙상 license 단독은 authorizing이
    # 아니라서 본문에서는 막힌다 — 그 성질을 그대로 이용한 음성 대조다.
    plain_mention = "사업자등록증"
    body_only = server.extract_doc_items(server.split_sections(section("공고문", f"<p>{plain_mention}</p>")))
    check("A10 음성 본문은 그대로 게이트 유지", body_only == [], str(body_only))

    attach_items = server.extract_doc_items({}, [("첨부:붙임1.hwp", plain_mention)])
    names = {item["name"] for item in attach_items}
    check("A10 양성 첨부는 제출 동사 없어도 추출", "사업자등록증" in names, str(sorted(names)))
    check("A10 sourceSection 첨부 라벨", attach_items[0]["sourceSection"] == "첨부:붙임1.hwp", str(attach_items[0]))

    # 조건 무시: 줄에 명시적 조건(공동입찰)이 있어도 첨부 항목의 condition은 "공통"이어야 한다
    # (조건 물림 구조가 첨부에서 자주 깨져 오귀속을 만들기 때문 — 2026-09-12 실측으로 정한 규칙).
    condition_line = "공동입찰 참가자는 인감증명서를 지참하십시오."
    cond_ignored = server.extract_doc_items({}, [("첨부:붙임2.hwp", condition_line)])
    seal_item = next(item for item in cond_ignored if item["name"] == "인감증명서")
    check("A10 조건 무시 → 공통", seal_item["conditions"] == ["공통"], str(seal_item["conditions"]))
    # 음성 대조: 같은 줄이 본문에 있으면 여전히 조건이 "공동입찰"로 붙어야 한다(본문 로직 불변 증명).
    cond_kept = server.extract_doc_items(server.split_sections(section("공고문", f"<p>{condition_line}</p>")))
    seal_body = next(item for item in cond_kept if item["name"] == "인감증명서")
    check("A10 음성 본문은 조건 유지", seal_body["conditions"] == ["공동입찰"], str(seal_body["conditions"]))

    # 1200자 상한 해제: 서류명이 긴 줄 안에 묻혀 있어도(첨부는 줄바꿈 없는 텍스트가 흔하다) 잡혀야 한다.
    long_line = ("가" * 1300) + " 사업자등록증 제출"
    long_attach = server.extract_doc_items({}, [("첨부:긴줄.pdf", long_line)])
    check("A10 양성 첨부 1200자 초과 줄도 추출", any(i["name"] == "사업자등록증" for i in long_attach), str(long_attach))
    # 음성 대조: 같은 길이의 줄이 본문 절에 있으면 여전히 상한에 걸려 안 잡혀야 한다(상한을 완전히
    # 지운 게 아니라 첨부에서만 뺐음을 증명).
    long_body = server.extract_doc_items(server.split_sections(section("공고문", f"<p>{long_line}</p>")))
    check("A10 음성 본문은 1200자 상한 유지", long_body == [], str(long_body))

    # 조항 표제 물림: 단계를 밝히는 줄은 표제뿐이고 서류명은 다음 줄에 있는 표 구조.
    # resolve_doc_stage() 가 HEADING_STAGE_RULES 로 그 표제 문자열을 직접 대조한다
    # (CONTRACT_STAGE_RE/carried_stage 는 2026-10-18 폐기 — stage-classification-design.md).
    stage_chunk = "라. 계약체결시 필요서류\n개인 주민등록초본, 인감증명서"
    stage_items = server.extract_doc_items({}, [("첨부:계약서류.pdf", stage_chunk)])
    stage_names = {item["name"]: item["stage"] for item in stage_items}
    check(
        "A10 양성 조항 표제 물림",
        stage_names.get("주민등록초본") == "낙찰 후·계약 시" and stage_names.get("인감증명서") == "낙찰 후·계약 시",
        str(stage_names),
    )
    # 음성 대조: 다음 최상위 번호(마.)로 넘어가면 표제 물림이 끊겨야 한다. 새 표제("마. 다른
    # 절")는 사전에 없고 그 줄("개인 주민등록초본")에도 결정적 문구가 없으니 "미분류"다 —
    # 옛 코드는 여기서 기본값 "입찰 전"으로 떨어졌다(추측 금지 · §3).
    reset_chunk = "라. 계약체결시 필요서류\n마. 다른 절\n개인 주민등록초본"
    reset_items = server.extract_doc_items({}, [("첨부:계약서류.pdf", reset_chunk)])
    reset_stage = next((i["stage"] for i in reset_items if i["name"] == "주민등록초본"), None)
    check("A10 음성 새 표제로 물림 끊김 → 미분류", reset_stage == "미분류", str(reset_stage))

    # A11. 문장 단위 판정 — 같은 블록 안에 「계약체결」 같은 낙찰 후 신호가 있어도, 그 서류가
    # 「속한 문장」에 없으면 더 이상 오염되지 않아야 한다. 표본 21(§4-3 appendix)이 실제로
    # 겪은 사고: "4. 입찰참가 등록서류" 표제 아래 서류들이 뒤이은 "5. 낙찰자 결정방법"의
    # "낙찰자"에 반응해 전부 낙찰 후로 끌려갔다. 표본 20의 인감증명서(13건 전부 같은 경로로
    # 오염)도 같은 사례다.
    bleed_chunk = (
        "4. 입찰참가 등록서류\n"
        "- 법인 등기사항증명서\n"
        "- 인감증명서\n"
        "5. 낙찰자 결정방법\n"
        "가. 낙찰자는 계약체결 후 사업을 개시하여야 한다.\n"
    )
    bleed_items = server.extract_doc_items({}, [("첨부:공고문.pdf", bleed_chunk)])
    bleed_stages = {item["name"]: item["stage"] for item in bleed_items}
    check(
        "A11 양성 — 입찰참가 등록서류 표제가 결정",
        bleed_stages.get("법인 등기사항증명서") == "입찰 전" and bleed_stages.get("인감증명서") == "입찰 전",
        str(bleed_stages),
    )
    # 돌연변이 대조 — resolve_doc_stage 의 표제 우선순위를 지우면(문장 레벨만 쓰면) 이 서류들은
    # 자기 줄에 결정적 문구가 없어 "미분류"로 떨어진다. HEADING_STAGE_RULES 매칭을 끈 경우를
    # 직접 재현해 이 축이 실제로 표제 판정에 의존함을 확인한다.
    heading_only = server.resolve_doc_stage("4. 입찰참가 등록서류", "- 법인 등기사항증명서")
    sentence_only = server.resolve_doc_stage("", "- 법인 등기사항증명서")
    check(
        "A11 돌연변이 — 표제 없이는 미분류로 떨어진다(표제 의존 증명)",
        heading_only == "입찰 전" and sentence_only == "미분류",
        f"heading={heading_only} sentence={sentence_only}",
    )
    # 돌연변이 대조 — 표제가 없는 상태에서 서류 줄 자체에 결정적 문구가 있으면(문장 단위
    # 판정) 그 줄만 보고 정해야 한다. "회송" 문구는 표본 20의 인감증명서 사례(매매계약서를
    # 우편으로 받아 인감날인 후 회송)가 근거다.
    sentence_decisive = server.resolve_doc_stage("", "매매계약서를 우편수취 후 인감날인하여 회송하십시오.")
    check(
        "A11 음성 — 표제 없이 문장 결정적 문구만으로도 정한다",
        sentence_decisive == "낙찰 후·계약 시",
        sentence_decisive,
    )

    # A12. 서식명 사전 — 공동입찰참가신청서·대리입찰신청서·미성년자 입찰참가 동의서는 "낙찰
    # 후·계약 시"를 확정하는 조항 표제("14. 계약체결 시 지참 서류") 아래 있어도 입찰 전으로
    # 고정돼야 한다(표본04~08·20 appendix 정답 — 어느 행도 "낙찰 후"가 아니다).
    form_name_heading = server.resolve_doc_stage("14. 계약체결 시 지참 서류", "- 공동입찰참가신청서", "공동입찰참가신청서")
    check(
        "A12 양성 — 낙찰 후 표제 아래서도 서식명이 입찰 전으로 고정",
        form_name_heading == "입찰 전",
        form_name_heading,
    )
    # 돌연변이 대조 — name 을 안 넘기면(FORM_NAME_STAGE_RULES 매칭이 꺼진 상태를 재현) 같은
    # 표제·문장이 "낙찰 후·계약 시"로 떨어져야 한다. 즉 지금의 "입찰 전" 결과는 FORM_NAME_
    # STAGE_RULES 가 실제로 그 판정을 뒤집고 있다는 뜻이다(표제 의존이 아니라는 증명).
    without_form_name = server.resolve_doc_stage("14. 계약체결 시 지참 서류", "- 공동입찰참가신청서")
    check(
        "A12 돌연변이 — 서식명 사전을 빼면 표제 판정(낙찰 후)으로 떨어진다",
        without_form_name == "낙찰 후·계약 시",
        without_form_name,
    )
    # extract_doc_items 레벨 통합 — 실제 파이프라인에서도 같은 역전이 일어나는지 확인한다.
    form_name_pipeline = server.extract_doc_items(
        {}, [("첨부:공고문.pdf", "14. 계약체결 시 지참 서류\n- 대리입찰신청서\n- 미성년자 입찰참가 동의서")]
    )
    form_name_stages = {item["name"]: item["stage"] for item in form_name_pipeline}
    check(
        "A12 통합 — 대리입찰신청서·미성년자 입찰참가 동의서 모두 입찰 전",
        form_name_stages.get("대리입찰신청서") == "입찰 전"
        and form_name_stages.get("미성년자 입찰참가 동의서") == "입찰 전",
        str(form_name_stages),
    )

    # A13. 조항 표제 사전 10종 — appendix 160행에서 인용한 표제를 각각 직접 대조한다.
    # 사전 크기 자체가 줄어들면(예: 2종으로 되돌리면) 이 축이 실패해야 한다 — 길이
    # 단정과 별개로, 사전에서 빠지면 바로 영향받는 리터럴 표제 3개를 직접 판정해 둔다.
    check(
        "A13 양성 — 조항 표제 사전이 최소 10종(appendix §555행 기준)",
        len(server.HEADING_STAGE_RULES) >= 10,
        len(server.HEADING_STAGE_RULES),
    )
    heading_cases = (
        ("계약체결시 필요서류", "- 주민등록초본", "낙찰 후·계약 시"),  # 표본15~17
        ("다. 계약체결 장소", "- 법인인감증명서", "낙찰 후·계약 시"),  # 표본12
        ("8. 낙찰자 제출서류 (낙찰일로부터 30일 이내 제출)", "- 법인인감증명서", "낙찰 후·계약 시"),  # 표본13
    )
    heading_results = {heading: server.resolve_doc_stage(heading, window) for heading, window, _ in heading_cases}
    check(
        "A13 양성 — appendix 인용 표제 3종(표본12·13·15~17) 직접 대조",
        all(heading_results[heading] == expected for heading, _, expected in heading_cases),
        str(heading_results),
    )
    # 돌연변이 대조 — 이 세 표제를 지우면(HEADING_STAGE_RULES 를 원래 2종으로 되돌린 것과
    # 같은 효과) 위 세 케이스 중 "계약체결시 필요서류"·"계약체결 장소"는 옛 2종 regex의
    # "계약.{0,20}(?:체결|지참)" 에 우연히 걸릴 수 있으나, "낙찰자 제출서류"는 옛 regex의
    # "낙찰\s*자.{0,10}제출" 에도 걸린다 — 그래서 셋 중 실제로 사전 확장에만 의존하는
    # 표제로 "계약체결 시 지참 서류"(표본22, 옛 2종 regex에는 없던 "지참" 조합)를 쓴다.
    mutated_heading_rules: tuple[tuple[re.Pattern[str], str], ...] = (
        (re.compile(r"구비\s*서류|낙찰\s*자.{0,10}제출|낙찰\s*일"), "낙찰 후·계약 시"),
        (re.compile(r"입찰\s*참가\s*자격|입찰\s*참가\s*(?:신청\s*)?등록\s*서류"), "입찰 전"),
    )
    original_heading_rules = server.HEADING_STAGE_RULES
    server.HEADING_STAGE_RULES = mutated_heading_rules
    try:
        mutated_result = server.resolve_doc_stage("14. 계약체결 시 지참 서류", "- 법인인감증명서")
    finally:
        server.HEADING_STAGE_RULES = original_heading_rules
    check(
        "A13 돌연변이 — '계약체결 시 지참 서류' 표제를 빼면 미분류로 떨어진다(사전 의존 증명)",
        mutated_result == "미분류",
        mutated_result,
    )

    # A14. "별도 문의 필요" — 컨소시엄 협정서처럼 온비드 공통 규정에 일반 근거가 없는
    # 서류는 조항 표제·문장 모두 못 정했을 때 "미분류"가 아니라 "별도 문의 필요"로 다르게
    # 나와야 한다. 음성 대조로 "주민등록등본"(NO_GENERAL_BASIS_DOC_NAMES 밖의 서류)는
    # 같은 조건에서 그대로 "미분류"여야 한다 — 이 축이 전체 미분류를 삼키면 안 된다.
    consortium_unresolved = server.resolve_doc_stage("", "컨소시엄 협정서 1부 포함", "컨소시엄 협정서")
    generic_unresolved = server.resolve_doc_stage("", "주민등록등본 1부", "주민등록등본")
    check(
        "A14 양성 — 컨소시엄 협정서는 미분류 대신 별도 문의 필요",
        consortium_unresolved == "별도 문의 필요",
        consortium_unresolved,
    )
    check(
        "A14 음성 — 일반 서류는 그대로 미분류(별도 문의로 전부 삼키지 않음)",
        generic_unresolved == "미분류",
        generic_unresolved,
    )
    # 돌연변이 대조 — NO_GENERAL_BASIS_DOC_NAMES 를 비우면(그 판정을 지우면) 컨소시엄
    # 협정서도 다시 "미분류"로 떨어져야 한다. 이 판정이 실제로 결과를 바꾼다는 증명이다.
    original_no_basis = server.NO_GENERAL_BASIS_DOC_NAMES
    server.NO_GENERAL_BASIS_DOC_NAMES = frozenset()
    try:
        mutated_consortium = server.resolve_doc_stage("", "컨소시엄 협정서 1부 포함", "컨소시엄 협정서")
    finally:
        server.NO_GENERAL_BASIS_DOC_NAMES = original_no_basis
    check(
        "A14 돌연변이 — NO_GENERAL_BASIS_DOC_NAMES 를 비우면 미분류로 되돌아간다",
        mutated_consortium == "미분류",
        mutated_consortium,
    )
    # 조항 표제가 "낙찰 후"를 확정하는 상황에서는 컨소시엄 협정서도 그 표제를 그대로
    # 따라야 한다 — NO_GENERAL_BASIS 는 "셋 다 못 정했을 때"의 최종 기본값일 뿐, 표제·문장
    # 판정보다 우선하지 않는다.
    consortium_with_heading = server.resolve_doc_stage("다. 계약 체결 시 구비서류", "컨소시엄 협정서", "컨소시엄 협정서")
    check(
        "A14 양성 — 표제가 확정되면 컨소시엄 협정서도 그 표제를 따른다(기본값이 아니라 최종 폴백)",
        consortium_with_heading == "낙찰 후·계약 시",
        consortium_with_heading,
    )

    # A15. 서식명 사전 완성도 — "오분류 N건"만 세면 사전이 비어 있어도 통과한다(이번 결함의
    # 뿌리). 사전 크기·등재 범위·오염 방지를 직접 센다.
    check(
        "A15 양성 — 서식명 사전이 표준 이름 3종(공동입찰·대리입찰·미성년자) 전부를 입찰 전으로 등재",
        server.FORM_NAME_STAGE_RULES == {
            "공동입찰참가신청서": "입찰 전",
            "대리입찰신청서": "입찰 전",
            "미성년자 입찰참가 동의서": "입찰 전",
        },
        server.FORM_NAME_STAGE_RULES,
    )
    # 08_온비드자료실_오픈API28종_조사_20260907.md 191~206행이 실제로 나열한 기관명 접두어
    # 변형 12개 전부를 raw 텍스트로 넣어, DOC_NAME_PATTERNS 정규화 + FORM_NAME_STAGE_RULES
    # 경로를 거쳐 전부 "입찰 전"으로 뽑히는지 센다 — 변형 중 하나라도 빠지면 그 변형은 사전
    # 등재 범위 밖이라는 뜻이다.
    # (표준명, 변형 원문) 쌍 — "(이용기관 입찰용) 대리입찰신청서(위임장) 양식"처럼 괄호 안
    # 참고 문구에 "위임장"(별도 범용 서류, DOC_NAME_PATTERNS 에 따로 있음)이 함께 뽑히는
    # 변형도 있다 — 그 경우 "대리입찰신청서" 쪽 판정만 본다. "위임장"은 이 사전의 대상이
    # 아니라 §2 설계 규칙대로 미분류로 남는 것이 맞다(추측 금지).
    FORM_NAME_VARIANTS_12 = (
        ("공동입찰참가신청서", "공동입찰참가신청서"),
        ("공동입찰참가신청서", "(이용기관 입찰용)공동입찰참가신청서"),
        ("공동입찰참가신청서", "(캠코 공유재산)공동입찰참가신청서"),
        ("공동입찰참가신청서", "유입자산 공동입찰참가신청서"),
        ("공동입찰참가신청서", "수탁담보주택 공동입찰참가신청서"),
        ("대리입찰신청서", "대리입찰신청서"),
        ("대리입찰신청서", "(이용기관 입찰용) 대리입찰신청서(위임장) 양식"),
        ("대리입찰신청서", "(캠코 공유재산)대리입찰신청서"),
        ("대리입찰신청서", "유입자산 대리입찰신청서"),
        ("대리입찰신청서", "수탁담보주택 대리입찰신청서"),
        ("미성년자 입찰참가 동의서", "(이용기관 입찰용) 미성년자입찰참가동의서 양식"),
        ("미성년자 입찰참가 동의서", "(캠코 공유재산)미성년자입찰참가동의서"),
    )
    variant_stages = {}
    for canonical, variant in FORM_NAME_VARIANTS_12:
        extracted = server.extract_doc_items({}, [("첨부:서식.pdf", variant)])
        matched = next((item for item in extracted if item["name"] == canonical), None)
        variant_stages[variant] = matched["stage"] if matched else "추출 안 됨"
    check(
        "A15 양성 — 변형 12종 전부 표준명으로 뽑혀 입찰 전으로 고정",
        all(stage == "입찰 전" for stage in variant_stages.values()),
        str(variant_stages),
    )
    # 돌연변이 대조 — 표준 이름 하나(공동입찰참가신청서)를 사전에서 빼면, 그 이름을 쓰는
    # 변형(기관명 접두어 붙은 것 포함)이 더 이상 입찰 전으로 고정되지 않아야 한다.
    mutated_form_rules = {k: v for k, v in server.FORM_NAME_STAGE_RULES.items() if k != "공동입찰참가신청서"}
    original_form_rules = server.FORM_NAME_STAGE_RULES
    server.FORM_NAME_STAGE_RULES = mutated_form_rules
    try:
        mutated_variant = server.extract_doc_items({}, [("첨부:서식.pdf", "(이용기관 입찰용)공동입찰참가신청서")])
        mutated_stage = {item["stage"] for item in mutated_variant}
    finally:
        server.FORM_NAME_STAGE_RULES = original_form_rules
    check(
        "A15 돌연변이 — 사전에서 표준 이름 하나를 빼면 그 변형이 더 이상 입찰 전으로 안 뽑힘",
        mutated_stage != {"입찰 전"},
        mutated_stage,
    )
    # 범용 서류(재산유형마다 단계가 달라지는 서류, §2 설계 규칙 2)가 서식명 사전에 들어가면
    # 그 자체가 새 오분류를 만든다 — 절대로 키로 들어가 있으면 안 된다.
    GENERIC_DOC_NAMES = {"인감증명서", "주민등록등본", "사업자등록증", "신분증", "위임장"}
    check(
        "A15 양성 — 서식명 사전에 범용 서류가 전혀 없음",
        not (GENERIC_DOC_NAMES & set(server.FORM_NAME_STAGE_RULES)),
        sorted(GENERIC_DOC_NAMES & set(server.FORM_NAME_STAGE_RULES)),
    )
    # 돌연변이 대조 — 범용 서류 하나를 사전에 몰래 넣으면 위 검사가 바로 잡아내야 한다.
    polluted_form_rules = {**server.FORM_NAME_STAGE_RULES, "인감증명서": "입찰 전"}
    check(
        "A15 돌연변이 — 범용 서류가 섞이면 검사가 실패를 잡아낸다(검사 자체의 유효성 증명)",
        bool(GENERIC_DOC_NAMES & set(polluted_form_rules)),
        sorted(GENERIC_DOC_NAMES & set(polluted_form_rules)),
    )

    # headline 출처 구분: 본문만/첨부만/둘 다 섞임을 각각 다른 문구로 말해야 한다.
    body_sections = server.split_sections(section("제출서류", "<p>사업자등록증 사본을 제출하십시오.</p>"))
    body_only_checklist = server.build_doc_checklist(body_sections, "공유재산", [])
    check("A10 headline 본문만", body_only_checklist["headline"].startswith("공고 원문에서"), body_only_checklist["headline"])

    attach_only_checklist = server.build_doc_checklist({}, "공유재산", [], [("첨부:붙임1.hwp", "인감증명서 지참")])
    check("A10 headline 첨부만", attach_only_checklist["headline"].startswith("첨부 파일에서"), attach_only_checklist["headline"])

    mixed_checklist = server.build_doc_checklist(
        body_sections, "공유재산", [], [("첨부:붙임1.hwp", "인감증명서 지참")]
    )
    check("A10 headline 본문+첨부 혼합", mixed_checklist["headline"].startswith("공고 원문과 첨부 파일에서"), mixed_checklist["headline"])

    # 하위호환: attachment_chunks 를 아예 안 넘긴 기존 3-인자 호출도 그대로 동작해야 한다.
    legacy_checklist = server.build_doc_checklist(body_sections, "공유재산", [])
    check("A10 하위호환 3-인자 호출", legacy_checklist["status"] == "extracted", str(legacy_checklist["status"]))
    check("A10 contact 기본값 빈 문자열", legacy_checklist.get("contact") == "", repr(legacy_checklist.get("contact")))

    # A14 연동 — build_notice 가 뽑은 담당부점/공고기관 연락처가 "별도 문의 필요" 화면
    # 안내에 쓰이도록 build_doc_checklist 가 그대로 돌려줘야 한다.
    contact_checklist = server.build_doc_checklist(body_sections, "공유재산", [], None, "한국자산관리공사 국유재산지원처")
    check(
        "A14 연동 — build_doc_checklist 가 contact 를 그대로 반환",
        contact_checklist.get("contact") == "한국자산관리공사 국유재산지원처",
        contact_checklist.get("contact"),
    )


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
    # 2026-10-19 커뮤니티 조사 1-5 반영 — 매각 코치에도 현장·실물 확인 항목이 있고, 판단 낱말은 없다.
    site_items = [item for item in real_coach["unresolvedChecks"] if "현장" in item["title"]]
    check("B1 매각 코치에 현장·실물 확인 항목", len(site_items) == 1, str(real_titles))
    check(
        "B1 음성 현장 항목은 상태 판단을 하지 않는다",
        site_items and not re.search(r"나쁘|좋|위험|추천", site_items[0]["reason"] + site_items[0]["action"]),
        str(site_items),
    )
    check(
        "B1 매각 코치 질문에 현장 확인 질문",
        any("현장" in q for q in real_coach["askAgency"]),
        str(real_coach["askAgency"]),
    )

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
    # 🔴 C형은 첨부가 있어도 첨부로 «보내지» 않는다. 표본에서 첨부에도 목록이 없었기 때문이다
    # (known-pitfalls.md:51). 첨부로 보내면 없는 목록을 찾으라고 앱 밖으로 내보내는 거짓 안내다.
    check(
        "B1 C형 첨부로 보내지 않음",
        "첨부 공고문을 확인" not in str(c_type["headline"]),
        str(c_type["headline"]),
    )
    # 그러나 첨부가 화면에 렌더되므로 그 사실은 언급해야 한다 — 안 하면 말과 화면이 어긋난다.
    check("B1 C형 첨부 존재 언급", "첨부 1건" in str(c_type["headline"]), str(c_type["headline"]))
    # 🔴 표본 수치로 이 공고의 첨부를 예측하지 않는다. 표본 2건은 일반화하기에 작고,
    # 화면이 「표본에서는 없었습니다」라고 하면 이 공고 첨부에 대한 예측이 된다.
    # 유형 수준의 사례 진술은 profile["detail"] 이 맡는다(2026-09-10 판정 P0-D).
    check("B1 C형 음성 — 표본 수치로 예측하지 않음", "표본" not in str(c_type["headline"]), str(c_type["headline"]))
    check("B1 C형 음성 — 원문 전체를 단정하지 않음", "원문에 없" not in str(c_type["headline"]), str(c_type["headline"]))
    # 음성 대조: 첨부가 «없는» C형은 첨부를 언급하지 않는다.
    c_no_attach = server.build_doc_checklist(empty, "파산자산", [])
    check(
        "B1 C형 음성 — 첨부 없으면 첨부를 말하지 않음",
        "첨부" not in str(c_no_attach["headline"]) and "찾지 못했습니다" in str(c_no_attach["headline"]),
        str(c_no_attach["headline"]),
    )
    check(
        "B1 C형 음성 — 준비를 단정하지 않음",
        "준비를 진행" not in str(c_type["headline"]),
        str(c_type["headline"]),
    )
    extracted = server.build_doc_checklist(server.split_sections(BULLET_CONDITION_NOTICE), "국유재산", [])
    check("B1 A형 추출됨", extracted["status"] == "extracted", str(extracted["status"]))
    # 🔴 부분 추출을 완전한 것처럼 말하지 않는다. 추출은 닫힌 어휘 기준이라 그 밖은 못 뽑는다.
    # 화면 게이트 N2 가 같은 것을 재지만 그쪽은 픽스처를 태운다 — 서버가 실제로 이 note 를
    # 만드는지는 여기서만 증명된다.
    check(
        "B1 A형 인식 범위 한정 안내",
        any("인식 범위가 한정적" in str(note) for note in extracted["notes"]),
        str(extracted["notes"]),
    )
    # 음성 대조: 추출하지 못한 상태에는 이 note 를 붙이지 않는다(붙이면 없는 목록의 범위를 말한다).
    check(
        "B1 음성 — 못 뽑은 상태엔 범위 한정 안내 없음",
        not any("인식 범위가 한정적" in str(note) for note in c_type["notes"]),
        str(c_type["notes"]),
    )
    # 🔴 섞인 표(실서류명 + 구분명)에도 총평 경고가 붙어야 한다. 전건 generic 만 보던 때는
    # 실서류명 한 줄 때문에 나머지 구분명 줄까지 실제 서류명으로 읽혔다.
    mixed_html = section(
        "제출서류",
        "<table><tr><th>구분</th><th>서류명</th></tr>"
        "<tr><td>매수신청</td><td>인감증명서</td></tr>"
        "<tr><td>공동입찰서류</td><td>공동입찰서류</td></tr></table>",
    )
    mixed = server.build_doc_checklist(server.split_sections(mixed_html), "국유재산", [])
    mixed_generic = [row for row in mixed["tableRows"] if row["generic"]]
    check("B1 섞인 표 도달 — generic 과 실서류명이 공존", 0 < len(mixed_generic) < len(mixed["tableRows"]), f"{len(mixed_generic)}/{len(mixed['tableRows'])}")
    check(
        "B1 섞인 표 총평 경고",
        any("구분명" in str(note) for note in mixed["notes"]),
        str(mixed["notes"]),
    )
    # 음성 대조: generic 이 하나도 없는 표에는 총평 경고를 붙이지 않는다.
    real_only_html = section(
        "제출서류",
        "<table><tr><th>구분</th><th>서류명</th></tr><tr><td>매수신청</td><td>인감증명서</td></tr></table>",
    )
    real_only = server.build_doc_checklist(server.split_sections(real_only_html), "국유재산", [])
    check(
        "B1 음성 — 실서류명만이면 총평 경고 없음",
        not any("구분명" in str(note) for note in real_only["notes"]),
        str(real_only["notes"]),
    )

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
    # 보증금 계산 기준 — 압류재산만 최저입찰가(예정가) 기준이고 국유·수탁·이용기관은 입찰금액
    # 기준이다(온비드 준수규칙). 원문이 「입찰금액 X 5%」인데 「기준이 되는 최저입찰가격은 …」을
    # 붙이면 기준을 잘못 안내한다(2026-10-19 정합성 대조 · 시연 공고 3건 중 2건이 입찰금액 기준).
    by_bid = server.deposit_basis_note("입찰금액 X 5%", "20,128,466")
    check("B4 입찰금액 기준은 최저입찰가격을 기준으로 말하지 않음", "입찰금액을 기준" in by_bid and "20,128,466" not in by_bid, by_bid)
    by_floor = server.deposit_basis_note("최저입찰가격 X 10%", "20,128,466")
    check("B4 음성 최저입찰가 기준은 그 값을 그대로 안내", "20,128,466" in by_floor and "입찰금액을 기준" not in by_floor, by_floor)
    # 「최저입찰금액」은 입찰금액 기준이 아니다(리뷰 r1 F3 · 「입찰금액」 부분 일치로 반대 안내가 나갔다).
    floor_amount = server.deposit_basis_note("최저입찰금액 X 10%", "20,128,466")
    check("B4 음성 「최저입찰금액」을 입찰금액 기준으로 말하지 않음", "입찰금액을 기준" not in floor_amount, floor_amount)
    unknown_basis = server.deposit_basis_note("공고문 참조", "20,128,466")
    check("B4 기준을 못 읽으면 단정하지 않음", "원문에서 확인" in unknown_basis and "20,128,466" not in unknown_basis, unknown_basis)
    # 배선 — extract_cost_terms 가 실제로 이 판정을 부른다(원문값이 입찰금액 기준인 절).
    bid_amount_sections = server.split_sections(ONBID_HELP_SECTION.replace("최저입찰가격 X 10%", "입찰금액 X 5%"))
    wired = next(term for term in server.extract_cost_terms(bid_amount_sections, "비공개") if term["title"] == "입찰보증금")
    check("B4 배선 입찰금액 기준 note", "입찰금액을 기준" in str(wired["note"]), str(wired))


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
    check("B5 목차 번호 제목", titles == ["1. 입찰방법", "2. 대금 납부"], str(titles))
    check("B5 목차 본문 연결", outline[0]["body"] == "온비드를 이용한 인터넷 공매입니다.", str(outline[0]))
    # 음성 대조 3종: 서술문·첨부 파일명·중복은 목차가 아니다.
    check("B5 목차 음성 서술문", all("연기될 수 있습니다" not in title for title in titles), str(titles))
    check("B5 목차 음성 첨부 파일명", all(".hwp" not in title for title in titles), str(titles))
    check("B5 목차 음성 중복 제거", len(titles) == len(set(titles)), str(titles))
    check("B5 목차 음성 절 없음", server.extract_notice_outline({}) == [], "")


def test_glossary() -> None:
    entries = server.build_glossary("압류재산", "매각", "2026년 제010차 압류재산 공매공고")
    terms = [entry["term"] for entry in entries]
    check("용어 압류재산", "압류재산" in terms, str(terms))
    check("용어 매각", "매각" in terms, str(terms))
    check("용어 중복 없음", len(terms) == len(set(terms)), str(terms))
    # 2026-10-19: 재산유형·처분방식을 읽지 못한 공고도 공통 절차 용어(group=basic · scope=common)는 보여 준다.
    # 종전 단정 「미상이면 []」은 「미상이면 표기 매칭(match) 0건 · 기본 용어는 공통 scope 만」으로 바뀌었다.
    unknown = server.build_glossary("재산유형 확인", "처분방식 확인", "")
    check("용어 음성 미상 — 표기 매칭 0건", [e for e in unknown if e["group"] == "match"] == [], str(unknown))
    # 기본 용어의 뜻풀이는 질문창과 같은 사전 ONBID_GUIDE_TERMS 에서 읽고, 용어 탭에 올릴 키만 GLOSSARY_TAB_TERMS 가 고른다.
    missing_keys = [t for t in server.GLOSSARY_TAB_TERMS if t not in server.ONBID_GUIDE_TERMS]
    check("B6 용어 탭 키가 전부 사전에 있다", missing_keys == [], str(missing_keys))
    common_terms = {t for t in server.GLOSSARY_TAB_TERMS if server.ONBID_GUIDE_TERMS[t]["scope"] == "common"}
    check(
        "용어 음성 미상 — 기본 용어는 공통 scope 만",
        unknown and all(e["group"] == "basic" and e["term"] in common_terms for e in unknown),
        str([e["term"] for e in unknown]),
    )
    # 리터럴 음성(리뷰 r1 P-38 ⑴) — 위 단정의 기대값은 사전 scope 에서 계산하므로 누가 「매각결정기일」의
    # scope 를 common 으로 바꾸면 함께 움직여 영원히 초록이다. 유형별 용어 이름을 여기 손으로 박는다.
    typed_terms = {"매각결정기일", "차순위 매수신청", "대부료", "소유권이전", "명도책임", "등기촉탁"}
    check(
        "용어 음성 미상 — 유형별 용어 없음(리터럴)",
        not any(e["term"] in typed_terms for e in unknown),
        str([e["term"] for e in unknown]),
    )
    # 감정평가금액 note(price_candidates)는 단정형이 아니라 가정형이어야 한다(리뷰 r1 #3 · 정본에 관계 서술 없음).
    source_text = Path(server.__file__).read_text(encoding="utf-8")
    check("B6 감정평가금액 note 가정형 문장 존재(소스 문자열 · 배선은 보지 않음)", "최저입찰가격과 다를 수 있고, 둘의 관계는 공고 원문에서 확인하십시오." in source_text, "")
    check("B6 음성 감정평가금액 단정형 0건", "최저입찰가격과는 다른 값" not in source_text, "")

    # B6 기본 용어(GLOSSARY_TAB_TERMS ∩ ONBID_GUIDE_TERMS) — 공고 유형에 따라 다른 묶음이 앞에 선다(2026-10-19 커뮤니티 조사 1-1 반영).
    groups = [entry["group"] for entry in entries]
    check("B6 기본 용어가 표기 매칭보다 앞", groups == sorted(groups, key=lambda g: 0 if g == "basic" else 1), str(groups))
    basic_sale = {e["term"] for e in entries if e["group"] == "basic"}
    check("B6 압류·매각 기본 용어에 매각결정기일", "매각결정기일" in basic_sale, str(basic_sale))
    check("B6 압류·매각 기본 용어에 대금납부기한·소유권이전", {"대금납부기한", "소유권이전"} <= basic_sale, str(basic_sale))
    check("B6 압류·매각 기본 용어에 유찰·개찰·입찰보증금", {"유찰", "개찰", "입찰보증금"} <= basic_sale, str(basic_sale))
    lease_entries = server.build_glossary("국유재산", "임대/대부입찰", "")
    basic_lease = {e["term"] for e in lease_entries if e["group"] == "basic"}
    check("B6 국유·임대 기본 용어에 대부료", "대부료" in basic_lease, str(basic_lease))
    check("B6 음성 국유·임대 기본 용어에 매각결정기일·소유권이전 없음", not ({"매각결정기일", "소유권이전"} & basic_lease), str(basic_lease))
    check("B6 음성 압류·매각 기본 용어에 대부료 없음", "대부료" not in basic_sale, str(basic_sale))
    # 도달 증거 — 두 집합이 실제로 다르다(둘 다 공통만 돌려주면 위 단정들이 영구 초록이 된다).
    check("B6 도달 증거 — 매각·임대 기본 용어 집합이 다름", basic_sale != basic_lease, "")
    # 음성 — 기본 용어는 판단을 담지 않는다. 금지 낱말은 CLAUDE.md 행동 규칙(입찰 여부·수익성·권리 판단).
    judging = [t for t in server.GLOSSARY_TAB_TERMS if re.search(r"수익|추천|유리|안전하|권리분석", str(server.ONBID_GUIDE_TERMS[t]["text"]))]
    check("B6 음성 기본 용어 뜻풀이에 판단 낱말 없음", judging == [], str(judging))
    check("B6 기본 용어마다 출처가 있다", all(e.get("source") for e in entries if e["group"] == "basic"), "")

    # B6 머리표 자르기 — 사전 text 가 「[압류재산] … [국유재산 매각] …」로 묶인 항목은 공고 분류의 조각만 남긴다.
    sale_due = next(e["meaning"] for e in entries if e["term"] == "대금납부기한")
    lease_due = next(e["meaning"] for e in lease_entries if e["term"] == "대금납부기한")
    unknown_due = next(e["meaning"] for e in unknown if e["term"] == "대금납부기한")
    check("B6 머리표 압류 조각만", "매각결정통지서" in sale_due and "국유재산" not in sale_due and "[" not in sale_due, sale_due[:80])
    check("B6 머리표 국유 대부 조각만", "5영업일" in lease_due and "매각결정통지서" not in lease_due and "60일" not in lease_due, lease_due[:80])
    check("B6 머리표 미상이면 원문 그대로", unknown_due.startswith("[압류재산]") and "[국유재산 매각]" in unknown_due, unknown_due[:80])
    lease_deposit = next(e["meaning"] for e in lease_entries if e["term"] == "보증금 귀속")
    check("B6 머리표 「국유재산」 하나로 묶인 글도 국유 대부에 맞춤", "국고에 귀속" in lease_deposit and "매도자" not in lease_deposit, lease_deposit[:80])
    local_lease = {e["term"]: e["meaning"] for e in server.build_glossary("공유재산", "임대", "") if e["group"] == "basic"}
    check("B6 머리표 이용기관 조각(공유 임대 대부료)", "공고기관마다" in local_lease["대부료"] and "5영업일" not in local_lease["대부료"], local_lease["대부료"][:80])
    # 음성 — 머리표가 없는 글은 손대지 않는다.
    plain = next(e["meaning"] for e in entries if e["term"] == "유찰")
    check("B6 머리표 없는 글은 원문 그대로", plain == str(server.ONBID_GUIDE_TERMS["유찰"]["text"]), "")
    # 처분방식 낱말 하나씩 — 「임대」·「대부」·「매각」·「공매」 어느 표기로 읽혀도 같은 조각을 고른다(돌연변이 분모 대조).
    due_for = lambda a, d: next(e["meaning"] for e in server.build_glossary(a, d, "") if e["term"] == "대금납부기한")  # noqa: E731
    check("B6 머리표 국유 「임대」 표기", "5영업일" in due_for("국유재산", "임대") and "60일" not in due_for("국유재산", "임대"), "")
    check("B6 머리표 국유 「대부」 표기", "5영업일" in due_for("국유재산", "대부") and "60일" not in due_for("국유재산", "대부"), "")
    check("B6 머리표 국유 「매각」 표기", "60일" in due_for("국유재산", "매각") and "5영업일" not in due_for("국유재산", "매각"), "")
    check("B6 머리표 국유 「공매」 표기", "60일" in due_for("국유재산", "공매") and "5영업일" not in due_for("국유재산", "공매"), "")
    check("B6 머리표 국유 처분방식 미상이면 매각·대부 둘 다", "60일" in due_for("국유재산", "처분방식 확인") and "5영업일" in due_for("국유재산", "처분방식 확인"), "")
    trust = {e["term"]: e["meaning"] for e in server.build_glossary("수탁재산", "매각", "") if e["group"] == "basic"}
    check("B6 머리표 수탁 조각(소유권이전)", "위임기관" in trust["소유권이전"] and "캠코" not in trust["소유권이전"], trust["소유권이전"][:80])
    etc_sale = {e["term"]: e["meaning"] for e in server.build_glossary("기타일반재산", "매각", "") if e["group"] == "basic"}
    check("B6 머리표 기타일반 조각(보증금 귀속)", "이용기관이 정합니다" in etc_sale["보증금 귀속"] and "국고" not in etc_sale["보증금 귀속"], etc_sale["보증금 귀속"][:80])
    # 머리표 정규식 직접 호출 — 대괄호 머리표만 자르고, 소괄호·꺾쇠는 머리표가 아니다.
    cut = server._guide_text_for("머리. [압류재산] 가. [국유재산] 나.", "압류재산", "매각")
    check("B6 머리표 함수 직접 호출", cut == "머리. 가.", cut)
    not_cut = server._guide_text_for("머리. (압류재산) 가. (국유재산) 나.", "압류재산", "매각")
    check("B6 음성 소괄호는 머리표가 아니다", not_cut == "머리. (압류재산) 가. (국유재산) 나.", not_cut)
    one_head = server._guide_text_for("[압류재산] 가.", "국유재산", "매각")
    check("B6 음성 머리표 하나뿐이고 안 맞으면 원문 그대로", one_head == "[압류재산] 가.", one_head)
    one_head_hit = server._guide_text_for("[압류재산] 가.", "압류재산", "매각")
    check("B6 머리표 하나뿐이어도 맞으면 자른다", one_head_hit == "가.", one_head_hit)
    # 산문 대괄호는 머리표가 아니다(리뷰 r3 R3-3) — 사전 「공매재산명세서」 text 의 「[입찰정보] 탭」이 그 예다.
    prose = server._guide_text_for("[압류재산] 상세페이지 [입찰정보] 탭에서 봅니다. [국유재산] 나.", "압류재산", "매각")
    check("B6 음성 산문 대괄호는 자르지 않는다", prose == "상세페이지 [입찰정보] 탭에서 봅니다.", prose)
    sheet = next(e["meaning"] for e in entries if e["term"] == "공매재산명세서")
    check("B6 음성 공매재산명세서 text 는 압류 분류에서도 원문 그대로", sheet == str(server.ONBID_GUIDE_TERMS["공매재산명세서"]["text"]), sheet[:80])
    # 임대·매각이 한 라벨에 있으면 미상처럼 둘 다 남긴다(리뷰 r3 R3-4).
    mixed = due_for("국유재산", "임대/매각")
    check("B6 머리표 혼합 라벨은 매각·대부 둘 다", "60일" in mixed and "5영업일" in mixed, mixed[:80])
    # 순서 — 재산유형 전용 용어가 공통 용어보다 앞(리뷰 r3 제안).
    sale_terms = [e["term"] for e in entries if e["group"] == "basic"]
    check(
        "B6 순서 유형별 → 매각/임대 → 공통",
        sale_terms.index("매각결정기일") < sale_terms.index("소유권이전") < sale_terms.index("입찰보증금"),
        str(sale_terms),
    )
    no_type = server._guide_text_for("[압류재산] 가. [국유재산] 나.", "", "")
    check("B6 음성 재산유형이 비면 원문 그대로", no_type == "[압류재산] 가. [국유재산] 나.", no_type)

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

    # B6-1 — 온비드 자료실 확장분(ONBID_GLOSSARY_TERMS)이 실제로 병합·필터링·매칭되는지.
    check(
        "B6-1 확장 사전 136건 병합",
        len(server.ONBID_GLOSSARY_TERMS) == 136,
        str(len(server.ONBID_GLOSSARY_TERMS)),
    )
    check(
        "B6-1 확장 사전이 TERM_GLOSSARY에 실제로 들어감",
        all(term in server.TERM_GLOSSARY for term in server.ONBID_GLOSSARY_TERMS),
        "",
    )
    short_terms = [term for term in server.ONBID_GLOSSARY_TERMS if len(term) <= 2]
    check("B6-1 음성 2글자 이하 소음어 제외", short_terms == [], str(short_terms))
    expanded_hit = server.build_glossary("", "", "감정가격 산정 기준 공고")
    check(
        "B6-1 양성 확장 용어가 build_glossary로 실제 매칭",
        any(entry["term"] == "감정가격" for entry in expanded_hit),
        str(expanded_hit),
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


# ---------------------------------------------------------------------------
# C3. API 엔드포인트 스킴 — 참고문서 규격은 6종 전부 https. http 는 인증키가 평문으로 나간다.
# 🔴 라이브 미검증: 이 기기에 ONBID_API_SERVICE_KEY 가 없어 실제 https 호출은 확인하지 못했다.
# ---------------------------------------------------------------------------
def test_public_data_endpoint_scheme() -> None:
    endpoints = server.PUBLIC_DATA_ENDPOINTS
    check("C3 엔드포인트 6종 고정", len(endpoints) == 6, str(len(endpoints)))
    # 🔴 양성 — 6종 전부 https 다.
    check(
        "C3 양성 6종 전부 https",
        all(url.startswith("https://") for url in endpoints.values()),
        str([name for name, url in endpoints.items() if not url.startswith("https://")]),
    )
    # 🔴 음성 대조 — http:// 로 시작하는 것이 하나도 없다. 한 줄만 되돌린 변이도 여기서 붉어진다.
    check(
        "C3 음성 http:// 0건",
        [name for name, url in endpoints.items() if url.startswith("http://")] == [],
        str([name for name, url in endpoints.items() if url.startswith("http://")]),
    )
    # 음성 대조 — 호스트는 바뀌지 않았다. 스킴만 고친 수정이다.
    check(
        "C3 음성 호스트 불변",
        all("://apis.data.go.kr/B010003/" in url for url in endpoints.values()),
        str(list(endpoints.values())),
    )


def test_public_data_endpoint_scheme_wiring() -> None:
    """상수가 https 인 것과 요청이 https 로 나가는 것은 다른 사실이다. 6종 전부 실제 URL 을 본다."""
    plain: list[str] = []
    for name in server.PUBLIC_DATA_ENDPOINTS:
        _result, urls = with_played_urlopen(
            OK_BODY,
            lambda name=name: server.call_public_data(name, {"cltrMngNo": API_CLTR_MNG_NO}, "DUMMY-KEY"),
        )
        check(f"C3 배선 도달 증거 {name} 요청 1건", len(urls) == 1, str(urls))
        if urls and not urls[0].startswith("https://"):
            plain.append(f"{name}={urls[0][:40]}")
    check("C3 배선 6종 요청 URL 전부 https", plain == [], str(plain))
    # 🔴 음성 대조 — 인증키는 여전히 URL 에 실린다. 이 수정은 키를 뺀 것이 아니라 채널을 바꾼 것이다.
    _result, urls = with_played_urlopen(
        OK_BODY,
        lambda: server.call_public_data("real_estate_detail", {"cltrMngNo": API_CLTR_MNG_NO}, "DUMMY-KEY"),
    )
    check("C3 배선 음성 serviceKey 는 그대로 실린다", "serviceKey=DUMMY-KEY" in urls[0], urls[0][:120])


def test_item_detail_uncertain_flag() -> None:
    """물건상세는 pbctCdtnNo 가 없으면 온비드가 500 을 준다(known-pitfalls.md:62-65).

    링크를 지우지 않고 확신을 낮춰 내보낸다. 화면이 그 플래그로 주의 표기를 붙이는지는
    tests/screen.spec.js N6 이 재고, 서버가 플래그를 «세우는지»는 여기서 잰다.
    """
    notice_url = (
        "https://www.onbid.co.kr/op/cltrpbancinf/pbanc/pbancdtlinf/PbancDtlInqController"
        "/mvmnPbancDtl.do?onbidPbancNo=886933&onbidCltrno=1413572"
    )
    # 2026-09-10 판은 인자를 둘만 넘겨 TypeError 로 죽는 코드였다. 실행 목록에 빠져 있어 하루 동안 아무도 몰랐다.
    urls = server.build_related_urls(notice_url, {}, {"onbidPbancNo": "886933", "onbidCltrno": "1413572", "pbctNo": "10032196"})
    check("C4 도달 — itemDetail 이 열렸다", bool(urls.get("itemDetail")), str(sorted(urls)))
    check("C4 pbctCdtnNo 없으면 확신 낮춤", urls.get("itemDetailUncertain") is True, str(urls.get("itemDetailUncertain")))
    check("C4 링크 자체는 남는다", "mvmnCltrDtl.do" in str(urls.get("itemDetail")), str(urls.get("itemDetail"))[:80])
    # 음성 대조 — pbctCdtnNo 가 있으면 플래그를 붙이지 않는다.
    with_cdtn = server.build_related_urls(
        notice_url + "&pbctCdtnNo=5988631",
        {},
        {"onbidPbancNo": "886933", "onbidCltrno": "1413572", "pbctNo": "10032196", "pbctCdtnNo": "5988631"},
    )
    check("C4 도달 음성 — pbctCdtnNo 가 실렸다", "pbctCdtnNo=5988631" in str(with_cdtn.get("itemDetail")), str(with_cdtn.get("itemDetail"))[:100])
    check("C4 음성 — 있으면 플래그 없음", "itemDetailUncertain" not in with_cdtn, str(sorted(with_cdtn)))


# ---------------------------------------------------------------------------
# C5. 재산유형 — 공고상세에서 좌측 메뉴 문구가 새지 않는다
# ---------------------------------------------------------------------------
# 온비드 좌측 메뉴 조각(pbanc_04.html 원문에서 잘라 공백만 줄였다). 「재산유형」 옆의 접근성 문구
# 「중메뉴 펼치기」를 values_after_label 이 값으로 읽는다. 공고상세 23/23 이 이 값을 냈다(2026-09-11).
NAV_ASSET_LABEL = (
    "<div class=\"tit_box01\"><a href='javascript:void(0)'><span class=\"tit01\">재산유형</span>"
    "<span class=\"ico_chevron_down_small\"><span class=\"a11y_blind\">중메뉴 펼치기</span></span></a></div>"
    "<ul class=\"depth3\"><li name=\"OP131\"><span class=\"tit01\">압류재산</span></li></ul>"
)


def asset_badge(name: str) -> str:
    return f"<ul><li class=\"op_cm_badge type01\">{name}</li><li class=\"op_cm_badge type02\">임대</li></ul>"


def test_asset_type_notice_detail() -> None:
    # 도달 증거 — 픽스처가 실제로 결함 분기(메뉴 문구)를 탄다. 못 닿으면 아래 단정은 영구 초록이다.
    check("C5 도달 — 메뉴 조각에서 라벨 값이 「중메뉴 펼치기」", server.values_after_label(NAV_ASSET_LABEL, "재산유형") == "중메뉴 펼치기",
          server.values_after_label(NAV_ASSET_LABEL, "재산유형"))
    # 판정 함수 직접 호출
    check("C5 배지 type01 을 읽는다", server.asset_type_badge(NAV_ASSET_LABEL + asset_badge("국유재산")) == "국유재산")
    check("C5 음성 — 배지가 없으면 빈 값", server.asset_type_badge(NAV_ASSET_LABEL) == "")
    check("C5 음성 — type02(처분방식) 배지를 재산유형으로 읽지 않는다",
          server.asset_type_badge("<li class=\"op_cm_badge type02\">임대</li>") == "")
    check("C5 가드 — 메뉴 문구는 재산유형이 아니다", server.known_asset_type("중메뉴 펼치기") == "")
    check("C5 가드 음성 — 알려진 재산유형은 통과", server.known_asset_type("기타일반재산") == "기타일반재산")

    # 배선 — build_notice 가 실제로 그 순서로 부르는가
    badged = notice_from_html(NAV_ASSET_LABEL + asset_badge("국유재산"))
    check("C5 배선 공고상세 배지를 싣는다", badged.get("assetType") == "국유재산", str(badged.get("assetType")))
    nav_only = notice_from_html(NAV_ASSET_LABEL)
    check("C5 배선 🔴 메뉴 문구가 화면으로 새지 않는다", nav_only.get("assetType") != "중메뉴 펼치기", str(nav_only.get("assetType")))
    check("C5 배선 못 읽으면 「재산유형 확인」", nav_only.get("assetType") == "재산유형 확인", str(nav_only.get("assetType")))
    # 우선순위 — 물건상세 hidden input 이 있으면 그것이 이긴다(시연 경로 회귀 방지).
    hidden = '<input type="hidden" id="scrnCltrPrptDivNm" name="scrnCltrPrptDivNm" value="공유재산">'
    both = notice_from_html(hidden + NAV_ASSET_LABEL + asset_badge("국유재산"))
    check("C5 배선 물건상세 hidden input 이 배지보다 먼저", both.get("assetType") == "공유재산", str(both.get("assetType")))
    # 재산유형이 A/B/C 판정으로 이어진다 — 파산자산 배지면 C형이어야 한다.
    bankrupt = notice_from_html(NAV_ASSET_LABEL + asset_badge("파산자산"))
    code = ((bankrupt.get("docChecklist") or {}).get("profile") or {}).get("code")
    check("C5 배선 재산유형이 C형 판정까지 흐른다", code == "C", str(code))


def test_question_board_state() -> None:
    long = "가" * 500
    raw = {
        "tasks": [{"id": f"t{i}", "title": long, "status": "s", "due": "d", "done": i < 2, "needsCheck": ""} for i in range(15)]
        + ["문자열은 버린다"],
        "docs": {"done": True, "total": 999, "pending": [long] * 20},
        "progress": {"done": 99, "total": 99},
        "evil": "모르는 키",
    }
    board = server.sanitize_board_state(raw)
    check("D1 할 일은 10개까지만 싣는다", len(board["tasks"]) == 10, str(len(board["tasks"])))
    check("D1 제목 길이를 자른다", len(board["tasks"][0]["title"]) == 60)
    check("D1 진행률은 화면 숫자가 아니라 정리한 tasks 에서 다시 센다", board["progress"] == {"done": 2, "total": 10},
          str(board["progress"]))
    check("D1 다음 할 일은 첫 미완료 항목이다", board["nextTaskId"] == "t2", board["nextTaskId"])
    check("D1 bool·범위 밖 숫자는 0 으로 본다", board["docs"]["done"] == 0 and board["docs"]["total"] == 0)
    check("D1 남은 서류는 10개까지", len(board["docs"]["pending"]) == 10)
    check("D1 모르는 키는 버린다", "evil" not in board)
    check("D1 dict 가 아니면 빈 보드", server.sanitize_board_state("x") == {} and server.sanitize_board_state(None) == {})
    check("D1 done 은 True 일 때만 완료", server.sanitize_board_state({"tasks": [{"id": "a", "done": "true"}]})["tasks"][0]["done"] is False)

    prompt = server.question_prompt({"title": "공고"}, [], "이제 뭘 해야 하나요?", board)
    check("D1 프롬프트에 board 가 실린다", prompt.get("board", {}).get("nextTaskId") == "t2")
    check("D1 프롬프트가 board 분류를 지시한다", "board" in prompt["instruction"] and "nextTaskId" in prompt["instruction"])

    norm = server.normalize_question_answer
    good = {"answerable": True, "answerType": "board", "answer": "공고 유형 확인부터 하세요.", "sourceField": "t2"}
    check("D1 보드가 있으면 board 답변을 통과시킨다", norm(good, board)["answerType"] == "board")
    check("D1 보드 없이 온 board 답변은 none 으로 버린다",
          norm(good, {})["answerType"] == "none" and norm(good, None)["answer"] == "")
    check("D1 옛 스키마(answerType 없음) answerable → notice",
          norm({"answerable": True, "answer": "10월 15일입니다."}, {})["answerType"] == "notice")
    check("D1 답이 비면 answerable 이어도 none", norm({"answerable": True, "answerType": "notice", "answer": ""}, board)["answerable"] is False)
    check("D1 none 이면 sourceField 도 비운다",
          norm({"answerable": False, "answerType": "none", "answer": "x", "sourceField": "t1"}, board)["sourceField"] == "")

    # 배선 — 라우트가 board 를 정리해서 모델 호출까지 넘기는가
    captured: list[object] = []
    original = (server.vertex_answer_question, server.gemini_answer_question)
    server.vertex_answer_question = lambda n, d, q, b=None: captured.append(b) or dict(good)
    server.gemini_answer_question = lambda n, d, q, b=None: None
    try:
        result = server.answer_notice_question({}, [], "이제 뭘 해야 하나요?", board)
    finally:
        server.vertex_answer_question, server.gemini_answer_question = original
    check("D1 배선: board 가 모델 호출까지 전달된다", captured and captured[0] is board, str(captured[:1]))
    check("D1 배선: 결과에 answerType 이 실린다", result.get("answerType") == "board" and result["connected"] is True)
    route = Path(server.__file__).read_text(encoding="utf-8")
    route_block = route[route.index('parsed.path == "/api/ask"'):route.index('self.send_json(404')]
    route_code = "\n".join(line.split("#")[0] for line in route_block.splitlines())
    check("D1 배선: /api/ask 가 sanitize_board_state 를 거쳐 board 를 넘긴다",
          'sanitize_board_state(payload.get("board"))' in route_code
          and "answer_notice_question(notice, docs, question, board)" in route_code)


class _FakeResponse:
    def __init__(self, body: str) -> None:
        self._body = body.encode("utf-8")
        self.headers = type("H", (), {"get_content_charset": staticmethod(lambda: "utf-8")})()

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> bool:
        return False


def _with_fake_vertex(codes: list[int], action):
    """urlopen 을 «codes 순서대로 HTTP 오류, 그다음 성공» 으로 바꾸고 sleep 을 기록만 한다."""
    import urllib.error
    calls: list[int] = []
    sleeps: list[float] = []
    body = json.dumps({"candidates": [{"content": {"parts": [{"text": json.dumps(
        {"answerable": True, "answerType": "notice", "answer": "10월 15일입니다.", "sourceField": "bidDeadline"},
        ensure_ascii=False)}]}}]}, ensure_ascii=False)

    def fake_urlopen(request, timeout=0):
        calls.append(1)
        if len(calls) <= len(codes):
            raise urllib.error.HTTPError("u", codes[len(calls) - 1], "err", {}, None)
        return _FakeResponse(body)

    original = (server.urllib.request.urlopen, server.time.sleep)
    server.urllib.request.urlopen = fake_urlopen
    server.time.sleep = sleeps.append
    try:
        try:
            result = action()
        except Exception as exc:  # noqa: BLE001 — 포기했는지만 본다
            result = exc
    finally:
        server.urllib.request.urlopen, server.time.sleep = original
    return result, len(calls), sleeps


FORBIDDEN_SCREEN_PHRASES = (
    "자동 입찰", "입찰 대행", "낙찰 가능성 예측", "투자수익률 판단", "법률 자문", "권리분석 대체",
    "PDF 리포트", "Q&A", "공고 해석 리포트", "Vertex AI", "Gemini AI", "Local MVP", "로컬 분석 API", "완전 자동",
)


def test_onbid_references() -> None:
    find = server.find_onbid_references
    terms = lambda question: [ref["term"] for ref in find(question)]  # noqa: E731
    got = find("감정가격이 뭐야?")
    check("D3 사전 용어를 찾아 설명과 출처를 붙인다",
          len(got) == 1 and got[0]["term"] == "감정가격" and got[0]["source"] == "온비드 자료실 용어사전" and got[0]["text"],
          str(got))
    check("D3 띄어쓰기를 무시한다", terms("감정 가격 은요") == ["감정가격"], str(terms("감정 가격 은요")))
    # 짧은 용어를 앞에 둔다. 찾기는 긴 이름부터 하므로, 순서 정렬을 지우면 이 질문에서 뒤집힌다.
    check("D3 질문 속 순서대로 싣는다", terms("감정가격이랑 개별공시지가 차이") == ["감정가격", "개별공시지가"],
          str(terms("감정가격이랑 개별공시지가 차이")))
    # 음성: TERM_GLOSSARY 에 「임대」가 있지만 2글자 사전 용어는 찾지 않는다.
    check("D3 2글자 사전 용어는 찾지 않는다", "임대" in server.TERM_GLOSSARY and terms("임대료는 언제 내나요?") == [],
          str(terms("임대료는 언제 내나요?")))
    check("D3 용어가 없으면 빈 목록", terms("이제 뭘 해야 하나요?") == [] and find("") == [] and find(None) == [])
    check("D3 긴 이름과 겹치는 짧은 이름은 버린다",
          "개발이익" in server.ONBID_GLOSSARY_TERMS and terms("개발이익환수제가 뭐야") == ["개발이익환수제"],
          str(terms("개발이익환수제가 뭐야")))
    check("D3 한 질문에 3건까지만", len(find("감정가격 개별공시지가 개발부담금 감가상각률")) == 3)

    # 온비드 이용안내·FAQ·준수규칙에서 옮긴 절차 용어(ONBID_GUIDE_TERMS). 2026-10-19 동원님이 「매각결정기일이 뭐지?」에
    # 「담당기관 문의 필요」가 뜬 화면을 보고 지시한 자리다.
    got = find("매각결정기일이 뭐지?")
    check("D3 절차 용어: 매각결정기일을 온비드 FAQ 출처로 찾는다",
          [ref["term"] for ref in got] == ["매각결정기일"] and "매각결정기일" in got[0]["source"]
          and "개찰일로부터 7일 이내" in got[0]["text"], str(got))
    check("D3 절차 용어도 띄어쓰기를 무시한다", terms("매각 결정 기일은 언제야") == ["매각결정기일"])
    check("D3 절차 용어는 2글자도 찾는다", terms("유찰되면 어떻게 돼?") == ["유찰"], str(terms("유찰되면 어떻게 돼?")))
    check("D3 별칭으로 찾는다(질문창 예시 문장)", terms("잔금은 언제까지 내야 하나요?") == ["대금납부기한"],
          str(terms("잔금은 언제까지 내야 하나요?")))
    # 음성: 사전의 「공유자우선매수」는 법원 경매 기준이라 온비드 공매 절차 설명과 같이 내지 않는다.
    check("D3 절차 용어 별칭과 같은 사전 용어는 싣지 않는다",
          "공유자우선매수" in server.ONBID_GLOSSARY_TERMS and terms("공유자우선매수가 뭐야") == ["우선매수 신청"],
          str(terms("공유자우선매수가 뭐야")))
    check("D3 긴 절차 용어 안의 짧은 절차 용어는 버린다", terms("적정최고가입찰이 뭐야") == ["적정최고가입찰"],
          str(terms("적정최고가입찰이 뭐야")))
    check("D3 공고 질문에는 용어 설명을 붙이지 않는다", terms("이 공고 입찰 마감이 언제야?") == [],
          str(terms("이 공고 입찰 마감이 언제야?")))
    # 2글자 이름은 낱말 첫머리에서만 찾는다(리뷰 r1 P1-1). 음성은 낱말 가운데·띄어쓰기를 건넌 자리다.
    # 「두 명 도장」·「몇 분 납부」는 낱말 첫머리에서 시작하지만 띄어쓰기를 건넌다(리뷰 r2 P2-a).
    for question in ("보증금 설명도 부탁해요", "공동 점유자가 있으면 어떻게 하나요?", "지명도 높은 기관인가요",
                     "몇 분 납부하면 돼요?"):
        check(f"D3 2글자 이름은 낱말 가운데서 찾지 않는다: {question}", terms(question) == [], str(terms(question)))
    for question, expected in (("명도는 누가 해요?", ["명도책임"]), ("동점이면 어떻게 돼요?", ["무작위 추첨"]),
                               ("(유찰) 뜻이 뭐예요", ["유찰"]),
                               # 앞 문장부호가 둘이다. 문장부호를 한 글자만 건너뛰면 여기서 깨진다.
                               ('"(유찰)" 표시는 뭐예요', ["유찰"]),
                               # 둘째 낱말 이후다. 낱말 자리 계산(offset)이 틀리면 여기서 깨진다(리뷰 r2 P2-b).
                               ("이 물건 유찰되면?", ["유찰"]),
                               # 같은 이름이 낱말 가운데(재유찰)와 첫머리(유찰되면)에 다 있다. 낱말 가운데 자리를
                               # 만났을 때 찾기를 멈추면(continue → break) 여기서 깨진다.
                               ("재유찰 말고 그냥 유찰되면?", ["유찰"]),
                               ("공동입찰자 두 명 도장이 필요한가요?", ["공동입찰"])):
        check(f"D3 2글자 이름은 낱말 첫머리에서 찾는다: {question}", terms(question) == expected, str(terms(question)))
    # 경계: 3글자 이상은 낱말 가운데서도 찾는다(붙여 쓴 「남은잔대금」). 「<= 2」를 「<= 3」으로 바꾸면 여기서 깨진다.
    check("D3 3글자 이상 이름은 낱말 가운데서도 찾는다", terms("남은잔대금은 언제 내요?") == ["대금납부기한"],
          str(terms("남은잔대금은 언제 내요?")))
    # 같은 용어가 두 번 나오면 첫 자리를 쓴다. 자리를 고르는 break 를 지우면 마지막 자리가 쓰여 순서가 뒤집힌다.
    check("D3 같은 용어가 두 번 나오면 첫 자리로 순서를 정한다",
          terms("유찰 뒤에 감정가격은 그대로인데 또 유찰되면?") == ["유찰", "감정가격"],
          str(terms("유찰 뒤에 감정가격은 그대로인데 또 유찰되면?")))
    check("D3 같은 용어는 별칭이 여러 번 맞아도 한 번만 싣는다", terms("잔금이랑 중도금은 언제 내요?") == ["대금납부기한"],
          str(terms("잔금이랑 중도금은 언제 내요?")))
    check("D3 겹친 자리 뒤에 또 나오면 그 자리를 쓴다",
          terms("매각결정기일 전에 매각결정이 취소되면?") == ["매각결정기일", "매각결정"],
          str(terms("매각결정기일 전에 매각결정이 취소되면?")))
    check("D3 references 에 scope 가 실린다(사전 용어는 빈 값)",
          find("매각결정기일이 뭐지?")[0].get("scope") == "압류재산" and find("감정가격이 뭐야?")[0].get("scope") == "",
          str([find("매각결정기일이 뭐지?")[0].get("scope"), find("감정가격이 뭐야?")[0].get("scope")]))
    # 화면이 escape 없이 넣는다(renderOnbidReferences). 상수에 「<」·「&」가 들어오면 그대로 HTML 이 된다.
    markup = [term for term, item in {**server.ONBID_GUIDE_TERMS, **{k: {"text": v} for k, v in server.TERM_GLOSSARY.items()}}.items()
              if any(ch in f"{term}{item.get('text', '')}{item.get('source', '')}" for ch in "<&")]
    check("D3 용어 설명 상수에 「<」·「&」가 없다", not markup, str(markup))
    scopes = {item.get("scope") for item in server.ONBID_GUIDE_TERMS.values()}
    check("D3 절차 용어의 scope 는 합의한 여섯 값 안에 있다",
          scopes <= {"common", "sale", "lease", "압류재산", "국유재산", "수탁재산"} and None not in scopes, str(scopes))

    prompt = server.question_prompt({"title": "공고"}, [], "감정가격이 뭐야?", {})
    check("D3 프롬프트에 onbidReference 가 실린다",
          [ref["term"] for ref in prompt.get("onbidReference", [])] == ["감정가격"], str(prompt.get("onbidReference")))
    check("D3 schema 가 general 을 허용한다", "general" in prompt["schema"]["answerType"], prompt["schema"]["answerType"])
    check("D3 지시가 onbidReference 를 근거로 답하라고 한다",
          "onbidReference" in prompt["instruction"] and "none 으로 답하지 않고" in prompt["instruction"])

    # 배선 — 모델이 none 으로 답하거나 연결되지 않아도 references 가 결과에 실린다.
    original = (server.vertex_answer_question, server.gemini_answer_question)
    none_answer = {"answerable": False, "answerType": "none", "answer": "", "sourceField": ""}
    try:
        server.vertex_answer_question = lambda n, d, q, b=None: dict(none_answer)
        server.gemini_answer_question = lambda n, d, q, b=None: None
        declined = server.answer_notice_question({}, [], "감정가격이 뭐야?", {})
        server.vertex_answer_question = lambda n, d, q, b=None: None
        offline = server.answer_notice_question({}, [], "감정가격이 뭐야?", {})
        plain = server.answer_notice_question({}, [], "이제 뭘 해야 하나요?", {})
    finally:
        server.vertex_answer_question, server.gemini_answer_question = original
    check("D3 배선: 모델이 none 이어도 references 가 실린다",
          declined["connected"] is True and declined["answerable"] is False
          and [ref["term"] for ref in declined.get("references", [])] == ["감정가격"], str(declined))
    check("D3 배선: 모델 미연결이어도 references 가 실린다",
          offline["connected"] is False and [ref["term"] for ref in offline.get("references", [])] == ["감정가격"],
          str(offline))
    check("D3 배선: 용어가 없으면 references 는 빈 목록", plain.get("references") == [], str(plain.get("references")))

    bad = [(term, phrase) for term, item in server.ONBID_GUIDE_TERMS.items()
           for phrase in FORBIDDEN_SCREEN_PHRASES if phrase in f"{item.get('text', '')} {item.get('source', '')}"]
    check("D3 절차 용어 설명·출처에 금지표현이 없다", not bad, str(bad))
    empty = [term for term, item in server.ONBID_GUIDE_TERMS.items() if not item.get("text") or not item.get("source")]
    check("D3 절차 용어마다 설명과 출처가 있다", not empty, str(empty))


def test_vertex_429_retry() -> None:
    import urllib.error
    req = lambda: server.vertex_read(server.urllib.request.Request("https://example.invalid", data=b"{}"), 5)  # noqa: E731
    result, n, sleeps = _with_fake_vertex([429], req)
    check("D2 429 한 번 뒤 성공하면 본문을 돌려준다", isinstance(result, str) and n == 2 and sleeps == [1.0], f"{n} {sleeps}")
    result, n, sleeps = _with_fake_vertex([429, 429, 429], req)
    check("D2 429 가 계속되면 3번째에서 포기한다", isinstance(result, urllib.error.HTTPError) and n == 3, f"{n} {result!r}")
    result, n, sleeps = _with_fake_vertex([500], req)
    check("D2 429 가 아니면 다시 보내지 않는다", isinstance(result, urllib.error.HTTPError) and n == 1 and sleeps == [], f"{n}")

    # 배선 — 질문 경로가 실제로 재시도 도우미를 거치는가
    original = (server.vertex_config, server.vertex_access_token)
    server.vertex_config = lambda: {"project": "p", "location": "global", "model": "m"}
    server.vertex_access_token = lambda: "t"
    try:
        result, n, _ = _with_fake_vertex([429], lambda: server.vertex_answer_question({}, [], "마감?", {}))
    finally:
        server.vertex_config, server.vertex_access_token = original
    check("D2 배선: 질문 호출이 429 뒤 재시도해서 답을 받는다",
          isinstance(result, dict) and result.get("answer") == "10월 15일입니다." and n == 2, f"{n} {result!r}")
    code = Path(server.__file__).read_text(encoding="utf-8")
    coach = code[code.index("def vertex_ai_coach("):code.index("def ", code.index("def vertex_ai_coach(") + 10)]
    coach_code = "\n".join(line.split("#")[0] for line in coach.splitlines())
    check("D2 배선: 코치 호출도 vertex_read 를 거친다",
          "vertex_read(request" in coach_code and "urlopen(" not in coach_code)


# ---------------------------------------------------------------------------
# E축 — 공공데이터 getCltrBidInf2 제출서류 필드 연동 (2026-10-18)
#
# 픽스처는 2026-10-18 에 실제 API 에서 받은 응답이다
# (tests/fixtures/cltr_bid_inf_samples.json · 재산유형 6종 · 각 65개 필드).
# 목 데이터를 만들지 않고 실제 응답을 고정 샘플로 저장해 쓴다 — 이 API 의 값은 명세를 읽어
# 추측하면 틀린다는 것이 이번 조사의 결론이었다(서류 「내용」 필드가 전부 비어 있었다).
# 테스트는 외부 네트워크에 의존하지 않고, 실제 호출 검증은 수동 1회로 따로 했다.
# ---------------------------------------------------------------------------

CLTR_BID_SAMPLES_PATH = Path(__file__).resolve().parent / "fixtures" / "cltr_bid_inf_samples.json"


def load_cltr_bid_samples() -> dict[str, dict[str, object]]:
    return json.loads(CLTR_BID_SAMPLES_PATH.read_text(encoding="utf-8"))


def test_api_doc_terms_flag_filter() -> None:
    samples = load_cltr_bid_samples()
    # 모수 하한 — 입력이 비면 아래 단정들이 「대상 0건」으로 조용히 통과한다.
    check("E1 고정 샘플 모수", len(samples) >= 6, f"{len(samples)}건")

    joint_n_with_value = samples["공유재산_매각_분양_202604-11680-00"]
    # 이 샘플이 이 축의 근거다 — 플래그가 N 인데 기한·방식 값이 남아 있다. 이 전제가 깨지면
    # 아래 양성 단정이 아무것도 증명하지 못하므로 전제부터 센다.
    check(
        "E1 전제 — 플래그 N 인데 기한 값이 남은 샘플이 실재한다",
        joint_n_with_value.get("collbBidPsblYn") == "N"
        and bool(joint_n_with_value.get("collbDcmtSbmsnTermNm")),
        repr(joint_n_with_value.get("collbDcmtSbmsnTermNm")),
    )
    terms = server.build_bid_doc_terms(joint_n_with_value)
    check(
        "E1 플래그 N 이면 그 입찰 방식의 기한·방식을 내보내지 않는다",
        not [term for term in terms if term["kind"] == "공동입찰"],
        repr(terms),
    )

    # 음성 대조 — 플래그가 Y 인 샘플에서는 반드시 내보낸다. 이것이 없으면 「전부 버리는」
    # 구현도 위 단정을 통과한다.
    proxy_y = samples["파산자산_매각_2026-1000-056230"]
    check("E1 음성 대조 전제 — subtBidPsblYn 이 Y", proxy_y.get("subtBidPsblYn") == "Y")
    proxy_terms = server.build_bid_doc_terms(proxy_y)
    proxy_row = next((term for term in proxy_terms if term["kind"] == "대리입찰"), None)
    check("E1 플래그 Y 이면 기한·방식을 내보낸다", proxy_row is not None, repr(proxy_terms))
    if proxy_row:
        check(
            "E1 내보낸 값이 응답 원문과 같다",
            proxy_row["due"] == "입찰마감일시 전까지" and proxy_row["method"] == "온라인/직접제출",
            repr(proxy_row),
        )


def test_api_unusable_term_value() -> None:
    samples = load_cltr_bid_samples()
    # bidPtctAplyTermNm 은 6건 전부 "~" 였다. 날짜도 문구도 없는 값이라 화면에 그대로
    # 내보내면 「기한 ~」이 된다.
    tilde_count = sum(1 for entry in samples.values() if entry.get("bidPtctAplyTermNm") == "~")
    check("E2 전제 — 쓸 수 없는 기한 값이 실제로 온다", tilde_count >= 1, f"{tilde_count}건")

    info = server.build_bid_participation_apply(samples["불용품_매각_2026-0600-033346"])
    check("E2 쓸 수 없는 기한 값은 빈 값으로 눌린다", info.get("due") == "", repr(info.get("due")))
    check("E2 Y·N 이 아니면 빈 dict — 화면이 블록을 그리지 않는다",
          server.build_bid_participation_apply({"bidPtctAplyYn": ""}) == {})
    check("E2 N 이면 required 가 False",
          server.build_bid_participation_apply({"bidPtctAplyYn": "N"}).get("required") is False)
    check("E2 Y 이면 required 가 True",
          server.build_bid_participation_apply({"bidPtctAplyYn": "Y"}).get("required") is True)

    # 판정 함수를 배선과 별개로 직접 부른다 — 본문을 비워도 위 단정이 통과하면 그 함수는
    # 아무것도 증명하지 못한다.
    check("E2 판정 직접 호출 — 「~」", server.api_meaningful_term("~") == "")
    check("E2 판정 직접 호출 — 「||」", server.api_meaningful_term("||") == "")
    # 음성 대조 — 쓸 수 있는 값은 그대로 통과해야 한다.
    check(
        "E2 음성 대조 — 쓸 수 있는 기한은 그대로 둔다",
        server.api_meaningful_term("입찰마감일시 전까지") == "입찰마감일시 전까지",
    )
    check("E2 음성 대조 — 「~」가 섞인 실제 기간은 버리지 않는다",
          server.api_meaningful_term("2026-10-01 ~ 2026-10-15") == "2026-10-01 ~ 2026-10-15")


def test_api_bid_limits() -> None:
    samples = load_cltr_bid_samples()
    limits = server.build_bid_limits(samples["공유재산_임대_2026-0800-045505"])
    by_key = {str(limit["key"]): limit for limit in limits}
    check("E3 지역 제한 값이 있으면 제한으로 판정한다",
          by_key.get("region", {}).get("restricted") is True, repr(limits))
    check("E3 「없음(모든 회원 입찰가능)」은 제한으로 판정하지 않는다",
          by_key.get("qualification", {}).get("restricted") is False, repr(limits))
    # 창 — 부분일치로 비교하면 「없음 다만 …」 같은 실제 제한 문구를 제한 없음으로 읽는다.
    etc = server.build_bid_limits({"etcLmtCdtnCont": "없음 다만 농지취득자격증명이 필요합니다"})
    check("E3 「없음」이 섞인 실제 제한 문구는 제한으로 판정한다",
          bool(etc) and etc[0]["restricted"] is True, repr(etc))
    check("E3 빈 응답이면 빈 목록", server.build_bid_limits({}) == [])


def test_api_pbct_cdtn_no_wiring() -> None:
    # 배선 검사 — build_notice() 가 cltrInfVO 의 pbctCdtnNo 를 보충해 공공데이터 호출에
    # 넘기는지 본다. 이 한 줄이 없으면 getCltrBidInf2 가 호출 목록에 들어가지 못한다.
    # 주석을 먼저 벗긴다 — 주석에 같은 문구가 있어 벗기지 않으면 주석만 보고 통과한다.
    source = (Path(__file__).resolve().parent.parent / "src" / "server.py").read_text(encoding="utf-8")
    stripped = "\n".join(
        line for line in source.splitlines() if not line.lstrip().startswith("#")
    )
    check(
        "E4 cltrInfVO 의 pbctCdtnNo 를 보충한다",
        'api_pbct_cdtn_no = pbct_cdtn_no or clean_text(str(cltr_detail.get("pbctCdtnNo")' in stripped,
    )
    # 창 — fetch_public_data_bundle 호출 블록 안에서 그 보충값을 쓰는지 본다. 보충만 하고
    # 넘기지 않으면 동작은 그대로다.
    bundle_call = stripped.split("public_data = fetch_public_data_bundle(", 1)
    check("E4 호출 블록이 하나 있다", len(bundle_call) == 2)
    if len(bundle_call) == 2:
        block = bundle_call[1].split(")", 1)[0]
        check("E4 보충값을 pbctCdtnNo 로 넘긴다", '"pbctCdtnNo": api_pbct_cdtn_no' in block, block[:200])
    # 서비스별 응답 분리 — items 를 합쳐 쓰면 같은 이름의 필드가 여러 API 에 있어 엉뚱한
    # 쪽 값을 집는다(tdpsSbtnDcmtYn 은 getCltrBidInf2 와 getPbancBidInf2 양쪽에 있다).
    check("E4 서비스별 응답을 따로 보관한다", '"itemsByService"' in stripped)
    check(
        "E4 item_bid_detail 응답만 골라 쓴다",
        'items_by_service.get("item_bid_detail", [])' in stripped,
    )
    # 화면이 쓰는 세 값이 응답에 실제로 실리는지 — 함수만 있고 배선이 없으면 화면은 빈다.
    for field, builder in (
        ('"bidParticipationApply"', "build_bid_participation_apply(item_bid_entry)"),
        ('"apiDocTerms"', "build_bid_doc_terms(item_bid_entry)"),
        ('"bidLimits"', "build_bid_limits(item_bid_entry)"),
    ):
        check(f"E4 응답에 {field} 를 싣는다", f"{field}: {builder}" in stripped)


def main() -> int:
    print_header()
    tests = (
        test_sections,
        test_doc_names,
        test_condition_carry,
        test_negative_condition,
        test_extras,
        test_profile,
        test_attachments,
        test_attachment_wiring,
        test_heading_layers,
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
        test_public_data_endpoint_scheme,
        test_public_data_endpoint_scheme_wiring,
        test_item_detail_uncertain_flag,
        test_asset_type_notice_detail,
        test_question_board_state,
        test_onbid_references,
        test_vertex_429_retry,
        test_api_doc_terms_flag_filter,
        test_api_unusable_term_value,
        test_api_bid_limits,
        test_api_pbct_cdtn_no_wiring,
    )
    for test in tests:
        test()
    # 🔴 정의만 하고 실행 목록에 안 넣은 test_ 함수를 잡는다. 2026-09-11 에 C4(test_item_detail_uncertain_flag)가
    # 정의만 된 채 하루 동안 한 번도 돌지 않았고, 그 사이 «213/213» 이 그 단정까지 증명한 것처럼 보고됐다.
    defined = sorted(n for n, v in globals().items() if n.startswith("test_") and callable(v))
    registered = {t.__name__ for t in tests}
    check("Z1 test_ 함수가 전부 실행 목록에 있다", not [n for n in defined if n not in registered],
          str([n for n in defined if n not in registered]))
    total = PASSED + len(FAILURES)
    for failure in FAILURES:
        print(f"FAIL {failure}")
    # 축 커버리지를 «실행된 단정 이름»에서 센다. 표의 「커버 Y」는 손으로 적은 선언이라 되읽으면
    # 항진명제다(화면 게이트 2026-09-09 리뷰 P0-1 과 같은 결함 · 이 파일에도 있었다).
    ran = {code for code, *_ in AXES if any(re.match(rf"{re.escape(code)}(\s|$)", n) for n in CHECK_NAMES)}
    uncovered = [f"{code} {name}" for code, name, *_ in AXES if code not in ran]
    declared_but_not_run = [code for code, *_rest, covered in AXES if covered == "Y" and code not in ran]
    print(
        f"{PASSED}/{total} 통과 · 연기 {len(PLAYED)}개 · 축 {len(AXES)}개 중 단정이 한 번도 안 돈 축 {len(uncovered)}개"
    )
    print(f"안 돈 축: {', '.join(uncovered) if uncovered else '없음'}. "
          "화면 축은 tests/screen.spec.js, 표본 축은 tests/measure_sample_23.py 가 맡는다.")
    if declared_but_not_run:
        print(f"🔴 표가 「커버 Y」라고 적었는데 단정이 한 번도 안 돈 축: {', '.join(declared_but_not_run)}")
        return 1
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
