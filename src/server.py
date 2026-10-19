from __future__ import annotations

import html
import http.cookiejar
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


HOST = "127.0.0.1"
PORT = 8975
ROOT = Path(__file__).resolve().parent


def code_revision(root: Path | None = None) -> dict[str, object]:
    """화면 머리에 띄울 코드 판을 git 에서 읽는다. git 이 없거나 저장소가 아니면 commit 이 빈 값이다.

    번호(number)는 HEAD 까지의 누적 커밋 수다. 같은 브랜치에서는 커밋할수록 커지므로
    「r352 가 떠 있다」처럼 판을 사람 눈으로 견줄 수 있다(2026-10-19 동원님 요청).
    dirty 는 src/ 에 커밋하지 않은 변경이 있는지다. 화면 코드는 src/ 만 쓴다.
    """
    base = root or ROOT.parent

    def git(*args: str) -> str:
        try:
            result = subprocess.run(["git", "-C", str(base), *args], capture_output=True, text=True, timeout=3)
        except (OSError, subprocess.SubprocessError):
            return ""
        return result.stdout.strip() if result.returncode == 0 else ""

    return {
        "commit": git("rev-parse", "--short", "HEAD"),
        "number": git("rev-list", "--count", "HEAD"),
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "committedAt": git("log", "-1", "--format=%cd", "--date=format:%Y-%m-%d %H:%M"),
        "dirty": bool(git("status", "--porcelain", "--", "src")),
    }


# server.py 는 기동할 때의 판으로 메모리에 올라 있다. 그 뒤 파일이 바뀌어도 재시작 전까지는
# 옛 판으로 돈다(known-pitfalls: 포트 18982 재시작). 그래서 기동 시점 판을 따로 들고 있다.
SERVER_STARTED_AT = time.strftime("%Y-%m-%d %H:%M:%S")
SERVER_REVISION = code_revision()
_VERTEX_TOKEN = ""
_VERTEX_TOKEN_EXPIRES_AT = 0.0
# 스킴은 `https` 다. 참고문서 6종의 「서비스URL · 운영환경」이 전부 `https://apis.data.go.kr/B010003/…`
# 이고, `http` 로 부르면 serviceKey 가 평문으로 나간다(2026-09-08 교체).
PUBLIC_DATA_ENDPOINTS = {
    "notice_list": "https://apis.data.go.kr/B010003/OnbidPbancListSrvc2/getPbancList2",
    "real_estate_list": "https://apis.data.go.kr/B010003/OnbidRlstListSrvc2/getRlstCltrList2",
    "real_estate_detail": "https://apis.data.go.kr/B010003/OnbidRlstDtlSrvc2/getRlstDtlInf2",
    "item_bid_detail": "https://apis.data.go.kr/B010003/OnbidCltrBidDtlSrvc2/getCltrBidInf2",
    "notice_detail": "https://apis.data.go.kr/B010003/OnbidPbancDtlnfSrvc2/getPbancDtlInf2",
    "notice_bid_detail": "https://apis.data.go.kr/B010003/OnbidPbancBidDtlSrvc2/getPbancBidInf2",
}
# 온비드 물건/공고 상세 컨트롤러는 이 파라미터 없이 열면 온비드 자체가 500을 반환한다.
DETAIL_CONTROLLER_REQUIRED_PARAM = {
    "CltrDtlController/mvmnCltrDtl.do": "onbidCltrno",
    "PbancDtlInqController/mvmnPbancDtl.do": "onbidPbancNo",
}


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    value = html.unescape(value)
    value = re.sub(r"<script\b.*?</script>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<style\b.*?</style>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


# 온비드 담당부점 필드가 "국유재산지원처 / 물건정보참조 / 물건정보참조 / 물건정보참조"처럼
# 실제 값과 의미 없는 placeholder(미입력 항목 안내 문구)를 " / "로 섞어 내려줄 때가 있다
# (2026-10-09 실측). 사용자에게는 placeholder만 반복돼 "참조하라는데 참조할 내용이 없다"로
# 읽힌다. "/ "로 나눈 뒤 이 문구와 완전히 같은 조각만 제거한다 — 값의 일부로 같은 글자가
# 섞인 경우까지 지우지 않도록 부분일치가 아닌 완전일치로 비교한다.
PLACEHOLDER_SEGMENTS = {"물건정보참조"}


def strip_placeholder_segments(value: str) -> str:
    if not value or " / " not in value:
        return value
    segments = [part.strip() for part in value.split(" / ")]
    kept = [part for part in segments if part and part not in PLACEHOLDER_SEGMENTS]
    return " / ".join(kept)


def attrs_from_tag(tag: str) -> dict[str, str]:
    attrs: dict[str, str] = {}
    for match in re.finditer(r"""([:\w-]+)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))""", tag):
        attrs[match.group(1)] = html.unescape(match.group(2) or match.group(3) or match.group(4) or "")
    return attrs


def hidden_inputs(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for match in re.finditer(r"<input\b[^>]*>", text, flags=re.I):
        attrs = attrs_from_tag(match.group(0))
        key = attrs.get("id") or attrs.get("name")
        value = attrs.get("value")
        if key and value and key not in values:
            values[key] = clean_text(value)
    return values


def class_text(text: str, class_name: str) -> str:
    pattern = rf"<[^>]*class=(?:\"[^\"]*\b{re.escape(class_name)}\b[^\"]*\"|'[^']*\b{re.escape(class_name)}\b[^']*')[^>]*>(.*?)</[^>]+>"
    match = re.search(pattern, text, flags=re.I | re.S)
    return clean_text(match.group(1)) if match else ""


def values_after_label(text: str, label: str) -> str:
    label_pattern = re.escape(label)
    pattern = rf"<span[^>]*class=(?:\"[^\"]*\btit01\b[^\"]*\"|'[^']*\btit01\b[^']*')[^>]*>\s*{label_pattern}\s*</span>(.*?)(?=<li\b|</ul>|</section>|</div>\s*</div>\s*</div>)"
    match = re.search(pattern, text, flags=re.I | re.S)
    if not match:
        return ""
    chunk = match.group(1)
    values = re.findall(r"<span[^>]*class=(?:\"[^\"]*\b(?:txt01|price01|price02|op_cm_badge)\b[^\"]*\"|'[^']*\b(?:txt01|price01|price02|op_cm_badge)\b[^']*')[^>]*>(.*?)</span>", chunk, flags=re.I | re.S)
    return clean_text(" ".join(values) if values else chunk)


def block_text(value: str | None) -> str:
    """블록 경계를 줄바꿈으로 남기고 태그를 제거한다.

    clean_text()는 모든 공백을 한 칸으로 접어서 표의 셀 경계와 항목 경계가 사라진다.
    제출서류 절은 항목 단위로 읽어야 하므로 별도 함수를 둔다.
    """
    if not value:
        return ""
    value = html.unescape(value)
    value = re.sub(r"<script\b.*?</script>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<style\b.*?</style>", " ", value, flags=re.I | re.S)
    value = re.sub(r"(?i)<br\s*/?>", "\n", value)
    value = re.sub(r"(?i)</(?:td|tr|li|p|div|h\d|dt|dd|span)>", "\n", value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"[ \t\r ]+", " ", value)
    value = re.sub(r"\n[ \t]*", "\n", value)
    value = re.sub(r"\n{2,}", "\n", value)
    return value.strip()


# 온비드 상세페이지는 <h2 class="tit">로 절을 나눈다. 표본 23/23에서 파싱됐다
# (docs/90_MVP개발/07_제출서류_표본조사_20260907.md §4). 물건상세는 같은 절이 PC/모바일
# 마크업으로 두 번 나오므로 같은 제목의 조각을 모두 모은다.
SECTION_HEADING_RE = re.compile(r"<h2[^>]*class=(?:\"[^\"]*\btit\b[^\"]*\"|'[^']*\btit\b[^']*')[^>]*>(.*?)</h2>", re.I | re.S)


def split_sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    matches = list(SECTION_HEADING_RE.finditer(text))
    for index, match in enumerate(matches):
        title = clean_text(match.group(1))
        if not title:
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections.setdefault(title, []).append(text[match.end() : end])
    return {title: "\n".join(chunks) for title, chunks in sections.items()}


def section_html(sections: dict[str, str], *titles: str) -> str:
    return "\n".join(sections.get(title, "") for title in titles if sections.get(title))


# 온비드 「입찰방법」·「입찰 제한 정보」 절의 도움말(툴팁)은 공고 내용이 아니라 온비드 UI 문구다.
# 표본 23/23에서 위임장·대리입찰신청서·공동입찰참가신청서를 포함하므로 서류명 탐색에서 뺀다.
DOC_SEARCH_SECTIONS = ("공고문", "제출서류")
TOOLTIP_BLOCK_RE = re.compile(r"<div[^>]*class=(?:\"[^\"]*\btooltip_wrap01\b[^\"]*\"|'[^']*\btooltip_wrap01\b[^']*')[^>]*>.*?</div>\s*</div>\s*</div>", re.I | re.S)


def strip_tooltips(chunk: str) -> str:
    return TOOLTIP_BLOCK_RE.sub(" ", chunk)


def label_value(chunk: str, label: str) -> str:
    """온비드 항목 박스의 `<span class="txt_01">라벨</span> … <span class="txt01">값</span>`을 읽는다."""
    for match in re.finditer(
        rf"<span[^>]*class=(?:\"[^\"]*\btxt_01\b[^\"]*\"|'[^']*\btxt_01\b[^']*')[^>]*>\s*{re.escape(label)}\s*</span>",
        chunk,
        flags=re.I,
    ):
        window = chunk[match.end() : match.end() + 1500]
        # 다음 라벨이 먼저 나오면 값이 비어 있는 항목이다.
        next_label = re.search(r"<span[^>]*class=(?:\"[^\"]*\btxt_01\b[^\"]*\"|'[^']*\btxt_01\b[^']*')[^>]*>", window, flags=re.I)
        value_match = re.search(r"<span[^>]*class=(?:\"[^\"]*\btxt01\b[^\"]*\"|'[^']*\btxt01\b[^']*')[^>]*>(.*?)</span>", window, flags=re.I | re.S)
        if not value_match:
            continue
        if next_label and next_label.start() < value_match.start():
            continue
        value = clean_text(value_match.group(1))
        if value:
            return value
    return ""


# 온비드 「입찰방법」 절의 가능/불가능 값은 `label_value()` 로 읽히지 않는다 — 값 span 이
# `txt01` 이 아니라 라벨과 같은 `txt_01` 이라 `next_label` 가드에 먼저 걸린다(표본 23/23 빈 문자열).
# 값은 항목 박스 오른쪽 `ico_box01` 안의 첫 `txt_01` 이다.
# 🔴 라벨과 값 사이에는 온비드 UI 툴팁이 끼어 있고, 그 본문에는 「공동입찰참가신청서」가
# 표본 23/23 전건 들어 있다. 절 전체를 훑어 문자열 존재만 보는 구현은 전건 오탐이다.
# (docs/90_MVP개발/09_공동입찰_명도책임_크롤링가용성_조사_20260908.md §2-1·§6-3)
BID_METHOD_SECTION = "입찰방법"
ICO_BOX_VALUE_RE = re.compile(
    r"<div[^>]*class=(?:\"[^\"]*\bico_box01\b[^\"]*\"|'[^']*\bico_box01\b[^']*')[^>]*>.*?"
    r"<span[^>]*class=(?:\"[^\"]*\btxt_01\b[^\"]*\"|'[^']*\btxt_01\b[^']*')[^>]*>(.*?)</span>",
    re.I | re.S,
)
# 다음 항목 박스의 라벨 영역. 값이 없는 항목이 옆 항목의 값을 집어오지 않도록 창을 여기서 끊는다.
TIT_AREA_RE = re.compile(r"<div[^>]*class=(?:\"[^\"]*\btit_area01\b[^\"]*\"|'[^']*\btit_area01\b[^']*')[^>]*>", re.I)


def bid_method_flag(sections: dict[str, str], label: str) -> str:
    """「입찰방법」 절에서 `공동입찰`·`대리입찰` 의 가능/불가능 값을 읽는다.

    못 읽으면 빈 문자열이다. 빈 값을 「불가능」으로 접지 않는다 — 표본에 없던 어휘가
    나오면 화면은 「원문 확인」을 띄워야 한다.
    """
    chunk = sections.get(BID_METHOD_SECTION, "")
    if not chunk:
        return ""
    for match in re.finditer(
        rf"<span[^>]*class=(?:\"[^\"]*\btxt_01\b[^\"]*\"|'[^']*\btxt_01\b[^']*')[^>]*>\s*{re.escape(label)}\s*</span>",
        chunk,
        flags=re.I,
    ):
        window = chunk[match.end() :]
        next_item = TIT_AREA_RE.search(window)
        if next_item:
            window = window[: next_item.start()]
        value_match = ICO_BOX_VALUE_RE.search(window)
        if not value_match:
            continue
        value = clean_text(value_match.group(1))
        if value:
            return value
    return ""


# 명도책임은 구조화 필드가 아니라 압류재산 공고문 본문의 한 문장이다(표본 3/23 · 어휘 `매수인` 하나).
# 조건 축에 물리지 않는다 — 분기를 만들 근거가 없다(같은 문서 §3·§6-2 5번).
EVICTION_RESPONSIBILITY_RE = re.compile(r"명도책임(?:은|이)?\s*([^\s,\.]{2,8}?)\s*부담")


def eviction_responsibility(sections: dict[str, str]) -> str:
    """공고문 본문에서 「명도책임은 ○○ 부담」의 ○○ 를 읽는다. 없으면 빈 문자열."""
    match = EVICTION_RESPONSIBILITY_RE.search(clean_text(sections.get("공고문", "")))
    return match.group(1) if match else ""


# 표본 23건에서 재산유형과 A/B/C 판정이 예외 0건으로 일치했다
# (docs/90_MVP개발/07_제출서류_표본조사_20260907.md §2).
# 표본은 층화추출이 아니므로 전체 공고의 분포 추정치가 아니다.
DOC_SOURCE_BY_ASSET_TYPE = (
    ("압류재산", "A"),
    ("국유재산", "A"),
    ("공유재산", "B"),
    ("기타일반재산", "B"),
    ("수탁재산", "B"),
    ("파산자산", "C"),
)
KNOWN_ASSET_TYPES = tuple(name for name, _ in DOC_SOURCE_BY_ASSET_TYPE)

# 공고상세 페이지 머리의 재산유형 배지(<li class="op_cm_badge type01">국유재산</li>).
# 공고상세에는 물건상세의 hidden input(scrnCltrPrptDivNm)이 없고, 「재산유형」 라벨을
# 찾으면 좌측 메뉴의 라벨이 먼저 걸려 메뉴 문구 「중메뉴 펼치기」가 재산유형으로 나갔다.
# 표본 공고상세 23/23 이 그랬고, 배지 type01 은 23/23 정답이었다(2026-09-11 실측).
ASSET_TYPE_BADGE_RE = re.compile(
    r"<li[^>]*class=(?:\"[^\"]*\bop_cm_badge\b[^\"]*\btype01\b[^\"]*\"|'[^']*\bop_cm_badge\b[^']*\btype01\b[^']*')[^>]*>(.*?)</li>",
    re.I | re.S,
)


def asset_type_badge(text: str) -> str:
    match = ASSET_TYPE_BADGE_RE.search(text)
    return clean_text(match.group(1)) if match else ""


def known_asset_type(value: str) -> str:
    """알려진 재산유형 이름을 담은 값만 통과시킨다. 메뉴 문구가 재산유형으로 새지 않게 막는 가드다."""
    return value if value and any(name in value for name in KNOWN_ASSET_TYPES) else ""

DOC_SOURCE_PROFILES = {
    "A": {
        "code": "A",
        "label": "공고 본문에서 서류 목록을 찾을 수 있는 유형입니다",
        "detail": "이 재산유형은 캠코가 직접 집행하는 표준 공고라 조건별 서류가 본문에 적혀 있는 경우가 많습니다.",
    },
    "B": {
        "code": "B",
        "label": "서류 목록이 첨부파일에 있을 가능성이 큰 유형입니다",
        "detail": "이용기관이 직접 작성하는 공고라 본문은 요약만 두고 목록을 첨부 공고문에 담는 경우가 많습니다. 첨부파일도 함께 확인하십시오.",
    },
    "C": {
        "code": "C",
        "label": "원문에 서류 목록이 없을 수 있는 유형입니다",
        "detail": "파산관재인이 개별 작성하는 공고라 본문과 첨부 어디에도 목록이 없는 표본이 있었습니다. 담당기관 확인이 필요합니다.",
    },
    "unknown": {
        "code": "unknown",
        "label": "재산유형으로는 어디에 서류 목록이 있는지 미리 알 수 없습니다",
        "detail": "본문과 첨부파일을 모두 확인하십시오.",
    },
}


def doc_source_profile(asset_type: str) -> dict[str, str]:
    for keyword, code in DOC_SOURCE_BY_ASSET_TYPE:
        if keyword in (asset_type or ""):
            return dict(DOC_SOURCE_PROFILES[code], assetType=asset_type)
    return dict(DOC_SOURCE_PROFILES["unknown"], assetType=asset_type or "")


# 서류명은 닫힌 어휘다. 표본 23건에서 실제로 관측된 이름만 담았고, 여기에 없는 서류명은
# 뽑히지 않는다(= 미추출로 보고된다). 긴 이름을 먼저 두고, 매칭된 구간은 가려서
# 짧은 패턴이 그 안에서 다시 잡히지 않게 한다.
DOC_NAME_PATTERNS: tuple[tuple[str, str], ...] = (
    ("법인인감증명서", r"법인\s*(?:의\s*)?인감\s*증명서"),
    ("법인 등기사항증명서", r"법인\s*등기\s*(?:사항\s*)?(?:전부\s*)?증명서|법인\s*등기부\s*등본"),
    ("등기사항증명서", r"(?:부동산\s*)?등기\s*사항\s*(?:전부\s*)?증명서|등기부\s*등본"),
    ("본인서명사실확인서", r"본인\s*서명\s*사실\s*확인서"),
    ("인감증명서", r"인감\s*증명서"),
    ("인감도장", r"인감\s*도장"),
    ("사용인감계", r"사용\s*인감계"),
    ("주민등록등본", r"주민등록\s*등본"),
    ("주민등록초본", r"주민등록\s*초본"),
    ("가족관계증명서", r"가족관계\s*증명서"),
    ("미성년자 입찰참가 동의서", r"미성년자\s*입찰\s*참가\s*동의서"),
    ("대리입찰신청서", r"대리\s*입찰\s*(?:참가\s*)?신청서"),
    ("공동입찰참가신청서", r"공동\s*입찰\s*(?:참가\s*)?신청서"),
    ("위임장", r"위임장"),
    ("컨소시엄 협정서", r"컨소시엄\s*협정서|공동수급\s*표준협정서"),
    ("농지취득자격증명", r"농지\s*취득\s*자격\s*증명(?:서)?"),
    ("농지대장", r"농지\s*대장"),
    ("토지이용계획 확인원", r"토지\s*이용\s*계획\s*확인(?:원|서)"),
    ("사업자등록증", r"사업자\s*등록증(?:명)?"),
    ("국세 및 지방세 완납증명서", r"국세\s*(?:,|및|과)\s*지방세[^\n]{0,10}완납\s*증명서?"),
    ("국세완납증명서", r"국세\s*완납\s*증명서?"),
    ("지방세완납증명서", r"지방세\s*완납\s*증명서?"),
    ("4대보험 가입확인서", r"(?:4대\s*보험|국민연금)[^\n]{0,20}가입\s*확인서"),
    ("영업신고증", r"영업\s*신고증"),
    ("청렴계약이행서약서", r"청렴\s*계약\s*이행\s*서약서"),
    ("청렴이행각서", r"청렴\s*이행\s*각서"),
    ("청렴계약서", r"청렴\s*계약서"),
    ("계약이행보증보험증권", r"계약\s*이행\s*보증\s*보험\s*증권"),
    ("전자보증서", r"전자\s*보증서"),
    ("보증보험증권", r"보증\s*보험\s*증권"),
    ("확약서", r"확약서"),
    ("운영계획서", r"(?:시설\s*)?운영\s*계획서"),
    ("사업계획서", r"사업\s*계획서"),
    ("사업제안서", r"사업\s*제안서"),
    ("제안서", r"제안서"),
    ("제안서 접수조서", r"제안서\s*접수\s*조서"),
    ("입찰참가신청서", r"입찰\s*참가\s*신청서"),
    ("임차신청서", r"임차\s*신청서"),
    # 이용기관 입주 공고의 신청서(2026-10-19 · 판교 글로벌R&D센터 「다. 입주신청서 1부」 · 수원 바이오센터 서식).
    ("입주신청서", r"입주\s*신청서"),
    ("제소전화해 신청동의서", r"제소전화해\s*신청\s*동의서"),
    ("시설물설치 이용승낙신청서", r"시설물\s*설치\s*이용\s*승낙\s*신청서"),
    ("재직증명서", r"재직\s*증명서"),
    ("건강보험자격득실확인서", r"건강보험\s*자격\s*득실\s*확인서"),
    ("관광사업등록증", r"관광\s*사업\s*등록증"),
    ("등급인정서", r"등급\s*인정서"),
    ("평가결과통보서", r"평가\s*결과\s*통보서"),
    ("부가가치세 과세표준증명서", r"부가가치세\s*과세표준\s*증명서"),
    ("표준재무제표증명서", r"표준\s*재무제표\s*증명서"),
    ("공유재산 사용허가 신청서", r"공유재산\s*사용허가\s*신청서"),
    ("성인지 관점 고려 확인서", r"성인지\s*관점\s*고려\s*확인서"),
    ("정보통신망 이용 송달 동의서", r"정보통신망\s*이용\s*송달\s*동의서"),
    ("신분증", r"신분증"),
    # 라벨이 빈 문자열이면 매칭된 원문을 그대로 서류명으로 쓴다(업종·자격 서류는 이름이 열려 있다).
    ("", r"[가-힣]{2,10}\s*등록증"),
    ("", r"[가-힣]{2,10}\s*면허증"),
)

# 서류를 요구하는 문장에만 붙는 동사. 이것이 없고 조건 문맥도 없으면 단순 언급으로 본다.
# 「갖추」는 넣지 않는다 — 「대항요건을 갖추고 있는 임차인」 같은 설명 문장이 걸린다(표본 01 실측).
DOC_REQUEST_RE = re.compile(r"제출|지참|구비|첨부|발급받아|제시")

# 「…를 제출한 것으로 간주함」은 따로 낼 것이 없다는 뜻이다(2026-10-19 · 청렴계약서 2건).
# 이 구절을 지운 나머지에 제출 동사가 또 있어야 요구로 본다 — 「간주하며, 낙찰자로 결정된 자는
# 계약 체결 시 … 제출하여야」처럼 같은 문장에 진짜 요구가 이어지는 경우를 지우지 않기 위해서다.
DEEMED_SUBMITTED_RE = re.compile(r"제출\s*(?:한|된)\s*것으로\s*(?:간주|본다|봅니다)")

# 「10. 낙찰(예정)자 제출서류」·「3. 증빙서류 목록」처럼 절 제목 자체가 제출 요구인 경우. 그 아래
# 나열 항목(「라. 사업계획서 1부」)에는 제출 동사가 없다(2026-10-19 · 판교 공고 실측).
SUBMISSION_LIST_HEADING_RE = re.compile(
    r"(?:제출|구비|지참|등록|필요|증빙|부대|입증)\s*(?:서류|자료)|서류\s*(?:제출|목록)|제출\s*서류"
)
# 제출 목록 절 안에서 동사 없이도 요구로 보는 줄의 최대 길이. 나열 항목·표 칸은 짧고, 긴 줄은 설명 문단이다.
SUBMISSION_LIST_ITEM_MAX_CHARS = 200


# 서류명 바로 뒤가 「…를 제출한 것으로 간주」·「… 등의 각종 공부를 열람」·「… 참조」면 그 서류는 요구가 아니다.
# 같은 줄의 다른 서류에 붙은 「제출」(「사업계획서를 작성, 제출하시기 바랍니다」)에 끌려 목록에 오르는 것을 막는다.
# 「간주하며, 낙찰자로 결정된 자는 … 제출하여야」처럼 뒤에 다시 요구가 오면 막지 않는다(폐교 매각 · 청렴계약이행서약서).
# 「위임장(참고⑧ 양식참조) 1부」처럼 서식을 가리키는 「참조」는 언급이 아니다(김해공항 · 측정 중 회귀 1건).
# 「등기사항증명서상 근저당설정최고액」처럼 바로 뒤가 「상」이면 그 서류의 내용을 가리키는 말이다.
DOC_MENTION_AFTER_RE = re.compile(
    r"^[^.。\n]{0,15}?(?<!양식)(?<!서식)(?<!양식 )(?<!서식 )(?:열람|참조|참고하)|^상\s"
)
DOC_MENTION_AFTER_REACH = 25


def doc_is_mention_only(line: str, end: int) -> bool:
    after = line[end : end + DOC_MENTION_AFTER_REACH]
    deemed = DEEMED_SUBMITTED_RE.search(after)
    if deemed:
        return not DOC_REQUEST_RE.search(DEEMED_SUBMITTED_RE.sub("", line[end + deemed.end() :]))
    return bool(DOC_MENTION_AFTER_RE.search(after)) and not DOC_REQUEST_RE.search(after)


def doc_request_in(text: str) -> bool:
    """제출 동사가 있는가. 「제출한 것으로 간주」 구절은 빼고 본다."""
    return bool(DOC_REQUEST_RE.search(DEEMED_SUBMITTED_RE.sub("", text)))


# 한 줄짜리 첨부에서 서류명 하나가 속한 조항 구간을 자르는 경계. 「1. 」·「가. 」 같은 번호와 ■·※ 같은 기호다.
# 날짜(「2026. 8. 3.」) 안의 「8. 」도 경계로 잡혀 구간이 짧아질 수 있다 — 짧아지는 쪽은 요구를 놓칠 뿐 지어내지 않는다.
CLAUSE_BREAK_RE = re.compile(r"(?<![\d.])\d{1,2}\s*[.)]\s+|(?<![가-힣])[가-하]\s*\.\s+|[■◆※○●□▪]")
CLAUSE_REACH = 300


def doc_clause_bounds(text: str, start: int, end: int) -> tuple[int, int]:
    """서류명(start~end)이 든 조항 구간. 앞뒤 CLAUSE_REACH 자 안에서 가장 가까운 경계까지다."""
    lo = max(0, start - CLAUSE_REACH)
    hi = min(len(text), end + CLAUSE_REACH)
    for match in CLAUSE_BREAK_RE.finditer(text, lo, start):
        lo = match.start()
    following = CLAUSE_BREAK_RE.search(text, end, hi)
    if following:
        hi = following.start()
    return lo, hi


def is_note_heading(line: str) -> bool:
    """「※ 낙찰자의 계약체결 전 제출서류」처럼 ※ 로 시작하는 짧은 표제 줄인가.

    ※ 줄 전부를 표제로 보면 ※ 문단의 문장 판정 분기(아래 SENTENCE_STAGE_RULES 로 표제 스택을 비우는 곳)가
    죽어 입찰 전 서류가 빠진다(2026-10-19 리뷰 r1 P1-1 재현 · 원문 36건에 ※ 줄 301개). 그래서 서류명이 없고
    표제 사전에 걸리는 INHERIT_ITEM_MAX_CHARS 이하 줄로 좁힌다.
    """
    stripped = line.strip()
    # 제출 목록 제목(SUBMISSION_LIST_HEADING_RE)이어야 한다 — 「※ 실거래 신고가 … 매매계약 체결시까지」 같은 설명 문장이
    # 「계약 체결」 규칙에 걸려 표제가 되는 것을 막는다(인천 남동구 공매 2건 · 측정 중 확인).
    return (
        stripped.startswith("※")
        and len(stripped) <= INHERIT_ITEM_MAX_CHARS
        and not find_doc_name_spans(stripped)
        and bool(SUBMISSION_LIST_HEADING_RE.search(stripped))
        and any(heading_rule_search(pattern, stripped) for pattern, _stage in HEADING_STAGE_RULES)
    )


NOTE_ITEM_NUMBER_RE = re.compile(r"^\s*(\d{1,2})\s*[.)]")
NOTE_ITEM_HANGUL_RE = re.compile(r"^\s*([가-하])\s*\.")


def continues_note_scope(scope: dict[str, object], line: str) -> bool:
    """※ 표제 아래 목록이 이어지는가. 번호는 1씩 늘어야 하고(다음 본 조항 「10.」에서 끊긴다), 긴 줄에서 끊긴다."""
    if len(line) > SUBMISSION_LIST_ITEM_MAX_CHARS:
        return False
    for kind, pattern, to_num in (
        ("number", NOTE_ITEM_NUMBER_RE, int),
        ("hangul", NOTE_ITEM_HANGUL_RE, lambda ch: ord(ch) - ord("가")),
    ):
        match = pattern.match(line)
        if match:
            num = to_num(match.group(1))
            if scope["kind"] in ("", kind) and (scope["num"] < 0 or num == scope["num"] + 1):
                scope["kind"], scope["num"] = kind, num
                return True
            return False
    return bool(SUB_ITEM_RE.match(line))


# 제출 목록을 여는 짧은 안내 줄(「④ 제출서류 : … 아래 서류를 첨부하여야 하며」 · 「제출서류명」)이 지나간 뒤
# 다음 목록 머리(번호 · ①~⑮ · ○ · ㅇ)가 나오기 전까지의 줄은 제출 목록 안으로 본다(인천공항 공고의 「A. 관광사업등록증」).
SUBMISSION_CUE_MAX_CHARS = 200
LIST_HEAD_RE = re.compile(r"^\s*(?:\d+\s*[.)]|[가-하]\s*\.|[IVX]+\s*\.|[①-⑮○ㅇ■◆])")

# 첨부 PDF는 문장 하나가 여러 줄로 잘린다(「…인감증명서와 주민등록등본 원본을 입찰기간의 마⏎감일 17:00까지 … 제출」).
# 그래서 첨부 줄의 제출 동사는 그 줄이 속한 문단(앞뒤로 다음 문단 머리까지 · PARAGRAPH_REACH 자 안)에서 찾는다.
PARAGRAPH_REACH = 300


def paragraph_bounds(text: str, start: int, end: int) -> tuple[int, int]:
    """start~end 가 든 문단. 문단 머리는 PARAGRAPH_START_RE(번호 · 기호로 시작하는 줄)다."""
    lo = max(0, start - PARAGRAPH_REACH)
    for match in PARAGRAPH_START_RE.finditer(text, lo, start + 1):
        lo = match.start() + 1
    hi = min(len(text), end + PARAGRAPH_REACH)
    following = PARAGRAPH_START_RE.search(text, end, hi)
    if following:
        hi = following.start()
    return lo, hi


# 한 줄짜리 첨부에서 서류명 앞쪽의 가장 가까운 본 조항 번호(「8. 」)부터 서류명까지에 제출 목록 표제가 있으면
# 그 목록 안으로 본다(광양 공고 「8. 낙찰자 제출서류 (…) 1) 공유재산 사용허가 신청서 1부. 2) …」).
TOP_CLAUSE_MARK_RE = re.compile(r"(?<![\d.])\d{1,2}\s*\.\s+")
TOP_CLAUSE_REACH = 600


def under_submission_heading_inline(text: str, start: int) -> bool:
    lo = max(0, start - TOP_CLAUSE_REACH)
    marks = list(TOP_CLAUSE_MARK_RE.finditer(text, lo, start))
    head = marks[-1].start() if marks else lo
    return bool(SUBMISSION_LIST_HEADING_RE.search(text, head, start))

# 서류명 자체가 단계를 확정하는 사전. 조항 표제·문장 판정보다 먼저 본다 — 이 서류들은
# 어느 공고에서도 "입찰기간 중에" 내는 신청서라, 공고문 작성자가 그 서류를 어느 조항
# 아래 적어 놓았는지와 무관하게 단계가 고정된다(stage-classification-design.md §1-A-3·§2-A).
#
# 근거: 압류재산 인터넷공매 입찰참가자준수규칙 제7조(공동명의 입찰·대리입찰·미성년자 명의
# 입찰의 신청서를 "입찰기간 중에" 제출), 전자자산처분시스템 적정최고가입찰참가자준수규칙
# 제6조⑤⑥(공동입찰참가신청서·대리입찰신청서를 "입찰기간 중에" 제출) — 두 규칙 모두 온비드
# 자료실 > 법령/규정에서 전문을 확보했다.
#
# 서식 자체는 재산유형별로 변형이 있다(docs/90_MVP개발/08_온비드자료실_오픈API28종_조사_20260907.md
# 191~206행, 온비드 서식자료 71건 전수조사) — 공동입찰참가신청서 5종(국유재산·이용기관
# 입찰용·캠코 공유재산·수탁재산·유입자산/수탁담보주택), 대리입찰신청서 5종(동일 구성),
# 미성년자입찰참가동의서 2종(이용기관 입찰용·캠코 공유재산). 합치면 12개의 변형 문자열이다.
# 🔴 설계 문서(§1-A-4)는 이 묶음을 "9건"이라 적었지만 바로 다음 문장이 실제로 나열한
# 변형은 5+5+2=12개다 — 설계 문서 자체의 집계와 본문이 어긋나 있어서, 추측으로 9개로
# 줄이지 않고 근거 문서(08번 조사)가 실제로 나열한 12개를 그대로 반영했다. 다만
# DOC_NAME_PATTERNS 가 기관명 접두어("(이용기관 입찰용)"·"(캠코 공유재산)"·"유입자산"
# 등)를 흡수해 12개 변형이 전부 아래 3개 표준 이름 중 하나로 뽑히므로, 사전은 변형별이
# 아니라 표준 이름 3개로 충분하다.
FORM_NAME_STAGE_RULES: dict[str, str] = {
    "공동입찰참가신청서": "입찰 전",
    "대리입찰신청서": "입찰 전",
    "미성년자 입찰참가 동의서": "입찰 전",
}

# 조건부 서류이면서 온비드 공통 가이드·준수규칙·법령 어디에도 일반 근거가 없는 서류명.
# 이 서류는 사전을 더 채워도 영구히 "미분류"가 아니라 "별도 문의 필요"로 다르게 보여준다 —
# "미분류"는 "사전을 넓히면 언젠가 찾을 수 있다"는 뜻인데, 이 서류는 전 재산유형에 적용되는
# 일반 규정이 없어(기관·공고마다 요구 여부와 시점이 다르다, 표본 21의 "컨소시엄 협정서"가
# 그 사례다) 사전을 넓혀도 못 찾는다. 추가하려면 §2-A 규정 근거 사전에 없는 서류인지
# 먼저 확인한다 — 있으면 미분류로 남겨 사전을 채울 대상으로 삼아야 한다.
NO_GENERAL_BASIS_DOC_NAMES: frozenset[str] = frozenset({"컨소시엄 협정서"})
NEEDS_INQUIRY_STAGE = "별도 문의 필요"

# 이 절/문장이 입찰 전 준비물인지 낙찰 후 계약 서류인지 표시한다.
#
# 🔴 옛 CONTRACT_STAGE_RE(자유 서술문 어디서나 키워드를 찾는 방식)는 폐기했다 — 블록
# 전체에서 계약/낙찰 키워드를 찾아 그 블록의 모든 서류를 끌고 가는 방식이라, 서류와
# 무관한 문장(예: 계약보증금 안내)이 뒤에 나오는 서류까지 전부 오염시켰다
# (team-reports/2026-10-18-bid-doc-timeline/stage-classification-design.md §0·§4 ·
# 23개 표본 재현에서 41.9% 불일치). 대신 세 단계로 판정한다.
#
# ⑴ FORM_NAME_STAGE_RULES 에 있는 서식명이면 그 즉시 확정한다(위 사전).
# ⑵ 조항 표제(번호·문자·■ 로 시작하는 줄)를 만나면 그 표제 문자열 자체를 들고 가서
#    HEADING_STAGE_RULES 사전과 대조한다. 사전에 없는 표제는 판정하지 않는다.
# ⑶ 표제가 없거나 사전에 없으면, 그 서류명이 «속한 그 줄 하나»만 보고
#    SENTENCE_STAGE_RULES 결정적 문구를 찾는다. 다른 줄의 단어는 참조하지 않는다.
# ⑷ 셋 다 못 정하면 NO_GENERAL_BASIS_DOC_NAMES 서류는 "별도 문의 필요", 그 밖은
#    "미분류" — 추측으로 입찰 전/낙찰 후 어느 쪽으로도 밀어 넣지 않는다.
#
# 신호는 설계 문서 §2 신호표·§2-A 규정 근거 사전·appendix 160행 전건 재대조(§5-2)에서
# 왔다. 아래 10개 항목 각각 appendix의 "근거" 칸에 인용된 조항 표제 원문 그대로다 —
# 인용에 없는 표제는 상상해서 넣지 않았다(설계 문서 §555행 "사전 항목 수는 최소 10종").
# 넓은 규칙 「계약 체결」은 표제의 첫 줄 안에서만 본다(heading_rule_search).
CONTRACT_HEAD_RE = re.compile(r"계약\s*체결")

HEADING_STAGE_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    # 입찰 전 (2개) — appendix 표본 04~08, 21.
    # 🔴 표본11의 "입찰 전" 판정은 이 표제가 아니라 "3) 제출서류" 조항의 SENTENCE_STAGE_RULES
    # "입찰 시 무효" 문구가 근거다(appendix 60행 — "사업계획서를…제출하지 않으면 입찰 시 무효").
    # 전에는 여기 "표본07·08·11"로 적었는데, appendix에 표본11을 "입찰참가자격" 표제로 인용한
    # 행이 없다 — 설계 대조 감사(2026-10-19)에서 확인한 인용 오류를 정정한다.
    (re.compile(r"입찰\s*참가\s*자격"), "입찰 전"),  # "2. 입찰참가자격"(표본04~08) · "입찰참가자격"(표본07·08)
    (re.compile(r"입찰\s*참가\s*등록\s*서류"), "입찰 전"),  # "4. 입찰참가 등록서류"(표본21)
    # 낙찰 후·계약 시 (8개) — appendix 표본 11~13, 15~17, 20, 22.
    (re.compile(r"구비\s*서류"), "낙찰 후·계약 시"),  # "다. 계약 체결 시 구비서류"(표본11) · "나. 구비서류"(표본12)
    (re.compile(r"계약\s*체결\s*장소"), "낙찰 후·계약 시"),  # "다. 계약체결 장소"(표본12, 나.구비서류 바로 다음 조항)
    # "8. 낙찰자 제출서류 (낙찰일로부터 30일 이내 제출)"(표본13) · "바. 낙찰자의 제출서류"(2026-10-19 실공고 909691 관측)
    # · "10. 낙찰(예정)자 제출서류"(판교 글로벌R&D센터) · "12. 낙찰자의 사용허가 신청시 제출서류"(과천시민회관)
    # · "※ 낙찰자의 계약체결 전 제출서류"(강남터미널 광고) — 2026-10-19 원문 36건 측정에서 앞 둘이 사전에 안 걸렸다.
    (re.compile(r"낙찰\s*(?:\(\s*예정\s*\)\s*)?자\s*의?\s*[^\n]{0,12}?제출\s*서류"), "낙찰 후·계약 시"),
    (re.compile(r"낙찰\s*일\s*로\s*부터"), "낙찰 후·계약 시"),  # 표본13 괄호 안 "낙찰일로부터 30일 이내" · 표본20 "낙찰일로부터"
    (re.compile(r"계약\s*체결\s*시\s*필요\s*서류"), "낙찰 후·계약 시"),  # "계약체결시 필요서류"(표본15~17)
    (re.compile(r"계약\s*체결\s*시\s*지참\s*서류"), "낙찰 후·계약 시"),  # "14. 계약체결 시 지참 서류"(표본22)
    (
        re.compile(r"제출\s*서류\s*\(\s*방문\s*시\s*계약서\s*날인용\s*도장\s*지참\s*\)"),
        "낙찰 후·계약 시",
    ),  # "■ 제출서류(방문시 계약서 날인용 도장 지참)"(표본20 일부)
    (CONTRACT_HEAD_RE, "낙찰 후·계약 시"),  # "7. 계약체결 ① 낙찰자는 낙찰일로부터…"(표본20 일부) 등 번호조항 변형
)


def heading_rule_search(pattern: re.Pattern[str], heading: str) -> bool:
    """표제 사전 한 항목이 그 표제에 걸리는가.

    넓은 규칙 「계약 체결」(CONTRACT_HEAD_RE)만은 표제의 «첫 줄» 안에서만 본다.
    표제 조각(최대 80자)이 줄을 넘어 표 칸까지 삼키면 「1. 입찰개요 ⏎ … 계약기간 ⏎ 계약체결일 ~ 5년」 같은
    표 내용이 걸려, 입찰 전 서류(예술의전당 「제안서」)가 낙찰 후로 갔다(2026-10-19 원문 36건 측정).
    처음에는 번호 뒤 20자로 좁혔는데, 그러면 「3) 이행보증보험증권 제출- … 계약체결 시」 같은 한 줄 표제의
    낙찰 후 판정 3건이 미분류로 떨어졌다(같은 측정). 그래서 폭이 아니라 줄 경계로 자른다.
    """
    if pattern is not CONTRACT_HEAD_RE:
        return bool(pattern.search(heading))
    first_line = heading.split("\n", 1)[0]
    # 「라. 입찰 절차 : 입찰공고 → 입찰서 및 제안서 제출 → … → 계약 체결」 같은 흐름 설명은 이 조항의 시점이 아니다(예술의전당).
    if "→" in first_line:
        return False
    return bool(pattern.search(first_line))

# 표제가 없거나(예: 하이픈·ㅇ 로만 이어지는 공고문 본문) 사전에 없는 표제일 때, 서류명이
# 속한 그 줄만 보고 찾는 결정적 문구. 다른 줄로 번지지 않는다.
SENTENCE_STAGE_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            r"입찰\s*(?:시\s*)?무효|입찰\s*참가\s*불승인"
            r"|입찰.{0,10}(?:마감|기간).{0,15}(?:까지|중)"
            r"|가격\s*개찰.{0,20}이전"
        ),
        "입찰 전",
    ),
    (re.compile(r"회송|매매계약.{0,30}회송"), "낙찰 후·계약 시"),
)

# 서류명 근처 문장 판정(doc_stage_at)에만 더 쓰는 낙찰 후 문구. 「낙찰자로 결정된 자가 … 10일 이내에 임차신청서를」
# (김해공항) · 「낙찰자로 결정된 자는 계약 체결 시 [별지4]를 … 제출」(폐교 매각) — 2026-10-19 원문 36건 측정.
# SENTENCE_STAGE_RULES 에 넣지 않은 이유: 그 목록은 서류명 없는 문단에서 표제 스택을 비우는 데도 쓰여(extract_doc_items),
# 흔한 이 문구가 들어가면 뒤 목록의 표제가 통째로 지워진다.
AWARDEE_SENTENCE_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    # 「낙찰자로 결정합니다」(선정 방식 설명)는 빼고, 그렇게 정해진 «사람·날»을 가리킬 때만 쓴다(김해공항 「제안서 평가점수 … 합산하여」).
    (
        re.compile(r"(?:낙찰자|계약\s*대상자)\s*로\s*(?:결정|선정|통보)\s*(?:된|한|받은)\s*(?:자|날|업체)"),
        "낙찰 후·계약 시",
    ),
)

# 조항 표제로 볼 줄 — 번호·문자 조항(LINE_RESET_RE)과 같지만, "■" 같은 기호 머리글도
# 표제로 본다(표본 20 「■ 제출서류(방문시 계약서 날인용 도장 지참)」가 숫자·문자로
# 시작하지 않는다). 조건 물림(LINE_RESET_RE)과는 별개 — 그 쪽은 바꾸지 않는다.
HEADING_LINE_RE = re.compile(r"^\s*(?:\d+\s*[.)]|[가-하]\s*\.|[IVX]+\s*\.|■|◆)")

# 조항 번호 체계별 층. 「10.」·「가.」·「1)」은 서로 다른 층이다. 표제를 «마지막 번호 줄
# 하나»로만 들고 가면 「10. 최종낙찰자 제출서류」 아래 「가. 사업자등록증 …」 같은 항목 줄이
# 표제를 덮어써, 사전에 있는 표제인데도 그 아래 서류가 전부 미분류로 떨어진다
# (2026-10-19 실공고 관측 — 909445 「10. 최종낙찰자 제출서류」 · 909691 「바. 낙찰자의 제출서류」).
# 그래서 층별로 쌓고, 안쪽 층부터 사전에 걸리는 표제를 찾는다. 「1)」을 「1.」보다 먼저 본다.
HEADING_KIND_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("paren", re.compile(r"^\s*\d+\s*\)")),
    ("number", re.compile(r"^\s*\d+\s*\.")),
    ("hangul", re.compile(r"^\s*[가-하]\s*\.")),
    ("roman", re.compile(r"^\s*[IVX]+\s*\.")),
    ("symbol", re.compile(r"^\s*[■◆]")),
)


# 바깥 표제를 물려받을 수 있는 목록 항목 줄의 최대 길이. 실공고 항목 줄은 60자 안팎이다
# (909691 「1). 주민등록등본(법인의 경우 법인등기부등본) 1부」 · 909445 「가. 사업자등록증 및 법인등기부등본 각1부」).
INHERIT_ITEM_MAX_CHARS = 100


# 목록 항목으로 볼 때 번호 뒤에서 첫 서류명까지 허용하는 거리(글자). 「1). 주민등록등본」은 0~1자다.
ITEM_NAME_OFFSET_MAX = 8


PREBID_WORD_RE = re.compile(r"입찰\s*참가|응찰|입찰\s*시|입찰\s*전")


def can_inherit_outer_heading(line: str) -> bool:
    """바깥 층 표제를 물려받아도 되는 줄인가 — 짧은 소제목(서류명 없음)이거나 번호 바로 뒤 서류명 목록 항목."""
    marker = HEADING_LINE_RE.match(line)
    if not marker or len(line) > INHERIT_ITEM_MAX_CHARS:
        return False
    starts = [start for _name, start, _end in find_doc_name_spans(line)]
    return not starts or min(starts) - marker.end() <= ITEM_NAME_OFFSET_MAX


def heading_kind(line: str) -> str:
    for kind, pattern in HEADING_KIND_RULES:
        if pattern.match(line):
            return kind
    return ""


def push_heading(stack: list[tuple[str, str]], line: str) -> None:
    """같은 층 번호가 다시 나오면 그 층과 그 아래 층을 걷어내고 바꾼다. 처음 보는 층이면 안쪽으로 쌓는다."""
    kind = heading_kind(line)
    for index, (existing, _line) in enumerate(stack):
        if existing == kind:
            del stack[index:]
            break
    stack.append((kind, line))


def stage_heading_from_stack(stack: list[tuple[str, str]]) -> str:
    """안쪽 층부터 HEADING_STAGE_RULES 에 걸리는 표제를 찾는다. 없으면 가장 안쪽 표제를 준다(옛 동작)."""
    for _kind, line in reversed(stack):
        if any(heading_rule_search(pattern, line) for pattern, _stage in HEADING_STAGE_RULES):
            return line
    return stack[-1][1] if stack else ""


def resolve_doc_stage(current_heading: str, window: str, name: str = "") -> str:
    if name in FORM_NAME_STAGE_RULES:
        return FORM_NAME_STAGE_RULES[name]
    for pattern, stage in HEADING_STAGE_RULES:
        if current_heading and heading_rule_search(pattern, current_heading):
            return stage
    for pattern, stage in SENTENCE_STAGE_RULES:
        if pattern.search(window):
            return stage
    return NEEDS_INQUIRY_STAGE if name in NO_GENERAL_BASIS_DOC_NAMES else "미분류"


# PDF/HWP 첨부는 줄바꿈이 없어 "한 줄"이 문서 전체(최대 89,290자 실측)일 수 있다. 그 안에도
# "8.  낙찰자  제출서류" 같은 조항 표제가 실려 있지만 줄 시작이 아니라 줄 «중간»에 있어
# HEADING_LINE_RE(^로 시작) 가 못 잡는다. 그래서 줄 중간의 번호·문자 마커도 찾는다.
# 🔴 [가-하] 단독 글자 뒤에 마침표(「다.」「나.」류)는 한국어 평서문이 거의 전부 「~합니다.」
# 「~한다.」로 끝나기 때문에, 앞 글자를 가리지 않으면 문장 종결마다 가짜 조항 표제로 오인한다
# (표본 07 "...제출하여야 합니다.\n또한..." 의 "다."가 그 사고였다 — 뒤 문장 전체를
# "조항 표제"로 끌어왔다). 그래서 바로 앞이 한글 음절이 «아닌» 경우만 조항 마커로 본다 —
# 진짜 「다. 계약체결 장소」같은 마커는 줄바꿈·공백·문자열 시작 뒤에 오지 한글 글자 뒤에 오지 않는다.
EMBEDDED_HEADING_MARKER_RE = re.compile(r"\d+\s*[.)]\s+|(?<![가-힣])[가-하]\s*\.\s+|■\s*|◆\s*")
HEADING_SNIPPET_MAX = 80
STAGE_WINDOW_BEFORE = 150
STAGE_WINDOW_AFTER = 220


def governing_heading(text: str, pos: int, carried_heading: str, section_start: int) -> str:
    """서류명 바로 앞(같은 조항 구간 안)에서 사전에 걸리는 조항 표제를 가까운 것부터 찾는다.

    section_start 는 LINE_RESET_RE 로 가른 "그 조항이 시작한 자리" 다 — 그 앞(다른 조항)으로는
    넘어가지 않는다. 이 구간 안에 없으면 이전 실제 줄에서 캡처해 들고 온 carried_heading 으로
    떨어진다.
    """
    markers = [m for m in EMBEDDED_HEADING_MARKER_RE.finditer(text, section_start, pos)]
    for marker in reversed(markers):
        snippet = text[marker.start() : min(pos, marker.start() + HEADING_SNIPPET_MAX)]
        for pattern, _stage in HEADING_STAGE_RULES:
            if heading_rule_search(pattern, snippet):
                return snippet
    return carried_heading


# 새 문단을 여는 줄 머리. 줄바꿈만 있고 이 머리가 없으면 앞 문장이 이어지는 것(PDF 줄 넘김)으로 본다.
PARAGRAPH_START_RE = re.compile(r"\n\s*(?:[※\-‐–▪·○ㅇ①-⑮■◆]|\(\d+\)|\d+\s*[.)]|[가-하]\s*\.)")


PREBID_CONFLICT_RE = re.compile(r"사전\s*확인\s*후\s*(?:응찰|입찰)")


def same_clause_has_prebid_phrase(text: str, start: int, end: int, section_bounds: tuple[int, int]) -> bool:
    """서류명이 든 문장(다음 문단 머리 전까지)과 그 앞 창에 입찰 전 결정 문구가 있는가.

    창 끝을 다음 문단 머리에서 끊는다. 끊지 않으면 바로 아래 「※ 입찰 참가 시에는 … 입찰 마감일까지」 같은
    다른 문단의 문구가 위 목록까지 미분류로 만든다(2026-10-19 리뷰 r1 T2 반영 중 관측).
    """
    lo = max(section_bounds[0], start - STAGE_WINDOW_BEFORE)
    hi = min(section_bounds[1], end + STAGE_WINDOW_AFTER)
    next_paragraph = PARAGRAPH_START_RE.search(text, end, hi)
    if next_paragraph:
        hi = next_paragraph.start()
    return bool(PREBID_CONFLICT_RE.search(text, lo, hi)) or any(pattern.search(text, lo, hi) for pattern, stage in SENTENCE_STAGE_RULES if stage == "입찰 전")


def doc_stage_at(
    text: str,
    start: int,
    end: int,
    carried_heading: str,
    section_bounds: tuple[int, int],
    name: str = "",
    inherited: bool = False,
) -> tuple[str, bool, str]:
    """단계·확정 여부와 함께 "어느 조항 표제를 근거로 썼는가"(source_heading)도 돌려준다.

    같은 서류명이 같은 문서 안에 여러 번 나올 수 있다(표본 20의 「신분증」은 대리입찰
    서류 안내에서 한 번, 「■ 제출서류」 낙찰 후 목록에서 또 한 번 나온다). 호출부가 먼저
    나온 쪽만 쓰면 더 확정적인 뒤쪽 조항 표제 판정을 놓친다 — confident 로 그 우선순위를
    판단하게 한다.

    name 이 FORM_NAME_STAGE_RULES 에 있으면(공동입찰참가신청서 등 서식명 자체가 단계를
    확정하는 서류) 조항 표제보다 먼저 보고 그 즉시 확정한다 — 이때는 근거가 표제가 아니라
    서식명 자체이므로 source_heading 은 빈 문자열이다.

    source_heading 은 HEADING_STAGE_RULES 가 매칭한 표제 원문 그대로다(§3-A-2의
    "표제 문자열을 그 자체로 들고 간다" 설계) — SENTENCE_STAGE_RULES 로 정해졌거나
    미분류/별도 문의 필요로 떨어지면 표제가 근거가 아니므로 빈 문자열로 둔다.
    """
    if name in FORM_NAME_STAGE_RULES:
        return FORM_NAME_STAGE_RULES[name], True, ""
    section_start, section_end = section_bounds
    embedded = governing_heading(text, start, "", section_start)
    heading = embedded or carried_heading
    if heading:
        for pattern, stage in HEADING_STAGE_RULES:
            if heading_rule_search(pattern, heading):
                # 🔴 바깥 층에서 «물려받은» 낙찰 후 표제가 서류가 든 문장의 입찰 전 결정 문구와 부딪히면 표제를
                # 버리고 아래 문장 판정으로 내려간다. 더 가까운 근거가 이긴다. 입찰 전 서류를 4단계로만 보내면
                # 사용자가 그 서류를 놓친다 — 가장 비싼 오배치다(2026-10-19 리뷰 r1 F1·T1·T3 · 표본 07·08
                # 「사전확인 후 응찰」). 리뷰어는 미분류를 권했고, 팀장은 문장 근거(입찰 전)를 택했다. 둘 다 2단계에 보인다.
                if inherited and not embedded and stage == "낙찰 후·계약 시" and same_clause_has_prebid_phrase(
                    text, start, end, section_bounds
                ):
                    break
                return stage, True, heading
    # 창이 넓어지면(표본 20) "회송"(낙찰 후, 같은 줄)과 "입찰무효"(입찰 전, 다음 문장)가
    # 한 창에 같이 걸릴 수 있다. 목록 순서가 아니라 «서류명과의 실제 거리»로 더 가까운
    # 결정적 문구를 우선한다 — 멀리 있는 문구가 가까운 문구를 이기면 안 된다.
    lo = max(section_start, start - STAGE_WINDOW_BEFORE)
    hi = min(section_end, end + STAGE_WINDOW_AFTER)
    center = (start + end) / 2
    best_stage: str | None = None
    best_dist: float | None = None
    for pattern, stage in SENTENCE_STAGE_RULES + AWARDEE_SENTENCE_RULES:
        for match in pattern.finditer(text, lo, hi):
            dist = min(abs(match.start() - center), abs(match.end() - center))
            if best_dist is None or dist < best_dist:
                best_dist, best_stage = dist, stage
    if best_stage:
        return best_stage, False, ""
    return (NEEDS_INQUIRY_STAGE if name in NO_GENERAL_BASIS_DOC_NAMES else "미분류"), False, ""


# 조건 축은 아래 10개다(`len(CONDITION_AXES) == 10` 으로 셀 것).
# 표본조사 §3-4 표의 8행에서 왔고, 그중 「개인 / 법인」 1행을 `corp`·`person` 2축으로 나눠 9개가 된다.
# 여기에 「지역 제한」을 더해 10개 — 2026-09-07 캠코 회의에서 정인기 차장이
# 제한경쟁 입찰의 지역 요건 증빙을 예로 들었다.
CONDITION_AXES: tuple[tuple[str, str, str], ...] = (
    ("proxy", "대리입찰", r"대리\s*입찰|대리인(?:을)?\s*(?:선임|방문|제출)|위임"),
    ("joint", "공동입찰", r"공동\s*(?:입찰|계약|매수)|여러\s*사람이\s*공동"),
    ("minor", "미성년자", r"미성년자"),
    ("consortium", "컨소시엄", r"컨소시엄"),
    ("seal", "사용인감", r"사용\s*인감"),
    ("region", "지역 제한(제한경쟁)", r"제한\s*경쟁|관내\s|소재지에\s*(?:주소|사업)|해당\s*지역에\s*(?:거주|소재)"),
    ("license", "업종·자격 요건", r"등록증|면허|자격\s*요건|업종\s*제한"),
    ("corp", "법인", r"법\s?인"),
    ("person", "개인", r"개\s?인(?!정보)"),
    ("foreign", "외국인", r"외국인"),
)

# 「~는 불가/불허용」이 같은 줄에 있으면 그 축은 서류 분기가 아니라 금지 안내다.
# 표본 19는 「공동입찰허용여부 [□ 허용 / ■ 불허용]」이라 키워드만 보면 오탐이 된다(§3-4).
CONDITION_NEGATIVE_RE = re.compile(r"불허용|불가능|불가하|허용하지\s*않|제외합니다|해당\s*없")

# 발급처 안내는 일반 상식 수준으로만 둔다. 여기에 없는 서류는 안내 문장을 만들지 않는다.
DOC_HOWTO = {
    "인감증명서": ("정부24 또는 주민센터", "https://www.gov.kr/"),
    "본인서명사실확인서": ("정부24 또는 주민센터", "https://www.gov.kr/"),
    "주민등록등본": ("정부24 또는 주민센터", "https://www.gov.kr/"),
    "주민등록초본": ("정부24 또는 주민센터", "https://www.gov.kr/"),
    "가족관계증명서": ("정부24 또는 주민센터", "https://www.gov.kr/"),
    "법인 등기사항증명서": ("인터넷등기소", "https://www.iros.go.kr/"),
    "법인인감증명서": ("인터넷등기소 또는 등기소", "https://www.iros.go.kr/"),
    "등기사항증명서": ("인터넷등기소", "https://www.iros.go.kr/"),
    "사업자등록증": ("국세청 홈택스", "https://www.hometax.go.kr/"),
    "국세완납증명서": ("국세청 홈택스", "https://www.hometax.go.kr/"),
    "지방세완납증명서": ("위택스 또는 정부24", "https://www.wetax.go.kr/"),
    "국세 및 지방세 완납증명서": ("홈택스(국세)·위택스(지방세)", "https://www.hometax.go.kr/"),
    "전자보증서": ("SGI서울보증", "https://www.sgic.co.kr/"),
    "보증보험증권": ("SGI서울보증", "https://www.sgic.co.kr/"),
    # 아래 세 건은 공고 첨부 서식이나 온비드 자료실 서식을 쓰는 것이 표본에서 관측됐다.
    "대리입찰신청서": ("공고 첨부 서식 또는 온비드 자료실 서식", "https://www.onbid.co.kr/"),
    "공동입찰참가신청서": ("공고 첨부 서식 또는 온비드 자료실 서식", "https://www.onbid.co.kr/"),
    "위임장": ("공고 첨부 서식 또는 온비드 자료실 서식", "https://www.onbid.co.kr/"),
    # 2026-10-17 추가분 — 발급처가 명확한 정부·공공기관 증명서만 넣었다(웹 검색으로 각
    # 사이트가 해당 서류를 실제로 발급한다는 것을 확인했다). 신분증·인감도장·사용인감계처럼
    # 발급처가 없거나, 위임장·확약서·사업계획서처럼 서비스 자체에서 제공해야 하는 서식,
    # 영업신고증·관광사업등록증처럼 지자체마다 온라인 창구가 달라 특정하기 어려운 서류는
    # 넣지 않았다.
    "농지취득자격증명": ("정부24(해당 읍면동)", "https://www.gov.kr/"),
    "농지대장": ("정부24", "https://www.gov.kr/"),
    "토지이용계획 확인원": ("정부24", "https://www.gov.kr/"),
    "4대보험 가입확인서": ("4대사회보험정보연계센터", "https://www.4insure.or.kr/"),
    "건강보험자격득실확인서": ("국민건강보험공단 또는 정부24", "https://www.nhis.or.kr/"),
    "부가가치세 과세표준증명서": ("국세청 홈택스", "https://www.hometax.go.kr/"),
    "표준재무제표증명서": ("국세청 홈택스", "https://www.hometax.go.kr/"),
    "계약이행보증보험증권": ("SGI서울보증", "https://www.sgic.co.kr/"),
}


def find_doc_name_spans(line: str) -> list[tuple[str, int, int]]:
    """서류명과 그 위치(시작·끝 오프셋)를 함께 낸다. 위치는 단계 판정이 "그 서류명 근처"만
    보게 하는 데 쓴다(resolve_doc_stage) — PDF/HWP 첨부는 줄바꿈이 없어 한 줄이 문서 전체일
    때가 있고, 그때는 위치 없이는 "근처"를 정의할 수 없다."""
    spans: list[tuple[str, int, int]] = []
    masked = line
    for label, pattern in DOC_NAME_PATTERNS:
        for match in re.finditer(pattern, masked):
            name = label or clean_text(match.group(0))
            if name:
                spans.append((name, match.start(), match.end()))
            masked = masked[: match.start()] + ("\x00" * (match.end() - match.start())) + masked[match.end() :]
    return spans


def find_doc_names(line: str) -> list[str]:
    names: list[str] = []
    for name, _start, _end in find_doc_name_spans(line):
        if name not in names:
            names.append(name)
    return names


def find_conditions(line: str) -> list[dict[str, str]]:
    conditions: list[dict[str, str]] = []
    negative = bool(CONDITION_NEGATIVE_RE.search(line))
    for key, label, pattern in CONDITION_AXES:
        if re.search(pattern, line):
            conditions.append({"key": key, "label": label, "negative": "1" if negative else ""})
    return conditions


def doc_extras(line: str) -> dict[str, str]:
    """서류 한 줄에 붙은 부가조건을 뽑는다. 없으면 빈 문자열이며 지어내지 않는다."""
    extras: dict[str, str] = {}
    if re.search(r"원본", line):
        extras["copy"] = "원본"
    elif re.search(r"사본", line):
        extras["copy"] = "사본"
    validity = re.search(r"(?:최근\s*)?(\d+\s*개월|공고일\s*이후|입찰\s*공고일\s*이후|계약\s*신청일로부터\s*\d+\s*개월)[^\n]{0,12}(?:이내\s*)?발급", line)
    if validity:
        extras["validity"] = clean_text(validity.group(0))
    method = re.search(r"온라인/직접제출|온라인제출|직접제출|우편|이메일|전자우편|방문", line)
    if method:
        extras["method"] = method.group(0)
    due = re.search(r"까지|이내", line)
    if due:
        # 기한 문구는 「입찰마감일시 전까지」처럼 공백을 포함한다. 종결어 앞 22자를 창으로
        # 잡고 구분자에서 잘라 마지막 조각만 쓴다.
        head = line[max(0, due.start() - 22) : due.end()]
        head = re.split(r"[,·)]\s*|\.\s+", head)[-1].strip()
        if re.search(r"마감|낙찰|계약|허가|개시|일시|\d", head):
            extras["due"] = clean_text(head)
    count = re.search(r"\d+\s*부(?![가-힣])", line)
    if count:
        extras["count"] = clean_text(count.group(0))
    return extras


LINE_RESET_RE = re.compile(r"^\s*(?:\d+\s*[.)]|[가-하]\s*\.|[IVX]+\s*\.)")
SUB_ITEM_RE = re.compile(r"^\s*(?:[-‐–▪·※○ㅇ①-⑮]|\(\d+\)|\d+\s*\))")


# 2026-10-19 · 표제·문장으로 단계를 못 정한(미분류) 서류에만 쓰는 보강 판정 둘. 확정된 판정은 덮지 않는다.
UNRESOLVED_STAGES = frozenset({"미분류", NEEDS_INQUIRY_STAGE})

# ⑴ 입찰 전 표지. 서류가 든 본 조항(표제 스택 가장 바깥 층의 한 조항) 안에 있을 때만 쓴다. 공고 전체에서
# 찾으면 안 된다 — 「입찰 마감」 문구는 온비드 툴팁 상용구라 원문 36건 전부에 있다(구현 계획 F2).
PREBID_MARKER_RES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("제출 기간", re.compile(r"제출\s*(?:기간|기한|일시)\s*[:：]?\s*(?:20\d\d|\d{1,2}\s*[./월])")),
    ("입찰 마감과 묶은 기한", re.compile(r"입찰\s*(?:서\s*)?(?:제출\s*)?마감\s*(?:일시|일|시간|시)?\s*(?:\([^)]{0,15}\)\s*)?(?:까지|전)")),
    ("입찰참가 등록·신청", re.compile(r"입찰\s*참가\s*(?:등록|신청)\s*(?:서류|기간|및|·|/)|참가\s*신청\s*(?:및|·|/)?\s*제안서")),
    ("입찰 제재", re.compile(r"입찰\s*시\s*무효|사전\s*판정에서\s*배제|입찰\s*참가\s*불승인")),
)
# 서류가 든 줄 자체가 입찰 뒤 시점을 말하면(「매각결정기일 전에 … 제출」) 같은 조항의 입찰 전 표지를 빌려 쓰지 않는다.
# 압류재산 공고 「16. 주의사항 · 다. 농지취득자격증명」이 같은 조항의 대리입찰 문장(「입찰마감 시간 전까지」)에 끌려
# 입찰 전이 된 것을 측정에서 확인했다(2026-10-19 · 5건 × 3종).
POST_BID_TIMING_RE = re.compile(r"매각\s*결정\s*기일|낙찰|계약\s*체결|잔금|소유권\s*이전|사용\s*허가\s*(?:신청|일)")
# ⑴-⒝ 는 입찰보증금 문맥이면 서류 기한이 아니다(「보증금은 입찰 마감 전까지 입금」).
PREBID_DEPOSIT_RE = re.compile(r"보증\s*(?:금|서|보험)")
PREBID_DEPOSIT_REACH = 40
# 한 줄짜리 첨부에서는 서류명 앞뒤로 본 조항 번호(「8. 」) 사이를 한 조항으로 보되, 이보다 길면 쓰지 않는다.
INLINE_BLOCK_MAX_CHARS = 1500


def prebid_marker_in(text: str) -> str:
    """입찰 전 표지가 있으면 그 이름, 없으면 빈 문자열."""
    for label, pattern in PREBID_MARKER_RES:
        for match in pattern.finditer(text):
            if label == "입찰 마감과 묶은 기한":
                near = text[max(0, match.start() - PREBID_DEPOSIT_REACH) : match.end() + PREBID_DEPOSIT_REACH]
                if PREBID_DEPOSIT_RE.search(near):
                    continue
            return label
    return ""


def inline_block_bounds(text: str, start: int, end: int) -> tuple[int, int] | None:
    """한 줄짜리 첨부에서 서류명이 든 본 조항(앞뒤 TOP_CLAUSE_MARK_RE 사이). 너무 길면 None."""
    lo = 0
    for match in TOP_CLAUSE_MARK_RE.finditer(text, max(0, start - INLINE_BLOCK_MAX_CHARS), start):
        lo = match.start()
    following = TOP_CLAUSE_MARK_RE.search(text, end, min(len(text), end + INLINE_BLOCK_MAX_CHARS))
    hi = following.start() if following else len(text)
    if hi - lo > INLINE_BLOCK_MAX_CHARS:
        return None
    return lo, hi


# ⑵ 온비드 준수규칙이 «입찰 마감 전 · 입찰기간 중» 제출을 정한 대리·공동·미성년 서류(구현 계획 3단계 · 검증
# team-reports/2026-10-19-bid-stage-sot/researcher-verify-sot-r1.md §2·H1~H3). 조문에 이름이 있는 서류만 넣었다.
# 이용기관(공유·기타일반) 공고는 넣지 않는다 — 최고가 입찰참가자 준수규칙 제6조 단서 「이용기관회원이 별도로 정하는
# 경우에는 그에 따릅니다」가 시점을 늦추는 것도 막지 않는다(H3).
SOT_PREBID_CONDITION_DOCS: dict[str, dict[str, frozenset[str]]] = {
    # 압류재산 인터넷공매 입찰참가자 준수규칙 제7조①②③ 「입찰 마감시간 전까지 … 공사에 제출」
    "압류재산": {
        "joint": frozenset({"공동입찰참가신청서", "인감증명서", "본인서명사실확인서"}),
        "proxy": frozenset({"대리입찰신청서", "인감증명서", "본인서명사실확인서"}),
        "minor": frozenset({"미성년자 입찰참가 동의서", "인감증명서", "본인서명사실확인서", "주민등록등본", "가족관계증명서"}),
    },
    # 국유재산 준수규칙 제7조①②③ 「입찰기간 중에」. 미성년 서류는 기본증명서(특정)라 가족관계증명서·등본을 넣지 않는다.
    "국유재산": {
        "joint": frozenset({"공동입찰참가신청서", "위임장", "인감증명서", "본인서명사실확인서"}),
        "proxy": frozenset({"대리입찰신청서", "위임장", "인감증명서", "본인서명사실확인서"}),
        "minor": frozenset({"미성년자 입찰참가 동의서", "인감증명서", "본인서명사실확인서"}),
    },
    # 수탁재산 준수규칙 제5조② 「입찰기간 중에 … 공동입찰신청서 … 또는 대리입찰신청서」(첨부 인감증명). 미성년 조항 없음.
    "수탁재산": {
        "joint": frozenset({"공동입찰참가신청서", "위임장", "인감증명서"}),
        "proxy": frozenset({"대리입찰신청서", "위임장", "인감증명서"}),
    },
}
SOT_PREBID_SOURCE = {
    "압류재산": "온비드 압류재산 입찰참가자 준수규칙 제7조(입찰 마감시간 전까지 제출)",
    "국유재산": "온비드 국유재산 입찰참가자 준수규칙 제7조(입찰기간 중 제출)",
    "수탁재산": "온비드 수탁재산 입찰참가자 준수규칙 제5조(입찰기간 중 제출)",
}


def sot_prebid_source(asset_type: str, name: str, condition_keys: set[str]) -> str:
    """대리·공동·미성년 문맥에 묶인 서류를 준수규칙으로 「입찰 전」 확정할 수 있으면 그 근거 문구."""
    table = SOT_PREBID_CONDITION_DOCS.get(asset_type.strip())
    if not table:
        return ""
    for key in ("joint", "proxy", "minor"):
        if key in condition_keys and name in table.get(key, frozenset()):
            return SOT_PREBID_SOURCE[asset_type.strip()]
    return ""


def extract_doc_items(
    sections: dict[str, str],
    attachment_chunks: list[tuple[str, str]] | None = None,
    asset_type: str = "",
) -> list[dict[str, object]]:
    """공고문·제출서류 절과 첨부 텍스트에서 조건별 서류 항목을 뽑는다.

    한 줄이 조건 문구만 담고 서류명이 없으면 그 조건을 다음 하위 항목들에 물려준다.
    새 상위 번호(1. / 가.)가 조건 없이 나오면 물림을 끊는다.
    첨부는 label 이 DOC_SEARCH_SECTIONS 밖의 값("첨부:파일명")이라 sourceSection 으로
    본문/첨부 출처를 구분할 수 있다.
    """
    items: list[dict[str, object]] = []
    # 값은 (items 안의 위치, 그 단계가 조항 표제로 확정됐는가). 같은 서류명이 같은 문서
    # 안에 단계가 다른 두 자리에서 나올 수 있다(표본 20 「신분증」). 2026-10-19 전까지는 주석과 달리 먼저 나온
    # 쪽만 남았다(리뷰 r1 F7). 지금은 앞이 미분류면 뒤의 확정 판정으로 바꾸고, 둘 다 확정이면 둘 다 남긴다(아래 key 분기).
    seen: dict[tuple[str, str], tuple[int, bool]] = {}
    # 같은 (서류명, 조건)이 단계를 달리해 두 번 남을 때 같은 단계가 세 번째로 쌓이지 않게 막는다.
    seen_stage: set[tuple[str, str, str]] = set()
    chunks = [(title, sections.get(title, "")) for title in DOC_SEARCH_SECTIONS]
    chunks.extend(attachment_chunks or [])
    for title, chunk in chunks:
        if not chunk:
            continue
        # 첨부는 온비드 공고 절과 문장 구조가 다르다(표·서식·PDF 텍스트화 결과라 「제출」·「지참」
        # 같은 동사가 그 줄에 없을 때가 많다). DOC_REQUEST_RE 게이트를 그대로 걸면 실측
        # 재현율이 어휘 그대로 매칭한 것보다 낮아진다(2026-09-12 측정 · 배선 38% vs 첨부모의 59%).
        # 그래서 2026-09-12 부터 첨부 줄은 서류명이 잡히면 그 자체로 요구로 봤다. 2026-10-19 부터는 첨부에도
        # 게이트를 다시 걸되, 제출 목록 절 안의 나열 항목(in_submission_list)을 요구로 인정해 그 재현율을 지킨다.
        # 검사 생략이 「등기사항증명서 참조」 같은 언급을 목록에 올렸기 때문이다(원문 36건 측정 · 언급 6건).
        is_attachment = title not in DOC_SEARCH_SECTIONS
        carried: list[dict[str, str]] = []
        # 「라. 계약체결시 필요서류」처럼 단계를 밝히는 줄은 제목뿐이고, 그 아래 표 행(「개인
        # 주민등록초본, 인감증명서…」)에는 단계 단어가 없다. 조건 물림과 같은 구조라 같은
        # 방식으로 물린다 — 표제 문자열 자체를 들고 가서 HEADING_STAGE_RULES 와 대조한다
        # (resolve_doc_stage). 안 물리면 표 아래 항목의 단계를 알 길이 없다(2026-09-12 · #15 실측).
        current_heading = ""
        heading_stack: list[tuple[str, str]] = []
        # 「※ 낙찰자의 계약체결 전 제출서류」 아래 번호 목록(is_note_heading · continues_note_scope).
        # 그 목록의 「1.」이 번호 층을 새로 열어 표제 스택에서 앞 표제를 걷어내므로, 표제 스택과 따로 든다.
        note_scope: dict[str, object] | None = None
        # 제출 목록 안내 줄(SUBMISSION_LIST_HEADING_RE · 서류명 없음)을 지나왔는가.
        submission_cue = False
        # 단계 판정 창(doc_stage_at)은 줄바꿈이 실제로 있는 공고문에서도 "그 줄 하나"가 아니라
        # «전체 절 텍스트 안에서의 실제 위치»를 기준으로 본다 — 결정적 문구가 서류명과 같은
        # 줄이 아니라 몇 줄 뒤(예: 「ㅇ 공동입찰의 경우…」 다음에 번호 목록, 그 뒤에야 「입찰
        # 기간 마감일까지 제출」)에 있는 경우가 실제로 있다(표본 04~08). 그래서 `full_text` 와
        # 그 안에서의 절대 오프셋을 들고 간다. 창은 LINE_RESET_RE 조항 경계를 넘지 않게
        # section_bounds() 로 자른다 — 안 자르면 다음 조항의 결정적 문구를 빌려 쓰게 된다.
        full_text = block_text(strip_tooltips(chunk))
        heading_boundaries: list[int] = []
        heading_marks: list[tuple[int, str]] = []
        # heading_stack 과 같은 규칙으로 쌓는 (층, 표제 줄 위치). parent_block 이 조항 범위를 자르는 데 쓴다.
        pos_stack: list[tuple[str, int]] = []
        _cursor = 0
        for _raw in full_text.split("\n"):
            _stripped = _raw.strip()
            if _stripped and LINE_RESET_RE.match(_stripped):
                heading_boundaries.append(_cursor + (len(_raw) - len(_raw.lstrip())))
            if _stripped and HEADING_LINE_RE.match(_stripped):
                heading_marks.append((_cursor + (len(_raw) - len(_raw.lstrip())), heading_kind(_stripped)))
            _cursor += len(_raw) + 1

        def parent_block(pos: int, line_is_heading: bool) -> str:
            """서류가 든 줄의 바로 위 조항(그 표제 줄부터 같은 층이나 바깥 층의 다음 표제 전까지)의 글.

            처음에는 가장 바깥 층 조항을 봤는데, 압류재산 공고에서 「1. 입찰방법」 안의 「입찰 마감시간 전까지」가
            같은 조항 아래 「다. 농지취득자격증명(매각결정기일 전)」까지 입찰 전으로 끌고 갔다(2026-10-19 측정 · 5건 × 3종).
            그래서 바로 위 조항으로 좁힌다. 서류 줄 자체가 목록 표제(「3) 제출서류: …」)면 그 위 조항을 본다.
            """
            parents = pos_stack[:-1] if line_is_heading else pos_stack
            if not parents:
                return ""
            kind, offset = parents[-1]
            enclosing = {k for k, _off in parents}
            end_bound = next((off for off, k in heading_marks if off > pos and k in enclosing), len(full_text))
            return full_text[offset:end_bound]

        def section_bounds(pos: int) -> tuple[int, int]:
            start_bound = 0
            end_bound = len(full_text)
            for boundary in heading_boundaries:
                if boundary <= pos:
                    start_bound = boundary
                else:
                    end_bound = boundary
                    break
            return start_bound, end_bound

        cursor = 0
        for raw_line in full_text.split("\n"):
            line = raw_line.strip()
            lstrip_len = len(raw_line) - len(raw_line.lstrip())
            line_offset = cursor + lstrip_len
            cursor += len(raw_line) + 1
            # 1200자 상한은 «지저분한 HTML»을 걸러내려는 것이다(공고 절 기준). PDF/HWP 첨부는
            # 줄바꿈 없이 문서 전체가 한 줄로 텍스트화될 때가 있어(실측 최대 89,290자) 상한을
            # 그대로 걸면 그 안의 서류명이 통째로 빠진다(2026-09-12 · 32건 실측). 첨부는 상한을 안 건다.
            if not line or (len(line) > 1200 and not is_attachment):
                continue
            # 조항 표제는 이름 유무와 무관하게 먼저 캡처한다 — 표제 줄 자체에 서류명이 실리는
            # 경우는 없지만, 캡처를 이름 분기 뒤로 미루면 그 표제가 적용되는 첫 항목을 놓친다.
            if note_scope is not None and not continues_note_scope(note_scope, line):
                note_scope = None
            if is_note_heading(line):
                note_scope = {"heading": line, "kind": "", "num": -1}
                current_heading = line
            elif HEADING_LINE_RE.match(line):
                push_heading(heading_stack, line)
                line_kind = heading_kind(line)
                for index, (existing_kind, _offset) in enumerate(pos_stack):
                    if existing_kind == line_kind:
                        del pos_stack[index:]
                        break
                pos_stack.append((line_kind, line_offset))
                # 바깥 표제를 물려받는 것은 짧은 소제목(서류명 없음 · 「가. 입찰 참가 신청」)이나 번호 바로 뒤에
                # 서류명이 오는 목록 항목일 때만이다. 「가. 입찰 시 유의사항 … 사업자등록증」 같은 문단이나 긴 줄이
                # 물려받으면 쪽 전체가 낙찰 후로 끌려간다(리뷰 r1 T5). 그 밖은 옛 동작(그 줄 자체가 표제)이다.
                if can_inherit_outer_heading(line):
                    current_heading = stage_heading_from_stack(heading_stack)
                    if (
                        current_heading != line
                        and resolve_doc_stage(current_heading, "") == "낙찰 후·계약 시"
                        and PREBID_WORD_RE.search(line)
                    ):
                        current_heading = line
                else:
                    current_heading = line
            elif not find_doc_name_spans(line) and any(pattern.search(line) for pattern, _ in SENTENCE_STAGE_RULES):
                # 번호 없는 문단(※ 등)이 단계를 밝히면 그 아래 목록은 앞 표제를 물려받지 않는다. 충돌 검사 창은
                # 조항 경계(「1)」 줄)에서 시작해 위 문단을 못 본다(리뷰 r1 T2 · 「※ 입찰 참가 시에는 … 입찰 마감일까지 제출」).
                heading_stack.clear()
                pos_stack.clear()
                current_heading = ""
            if note_scope is not None:
                current_heading = str(note_scope["heading"])
            # 다음 줄부터의 제출 목록 안내(submission_cue)를 이 줄 판정 «뒤»에 바꾸려고 값을 먼저 잡아 둔다.
            cue_before = submission_cue
            if not find_doc_name_spans(line):
                if len(line) <= SUBMISSION_CUE_MAX_CHARS and SUBMISSION_LIST_HEADING_RE.search(line):
                    submission_cue = True
                elif LIST_HEAD_RE.match(line):
                    submission_cue = False
            conditions = [item for item in find_conditions(line) if not item["negative"]]
            name_spans = find_doc_name_spans(line)
            names: list[str] = []
            first_span: dict[str, tuple[int, int]] = {}
            for name, start, end in name_spans:
                if name not in first_span:
                    first_span[name] = (start, end)
                    names.append(name)
            if not names:
                if conditions and DOC_REQUEST_RE.search(line):
                    carried = conditions
                elif LINE_RESET_RE.match(line):
                    carried = []
                continue
            carried_applies = bool(carried) and bool(SUB_ITEM_RE.match(line))
            # 첨부는 조건 물림 구조(번호·하위항목 서식)가 공고 절과 다르게 깨져 있어, 조건을
            # 잘못 붙이면(엉뚱한 줄의 「법인」이 따라붙는 등) 맞는 항목을 조건 불일치로 놓친다.
            # 조건 없이 "공통"으로 두는 편이 실측상 더 맞다(2026-09-12 · 배선 47%→59%로 상승 확인).
            active = [] if is_attachment else (conditions or (carried if carried_applies else []))
            # 「업종·자격 요건」 축은 `등록증`·`면허` 같은 서류명 토큰으로 잡히므로
            # 그것만으로 제출 요구를 증명하지 못한다. authorizing 축에서 뺀다.
            authorizing = [item for item in conditions if item["key"] != "license"]
            # 제출 목록 절(「10. 낙찰(예정)자 제출서류」) 안의 짧은 나열 항목은 동사가 없어도 요구다.
            in_submission_list = len(line) <= SUBMISSION_LIST_ITEM_MAX_CHARS and (
                any(SUBMISSION_LIST_HEADING_RE.search(heading) for _kind, heading in heading_stack)
                or bool(note_scope and SUBMISSION_LIST_HEADING_RE.search(note_scope["heading"]))
                or cue_before
            )
            line_requested = doc_request_in(line)
            if is_attachment and not line_requested and len(line) <= 1200:
                para_lo, para_hi = paragraph_bounds(full_text, line_offset, line_offset + len(line))
                line_requested = doc_request_in(full_text[para_lo:para_hi])
            # 줄바꿈 없이 문서 전체가 한 줄인 첨부는 줄 단위로 보면 어디엔가 「제출」이 있어 언제나 통과한다.
            # 그런 줄은 아래에서 서류명마다 그 조항 구간(doc_clause_bounds)만 보고 따로 판정한다.
            long_line = len(line) > 1200
            if (
                not long_line
                and not authorizing
                and not carried_applies
                and not in_submission_list
                and not line_requested
            ):
                # 조건 문맥도 제출 동사도 제출 목록 절도 없으면 단순 언급이다(예: 「부동산의 표시는
                # 등기사항증명서 기준」 · 첨부의 「등기사항증명서 참조」). 2026-10-19 부터 첨부에도 건다.
                continue
            extras = doc_extras(line)
            labels = [item["label"] for item in active] or ["공통"]
            for name in names:
                # 🔴 추측으로 입찰 전/낙찰 후 어느 한쪽에 밀어 넣지 않는다. 뒤집지 말 것.
                # 화면은 이 값으로 서류를 2단계(입찰 전 준비)와 4단계(낙찰 후 준비)에 물리적으로
                # 나눠 담는다(app.js isPostAwardDoc). doc_stage_at 가 조항 표제·결정적 문구
                # 어느 쪽으로도 못 정하면 "미분류" — 그 서류명 «바로 근처»만 보고 판정하므로
                # 멀리 떨어진 말에 더 이상 오염되지 않는다. PDF/HWP 첨부는 줄바꿈이 없어 한
                # 줄이 문서 전체일 수 있어, 이름마다 그 위치 기준으로 따로 판정한다
                # (team-reports/2026-10-18-bid-doc-timeline/stage-classification-design.md §0·§3).
                start, end = first_span[name]
                if doc_is_mention_only(line, end):
                    continue
                if long_line:
                    clause_lo, clause_hi = doc_clause_bounds(line, start, end)
                    clause = line[clause_lo:clause_hi]
                    clause_authorizing = [
                        item for item in find_conditions(clause) if not item["negative"] and item["key"] != "license"
                    ]
                    if (
                        not clause_authorizing
                        and not doc_request_in(clause)
                        and not under_submission_heading_inline(line, start)
                    ):
                        continue
                start_global, end_global = line_offset + start, line_offset + end
                stage, _confident, source_heading = doc_stage_at(
                    full_text,
                    start_global,
                    end_global,
                    current_heading,
                    section_bounds(start_global),
                    name,
                    inherited=bool(heading_stack) and current_heading != heading_stack[-1][1],
                )
                if stage in UNRESOLVED_STAGES:
                    # 표제·문장으로 못 정했으면 ① 준수규칙(대리·공동·미성년 문맥) ② 같은 본 조항 안의 입찰 전 표지 순으로 본다.
                    # 둘 다 「입찰 전」으로만 확정한다 — 낙찰 후로 보내는 보강 판정은 두지 않는다(구현 계획 D1).
                    # 조건은 판정에만 쓴다. 첨부의 화면 조건 라벨(active)은 지금처럼 비운다(위 47%→59% 주석).
                    decision_conditions = clause_authorizing if long_line else conditions
                    decision_keys = {item["key"] for item in decision_conditions}
                    if carried_applies:
                        decision_keys |= {item["key"] for item in carried}
                    sot_source = sot_prebid_source(asset_type, name, decision_keys)
                    if long_line:
                        bounds = inline_block_bounds(line, start, end)
                        block = line[bounds[0] : bounds[1]] if bounds else ""
                    else:
                        block = parent_block(start_global, bool(HEADING_LINE_RE.match(line)))
                    own_text = clause if long_line else line
                    marker = "" if sot_source or POST_BID_TIMING_RE.search(own_text) else prebid_marker_in(block)
                    if sot_source:
                        stage, _confident, source_heading = "입찰 전", True, sot_source
                    elif marker:
                        stage, _confident, source_heading = "입찰 전", True, f"같은 조항의 입찰 전 표지: {marker}"
                key = (name, " · ".join(labels))
                howto, howto_url = DOC_HOWTO.get(name, ("", ""))
                item = {
                    "name": name,
                    "conditions": labels,
                    "conditionKeys": [item["key"] for item in active],
                    "copy": extras.get("copy", ""),
                    "validity": extras.get("validity", ""),
                    "method": extras.get("method", ""),
                    "due": extras.get("due", ""),
                    "count": extras.get("count", ""),
                    "stage": stage,
                    "sourceHeading": source_heading,
                    "howto": howto,
                    "howtoUrl": howto_url,
                    "sourceSection": title,
                    "evidence": line[:300],
                }
                if key in seen:
                    # 같은 서류가 다시 나왔다. 앞이 미분류였고 이번에 단계가 정해졌으면 이번 것으로 바꾼다.
                    # 둘 다 정해졌는데 단계가 다르면 둘 다 남긴다 — 같은 서류를 입찰 전에 한 번(사본 · 자격 확인),
                    # 계약 때 또 내는 공고가 있다(강남터미널 광고의 사업자등록증). 앞의 확정 판정은 덮지 않는다.
                    # 한 줄짜리 첨부(long_line)의 판정은 조항 경계가 흐려 둘째 항목을 더하지 않는다(인천공항 제안요청서 · 측정 중 확인).
                    at, _was_confident = seen[key]
                    if items[at]["stage"] in UNRESOLVED_STAGES and stage not in UNRESOLVED_STAGES:
                        items[at] = item
                        seen[key] = (at, _confident)
                    elif (
                        not long_line
                        and items[at]["stage"] not in UNRESOLVED_STAGES
                        and stage not in UNRESOLVED_STAGES
                        and stage != items[at]["stage"]
                        and (name, key[1], stage) not in seen_stage
                    ):
                        seen_stage.add((name, key[1], stage))
                        items.append(item)
                    continue
                seen[key] = (len(items), _confident)
                seen_stage.add((name, key[1], stage))
                items.append(item)
    link_form_attachment_stages(items)
    return items


# 첨부 서식 파일(「붙임 3. 입주신청서_및_심의자료_서식.hwp」) 끝의 「첨부 ː 1. 사업계획서 …」 목록은 그 서식과 함께 낸다.
# 본문이 그 서식(「다. 입주신청서 1부」)의 시점을 정했으면 서식의 첨부 서류도 같은 시점이다(판교 · 수원 공고).
# 파일 이름에 서식·양식·신청서가 있고, 그 이름 속 서류명이 본문에서 단계가 정해진 항목일 때만 잇는다.
FORM_FILE_RE = re.compile(r"서식|양식|신청서")


def link_form_attachment_stages(items: list[dict[str, object]]) -> None:
    body_stage: dict[str, str] = {}
    for item in items:
        if item["sourceSection"] in DOC_SEARCH_SECTIONS and item["stage"] not in UNRESOLVED_STAGES:
            body_stage.setdefault(str(item["name"]), str(item["stage"]))
    for item in items:
        section = str(item["sourceSection"])
        if item["stage"] not in UNRESOLVED_STAGES or section in DOC_SEARCH_SECTIONS:
            continue
        file_name = section.split(":", 1)[-1]
        if not FORM_FILE_RE.search(file_name):
            continue
        for form_name in find_doc_names(file_name):
            if form_name != item["name"] and form_name in body_stage:
                item["stage"] = body_stage[form_name]
                item["sourceHeading"] = f"첨부 서식 「{form_name}」에 딸린 서류 · 본문 「{form_name}」 항목과 같은 시점"
                break


# 온비드 「제출서류」 표의 서류명 칸이 구분명 그대로이거나 「공고문 확인」이면
# 실제 서류명이 아니다. 표본 15건 전건이 여기에 해당했다(§4-1).
GENERIC_DOC_NAME_RE = re.compile(r"^(?:-|공고문\s*확인)$|서류$|\(공고문\s*확인\)$")


def extract_docs_table(sections: dict[str, str]) -> list[dict[str, object]]:
    chunk = sections.get("제출서류", "")
    if not chunk:
        return []
    rows: list[dict[str, object]] = []
    seen: set[tuple[str, ...]] = set()
    for table in re.findall(r"<table\b.*?</table>", chunk, flags=re.I | re.S):
        for row in re.findall(r"<tr\b.*?</tr>", table, flags=re.I | re.S):
            cells = [clean_text(cell) for cell in re.findall(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", row, flags=re.I | re.S)]
            cells = [cell for cell in cells if cell]
            if len(cells) < 2 or cells[0] == "구분":
                continue
            key = tuple(cells[:4])
            if key in seen:
                continue
            seen.add(key)
            name = cells[1]
            rows.append(
                {
                    "category": cells[0],
                    "name": name,
                    "due": cells[2] if len(cells) > 2 else "",
                    "method": cells[3] if len(cells) > 3 else "",
                    "generic": bool(name == cells[0] or GENERIC_DOC_NAME_RE.search(name)),
                }
            )
    return rows


def build_doc_checklist(
    sections: dict[str, str],
    asset_type: str,
    attachments: list[dict[str, str]],
    attachment_chunks: list[tuple[str, str]] | None = None,
    contact: str = "",
    attachment_reads: list[dict[str, str]] | None = None,
) -> dict[str, object]:
    profile = doc_source_profile(asset_type)
    items = extract_doc_items(sections, attachment_chunks, asset_type)
    table_rows = extract_docs_table(sections)
    generic_only = bool(table_rows) and all(row["generic"] for row in table_rows)

    groups: dict[str, dict[str, object]] = {}
    for item in items:
        label = " · ".join(item["conditions"])
        group = groups.setdefault(label, {"condition": label, "items": []})
        group["items"].append(item)

    if items:
        status = "extracted"
        # 서류 출처가 본문뿐인지 첨부까지 갔는지에 따라 문구를 갈라, 「공고 원문에서」라고
        # 실제로 안 읽은 곳까지 읽은 것처럼 말하지 않는다.
        from_body = any(item["sourceSection"] in DOC_SEARCH_SECTIONS for item in items)
        from_attachment = any(item["sourceSection"] not in DOC_SEARCH_SECTIONS for item in items)
        if from_body and from_attachment:
            source_label = "공고 원문과 첨부 파일에서"
        elif from_attachment:
            source_label = "첨부 파일에서"
        else:
            source_label = "공고 원문에서"
        headline = f"{source_label} 서류 {len(items)}건을 찾았습니다. 참고해서 준비하십시오."
    elif profile["code"] == "C":
        status = "not_in_notice"
        if attachments:
            # 이 공고에 대해 «관측한 것»만 말한다. 우리가 읽은 것은 본문뿐이고 첨부는 열지
            # 않았으므로 「원문에 없다」고 하지 않는다. 첨부가 화면에 렌더되므로 그 존재는
            # 말한다 — 말하지 않으면 「없다」와 눈앞의 첨부가 어긋난다.
            # 표본 수치로 이 공고의 첨부를 예측하지 않는다. 유형 수준의 사례 진술은
            # profile["detail"] 이 이미 맡는다.
            headline = f"본문에서 서류 목록을 찾지 못했습니다. 첨부 {len(attachments)}건이 있습니다."
        else:
            headline = "이 공고에서는 서류 목록을 찾지 못했습니다."
    elif attachments:
        status = "attachment_only"
        headline = "본문에서 서류 목록을 찾지 못했습니다. 첨부 공고문을 확인하십시오."
    else:
        status = "not_found"
        headline = "이 공고에서는 서류 목록을 찾지 못했습니다."

    notes: list[str] = []
    # 전건 generic 뿐 아니라 «섞인» 표에도 경고가 필요하다. 섞이면 실서류명 몇 줄 때문에
    # 나머지 구분명 줄까지 실제 서류명으로 읽힌다.
    generic_mixed = bool(table_rows) and any(row.get("generic") for row in table_rows)
    if generic_mixed:
        notes.append(
            "온비드 제출서류 표의 서류명 칸은 구분명(예: 공동입찰서류)이라 실제 준비할 서류명이 아닙니다."
        )
    if status == "extracted":
        # 부분 추출을 완전한 것처럼 말하지 않는다. 추출은 닫힌 어휘 기준이라 그 밖은 못 뽑는다.
        notes.append(
            "자동 인식은 닫힌 어휘 기준이라 인식 범위가 한정적입니다. 목록에 없는 서류가 있을 수 "
            "있으니 원문과 대조하십시오."
        )
    if status != "extracted":
        notes.append("자동 추출이 목록을 만들지 못한 상태입니다. 준비 보드는 그대로 진행할 수 있습니다.")
    if profile["code"] == "B" and status == "extracted":
        notes.append("이 재산유형은 첨부 공고문에 목록이 더 있을 수 있습니다. 첨부도 함께 확인하십시오.")
    notes.append("서류마다 제출기한이 다를 수 있습니다. 각 항목의 기한을 따로 확인하십시오.")

    return {
        "status": status,
        "headline": headline,
        "profile": profile,
        "items": items,
        "groups": list(groups.values()),
        "tableRows": table_rows,
        "tableGenericOnly": generic_only,
        "notes": notes,
        "reference": "이 목록은 참고용입니다. 빠진 항목이 있어도 진행은 막지 않으며, 최종 확인은 온비드 원문과 담당기관 기준입니다.",
        # "별도 문의 필요" 서류(NO_GENERAL_BASIS_DOC_NAMES) 화면 안내에 쓴다 — 이미 build_notice
        # 가 추출해 둔 담당부점/공고기관 값을 그대로 물려받는다. 못 찾았으면 빈 문자열이고,
        # 화면은 빈 값일 때 "공고 원문에서 확인" 같은 대체 문구를 쓴다(app.js).
        "contact": contact,
        # 첨부별 읽기 결과(attachment_doc_reads). 화면은 read 가 아닌 것이 있으면 「첨부 N개를 읽지 못했습니다」를 보인다.
        # None 이면 첨부를 읽으려 하지 않은 호출(테스트 · 첨부 없음)이라 빈 목록으로 둔다.
        "attachmentReads": list(attachment_reads or []),
        "attachmentUnread": sum(1 for read in (attachment_reads or []) if read.get("status") != "read"),
    }


# 첨부 앵커는 devUtil.fn_chkPdfRead('<atchFileLstNo>','<atchSn>','<pdfCnvsPrgnStatCd>',
# '<physFileNm>','<hashCrpsNo>') 로 고정이고, 다운로드는 로그인 없이 200을 준다.
# 표본 26/26 성공(docs/90_MVP개발/07_제출서류_표본조사_20260907.md §4·부록 A).
ATTACHMENT_DOWNLOAD_PATH = "/op/cm/syc/filemng/filemngprcs/FileMngPrcsController/dnldFile.do"
ATTACHMENT_ANCHOR_RE = re.compile(
    r"<a\b[^>]*fn_chkPdfRead\(\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*\)[^>]*>(.*?)</a>",
    re.I | re.S,
)


def extract_related_docs(text: str, base_url: str = "https://www.onbid.co.kr") -> list[dict[str, str]]:
    docs: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for match in ATTACHMENT_ANCHOR_RE.finditer(text):
        file_list_no, file_sn, _pdf_state, phys_file_nm, hash_no, inner = match.groups()
        key = (file_list_no, file_sn)
        if not file_list_no or not hash_no or key in seen:
            continue
        seen.add(key)
        name_match = re.search(r"<span[^>]*class=(?:\"[^\"]*\btxt01\b[^\"]*\"|'[^']*\btxt01\b[^']*')[^>]*>(.*?)</span>", inner, flags=re.I | re.S)
        name = clean_text(name_match.group(1)) if name_match else clean_text(inner)
        if not name:
            name = phys_file_nm
        docs.append(
            {
                "name": name,
                "downloadUrl": make_onbid_url(
                    base_url,
                    ATTACHMENT_DOWNLOAD_PATH,
                    {"atchFileLstNo": file_list_no, "atchSn": file_sn, "hashCrpsNo": hash_no},
                ),
            }
        )
    return docs


# 첨부(PDF·HWP·HWPX) 파싱은 별도 venv 의 python 으로 subprocess 격리 호출한다 — 서버는
# 시스템 python3.9(표준 라이브러리만)라 pdfminer·pypdf·pyhwp 를 못 들인다(src/attachment_parser.py 주석 참고).
ATTACHMENT_PARSER_SCRIPT = Path(__file__).resolve().parent / "attachment_parser.py"
ATTACHMENT_PARSER_PYTHON = os.environ.get(
    "OPADA_ATTACHMENT_PYTHON", str(Path.home() / "Documents/Dev/.opada-venv/bin/python")
)
ATTACHMENT_MAX_BYTES = 8 * 1024 * 1024  # 대용량 스캔본 PDF도 받되 요청 지연을 막는 상한
ATTACHMENT_MAX_COUNT = 4  # 요청 1건당 파싱할 첨부 개수 상한 — 지연시간 보호


def fetch_attachment_bytes(url: str) -> bytes:
    validate_onbid_url(url)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) OnBidDocAgentMVP/0.1"},
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return response.read(ATTACHMENT_MAX_BYTES + 1)


def attachment_text(data: bytes) -> str:
    """첨부 바이트를 별도 venv subprocess 로 텍스트화한다. venv 가 없거나 실패하면 빈 문자열 —
    첨부 하나의 실패가 분석 전체를 막지 않는다(build_doc_checklist 는 본문만으로도 동작)."""
    if not data or not Path(ATTACHMENT_PARSER_PYTHON).exists():
        return ""
    try:
        result = subprocess.run(
            [ATTACHMENT_PARSER_PYTHON, str(ATTACHMENT_PARSER_SCRIPT)],
            input=data,
            capture_output=True,
            timeout=30,
        )
    except Exception:  # noqa: BLE001 — subprocess 환경 문제까지 포함해 요청 전체를 막지 않는다
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.decode("utf-8", errors="replace")


# 첨부를 읽는 순서(2026-10-19 · 구현 계획 D2). 개수 상한(ATTACHMENT_MAX_COUNT)은 그대로 두고, 서류 목록이 있을
# 만한 파일을 앞에 둔다. 원문 36건에서 감정평가서가 4자리 중 첫 자리를 차지하고(예술의전당), 변경 공지사항 9개가
# 뒤로 밀려 열리지 않았다(인천공항). 같은 순위 안에서는 온비드 목록 순서를 지킨다.
ATTACHMENT_DEFER_RE = re.compile(r"감정\s*평가|도면|평면도|위치도|지적도|등기부|등기사항|건축물\s*대장|사진|쉽게\s*풀어")
ATTACHMENT_PRIORITY_RE = re.compile(r"공고|제안\s*요청서|현장\s*설명|공지|서식|양식|조건|유의\s*사항|신청서")


def attachment_read_order(attachments: list[dict[str, str]]) -> list[dict[str, str]]:
    def rank(doc: dict[str, str]) -> int:
        name = str(doc.get("name", ""))
        if ATTACHMENT_DEFER_RE.search(name):
            return 2
        return 0 if ATTACHMENT_PRIORITY_RE.search(name) else 1

    return sorted(attachments, key=rank)


def attachment_doc_reads(
    attachments: list[dict[str, str]],
) -> tuple[list[tuple[str, str]], list[dict[str, str]]]:
    """첨부를 읽는 순서대로 내려받아 텍스트화하고, (label, text) 쌍과 첨부별 읽기 결과를 함께 낸다.

    읽기 결과(status): read · not_tried(개수 상한) · too_large(크기 상한) · failed(다운로드 실패 · 빈 텍스트 · 파싱 실패).
    지금까지는 실패를 조용히 건너뛰어, 화면이 첨부를 다 읽은 것처럼 보였다(원문 36건 중 18건이 일부를 못 읽음).
    """
    chunks: list[tuple[str, str]] = []
    reads: list[dict[str, str]] = []
    for position, doc in enumerate(attachment_read_order(attachments)):
        name = str(doc.get("name", ""))
        url = doc.get("downloadUrl", "")
        if position >= ATTACHMENT_MAX_COUNT:
            reads.append({"name": name, "status": "not_tried"})
            continue
        if not url:
            reads.append({"name": name, "status": "failed"})
            continue
        try:
            data = fetch_attachment_bytes(url)
        except Exception:  # noqa: BLE001 — 첨부 하나 다운로드 실패가 전체를 막지 않는다
            reads.append({"name": name, "status": "failed"})
            continue
        if data and len(data) > ATTACHMENT_MAX_BYTES:
            reads.append({"name": name, "status": "too_large"})
            continue
        text = attachment_text(data) if data else ""
        if text.strip():
            chunks.append((f"첨부:{name}", text))
            reads.append({"name": name, "status": "read"})
        else:
            reads.append({"name": name, "status": "failed"})
    return chunks, reads


def attachment_doc_chunks(attachments: list[dict[str, str]]) -> list[tuple[str, str]]:
    """첨부 목록을 내려받아 텍스트화하고, extract_doc_items 가 쓸 (label, text) 쌍으로 낸다."""
    return attachment_doc_reads(attachments)[0]


# 공고문 절을 번호 제목 단위로 잘라 목차를 만든다. 첨부 파일(PDF·HWP) 내부는 열지 않는다.
NOTICE_OUTLINE_RE = re.compile(r"^\s*(?:\d{1,2}\s*[.)]|[가-하]\s*\.|[■●▣]|\d{1,2}\s*장)\s*(\S[^\n]{0,60})$")
# 「가. …합니다.」처럼 서술로 끝나는 줄은 목차 제목이 아니라 본문이다.
OUTLINE_SENTENCE_RE = re.compile(r"(?:니다|하세요|바랍니다|있음|없음)\s*\.?$")
# 물건상세의 공고문 절에는 첨부 목록이 「1. 공고문.hwp」 꼴로 함께 들어온다. 목차가 아니다.
OUTLINE_FILENAME_RE = re.compile(r"\.(?:hwpx?|pdf|zip|jpe?g|png|docx?|xlsx?)\s*$", re.I)


def extract_notice_outline(sections: dict[str, str]) -> list[dict[str, str]]:
    chunk = sections.get("공고문", "")
    if not chunk:
        return []
    outline: list[dict[str, str]] = []
    seen: set[str] = set()
    lines = [line.strip() for line in block_text(strip_tooltips(chunk)).split("\n") if line.strip()]
    for index, line in enumerate(lines):
        match = NOTICE_OUTLINE_RE.match(line)
        if not match or OUTLINE_SENTENCE_RE.search(line) or OUTLINE_FILENAME_RE.search(line):
            continue
        title = clean_text(line)[:80]
        if title in seen:
            continue
        seen.add(title)
        body = ""
        for follow in lines[index + 1 : index + 3]:
            if NOTICE_OUTLINE_RE.match(follow) or OUTLINE_FILENAME_RE.search(follow):
                break
            body = f"{body} {follow}".strip()
        outline.append({"title": title, "body": clean_text(body)[:220]})
        if len(outline) >= 20:
            break
    return outline


def deposit_basis_note(deposit: str, minimum_bid_display: str) -> str:
    """입찰보증금 원문 표시값이 무엇을 기준으로 계산되는지에 맞춰 note 를 고른다.

    🔴 기준은 재산유형마다 다르다. 압류재산만 공매예정가격(최저입찰가) 기준이고, 국유·수탁·
    이용기관 물건은 «입찰금액» 기준이다(온비드 준수규칙 — 압류 제8조① · 국유 제8조① · 수탁
    제6조① · 최고가 제8조①). 옛 note 는 원문이 「입찰금액 X 5%」인데도 「기준이 되는
    최저입찰가격은 …」이라고 붙여 기준을 잘못 안내했다(2026-10-19 정합성 대조).
    """
    if re.search(r"(?<!최저)(?<!최저 )입찰\s*금액", deposit):
        return "온비드 원문 표시값입니다. 이 보증금은 최저입찰가격이 아니라 내가 써 내는 입찰금액을 기준으로 계산합니다."
    if re.search(r"최저\s*입찰\s*가|예정\s*가", deposit):
        return f"온비드 원문 표시값입니다. 기준이 되는 최저입찰가격은 {minimum_bid_display or '원문 확인'}입니다."
    return "온비드 원문 표시값입니다. 계산 기준은 공고 원문에서 확인하십시오."


def extract_cost_terms(sections: dict[str, str], minimum_bid_display: str) -> list[dict[str, str]]:
    """공고 원문에 적힌 비용 조건만 모은다. 세율·요율은 계산하지 않는다."""
    chunk = strip_tooltips(section_html(sections, "입찰방법"))
    terms: list[dict[str, str]] = []
    deposit = label_value(chunk, "입찰보증금")
    if deposit:
        terms.append(
            {
                "title": "입찰보증금",
                "value": deposit,
                "note": deposit_basis_note(deposit, minimum_bid_display),
                "source": "온비드 상세 페이지 > 입찰방법",
            }
        )
    for label in ("잔대금 납부방법", "잔대금 납부기한"):
        value = label_value(chunk, label)
        if value:
            terms.append(
                {
                    "title": label,
                    "value": value,
                    # 온비드 화면 필드가 첨부 공고문 본문과 어긋난 사례가 있다(시연 공고 887335 —
                    # 필드 「낙찰 후 7일 이내」 · 공고문 「계약 체결 후 30일 이내」 · 2026-10-19 관측).
                    "note": "온비드 원문 표시값입니다. 첨부 공고문 본문의 기한과 다를 수 있으니 공고문도 확인하십시오.",
                    "source": "온비드 상세 페이지 > 입찰방법",
                }
            )
    terms.append(
        {
            "title": "낙찰 후 세금·부대비용",
            "value": "값 없음 — 사용자 확인 필요",
            "note": "취득세·등록면허세·중개 및 이전 비용은 온비드가 제공하지 않습니다. 세율과 금액은 이 서비스에서 계산하지 않으며 담당기관과 관할 세무서에서 확인하십시오.",
            "source": "온비드 미제공 항목",
        }
    )
    return terms


# 온비드는 최저입찰가격 공개 여부를 lowstBidPrcHideDivCd 로 가른다.
# 온비드 물건상세 페이지의 자체 스크립트가 `lowstBidPrcHideDivCd != '0001'` 이면 "비공개"를
# 찍는다(2026-09-07 물건상세 HTML 실측). 공개 여부는 이용기관이 정한다(캠코 회의 확인).
PRICE_UNDISCLOSED = "비공개"

# 입찰기간·최저입찰가격을 추출하지 못했을 때 화면 다섯 곳(작업 카드 action/due, AI 코치
# facts, 상단 알림, 분석 직후 미리보기)에 제각각 뜨던 실패 문구를 하나로 합친다(2026-09-22 UI 정리).
NOTICE_VALUE_FALLBACK = "원문 확인 필요"


def minimum_bid_value(inputs: dict[str, str], raw_value: str, extra_hide_code: str = "") -> str:
    hide_code = (inputs.get("lowstBidPrcHideDivCd") or extra_hide_code or "").strip()
    if hide_code and hide_code != "0001":
        return PRICE_UNDISCLOSED
    digits = re.sub(r"\D", "", raw_value or "")
    if raw_value and digits and int(digits) == 0:
        return PRICE_UNDISCLOSED
    return raw_value or ""


def validate_onbid_url(raw_url: str) -> str:
    raw_url = raw_url.strip()
    url_match = re.search(r"https?://\S+", raw_url)
    if url_match:
        raw_url = url_match.group(0)
    if not raw_url:
        raise ValueError("온비드 URL을 입력해야 합니다.")
    parsed = urllib.parse.urlparse(raw_url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("http 또는 https 온비드 URL만 분석할 수 있습니다.")
    host = (parsed.hostname or "").lower()
    if host != "onbid.co.kr" and not host.endswith(".onbid.co.kr"):
        raise ValueError("현재 MVP는 onbid.co.kr URL만 분석합니다.")
    for suffix, required_param in DETAIL_CONTROLLER_REQUIRED_PARAM.items():
        if parsed.path.endswith(suffix) and not urllib.parse.parse_qs(parsed.query).get(required_param):
            raise ValueError(
                "이 링크에는 물건을 특정하는 정보가 없습니다. 온비드 화면 주소창 URL이 아니라, "
                "물건상세/공고상세 화면 오른쪽 위 '공유하기' 버튼을 눌러 'URL 복사'로 가져온 링크를 붙여넣어 주세요."
            )
    return raw_url


def fetch_onbid(raw_url: str) -> tuple[str, str]:
    url = validate_onbid_url(raw_url)
    cookie_jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cookie_jar),
        urllib.request.HTTPRedirectHandler(),
    )
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) OnBidDocAgentMVP/0.1",
            "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
        },
    )
    with opener.open(request, timeout=20) as response:
        content = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
        return response.url, content.decode(charset, errors="replace")


# 온비드 물건상세 화면이 입찰기간·최저입찰가격·물건관리번호를 자바스크립트로 채워 넣을 때
# 쓰는 내부 XHR이다(공식 문서 없음, 2026-10-09 브라우저 네트워크 기록으로 확인). 회차별
# 표가 정적 HTML에 없어 못 읽던 값을 이 엔드포인트가 그대로 돌려준다. 공식 API가 아니므로
# 온비드가 구조를 바꾸면 깨질 수 있다 — 실패해도 조용히 빈 값으로 넘어가 기존 폴백을 막지 않는다.
def fetch_onbid_cltr_detail(
    final_url: str, query_params: dict[str, list[str]], ids: dict[str, str]
) -> dict[str, object]:
    if not ids.get("onbidPbancNo") and not ids.get("onbidCltrno"):
        return {}
    parsed = urllib.parse.urlparse(final_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    payload = {
        "cltrPrptDivCd": single_query_value(query_params, "cltrPrptDivCd"),
        "cltrScrnGrpCd": single_query_value(query_params, "cltrScrnGrpCd") or "0001",
        "onbidCltrno": ids.get("onbidCltrno", ""),
        "onbidPbancNo": ids.get("onbidPbancNo", ""),
        "pbctCdtnNo": ids.get("pbctCdtnNo", ""),
        "pbctNo": ids.get("pbctNo", ""),
    }
    data = urllib.parse.urlencode({key: value for key, value in payload.items() if value}).encode("utf-8")
    request = urllib.request.Request(
        f"{origin}/op/cltrpbancinf/pbanc/pbancdtlinf/PbancDtlInqController/inqPbancDtlCltrInf.do",
        data=data,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) OnBidDocAgentMVP/0.1",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read().decode("utf-8", errors="replace")
        parsed_body = json.loads(body)
        items = parsed_body.get("cltrInfVO")
        if isinstance(items, list) and items and isinstance(items[0], dict):
            return items[0]
    except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
        return {}
    return {}


def public_data_service_key() -> str:
    return secret_value("ONBID_API_SERVICE_KEY", "DATA_GO_KR_SERVICE_KEY", "PUBLIC_DATA_SERVICE_KEY")


def env_file_value(path: Path, name: str) -> str:
    if not path.exists():
        return ""
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.lstrip().startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() == name:
                return value.strip().strip('"').strip("'")
    except OSError:
        return ""
    return ""


def secret_value(*names: str) -> str:
    for name in names:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    env_paths = [
        Path(__file__).resolve().parent.parent / ".env.local",
        Path(os.environ.get("BIZKETCH_ENV_LOCAL", "")),
        Path.home() / "Documents" / "Dev" / "Bizketch" / "app" / ".env.local",
    ]
    for path in env_paths:
        if not str(path):
            continue
        for name in names:
            value = env_file_value(path, name)
            if value:
                return value
    return ""


def gemini_api_key() -> str:
    return secret_value("GEMINI_API_KEY", "GOOGLE_API_KEY")


def vertex_config() -> dict[str, str]:
    project = secret_value("GOOGLE_CLOUD_PROJECT_ID", "GOOGLE_CLOUD_PROJECT")
    location = secret_value("GOOGLE_CLOUD_LOCATION", "GOOGLE_CLOUD_REGION") or "global"
    model = os.environ.get("VERTEX_GEMINI_MODEL", os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")).strip()
    return {"project": project, "location": location, "model": model or "gemini-3.1-flash-lite"}


VERTEX_429_BACKOFF = (1.0, 2.0)


def vertex_read(request: urllib.request.Request, timeout: int) -> str:
    """Vertex 응답 본문을 읽는다. 429(공유 처리량 일시 초과)만 짧게 기다렸다 다시 시도한다.

    2026-10-04 실측 — 같은 요청 6회 중 1회가 429 였고, 그대로 두면 화면이 「AI 연결 안 됨」으로 떨어졌다.
    다른 오류는 재시도하지 않는다(인증·요청 오류는 다시 보내도 같다).
    """
    for wait in (*VERTEX_429_BACKOFF, None):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read().decode(response.headers.get_content_charset() or "utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or wait is None:
                raise
            time.sleep(wait)
    raise urllib.error.URLError("unreachable")


def vertex_access_token() -> str:
    global _VERTEX_TOKEN, _VERTEX_TOKEN_EXPIRES_AT
    if _VERTEX_TOKEN and time.time() < _VERTEX_TOKEN_EXPIRES_AT:
        return _VERTEX_TOKEN
    cmd = "gcloud.cmd" if os.name == "nt" else "gcloud"
    try:
        completed = subprocess.run(
            [cmd, "auth", "application-default", "print-access-token"],
            check=True,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    token = completed.stdout.strip()
    if token:
        _VERTEX_TOKEN = token
        _VERTEX_TOKEN_EXPIRES_AT = time.time() + 2700
    return token


def public_data_url(endpoint: str, params: dict[str, str], service_key: str) -> str:
    query = urllib.parse.urlencode({key: value for key, value in params.items() if value})
    encoded_key = service_key if "%" in service_key else urllib.parse.quote(service_key, safe="")
    return f"{endpoint}?serviceKey={encoded_key}&{query}" if query else f"{endpoint}?serviceKey={encoded_key}"


def parse_public_data_payload(raw: str) -> tuple[dict[str, object] | None, str]:
    try:
        return json.loads(raw), raw
    except json.JSONDecodeError:
        return None, clean_text(raw)


def api_items(payload: object) -> list[dict[str, object]]:
    if not isinstance(payload, dict):
        return []
    if "result" in payload and not any(key in payload for key in ("response", "body", "items", "item")):
        return []
    # 게이트웨이 오류 봉투는 데이터가 아니다. 이 가드가 없으면 아래 마지막 분기가 봉투 자체를
    # item 1건으로 돌려주어 오류가 데이터로 세어진다.
    if "OpenAPI_ServiceResponse" in payload:
        return []
    current: object = payload
    for key in ("response", "body", "items"):
        if isinstance(current, dict) and key in current:
            current = current[key]
    if isinstance(current, dict) and "item" in current:
        current = current["item"]
    if isinstance(current, list):
        return [item for item in current if isinstance(item, dict)]
    if isinstance(current, dict):
        return [current]
    return []


# 게이트웨이(공공데이터포털) 오류는 서비스 응답과 봉투가 다르다.
#   {"OpenAPI_ServiceResponse": {"cmmMsgHeader": {"returnReasonCode": "22", "returnAuthMsg": …, "errMsg": …}}}
# 사유 코드가 `resultCode` 가 아니라 `returnReasonCode` 에 있어, 이 분기가 없으면 헤더가 {} 가 되고
# resultCode 가 빈 문자열이 된다. 개발계정 한도(일 1,000건) 초과 코드 22 는 HTTP 200 에 실려 오므로
# HTTPError 경로에도 걸리지 않고 화면에는 원인 없는 `failed` 로만 보인다(2026-09-08 신설).
def gateway_error_header(raw: dict[str, object]) -> dict[str, object]:
    """게이트웨이 오류 봉투의 사유 코드·메시지를 서비스 헤더와 같은 키로 옮긴다."""
    header = dict(raw)
    header["resultCode"] = str(raw.get("returnReasonCode") or "")
    header["resultMsg"] = str(raw.get("returnAuthMsg") or raw.get("errMsg") or "")
    return header


def api_header(payload: object) -> dict[str, object]:
    if not isinstance(payload, dict):
        return {}
    response = payload.get("response")
    if isinstance(response, dict) and isinstance(response.get("header"), dict):
        return response["header"]
    gateway = payload.get("OpenAPI_ServiceResponse")
    if isinstance(gateway, dict) and isinstance(gateway.get("cmmMsgHeader"), dict):
        return gateway_error_header(gateway["cmmMsgHeader"])
    if isinstance(payload.get("result"), dict):
        return payload["result"]
    if isinstance(payload.get("header"), dict):
        return payload["header"]
    return {}


def call_public_data(
    name: str,
    params: dict[str, str],
    service_key: str,
) -> dict[str, object]:
    endpoint = PUBLIC_DATA_ENDPOINTS[name]
    base_params = {
        "pageNo": "1",
        "numOfRows": "10",
        "resultType": "json",
    }
    base_params.update(params)
    url = public_data_url(endpoint, base_params, service_key)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "OnBidDocAgentMVP/0.1",
            "Accept": "application/json, application/xml;q=0.8, */*;q=0.5",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            raw = response.read().decode(response.headers.get_content_charset() or "utf-8", errors="replace")
            payload, raw_text = parse_public_data_payload(raw)
            header = api_header(payload)
            result_code = str(header.get("resultCode", "") or header.get("resultcode", ""))
            ok = response.status == 200 and result_code not in {"03", "04", "20", "22", "30"} and bool(api_items(payload))
            return {
                "name": name,
                "ok": ok,
                "status": response.status,
                "resultCode": result_code,
                "resultMsg": header.get("resultMsg") or header.get("resultmsg") or "",
                "items": api_items(payload),
                "rawText": raw_text[:500],
            }
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        payload, raw_text = parse_public_data_payload(raw)
        header = api_header(payload)
        fallback_message = "인증키 권한이 아직 게이트웨이에 반영되지 않았거나 해당 API 접근이 차단되었습니다." if exc.code == 403 else clean_text(raw_text)[:160]
        return {
            "name": name,
            "ok": False,
            "status": exc.code,
            "resultCode": str(header.get("resultCode", "") or header.get("resultcode", "")),
            "resultMsg": header.get("resultMsg") or header.get("resultmsg") or fallback_message,
            "items": [],
            "rawText": raw_text[:500],
        }
    except urllib.error.URLError as exc:
        return {
            "name": name,
            "ok": False,
            "status": "network_error",
            "resultCode": "",
            "resultMsg": str(exc.reason),
            "items": [],
            "rawText": "",
        }


# 온비드 물건상세 페이지의 hidden input은 물건관리번호를 하이픈 없이 준다(20260800045167).
# 공공데이터 API는 4-4-6 하이픈 형식만 인정하고, 하이픈이 없으면 200 + NODATA_ERROR를 돌려준다.
# 2026-09-07 실측: 시연 3건 모두 하이픈 없으면 NODATA, 넣으면 데이터 1건.
def api_cltr_mng_no(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    if len(digits) != 14:
        return value or ""
    return f"{digits[:4]}-{digits[4:8]}-{digits[8:]}"


def fetch_public_data_bundle(ids: dict[str, str]) -> dict[str, object]:
    service_key = public_data_service_key()
    if not service_key:
        return {
            "status": "missing_key",
            "message": "공공데이터 인증키가 없어 온비드 원문 HTML 분석만 사용했습니다.",
            "services": [],
            "items": [],
        }

    services: list[dict[str, object]] = []
    cltr_mng_no = api_cltr_mng_no(ids.get("cltrMngNo", ""))
    pbct_cdtn_no = ids.get("pbctCdtnNo", "")
    pbanc_mng_no = ids.get("pbancMngNo", "")

    if cltr_mng_no:
        params = {"cltrMngNo": cltr_mng_no}
        if pbct_cdtn_no:
            params["pbctCdtnNo"] = pbct_cdtn_no
        services.append(call_public_data("real_estate_detail", params, service_key))
    if cltr_mng_no and pbct_cdtn_no:
        services.append(
            call_public_data(
                "item_bid_detail",
                {"cltrMngNo": cltr_mng_no, "pbctCdtnNo": pbct_cdtn_no},
                service_key,
            )
        )
    if pbanc_mng_no:
        services.append(call_public_data("notice_detail", {"pbancMngNo": pbanc_mng_no}, service_key))
        services.append(call_public_data("notice_bid_detail", {"pbancMngNo": pbanc_mng_no}, service_key))

    if not services:
        return {
            "status": "skipped",
            "message": "공공데이터 API 호출에 필요한 물건관리번호 또는 공고관리번호를 찾지 못했습니다.",
            "services": [],
            "items": [],
        }

    items: list[dict[str, object]] = []
    for service in services:
        items.extend(service.get("items", []))
    ok_count = sum(1 for service in services if service.get("ok"))
    forbidden_count = sum(1 for service in services if service.get("status") == 403)
    no_data_count = sum(1 for service in services if service.get("resultCode") == "03")
    if ok_count == len(services):
        status = "connected"
    elif ok_count:
        status = "partial"
    elif no_data_count == len(services):
        status = "no_data"
    elif forbidden_count:
        status = "pending"
    else:
        status = "failed"
    message = f"공공데이터 API {ok_count}/{len(services)}개 응답을 분석했습니다."
    if forbidden_count:
        message += f" {forbidden_count}개는 승인 직후 권한 반영 대기 또는 접근 차단 상태입니다."
    if no_data_count:
        message += f" {no_data_count}개는 조회 조건에 해당 데이터가 없습니다."
    if status in {"no_data", "pending"}:
        message += " 현재 화면은 온비드 원문 HTML 분석값으로 정상 생성했습니다."
    return {
        "status": status,
        "message": message,
        "services": [
            {
                "name": service.get("name"),
                "ok": service.get("ok"),
                "status": service.get("status"),
                "resultCode": service.get("resultCode"),
                "resultMsg": service.get("resultMsg"),
                "itemCount": len(service.get("items", [])),
            }
            for service in services
        ],
        "items": items,
        # 서비스별 응답을 따로 보관한다. items 를 합쳐 놓으면 "이 값이 어느 API 에서 왔는가"를
        # 알 수 없고, 같은 이름의 필드가 여러 API 에 있어 엉뚱한 쪽 값을 집을 수 있다
        # (예: tdpsSbtnDcmtYn 은 getCltrBidInf2 와 getPbancBidInf2 양쪽에 있다).
        "itemsByService": {
            str(service.get("name") or ""): [
                item for item in service.get("items", []) if isinstance(item, dict)
            ]
            for service in services
        },
    }


# getCltrBidInf2(공공데이터 온비드 물건 입찰상세)가 주는 제출서류 관련 필드를 화면이 쓸
# 구조로 바꾼다. 2026-10-18 에 재산유형 6종의 실제 응답을 받아 확인한 사실에 맞춰 설계했다
# (team-reports/2026-10-18-bid-doc-timeline/api-integration.md §1 · 고정 샘플은
# tests/fixtures/cltr_bid_inf_samples.json).
#
# ⑴ 서류 「내용」 필드(bidRltnDcmtCont · collbMthodDcmtCont · bidPtctAplyDcmtCont ·
#    tdpsSbtnDcmtCont)는 6건 모두 비어 있었다. subtBidDcmtCont 만 2건에서 값이 왔는데 그
#    값이 「대리입찰서류」라는 구분명 그대로다. 그래서 서류 「이름」은 이 API 에서 가져오지
#    않고 기존 화면 파싱 경로를 그대로 쓴다.
# ⑵ 제출기한·제출방식에는 쓸 만한 값이 온다. 화면 파싱으로 얻기 어려웠던 것이 이쪽이다.
# ⑶ 🔴 플래그가 N 인데도 기한·방식 값이 남아 있는 사례가 실제로 있다. 공유재산 분양 건은
#    collbBidPsblYn=N(공동입찰 불가)인데 collbDcmtSbmsnTermNm 에 값이 있었다. 그러므로 그
#    입찰 방식이 실제로 가능한지를 플래그로 먼저 걸러야 한다. 걸러지 않으면 「공동입찰이 안
#    되는 물건에 공동입찰 서류 제출기한을 안내하는」 거짓 안내가 된다.
BID_DOC_TERM_SPECS = (
    {
        "kind": "공동입찰",
        "availableField": "collbBidPsblYn",
        "dueField": "collbDcmtSbmsnTermNm",
        "methodField": "collbDcmtSbmsnMthodNm",
    },
    {
        "kind": "대리입찰",
        "availableField": "subtBidPsblYn",
        "dueField": "subtBidDcmtSbmsnTermNm",
        "methodField": "subtBidDcmtSbmsnMthodNm",
    },
    {
        "kind": "입찰참가신청",
        "availableField": "bidPtctAplyYn",
        "dueField": "bidPtctAplyTermNm",
        "methodField": "bidPtctDcmtSbmsnMthodNm",
    },
    {
        "kind": "입찰보증금 대체서류",
        "availableField": "tdpsSbtnDcmtYn",
        "dueField": "tdpsSbtnDcmtSbmsnTermNm",
        "methodField": "tdpsSbtnDcmtSbmsnMthodNm",
    },
)

# bidPtctAplyTermNm 은 6건 전부 "~" 였다. 시작과 끝을 잇는 구분자만 남고 날짜가 없는 값이라
# 화면에 그대로 내보내면 「기한 ~」이 된다. evlPtdbClgCont 의 "||" 도 같은 부류다.
# 날짜도 문구도 없는 값은 값이 없는 것으로 본다.
EMPTY_API_TERM_VALUES = {"", "~", "-", "||", "~~"}


def api_field_text(entry: dict[str, object], field: str) -> str:
    value = entry.get(field)
    if value is None:
        return ""
    return clean_text(str(value))


def api_meaningful_term(value: str) -> str:
    return "" if value.strip() in EMPTY_API_TERM_VALUES else value


def build_bid_doc_terms(entry: dict[str, object]) -> list[dict[str, str]]:
    terms: list[dict[str, str]] = []
    for spec in BID_DOC_TERM_SPECS:
        if api_field_text(entry, str(spec["availableField"])).upper() != "Y":
            continue
        due = api_meaningful_term(api_field_text(entry, str(spec["dueField"])))
        method = api_meaningful_term(api_field_text(entry, str(spec["methodField"])))
        if not due and not method:
            continue
        terms.append({"kind": str(spec["kind"]), "due": due, "method": method})
    return terms


# 입찰참가신청 필요 여부. 이 값이 Y 면 공고기관 승인을 먼저 받아야 입찰할 수 있어서, 서류
# 준비 순서가 통째로 바뀐다. 값이 Y 도 N 도 아니면 빈 dict 을 돌려준다 — 화면이 「우리가
# 모른다」를 가장 눈에 띄는 자리에 두지 않게 하려는 것이다(2026-10-18 ux-design-review P1-1).
def build_bid_participation_apply(entry: dict[str, object]) -> dict[str, object]:
    flag = api_field_text(entry, "bidPtctAplyYn").upper()
    if flag not in {"Y", "N"}:
        return {}
    return {
        "required": flag == "Y",
        "docs": api_field_text(entry, "bidPtctAplyDcmtCont"),
        "due": api_meaningful_term(api_field_text(entry, "bidPtctAplyTermNm")),
        "method": api_meaningful_term(api_field_text(entry, "bidPtctDcmtSbmsnMthodNm")),
        "source": "공공데이터 온비드 물건 입찰상세(getCltrBidInf2) · bidPtctAplyYn",
    }


# 자격제한·지역제한·기타제한. 「이 물건에 응찰할 자격이 되는가」는 사용자가 가장 먼저 알아야
# 하는 것이라 1단계(공고 확인)에 둔다. 「없음(모든 회원 입찰가능)」처럼 제한이 없다는 값도
# 유용하므로 버리지 않고, 제한이 있을 때만 화면에서 강조한다.
BID_LIMIT_SPECS = (
    {"key": "qualification", "label": "자격 제한", "field": "qlfcLmtCdtnCont"},
    {"key": "region", "label": "지역 제한", "field": "rgnLmtCdtnCont"},
    {"key": "etc", "label": "기타 제한", "field": "etcLmtCdtnCont"},
)

# 제한 없음을 뜻하는 값. 이 값이면 화면에서 강조하지 않는다. 부분일치로 비교하지 않는다 —
# 「없음」이 값의 일부로 섞인 실제 제한 문구(예: 「제한 없음 다만 …」)를 제한 없음으로
# 읽으면 안 된다.
NO_LIMIT_VALUES = {"없음", "없음(모든 회원 입찰가능)", "제한없음", "해당없음"}


def build_bid_limits(entry: dict[str, object]) -> list[dict[str, object]]:
    limits: list[dict[str, object]] = []
    for spec in BID_LIMIT_SPECS:
        value = api_field_text(entry, str(spec["field"]))
        if not api_meaningful_term(value):
            continue
        limits.append(
            {
                "key": str(spec["key"]),
                "label": str(spec["label"]),
                "value": value,
                "restricted": value.strip() not in NO_LIMIT_VALUES,
            }
        )
    return limits


def api_value(items: list[dict[str, object]], *keys: str) -> str:
    wanted = {key.lower() for key in keys}
    for item in items:
        for key, value in item.items():
            if key.lower() in wanted and value not in (None, ""):
                return clean_text(str(value))
    return ""


def first_value(*values: str) -> str:
    for value in values:
        if value:
            return value
    return ""


def single_query_value(params: dict[str, list[str]], key: str) -> str:
    return (params.get(key) or [""])[0]


def make_onbid_url(base_url: str, path: str, params: dict[str, str]) -> str:
    parsed = urllib.parse.urlparse(base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    query = urllib.parse.urlencode({key: value for key, value in params.items() if value})
    return f"{origin}{path}?{query}" if query else f"{origin}{path}"


def build_related_urls(
    final_url: str,
    params: dict[str, list[str]],
    ids: dict[str, str],
) -> dict[str, str]:
    common = {
        "cltrScrnGrpCd": single_query_value(params, "cltrScrnGrpCd") or single_query_value(params, "cltrScrnGrpCd2") or "0001",
        "cltrPrptDivCd": single_query_value(params, "cltrPrptDivCd") or single_query_value(params, "cltrPrptDivCd2"),
        "onbidCltrno": ids.get("onbidCltrno", ""),
        "onbidPbancNo": ids.get("onbidPbancNo", ""),
        "pbctNo": ids.get("pbctNo", ""),
        "pbctCdtnNo": ids.get("pbctCdtnNo", ""),
    }
    item_url = make_onbid_url(
        final_url,
        "/op/cltrpbancinf/cltrdtl/CltrDtlController/mvmnCltrDtl.do",
        common,
    )
    notice_url = make_onbid_url(
        final_url,
        "/op/cltrpbancinf/pbanc/pbancdtlinf/PbancDtlInqController/mvmnPbancDtl.do",
        common,
    )
    urls = {"source": final_url}
    if common["onbidCltrno"]:
        urls["itemDetail"] = item_url
        # 물건상세는 pbctCdtnNo 가 없으면 온비드가 500 을 준다(known-pitfalls.md:62-65).
        # 표본 23건의 보유는 0/23 이라 이 경로가 기본값에 가깝다. 링크를 지우지 않고
        # «확신을 낮춰» 내보낸다 — 화면이 이 플래그로 주의 표기를 붙인다.
        if not common["pbctCdtnNo"]:
            urls["itemDetailUncertain"] = True
    if common["onbidPbancNo"]:
        urls["noticeDetail"] = notice_url
    return urls


def infer_focus(disposition: str, asset_type: str) -> str:
    text = f"{disposition} {asset_type}"
    if "대부" in text or "임대" in text:
        return "lease"
    if "매각" in text or "공매" in text or "압류" in text:
        return "sale"
    return "lease"


def build_tasks(notice: dict[str, str], docs: list[str]) -> list[dict[str, object]]:
    disposition = notice.get("dispositionLabel", "")
    checklist = notice.get("docChecklist") if isinstance(notice.get("docChecklist"), dict) else {}
    price_label = "최저입찰가격"
    price_value = notice.get("minimumBidPrice") or notice.get("bidDeposit") or NOTICE_VALUE_FALLBACK
    docs_detail = " / ".join(docs[:2]) if docs else str(checklist.get("headline") or "공고 원문과 첨부 확인")
    final_url = notice["sourceUrl"]

    tasks: list[dict[str, object]] = [
        {
            "id": "notice-type",
            "title": "공고 유형 확인",
            "action": f"{notice.get('assetType', '재산유형 확인')} / {disposition or '처분방식 확인'}",
            "due": "분석 직후",
            "detail": "온비드 원문에서 가져온 재산유형과 처분방식입니다. 사용자 목적과 맞는지 먼저 확인합니다.",
            "question": "이 물건이 내가 찾는 임대, 매각, 공매 목적과 맞는지 담당기관이나 원문에서 확인합니다.",
            "source": "온비드 상세 페이지 > 재산유형/처분방식",
            "cta": "온비드 원문",
            "url": final_url,
            "defaultDone": False,
        },
        {
            "id": "bid-period",
            "title": "입찰기간 확인",
            "action": notice.get("bidPeriod") or NOTICE_VALUE_FALLBACK,
            "due": notice.get("bidDeadline") or NOTICE_VALUE_FALLBACK,
            "detail": "입찰 시작/마감, 개찰일시, 매각결정일시는 물건별로 다릅니다. 캘린더에 옮기기 전에 원문을 다시 확인합니다.",
            "question": "입찰 마감, 개찰, 낙찰 후 후속 일정이 각각 언제인지 담당기관에 확인합니다.",
            "source": "온비드 상세 페이지 > 입찰기간/입찰일정",
            "cta": "온비드 원문",
            "url": final_url,
            "defaultDone": False,
        },
        {
            "id": "price",
            "title": f"{price_label} 확인",
            "action": price_value,
            "due": "입찰 전",
            "detail": (
                "최저입찰가격이 「비공개」이면 이용기관이 공개하지 않기로 선택한 것입니다. 입찰보증금이 입찰금액 기준인지 최저입찰가격 기준인지는 공고마다 다르니 비용 항목의 원문 표시값을 확인하십시오."
                if price_value == PRICE_UNDISCLOSED
                else "가격, 보증금, 대부료, 납부 방식은 입찰 판단에 영향을 주지만 본 MVP는 수익성 판단을 제공하지 않습니다."
            ),
            "question": "입찰보증금, 납부 방식, 낙찰 후 비용을 공고 원문과 담당기관에 확인합니다.",
            "source": "온비드 상세 페이지 > 가격/보증금/비용 항목",
            "cta": "온비드 원문",
            "url": final_url,
            "defaultDone": False,
        },
        {
            "id": "documents",
            "title": "제출서류 확인",
            "action": docs_detail,
            "due": "입찰 마감 전",
            "detail": "공동입찰, 대리입찰, 법인/개인 여부에 따라 제출서류와 제출방법이 달라질 수 있습니다. 이 목록은 참고용이며 빠진 항목이 있어도 진행을 막지 않습니다.",
            "question": "이번 물건에서 원본 제출, 직접 제출, 공동/대리입찰 서류 조건이 무엇인지 담당기관에 확인합니다.",
            "source": "온비드 상세 페이지 > 제출서류",
            "cta": "온비드 원문",
            "url": final_url,
            "defaultDone": False,
        },
    ]
    return tasks


def local_ai_coach(notice: dict[str, object], docs: list[str]) -> dict[str, object]:
    asset_type = str(notice.get("assetType") or "재산유형 확인")
    disposition = str(notice.get("dispositionLabel") or "처분방식 확인")
    bid_period = str(notice.get("bidPeriod") or notice.get("bidDeadline") or NOTICE_VALUE_FALLBACK)
    price = str(notice.get("minimumBidPrice") or notice.get("bidDeposit") or NOTICE_VALUE_FALLBACK)
    contact = str(notice.get("contact") or notice.get("agency") or "담당기관 확인")
    checklist = notice.get("docChecklist") if isinstance(notice.get("docChecklist"), dict) else {}
    checklist_items = checklist.get("items", []) if isinstance(checklist, dict) else []
    condition_keys = {key for item in checklist_items for key in item.get("conditionKeys", [])}
    docs_summary = " / ".join(docs[:2]) if docs else "제출서류 표 확인"
    is_sale = "매각" in disposition or "공매" in disposition or "압류" in asset_type
    # 근거는 항목의 제출방법이 우선이고, 온비드 제출서류 표(`tableRows`)의 제출방법 칸은
    # **서류를 1건 이상 뽑았을 때에 한해** 보조 근거로 인정한다.
    # 서류 0건일 때 표를 근거로 삼으면, 「못 뽑았습니다」를 띄운 바로 다음 줄이
    # 「직접제출 서류」의 존재를 전제한다 — `bool(checklist_items)` 가드가 그 경로를 막는다.
    # 표본 23건 실측 `[관측]`: 항목만 = 2/23 · 이 중간안 = 10/23 · 무가드 = 16/23.
    # 화면 노출 기준(`is_sale=True` 3건)으로는 위양성 0/0/0 · 정당한 안내 0/3/3 이라,
    # 이 가드는 위양성을 늘리지 않으면서 압류재산 3건의 안내를 되살린다.
    has_direct_submit = any(item.get("method") for item in checklist_items) or (
        bool(checklist_items)
        and any(row.get("method") for row in checklist.get("tableRows", []))
    )
    # 서류 줄 정규식 근거(`condition_keys`)를 그대로 두고 「입찰방법」 절의 화면 값을 `or` 로 **더한다**.
    # 값이 `불가능` 이어도 서류 근거로 켜진 축을 **끄지 않는다** — 이 값은 「공동입찰 자체의 허용 여부」이지
    # 「내가 단독입찰인지」가 아니다.
    # 표본 23건 실측 `[관측]`: 서류 근거만 9/23 → 화면 값 합산 12/23. 늘어나는 3건(17·18·21)은
    # 전부 서류 추출 0건 공고이고, 반대 방향 불일치(서류 켜짐 · 화면 「불가능」)는 0/23 이라
    # 기존 9건의 판정을 뒤집지 않는 순수 증분이다.
    # 다만 「3건」은 **조건 축 기준**이다 — 화면 코치 노출은 2건(17·18)이다.
    # 21 은 임대(`is_sale=False`)라 아래 코치 블록에 들어오지 못하고 quick-facts 행만 남는다
    # (docs/90_MVP개발/09_공동입찰_명도책임_크롤링가용성_조사_20260908.md §5).
    joint_allowed = str(notice.get("jointBidAllowed") or "")
    has_doc_condition = bool({"proxy", "joint"} & condition_keys)
    has_proxy_or_joint = has_doc_condition or joint_allowed == "가능"
    has_docs = bool(docs)

    confirmed_facts = [
        {"label": "공고 유형", "value": f"{asset_type} · {disposition}"},
        {"label": "입찰기간", "value": bid_period},
        {"label": "가격 기준", "value": price},
        {"label": "담당기관", "value": contact},
    ]

    unresolved_checks: list[dict[str, str]] = []
    ask_agency: list[str] = []

    if is_sale:
        headline = "AI 누락 점검: 공고가 말하지 않는 빈칸"
        plain_summary = "아래 항목은 원문에 값이 있더라도 실제 준비 전 확인이 필요한 부분만 추렸습니다."
        if has_proxy_or_joint:
            unresolved_checks.append(
                {
                    "title": "공동/대리입찰 서류가 나에게 필요한지",
                    # 서류를 못 뽑은 공고에서 「원문에는 …가 보이지만」이라고 쓰면 없는 서류 목록을 전제한다.
                    # 근거가 화면 값뿐일 때는 그 사실을 그대로 적는다.
                    "reason": (
                        f"원문에는 `{docs_summary}`가 보이지만, 단독 전자입찰이면 일부 서류가 불필요할 수 있습니다."
                        if has_doc_condition
                        else f"온비드 「입찰방법」에 공동입찰이 `{joint_allowed}`으로 표시돼 있습니다. 서류 목록은 원문에서 뽑지 못했습니다."
                    ),
                    # reason 과 같은 분기다. 서류를 0건 뽑은 공고에서 「필요한 서류만 남깁니다」라고 쓰면
                    # 화면에 없는 목록을 전제한다 — 못 뽑았으면 못 뽑았다고 말한다.
                    "action": (
                        "내 입찰 방식이 단독/공동/대리 중 무엇인지 정하고 필요한 서류만 남깁니다."
                        if has_doc_condition
                        else "내 입찰 방식이 단독/공동/대리 중 무엇인지 정하고, 필요한 서류는 온비드 원문·첨부에서 직접 확인하십시오."
                    ),
                    "source": "제출서류 표" if has_doc_condition else "온비드 입찰방법",
                }
            )
            ask_agency.append("단독 전자입찰이면 공동입찰서류·대리입찰서류를 제출하지 않아도 되는지 확인할 수 있나요?")
        if has_direct_submit:
            unresolved_checks.append(
                {
                    "title": "직접제출 서류의 실제 마감 시각",
                    "reason": "원문에 직접제출 조건이 있어 우편/온라인 대체 가능 여부와 접수 마감 시각이 준비 시간을 좌우합니다.",
                    "action": "방문 제출 필요 여부와 접수처 운영시간을 확인합니다.",
                    "source": "제출방법",
                }
            )
            ask_agency.append("직접제출 서류의 접수처, 접수 가능 시간, 우편 또는 온라인 대체 가능 여부를 확인할 수 있나요?")
        unresolved_checks.append(
            {
                "title": "보증금·잔금·추가 비용의 납부 순서",
                "reason": "공매예정가격은 확인됐지만 보증금, 잔금, 이전/발급 비용은 서로 다른 일정으로 발생할 수 있습니다.",
                "action": "입찰 전 납부할 금액과 낙찰 후 납부할 금액을 분리해 메모합니다.",
                "source": "가격/입찰정보",
            }
        )
        ask_agency.append("입찰 전 보증금과 낙찰 후 납부금의 납부 방식·기한을 각각 확인할 수 있나요?")
        # 매각 공고에도 현장·실물 확인 질문을 둔다. 임대 분기에만 있어서 차량·동산 매각(사진·기재와
        # 실물이 다른 사례)에서는 코치가 아무 말도 하지 않았다(2026-10-19 커뮤니티 조사 1-5 · 4-2 B).
        # 상태가 좋다·나쁘다는 판단은 쓰지 않는다. 확인 가능 여부를 묻는 문장까지만이다.
        unresolved_checks.append(
            {
                "title": "현장·실물 상태를 확인할 수 있는지",
                "reason": "사진과 기재 내용만으로는 실물 상태, 보관 장소, 낙찰 후 인수 방법이 드러나지 않을 수 있습니다.",
                "action": "현장 확인 가능 시간과 인수 방법을 담당기관에 묻고, 공고 원문의 현황 기재와 대조합니다.",
                "source": "물건 상세/담당기관",
            }
        )
        ask_agency.append("현장이나 실물을 확인할 수 있는 시간과 방법, 낙찰 후 인수 절차를 확인할 수 있나요?")
    else:
        headline = "AI 누락 점검: 임대 후 실제 사용 조건"
        plain_summary = "대부료나 기간보다 실제 사용 가능 조건, 현장 상태, 추가 비용이 빠지기 쉽습니다."
        unresolved_checks.extend(
            [
                {
                    "title": "내 업종으로 실제 사용 가능한지",
                    "reason": "임대/대부 공고는 가격보다 용도 제한과 사용 승인 조건이 더 중요한 경우가 많습니다.",
                    "action": "공고명과 시설 용도가 내 사업 목적과 맞는지 담당기관 확인 대상으로 올립니다.",
                    "source": "공고명/재산유형",
                },
                {
                    "title": "현장 상태와 인수 범위",
                    "reason": "원문에 시설 상태, 기존 비품, 철거·원상복구 책임이 충분히 안 보일 수 있습니다.",
                    "action": "현장 확인 가능 시간과 인수·원상복구 책임을 먼저 묻습니다.",
                    "source": "물건 상세/담당기관",
                },
                {
                    "title": "대부료 외 반복 비용",
                    "reason": "대부료 외 관리비, 공과금, 보험, 보증금 조건은 공고별로 다를 수 있습니다.",
                    "action": "월별 고정비 후보를 별도 메모로 분리합니다.",
                    "source": "가격/계약조건",
                },
            ]
        )
        ask_agency.extend(
            [
                "이 장소를 내 업종으로 사용할 수 있는지, 사용 제한이나 별도 승인이 필요한지 확인할 수 있나요?",
                "현장 확인 가능 시간, 기존 시설·비품 인수 범위, 원상복구 책임을 확인할 수 있나요?",
                "대부료 외 관리비·공과금·보험·보증금 등 반복 비용이 있는지 확인할 수 있나요?",
            ]
        )

    if not has_docs:
        # 🔴 못 뽑았으면 못 뽑았다고 말한다. 구분명만 있는 온비드 표(공동입찰서류 등)를
        # 추출 성공으로 세지 않는다 — 2026-09-07 표본조사에서 15건이 이 경로로 허위 통과했다.
        status = str(checklist.get("status") or "not_found")
        reason = {
            "attachment_only": "본문에 서류명이 없고 목록이 첨부 공고문 안에 있는 유형입니다. 첨부를 열어야 확인됩니다.",
            "not_in_notice": "이 재산유형은 본문과 첨부 어디에도 목록이 없는 표본이 있었습니다. 담당기관 확인이 필요합니다.",
        }.get(status, "자동 추출이 이 공고에서 서류명을 찾지 못했습니다. 온비드 원문과 첨부를 직접 확인해야 합니다.")
        unresolved_checks.insert(
            0,
            {
                "title": "서류 목록을 자동으로 뽑지 못했습니다",
                "reason": reason,
                "action": "온비드 원문의 공고문 절과 첨부파일을 직접 확인합니다. 준비 보드는 그대로 진행할 수 있습니다.",
                "source": "자동 추출 결과",
            },
        )
        ask_agency.insert(0, "이 공고의 제출서류 목록과 제출 방법이 별도 첨부파일에 있는지 확인할 수 있나요?")
    elif str(checklist.get("profile", {}).get("code")) == "B":
        unresolved_checks.insert(
            0,
            {
                "title": "첨부 공고문에 서류가 더 있을 수 있습니다",
                "reason": "이 재산유형은 이용기관이 직접 작성해 목록을 첨부에 담는 경우가 많습니다.",
                "action": "본문에서 찾은 목록과 첨부 공고문을 나란히 비교합니다.",
                "source": "재산유형 기반 사전 판정",
            },
        )

    next_steps = [
        f"`{unresolved_checks[0]['title']}`부터 확인합니다." if unresolved_checks else "분석된 주요 값을 준비 보드에 저장합니다.",
        "이미 추출된 값은 다시 묻지 말고, 아래 미해결 질문만 담당기관에 확인합니다.",
        "확인 결과가 나오면 준비 보드 체크리스트에서 해당 항목을 완료 처리합니다.",
    ]

    return {
        "mode": "AI 누락 점검",
        "headline": headline,
        "plainSummary": plain_summary,
        "whyThisMatters": "온비드 원문에서 이미 보이는 값은 요약에 그치고, 사용자가 실제로 놓치기 쉬운 미해결 항목만 분리합니다.",
        "confirmedFacts": confirmed_facts,
        "unresolvedChecks": unresolved_checks[:3],
        "nextSteps": next_steps,
        "askAgency": ask_agency[:3],
        "safeBoundary": "입찰 참여 여부, 수익성, 권리관계, 법률 판단은 제공하지 않습니다. 최종 판단은 공고 원문과 담당기관 확인을 우선합니다.",
        "confidence": "원문 추출 기반",
        "inputsUsed": [asset_type, disposition, bid_period, price, contact],
    }


def parse_gemini_json(payload: object) -> dict[str, object] | None:
    if not isinstance(payload, dict):
        return None
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        return None
    content = candidates[0].get("content") if isinstance(candidates[0], dict) else None
    parts = content.get("parts") if isinstance(content, dict) else None
    if not isinstance(parts, list):
        return None
    text = ""
    for part in parts:
        if isinstance(part, dict) and isinstance(part.get("text"), str):
            text += part["text"]
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I | re.S).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def sanitize_ai_text(value: object) -> object:
    replacements = {
        "정상적인 입찰 참여를 보장": "입찰 준비 누락을 줄이는 데 도움",
        "입찰 참여를 보장": "입찰 준비 누락을 줄이는 데 도움",
        "입찰을 진행하세요": "원문 절차를 확인하세요",
        "입찰을 원하시면": "검토를 계속하려면",
        "입찰 금액을 결정하세요": "가격 기준과 비용 항목을 원문에서 확인하세요",
        "입찰 금액을 결정": "가격 기준과 비용 항목을 원문에서 확인",
        "입찰 금액 결정": "가격 기준 확인",
        "성공적인 입찰의 첫걸음": "누락 없는 준비의 첫 단계",
        "성공적인 입찰": "누락 없는 준비",
        "입찰 참여 준비 안내": "입찰 준비 안내",
        "입찰 참여 준비": "입찰 준비",
        "입찰 참여": "입찰 준비",
        "해당 물건의 권리관계는 어떻게 되나요?": "공고 원문에 표시된 유의사항이 추가로 있는지 확인할 수 있나요?",
        "권리관계": "공고 원문상 유의사항",
        "수익성": "가격/비용",
        "보장": "확인",
        "추천": "안내",
    }
    if isinstance(value, str):
        result = value
        for old, new in replacements.items():
            result = result.replace(old, new)
        return result
    if isinstance(value, list):
        return [sanitize_ai_text(item) for item in value]
    if isinstance(value, dict):
        return {key: sanitize_ai_text(item) for key, item in value.items()}
    return value


def gemini_ai_coach(notice: dict[str, object], docs: list[str]) -> dict[str, object] | None:
    api_key = gemini_api_key()
    if not api_key:
        return None
    model = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite").strip() or "gemini-3.1-flash-lite"
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{urllib.parse.quote(model, safe='')}:generateContent?key={urllib.parse.quote(api_key, safe='')}"
    prompt = {
        "role": "온비드 공공자산 입찰 준비 코치",
        "instruction": (
            "초보 사용자가 온비드 공고에서 놓치기 쉬운 미해결 항목을 찾도록 한국어로 안내한다. "
            "공고에 이미 값이 있는 입찰기간, 가격, 제출서류 목록을 그대로 반복하지 않는다. "
            "입찰 참여 권유, 가격 결정 권유, 수익성 판단, 법률/권리관계 판단은 하지 않는다. "
            "'보장', '추천', '수익성', '입찰 참여를 보장', '입찰 금액을 결정' 같은 표현을 쓰지 않는다. "
            "담당기관 질문은 제출서류, 제출방법, 마감/납부 일정, 담당부서 확인으로 제한한다. "
            "화면 미리보기용이므로 짧고 행동 중심으로 쓴다. "
            "반드시 JSON 객체만 반환한다."
        ),
        "notice": {
            "title": notice.get("title", ""),
            "pageType": notice.get("pageType", ""),
            "assetType": notice.get("assetType", ""),
            "disposition": notice.get("dispositionLabel", ""),
            "bidMethod": notice.get("bidMethod", ""),
            "bidPeriod": notice.get("bidPeriod", ""),
            "bidDeadline": notice.get("bidDeadline", ""),
            "price": notice.get("minimumBidPrice", "") or notice.get("bidDeposit", ""),
            "appraisalPrice": notice.get("appraisalPrice", ""),
            "agency": notice.get("agency", ""),
            "contact": notice.get("contact", ""),
            "requiredDocs": docs[:4],
        },
        "schema": {
            "mode": "AI 누락 점검",
            "headline": "미해결 항목 중심 한 문장, 35자 이내",
            "plainSummary": "이미 확인된 값을 반복하지 않는 설명 1문장",
            "unresolvedChecks": [{"title": "빈칸", "reason": "왜 원문만으로 부족한지", "action": "사용자가 바로 할 일", "source": "근거 필드"}],
            "askAgency": ["이미 값이 있는 내용을 다시 묻지 않는 담당기관 질문 2개"],
            "safeBoundary": "법률/투자/입찰 판단이 아님을 알리는 1문장",
            "confidence": "원문 추출 기반",
            "inputsUsed": ["사용한 핵심 입력값"],
        },
    }
    request_body = {
        "contents": [{"role": "user", "parts": [{"text": json.dumps(prompt, ensure_ascii=False)}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 1000,
            "responseMimeType": "application/json",
        },
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(request_body, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read().decode(response.headers.get_content_charset() or "utf-8", errors="replace")
        parsed = parse_gemini_json(json.loads(raw))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None
    if not parsed:
        return None
    local = local_ai_coach(notice, docs)
    coach = sanitize_ai_text(local)
    coach["mode"] = "AI 누락 점검"
    coach["llmStatus"] = "connected"
    coach["model"] = model
    return coach


def vertex_ai_coach(notice: dict[str, object], docs: list[str]) -> dict[str, object] | None:
    config = vertex_config()
    if not config["project"]:
        return None
    token = vertex_access_token()
    if not token:
        return None
    location = config["location"]
    host = "aiplatform.googleapis.com" if location == "global" else f"{location}-aiplatform.googleapis.com"
    endpoint = (
        f"https://{host}/v1/projects/{urllib.parse.quote(config['project'], safe='')}"
        f"/locations/{urllib.parse.quote(location, safe='')}/publishers/google/models/"
        f"{urllib.parse.quote(config['model'], safe='')}:generateContent"
    )
    prompt = {
        "role": "온비드 공공자산 입찰 준비 코치",
        "instruction": (
            "초보 사용자가 온비드 공고에서 놓치기 쉬운 미해결 항목을 찾도록 한국어로 안내한다. "
            "공고에 이미 값이 있는 입찰기간, 가격, 제출서류 목록을 그대로 반복하지 않는다. "
            "입찰 참여 권유, 가격 결정 권유, 수익성 판단, 법률/권리관계 판단은 하지 않는다. "
            "'보장', '추천', '수익성', '입찰 참여를 보장', '입찰 금액을 결정' 같은 표현을 쓰지 않는다. "
            "담당기관 질문은 제출서류, 제출방법, 마감/납부 일정, 담당부서 확인으로 제한한다. "
            "화면 미리보기용이므로 짧고 행동 중심으로 쓴다. "
            "반드시 JSON 객체만 반환한다."
        ),
        "notice": {
            "title": notice.get("title", ""),
            "pageType": notice.get("pageType", ""),
            "assetType": notice.get("assetType", ""),
            "disposition": notice.get("dispositionLabel", ""),
            "bidMethod": notice.get("bidMethod", ""),
            "bidPeriod": notice.get("bidPeriod", ""),
            "bidDeadline": notice.get("bidDeadline", ""),
            "price": notice.get("minimumBidPrice", "") or notice.get("bidDeposit", ""),
            "appraisalPrice": notice.get("appraisalPrice", ""),
            "agency": notice.get("agency", ""),
            "contact": notice.get("contact", ""),
            "requiredDocs": docs[:4],
        },
        "schema": {
            "mode": "AI 누락 점검",
            "headline": "미해결 항목 중심 한 문장, 35자 이내",
            "plainSummary": "이미 확인된 값을 반복하지 않는 설명 1문장",
            "unresolvedChecks": [{"title": "빈칸", "reason": "왜 원문만으로 부족한지", "action": "사용자가 바로 할 일", "source": "근거 필드"}],
            "askAgency": ["이미 값이 있는 내용을 다시 묻지 않는 담당기관 질문 2개"],
            "safeBoundary": "법률/투자/입찰 판단이 아님을 알리는 1문장",
            "confidence": "원문 추출 기반",
            "inputsUsed": ["사용한 핵심 입력값"],
        },
    }
    request_body = {
        "contents": [{"role": "user", "parts": [{"text": json.dumps(prompt, ensure_ascii=False)}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 1000,
            "responseMimeType": "application/json",
        },
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(request_body, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    try:
        raw = vertex_read(request, timeout=30)
        parsed = parse_gemini_json(json.loads(raw))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None
    if not parsed:
        return None
    local = local_ai_coach(notice, docs)
    coach = sanitize_ai_text(local)
    coach["mode"] = "AI 누락 점검"
    coach["llmStatus"] = "connected"
    coach["model"] = config["model"]
    return coach


def build_ai_coach(notice: dict[str, object], docs: list[str]) -> dict[str, object]:
    coach = vertex_ai_coach(notice, docs) or gemini_ai_coach(notice, docs)
    if coach:
        return coach
    rule_based = local_ai_coach(notice, docs)
    rule_based["llmStatus"] = "rule_based"
    return rule_based


ANSWER_TYPES = ("notice", "board", "general", "none")


def _clip(value: object, limit: int = 120) -> str:
    return clean_text(str(value or ""))[:limit]


def sanitize_board_state(raw: object) -> dict[str, object]:
    """화면이 보낸 준비 보드 상태를 프롬프트에 넣을 크기·모양으로 줄인다.

    브라우저가 보낸 값이라 그대로 믿지 않는다 — 개수·길이를 자르고 모르는 키는 버린다.
    """
    if not isinstance(raw, dict):
        return {}
    tasks = []
    for item in raw.get("tasks") if isinstance(raw.get("tasks"), list) else []:
        if not isinstance(item, dict):
            continue
        tasks.append({
            "id": _clip(item.get("id"), 40),
            "title": _clip(item.get("title"), 60),
            "status": _clip(item.get("status")),
            "due": _clip(item.get("due"), 40),
            "done": item.get("done") is True,
            "needsCheck": _clip(item.get("needsCheck"), 80),
        })
        if len(tasks) >= 10:
            break
    docs = raw.get("docs") if isinstance(raw.get("docs"), dict) else {}
    pending = docs.get("pending") if isinstance(docs.get("pending"), list) else []

    def count(value: object) -> int:
        return value if isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 100 else 0

    done_count = sum(1 for task in tasks if task["done"])
    next_task = next((task["id"] for task in tasks if not task["done"]), "")
    return {
        # 진행률·다음 할 일은 화면이 보낸 숫자 대신 정리한 tasks 에서 다시 센다.
        "progress": {"done": done_count, "total": len(tasks)},
        "nextTaskId": next_task,
        "tasks": tasks,
        "docs": {
            "done": count(docs.get("done")),
            "total": count(docs.get("total")),
            "pending": [_clip(name, 60) for name in pending[:10]],
        },
        "userType": _clip(raw.get("userType"), 40),
    }


def question_prompt(
    notice: dict[str, object], docs: list[str], question: str, board: dict[str, object] | None = None
) -> dict[str, object]:
    return {
        "role": "온비드 공공자산 입찰 준비 코치",
        "instruction": (
            "사용자가 이 공고의 준비 보드를 보면서 질문했다. 질문을 아래 넷 중 하나로 분류해 answerType 에 적는다. "
            "(1) notice: 공고 사실(기간·가격·기관·서류 등)을 묻는 질문. notice 필드와 requiredDocs 안에서 "
            "확실히 답할 수 있을 때만 근거 값 그대로 답하고, sourceField 에 notice 필드 이름을 적는다. "
            "(2) board: 다음에 할 일·순서·진행 상황·무엇부터 할지를 묻는 질문. board 의 tasks 순서와 done, "
            "needsCheck, docs.pending 만 근거로 다음에 손댈 준비 항목을 안내하고, sourceField 에 그 task id 를 적는다. "
            "아직 끝내지 않은 첫 할 일(board.nextTaskId)부터 위에서 아래 순서로 진행하도록 권하고, "
            "안내하는 첫 할 일의 needsCheck 가 비어 있지 않으면 그 내용을 반드시 한 번 짚는다. "
            "board.tasks 가 비어 있으면 board 로 답하지 않는다. 모든 할 일이 끝났으면 원문과 담당기관 최종 확인을 안내한다. "
            "(3) general: 이 공고에 한정되지 않은 온비드 공매 제도·절차·용어를 묻는 질문"
            "(매각결정기일이 무엇인지, 전자입찰 진행 방식, 서류 제출 뒤 절차 흐름, 입찰 보증금 일반 규정 등). "
            "onbidReference 는 온비드 이용안내·FAQ·준수규칙·용어사전에서 옮긴 설명이다. 질문한 용어가 onbidReference 에 "
            "있으면 none 으로 답하지 않고, 그 text 를 근거로 쉬운 말로 풀어 답하며, text 에 없는 사실은 덧붙이지 않고, "
            "sourceField 에 그 source 를 적는다. onbidReference 가 비어 있으면 공매 절차에 대한 일반 지식만으로 "
            "확실히 답할 수 있을 때만 쓰고, sourceField 는 빈 문자열로 둔다. "
            "이 공고에만 해당하는 사실(가격·기간·기관 등)이나 notice 에 없는 이 물건 특정 내용은 general 로 답하지 않는다. "
            "(4) none: 위 근거로 답할 수 없거나 추측·해석이 필요한 질문. answerable 을 false, answer 를 빈 문자열로 둔다. "
            "notice, board, general 은 answerable 을 true 로 한다. 모르는데 지어내지 않는다. "
            "onbidReference 가 비어 있고 general 로 답할 만한 일반 지식도 확신이 없으면 none 으로 남긴다. "
            "board 안내는 준비 순서에 대한 것이며 입찰 여부를 판단하는 말이 아니다. "
            "general 안내도 공매 절차에 대한 일반 지식일 뿐이며 이 공고에 대한 판단이 아니다. "
            "입찰 참여 권유, 가격 결정 권유, 수익성 판단, 법률/권리관계 판단은 어느 갈래로도 하지 않는다. "
            "'보장', '추천', '수익성' 같은 표현을 쓰지 않는다. "
            "답은 한국어 존댓말 1~3문장으로 짧게 쓴다. 반드시 JSON 객체만 반환한다."
        ),
        "notice": {
            "title": notice.get("title", ""),
            "assetType": notice.get("assetType", ""),
            "disposition": notice.get("dispositionLabel", ""),
            "bidMethod": notice.get("bidMethod", ""),
            "bidPeriod": notice.get("bidPeriod", ""),
            "bidDeadline": notice.get("bidDeadline", ""),
            "price": notice.get("minimumBidPrice", "") or notice.get("bidDeposit", ""),
            "appraisalPrice": notice.get("appraisalPrice", ""),
            "agency": notice.get("agency", ""),
            "contact": notice.get("contact", ""),
            "requiredDocs": docs[:10],
            # 입찰 참여 단계(3단계) 질문창이 보내는 사용자 답 — 공고 원문 추출값이 아니라
            # 사용자가 2단계에서 고른 선택이다. 없으면 빈 문자열이고 근거로 쓰지 않는다.
            "jointBidAnswer": notice.get("jointBidAnswer", ""),
            "proxyBidAnswer": notice.get("proxyBidAnswer", ""),
        },
        "board": board or {},
        "onbidReference": find_onbid_references(question),
        "question": question,
        "schema": {
            "answerable": True,
            "answerType": "notice | board | general | none",
            "answer": "공고 내용, 준비 보드 상태, 또는 onbidReference 에 근거한 답변, 또는 빈 문자열",
            "sourceField": "근거로 쓴 notice 필드 이름, task id, onbidReference 의 source, 또는 빈 문자열",
        },
    }


def vertex_answer_question(
    notice: dict[str, object], docs: list[str], question: str, board: dict[str, object] | None = None
) -> dict[str, object] | None:
    config = vertex_config()
    if not config["project"]:
        return None
    token = vertex_access_token()
    if not token:
        return None
    location = config["location"]
    host = "aiplatform.googleapis.com" if location == "global" else f"{location}-aiplatform.googleapis.com"
    endpoint = (
        f"https://{host}/v1/projects/{urllib.parse.quote(config['project'], safe='')}"
        f"/locations/{urllib.parse.quote(location, safe='')}/publishers/google/models/"
        f"{urllib.parse.quote(config['model'], safe='')}:generateContent"
    )
    request_body = {
        "contents": [
            {"role": "user", "parts": [{"text": json.dumps(question_prompt(notice, docs, question, board), ensure_ascii=False)}]}
        ],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 400, "responseMimeType": "application/json"},
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(request_body, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8", "Authorization": f"Bearer {token}"},
        method="POST",
    )
    try:
        raw = vertex_read(request, timeout=20)
        parsed = parse_gemini_json(json.loads(raw))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None
    return sanitize_ai_text(parsed) if parsed else None


def gemini_answer_question(
    notice: dict[str, object], docs: list[str], question: str, board: dict[str, object] | None = None
) -> dict[str, object] | None:
    api_key = gemini_api_key()
    if not api_key:
        return None
    model = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite").strip() or "gemini-3.1-flash-lite"
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{urllib.parse.quote(model, safe='')}:generateContent?key={urllib.parse.quote(api_key, safe='')}"
    request_body = {
        "contents": [
            {"role": "user", "parts": [{"text": json.dumps(question_prompt(notice, docs, question, board), ensure_ascii=False)}]}
        ],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 400, "responseMimeType": "application/json"},
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(request_body, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read().decode(response.headers.get_content_charset() or "utf-8", errors="replace")
        parsed = parse_gemini_json(json.loads(raw))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None
    return sanitize_ai_text(parsed) if parsed else None


def normalize_question_answer(result: dict[str, object], board: dict[str, object] | None = None) -> dict[str, object]:
    answer = str(result.get("answer") or "").strip()
    answer_type = str(result.get("answerType") or "").strip()
    if answer_type not in ANSWER_TYPES:
        # 옛 스키마(answerType 없음)로 답하면 공고 사실 답변으로 본다.
        answer_type = "notice" if result.get("answerable") else "none"
    # 보드 상태를 받지 않았는데 「준비 보드 기반 안내」라고 하면 근거 없이 지어낸 것이다.
    if answer_type == "board" and not (board or {}).get("tasks"):
        answer_type = "none"
    answerable = bool(result.get("answerable")) and answer_type != "none" and bool(answer)
    return {
        "connected": True,
        "answerable": answerable,
        "answerType": answer_type if answerable else "none",
        "answer": answer if answerable else "",
        "sourceField": str(result.get("sourceField") or "").strip() if answerable else "",
    }


# 초보자가 커뮤니티에서 자주 묻고 곤란해하는 질문에는 모델 대신 고정 문장으로 답한다(2026-10-19 동원님 지시:
# 「입찰금액은 어떻게 정하면 좋을까요?」에 「담당기관에 문의」만 나왔다). 질문 갈래는
# docs/60_본선준비/24_공매초보_어려움_커뮤니티조사_20261019.md 1절·3절에서 골랐고, 문장은 온비드 이용안내·FAQ·
# 입찰참가자 준수규칙(team-reports/2026-10-19-onbid-journey-conformance/researcher-onbid-journey.md)과
# ONBID_GUIDE_TERMS 에 있는 사실만 쓴다. 얼마를 쓸지·권리관계·수익성은 여기서도 판단하지 않고, 판단 대신
# 「정하기 전에 확인할 것」을 적는다(CLAUDE.md 행동 규칙 · 커뮤니티 조사 4-3).
# patterns 는 띄어쓰기를 지운 질문에 맞춘다. 목록 순서가 우선순위다 — 「낙찰되면 보증금은?」은 낙찰 뒤 절차,
# 「보증금 몇 퍼센트?」는 보증금으로 가야 하므로 보증금을 입찰금액보다 앞에 둔다.
# exclude 는 다른 경로가 이미 맞게 답하는 질문을 돌려보낸다. 「유찰되면 보증금은?」은 유찰 용어 설명이 답한다.
COMMON_QUESTION_GUIDES: tuple[dict[str, object], ...] = (
    {
        "id": "after-award",
        "title": "낙찰 뒤 절차",
        "patterns": (
            r"낙찰(후|뒤|되면|돼면|받으면|받고|받은|이후|다음|된다음|된뒤|된후)",
            r"(잔금|잔대금)\S{0,6}(언제|어떻게|기한|납부|내야|내나|낼)",
            r"(소유권이전|이전등기|등기)\S{0,6}(어떻게|절차|언제|하나|해야|하면)",
            r"(낙찰|계약)\S{0,4}포기",
        ),
        "exclude": (),
    },
    {
        "id": "bid-cancel",
        "title": "입찰서 취소·수정",
        "patterns": (
            r"(입찰|입찰서|응찰)\S{0,4}(취소|철회|수정|변경|바꿀|바꾸|바꿔)",
            r"(제출한|낸|넣은)\S{0,6}(취소|수정|변경|바꿀|바꾸|바꿔)",
        ),
        "exclude": (r"개찰결과", r"결과가취소"),
    },
    {
        "id": "result-check",
        "title": "입찰 결과 확인",
        "patterns": (
            r"(낙찰|입찰|개찰)결과\S{0,4}(확인|어디|언제|볼|알)",
            r"낙찰(됐|되었|여부)\S{0,6}(확인|어디|알|볼)",
            r"입찰자(수|가몇)",
            r"누가낙찰",
            r"몇명\S{0,4}(입찰|응찰)",
        ),
        "exclude": (),
    },
    {
        "id": "certificate",
        "title": "입찰에 쓰는 인증서",
        "patterns": (r"인증서", r"간편인증", r"입찰버튼"),
        "exclude": (),
    },
    {
        "id": "qualification",
        "title": "입찰 자격",
        "patterns": (
            r"(개인|사업자|법인|외국인|미성년)\S{0,6}(입찰|참여|참가|응찰)\S{0,4}(할수|가능|되|돼|있)",
            r"(입찰|참가)자격",
        ),
        "exclude": (),
    },
    {
        "id": "rights",
        "title": "권리관계·명도",
        "patterns": (r"권리", r"인수", r"임차인", r"세입자", r"(?<!설)명도", r"인도명령", r"떠안", r"선순위", r"가압류", r"근저당"),
        "exclude": (),
    },
    {
        "id": "deposit",
        "title": "입찰보증금",
        "patterns": (r"보증금(은|을|는|이)?(얼마|몇|언제|어떻게|어디|계좌|납부|내야|내나|내면|넣)",),
        "exclude": (r"유찰", r"패찰", r"떨어지", r"떨어졌", r"탈락"),
    },
    {
        "id": "bid-amount",
        "title": "입찰금액을 정할 때 확인할 것",
        "patterns": (
            r"입찰(금액|가격|가)(은|는|을|를)?(어떻게|얼마|정하|정해|정할|써야|쓰면|적어|넣어|결정)",
            r"얼마(를|에|로|정도)?(써|쓰|적|넣|입찰|응찰)",
            r"몇(프로|퍼센트|%)",
            r"(적정|적당한)(가|가격|금액|입찰)",
            r"(시세|낙찰가율)",
        ),
        "exclude": (),
    },
    {
        "id": "site-check",
        "title": "사진·현장 확인",
        "patterns": (r"사진", r"현장", r"실물", r"직접(가|볼|봐)", r"구경"),
        "exclude": (),
    },
)


def _notice_text(notice: dict[str, object], key: str) -> str:
    value = str(notice.get(key) or "").strip()
    return "" if value in ("", "-", NOTICE_VALUE_FALLBACK) else value


def _deposit_rule_line(notice: dict[str, object]) -> str:
    """재산유형별 입찰보증금 기준 한 문장. 근거는 ONBID_GUIDE_TERMS['입찰보증금'] 과 같은 준수규칙 조항이다."""
    asset = str(notice.get("assetType") or "")
    shown = _notice_text(notice, "bidDeposit")
    shown_part = f" 이 공고의 표시는 「{shown}」입니다." if shown else ""
    if "압류재산" in asset:
        base = "압류재산의 입찰보증금(공매보증)은 내가 쓴 입찰금액이 아니라 공매예정가격의 10% 이상입니다."
    elif "국유재산" in asset:
        base = "국유재산의 입찰보증금은 내가 쓴 입찰금액의 5% 이상이라, 금액을 높여 쓰면 보증금도 함께 늘어납니다."
    elif "수탁재산" in asset:
        base = "수탁재산의 입찰보증금은 내가 쓴 입찰금액의 10% 이상이라, 금액을 높여 쓰면 보증금도 함께 늘어납니다."
    else:
        base = "이용기관 물건의 입찰보증금은 기관이 정한 「입찰금액의 일정률」 이상입니다. 입찰금액 기준이면 금액을 높여 쓸수록 보증금도 늘어납니다."
    return base + shown_part


def _is_lease_notice(notice: dict[str, object]) -> bool:
    label = str(notice.get("dispositionLabel") or "")
    return bool(re.search(r"임대|대부", label)) and not re.search(r"매각|공매", label)


def common_question_lines(guide_id: str, notice: dict[str, object], board: dict[str, object] | None) -> tuple[list[str], str]:
    """자주 묻는 질문 갈래마다 이 공고 값을 넣은 안내 문장과 출처를 돌려준다."""
    minimum = _notice_text(notice, "minimumBidPrice")
    appraisal = _notice_text(notice, "appraisalPrice")
    asset = str(notice.get("assetType") or "")
    if guide_id == "bid-amount":
        if minimum == "비공개":
            minimum_line = "이 물건의 최저입찰가격은 「비공개」입니다. 이용기관이 공개하지 않기로 한 값이라 담당기관에 문의하십시오."
        elif minimum:
            minimum_line = f"이 물건의 최저입찰가격은 {minimum}입니다. 이 회차에 입찰할 수 있는 가장 낮은 금액이라 이보다 낮게 쓸 수 없습니다."
        else:
            minimum_line = "최저입찰가격(이 회차에 입찰할 수 있는 가장 낮은 금액)은 공고 원문에서 확인하십시오."
        lines = [
            "얼마를 쓸지는 이 서비스가 정해 드리지 않습니다. 적정 가격·낙찰 가능성·수익성은 판단하지 않고, 금액을 정하기 전에 확인할 것만 정리합니다.",
            minimum_line,
            _deposit_rule_line(notice),
        ]
        if appraisal:
            lines.append(f"감정평가금액({appraisal})은 최저입찰가격과 다른 값입니다. 둘의 관계는 공고마다 다르므로 공고 원문에서 확인하십시오.")
        lines.append("제출한 입찰서는 수정·변경·취소할 수 없는 것이 원칙입니다. 제출 전에 금액의 자릿수(0의 개수)를 다시 확인하십시오.")
        if _is_lease_notice(notice):
            lines.append("낙찰되면 대부료·사용료를 공고문이 정한 기한 안에 내야 합니다. 기한과 금액 산정 방식은 공고 원문에서 확인하십시오.")
        else:
            lines.append("낙찰되면 잔대금을 공고문이 정한 기한 안에 내야 합니다. 취득세 같은 세금과 이전 비용은 이 서비스가 계산하지 않으니 관할 세무서와 담당기관에서 확인하십시오.")
        lines.append("가격을 판단할 때 쓸 물건 상태와 이용 조건은 공고 첨부, 현장 확인, 담당기관 문의로 직접 확인하십시오.")
        return lines, "온비드 용어 설명(최저입찰가격·입찰보증금·감정평가금액) · 온비드 FAQ 「입찰 및 개찰 일정」 · 입찰참가자 준수규칙 보증금 조항"
    if guide_id == "deposit":
        return [
            _deposit_rule_line(notice),
            "납부 계좌는 입찰서를 제출한 뒤 물건마다 따로 주어지는 1회용 가상계좌입니다.",
            "입찰 마감 시각까지 보증금을 내지 않으면 입찰이 무효가 됩니다.",
            "보증금이 1천만 원을 넘으면 마감 전까지 나눠 낼 수 있다고 온비드가 안내하지만, 분할 납부를 막는 공고도 있으니 공고문을 확인하십시오.",
        ], "온비드 이용안내 「입찰참가 안내」 STEP04-5·STEP05 · 입찰참가자 준수규칙 보증금 조항"
    if guide_id == "bid-cancel":
        return [
            "제출한 입찰서는 수정·변경·취소할 수 없는 것이 원칙입니다.",
            "온비드에서 2회 이상 입찰서 제출이 가능하다고 안내된 물건이면 같은 회차에 다시 입찰할 수 있습니다.",
            "입찰보증금을 마감 시각까지 내지 않으면 그 입찰은 무효가 됩니다. 무효가 된 입찰에 다른 불이익이 따르는지는 공고문과 담당기관에서 확인하십시오.",
        ], "온비드 FAQ 「입찰 및 개찰 일정」 · 온비드 FAQ(같은 회차 재입찰) · 압류재산 입찰참가자 준수규칙 제8조②"
    if guide_id == "result-check":
        return [
            "개찰일시는 공고기관이 개찰을 시작하는 시각입니다. 개찰이 끝난 뒤에 결과를 볼 수 있습니다.",
            "내 입찰 결과는 온비드 「나의온비드 > 입찰관리 > 입찰결과내역」에서 직접 확인합니다. 결과 알림도 신청할 수 있습니다.",
            "낙찰자가 누구인지는 공개되지 않습니다.",
            "입찰 결과의 「유찰」은 내 입찰만 탈락한 경우와 물건 자체가 유찰된 경우, 두 가지 뜻이 있습니다.",
        ], "온비드 이용안내 「입찰참가 안내」 STEP06 · 온비드 FAQ 「본인의 입찰결과를 확인하는 방법」·「입찰결과에서 '유찰'의 의미」 · 국유재산 입찰참가자 준수규칙 제12조③"
    if guide_id == "certificate":
        lines = [
            "온비드 전자입찰에는 공동인증서나 간편인증서(개인회원만)가 필요합니다.",
            "공동인증서는 전자거래범용인증서나 온비드전용인증서를 온비드에 등록해야 합니다. 은행용·증권용처럼 용도가 정해진 인증서는 등록할 수 없습니다.",
            "유료 인증서 수수료(1년)는 개인 온비드전용 1,100원 · 범용 4,400원, 사업자·법인·단체 11,000원 · 88,000원입니다.",
        ]
        user_type = str((board or {}).get("userType") or "")
        if user_type and user_type != "개인":
            lines.append(f"지금 고른 사용자 유형은 「{user_type}」입니다. 사업자·법인 회원은 간편인증서 없이 공동인증서를 씁니다.")
        return lines, "온비드 인증서 안내 · 온비드 이용안내 「입찰참가 안내」 STEP02"
    if guide_id == "qualification":
        lines = [
            "누가 입찰할 수 있는지는 공고문의 참가자격 조항이 정합니다. 개인·사업자·법인 가운데 누가 입찰할 수 있는지는 공고마다 다릅니다.",
            "조항에 괄호 안 표기(예: 일반사업자 또는 법인사업자)가 있으면 그 뜻은 공고 원문과 담당기관에서 확인하십시오.",
        ]
        user_type = str((board or {}).get("userType") or "")
        if user_type:
            lines.append(f"지금 고른 사용자 유형은 「{user_type}」입니다. 이 유형이 참가자격 조항에 해당하는지 확인하십시오.")
        return lines, "공고문 참가자격 조항 · 공공데이터 온비드 물건 입찰정보(입찰 자격 조건)"
    if guide_id == "rights":
        lines = ["권리관계, 인수해야 할 권리, 명도 책임은 이 서비스가 판단하지 않습니다. 확인할 곳만 안내합니다."]
        eviction = _notice_text(notice, "evictionResponsibility")
        if eviction:
            lines.append(f"이 공고의 명도책임 표시는 「{eviction} 부담」입니다.")
        if "압류재산" in asset:
            lines.append("압류재산은 권리 관련 사항을 공매재산명세서로 안내합니다. 입찰시작 7일 전부터 입찰마감 전까지 물건 상세페이지 [입찰정보] 탭에서 볼 수 있습니다.")
        else:
            lines.append("공고문의 유의사항·명도 조항과 등기사항증명서를 직접 확인하십시오.")
        lines.append("확인한 내용의 뜻이 분명하지 않으면 입찰 전에 담당기관이나 법률 전문가에게 문의하십시오.")
        return lines, "온비드 FAQ(압류재산 · 공매재산명세서) · 공고 원문"
    if guide_id == "site-check":
        return [
            "온비드 사진과 기재 내용만으로 물건 상태를 판단하지 마십시오. 기재 내용이 실제와 달랐다는 이용자 후기가 있습니다.",
            "현장을 볼 수 있는지, 언제 볼 수 있는지는 담당기관에 문의하십시오.",
            "부동산은 등기사항증명서·건축물대장, 차량은 자동차등록원부 같은 공적 서류로 기재 내용을 다시 확인할 수 있습니다.",
        ], "공고 원문과 담당기관 확인 원칙"
    # after-award 는 재산유형별 절차 문장이 화면(postAwardProcessNote)에 있어 화면이 이어 붙인다.
    return ["낙찰 뒤 절차와 기한, 입찰보증금 처리는 재산유형마다 다릅니다."], "온비드 이용안내 「낙찰절차 안내」"


GUIDE_JUMPS = {
    "after-award": (4, "2-4 낙찰 후 준비 보기"),
    "qualification": (1, "2-1 입찰 자격 조건 보기"),
    "bid-amount": (3, "2-3 입찰 참여 보기"),
    "deposit": (3, "2-3 입찰 참여 보기"),
}


def match_common_question(
    question: str, notice: dict[str, object] | None = None, board: dict[str, object] | None = None
) -> dict[str, object] | None:
    """자주 묻는 질문 갈래에 맞으면 고정 안내를 돌려준다. 맞는 갈래가 없으면 None 이다."""
    compact = re.sub(r"\s+", "", question or "")
    if not compact:
        return None
    for guide in COMMON_QUESTION_GUIDES:
        if any(re.search(pattern, compact) for pattern in guide["exclude"]):
            continue
        if not any(re.search(pattern, compact) for pattern in guide["patterns"]):
            continue
        lines, source = common_question_lines(str(guide["id"]), notice or {}, board)
        result: dict[str, object] = {"id": guide["id"], "title": guide["title"], "lines": lines, "source": source}
        jump = GUIDE_JUMPS.get(str(guide["id"]))
        if jump:
            result["jump"], result["jumpLabel"] = jump
        return result
    return None


def answer_notice_question(
    notice: dict[str, object], docs: list[str], question: str, board: dict[str, object] | None = None
) -> dict[str, object]:
    # 자주 묻는 질문은 모델을 부르지 않고 고정 안내로 답한다. 모델이 붙지 않았으므로 connected 는 False 다.
    guide = match_common_question(question, notice, board)
    if guide:
        return {
            "connected": False, "answerable": True, "answerType": "guide", "answer": "",
            "sourceField": str(guide["id"]), "guide": guide, "references": find_onbid_references(question),
        }
    # 모델에 붙지 않았으면 「AI 가 확인했다」고 말하지 않는다(coach 의 llmStatus 와 같은 원칙).
    result = vertex_answer_question(notice, docs, question, board) or gemini_answer_question(notice, docs, question, board)
    if isinstance(result, dict) and isinstance(result.get("answerable"), bool):
        answer = normalize_question_answer(result, board)
    else:
        answer = {"connected": False, "answerable": False, "answerType": "none", "answer": "", "sourceField": ""}
    # 온비드 용어 설명은 모델 답과 따로 싣는다. 모델이 답하지 못했거나 연결되지 않았어도 화면이
    # 「담당기관 문의 필요」 대신 이 설명을 보여 줄 수 있게 한다(2026-10-19 동원님 지시).
    answer["references"] = find_onbid_references(question)
    return answer


def bid_deadline_passed(bid_period: str, bid_deadline: str) -> tuple[bool, str]:
    """입찰 마감일시가 분석 시각 기준으로 지났는지 순수 날짜 비교로 판정한다.

    입찰 여부·법률·수익성 판단은 하지 않는다. 마감 시각(입찰기간의 종료값 또는
    bid_deadline)을 파싱해 현재 시각과 비교만 한다. 파싱이 불확실하면 (False, "")를
    반환해 오탐(진행 중 공고에 경고)을 피한다.
    """
    end_raw = ""
    if bid_period and "~" in bid_period:
        end_raw = bid_period.split("~")[-1].strip()
    if not end_raw:
        end_raw = (bid_deadline or "").strip()
    match = re.search(r"(\d{4})-(\d{2})-(\d{2})(?:\s+(\d{2}):(\d{2}))?", end_raw)
    if not match:
        return False, ""
    year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
    hour = int(match.group(4)) if match.group(4) else 23
    minute = int(match.group(5)) if match.group(5) else 59
    try:
        end_dt = datetime(year, month, day, hour, minute)
    except ValueError:
        return False, ""
    if end_dt < datetime.now():
        stamp = match.group(0)
        return True, stamp
    return False, ""


def parse_notice_datetime(raw: str) -> datetime | None:
    match = re.search(r"(\d{4})-(\d{2})-(\d{2})(?:\s+(\d{2}):(\d{2}))?", raw or "")
    if not match:
        return None
    try:
        return datetime(
            int(match.group(1)),
            int(match.group(2)),
            int(match.group(3)),
            int(match.group(4)) if match.group(4) else 23,
            int(match.group(5)) if match.group(5) else 59,
        )
    except ValueError:
        return None


def bid_countdown(bid_period: str, bid_deadline: str, now: datetime | None = None) -> dict[str, object]:
    """마감까지 남은 일수를 화면 표시용으로 계산한다. 알림 발송은 하지 않는다."""
    now = now or datetime.now()
    start_raw = bid_period.split("~")[0].strip() if bid_period and "~" in bid_period else ""
    end_raw = bid_period.split("~")[-1].strip() if bid_period and "~" in bid_period else (bid_deadline or "").strip()
    end_dt = parse_notice_datetime(end_raw)
    start_dt = parse_notice_datetime(start_raw)
    if not end_dt:
        return {"state": "unknown", "label": "", "deadline": "", "daysLeft": None}
    days_left = (end_dt.date() - now.date()).days
    deadline = end_dt.strftime("%Y-%m-%d %H:%M")
    if end_dt < now:
        return {"state": "closed", "label": "입찰 마감 지남", "deadline": deadline, "daysLeft": days_left}
    if start_dt and start_dt > now:
        return {"state": "before", "label": f"입찰 시작 전 · 마감 D-{days_left}", "deadline": deadline, "daysLeft": days_left}
    label = "마감 당일" if days_left == 0 else f"마감 D-{days_left}"
    return {
        "state": "urgent" if days_left <= 3 else "open",
        "label": label,
        "deadline": deadline,
        "daysLeft": days_left,
    }


# 재산유형·처분방식은 온비드 값을 그대로 쓰고 뜻만 따로 안내한다(2026-09-07 캠코 회의 확정).
# 설명 문장은 그 회의에서 정인기 차장이 말한 내용을 옮긴 것이다.
# 🔴 여기에는 **뜻만** 적는다. 처분방식 사이의 금액·보증금 비교는 담지 않는다 —
# 「임대의 최저입찰가격과 보증금 구조는 매각과 같다」는 회의록 근거가 있으나(11_캠코_회의록 265행),
# 임대는 사용료·매각은 매매대금이라 사용자가 금액 규모를 같게 오해할 수 있다. 값 자체는 원문에서 읽는다.
TERM_GLOSSARY = {
    "압류재산": "체납자의 압류 재산을 국세청 등에서 위임받아 캠코가 처리하는 재산입니다.",
    "국유재산": "나라가 소유한 땅과 시설입니다. 부두 공공시설, 휴양림 부지 등을 민간에 매각하거나 임대합니다.",
    "기타일반재산": "압류재산·국유재산에 해당하지 않는 재산을 묶은 분류입니다.",
    "공유재산": "지방자치단체가 소유한 재산입니다.",
    "수탁재산": "금융기관·기업 등이 캠코에 처분을 맡긴 재산입니다.",
    "파산자산": "파산관재인이 처분하는 재산입니다.",
    "매각": "소유권을 넘기는 처분 방식입니다.",
    "임대": "일정 기간 빌려 쓰도록 하는 처분 방식입니다.",
    "대부": "국유재산을 빌려 쓰는 것을 가리키는 용어입니다.",
}


# 온비드 자료실 용어사전(https://www.onbid.co.kr 용어사전 메뉴)에서 2026-09-14에 수집한 확장분이다.
# 사이트는 총 208건을 제공하며, 다중 출처 병기·번호목록 파싱이 갈리는 항목을 걸러 136건을 담았다(실제 수집).
# 정의문은 온비드가 인용한 원출처(국립국어원 표준국어대사전·우리말샘, 관계 법령 등)의 뜻풀이를 그대로 옮겼다 —
# 온비드 사이트 자체에 공공누리(OGL) 표시가 확인되지 않아, 온비드가 편집한 문장을 대량 복제하지 않고
# 법령·사전에 근거한 짧은 뜻풀이만 두었다. 2글자 이하의 일반 명사(재산·계약·건축 등)는 어느 문구에나
# 우연히 들어맞아 안내가 소음이 되므로 제외했다.
ONBID_GLOSSARY_TERMS = {
    "가장 임차인": "주택임대차보호법을 악용하여 실제 임차인으로서의 대항력을 취득하지 못하였으나 외형상 대항력이 있는 임차인인 것처럼 가장(위장)하여 경매절차에서 배당을 받거나 낙찰자에게 대항력을 행사하는 경우를 통칭하는 개념을 말한다.",
    "감가보상": "구획정리 따위를 시행한 뒤에 교환 토지로 처분한 토지 가격이 사업 시행 전보다 낮을 때에 그 가격의 차이만큼 보상해 주는 일.",
    "감가상각": "토지를 제외한 고정 자산에 생기는 가치의 소모를 셈하는 회계상의 절차. 고정 자산 가치의 소모를 각 회계 연도에 할당하여 그 자산의 가격을 줄여 간다.",
    "감가상각률": "유형의 고정 자산의 원가에 대한 감가상각액의 비율. 감가상각의 방법에는 정액법, 정률법, 급수법, 생산액 비례법 등이 있다.",
    "감보율": "토지 구획의 정리에 따라 개인의 땅이 줄어드는 비율. ※ 감보율 산식(減步率算式) : 부동산에서 감보율을 구하는 계산식.",
    "감액률": "줄이거나 줄어든 액수의 비율.",
    "감정가격": "「감정평가 및 감정평가사에 관한 법률」에 의거 감정평가업자가 평가한 자산의 가격을 말한다.",
    "감정가액": "감정인이 평가한 공매대상 재산의 가액을 말한다. 감정인 감정인(鑑定人) 공매대상 재산이 부동산인 경우에는 「감정평가 및 감정평가사에 관한 법률」 제2조제4호에 따른 감정평가법인등, 공매대상 재산이 부동산 외의 재산인 경우에는 해당 재산과…",
    "강제경매": "법원에서 채무자의 부동산을 압류한 다음 경매하여 그 대금으로 채권자의 금전 채권을 충당하는 강제 집행.",
    "개발부담금": "개발이익 중 이 법에 따라 국가가 부과ㆍ징수하는 금액을 말하며, 개발부담금의 부과 대상인 개발사업은 다음 각 호에 해당하는 사업으로 한다. 1. 택지개발사업(주택단지조성사업을 포함한다) 2. 산업단지개발사업 3.",
    "개발이익": "개발사업의 시행이나 토지이용계획의 변경, 그 밖에 사회적ㆍ경제적 요인에 따라 정상지가(正常地價)상승분을 초과하여 개발사업을 시행하는 자나 토지 소유자에게 귀속되는 토지 가액의 증가분을 말한다.",
    "개발이익환수제": "토지를 개발하면서 땅값이 상승하여 얻은 이익 가운데 일정액을 정부가 거두어들이는 제도.",
    "개발제한구역": "국토교통부장관은 도시의 무질서한 확산을 방지하고 도시주변의 자연환경을 보전하여 도시민의 건전한 생활환경을 확보하기 위하여 도시의 개발을 제한할 필요가 있거나 국방부장관의 요청이 있어 보안상 도시의 개발을 제한할 필요가 있다고 인정되면…",
    "개발진흥지구": "주거기능ㆍ상업기능ㆍ공업기능ㆍ유통물류기능ㆍ관광기능ㆍ휴양기능 등을 집중적으로 개발ㆍ정비할 필요에 의해 『국토의 계획 및 이용에 관한 법률』에 따라 도시ㆍ군관리계획으로 결정ㆍ고시된 용도지구를 말하며, 주거개발진흥지구, 산업ㆍ유통개발진흥지구,…",
    "개별공시지가": "국토교통부장관이 평가ㆍ공시한 표준지공시지가를 기준으로 하여 시장ㆍ군수 또는 구청장이 결정ㆍ공시한 개별토지의 단위면적당 가격을 말한다.",
    "개인신용평가시스템": "대출을 신청하는 사람이 작성한 인적 사항, 직장, 소득 현황, 재무 상태 따위의 신용 관련 사항을 항목별로 점수화하여 대출 가능성과 대출 금액을 판단하는 시스템.",
    "개인정보": "생존하고 있는 개인에 관한 정보로서 성명ㆍ주민등록번호 등에 의하여 해당 개인을 알아볼 수 있는 부호ㆍ문자ㆍ음성ㆍ음향ㆍ영상 및 생체특성 등에 관한 정보(해당 정보만으로는 특정 개인을 알아볼 수 없는 경우에도 다른 정보와 용이하게 결합하여 알…",
    "거래사례 비교법": "거래사례비교법(去來事例比較法) 재산의 감정 평가에서, 대상 물건과 유사성이나 동일성이 있는 다른 물건의 매매 사례와 비교하여 가격을 정하는 방법.",
    "건부지": "건축물이 세워져 있는 토지. 건축물 주인과 토지 주인이 같고, 해당 토지의 사용이나 수익을 제한하는 다른 권리가 없는 토지이다.",
    "건축물": "토지에 정착(定着)하는 공작물 중 지붕과 기둥 또는 벽이 있는 것과 이에 딸린 시설물, 지하나 고가(高架)의 공작물에 설치하는 사무소ㆍ공연장ㆍ점포ㆍ차고ㆍ창고 등의 것을 말한다.",
    "건축물 개축": "기존 건축물의 전부 또는 일부[내력벽ㆍ기둥ㆍ보ㆍ지붕틀(한옥의 경우에는 지붕틀의 범위에서 서까래는 제외한다) 중 셋 이상이 포함되는 경우를 말한다]를 해체하고 그 대지에 종전과 같은 규모의 범위에서 건축물을 다시 축조하는 것을 말한다.",
    "건축물 신축": "건축물이 없는 대지(기존 건축물이 해체되거나 멸실된 대지를 포함한다)에 새로 건축물을 축조(築造)하는 것[부속건축물만 있는 대지에 새로 주된 건축물을 축조하는 것을 포함하되, 개축(改築) 또는 재축(再築)하는 것은 제외한다]을 말한다.",
    "건축물 이전": "건축물의 주요구조부를 해체하지 아니하고 같은 대지의 다른 위치로 옮기는 것을 말한다.",
    "건축물 재축": "건축물이 천재지변이나 그 밖의 재해(災害)로 멸실된 경우 그 대지에 다음 각 목의 요건을 모두 갖추어 다시 축조하는 것을 말한다. 가. 연면적 합계는 종전 규모 이하로 할 것 나.",
    "건축물 증축": "기존 건축물이 있는 대지에서 건축물의 건축면적, 연면적, 층수 또는 높이를 늘리는 것을 말한다.",
    "건축물대장": "건축물의 소유ㆍ이용 및 유지ㆍ관리 상태를 확인하거나 건축정책의 기초 자료로 활용하기 위하여 건축물과 그 대지의 현황 및 건축물의 구조내력(構造耐力)에 관한 정보를 기재한 장부를 말한다.",
    "건축설비": "건축물에 설치하는 전기ㆍ전화 설비, 초고속 정보통신 설비, 지능형 홈네트워크 설비, 가스ㆍ급수ㆍ배수(配水)ㆍ배수(排水)ㆍ환기ㆍ난방ㆍ냉방ㆍ소화(消火)ㆍ배연(排煙) 및 오물처리의 설비, 굴뚝, 승강기, 피뢰침, 국기 게양대, 공동시청 안테나,…",
    "건폐율": "대지면적에 대한 건축면적(대지에 건축물이 둘 이상 있는 경우에는 이들 건축면적의 합계로 한다)의 비율을 말한다.",
    "검인계약서": "검토한 표시로 도장을 찍어 계약이 성립되었음을 증명하는 서류.",
    "경계복원측량": "경계복원측량(境界復元測量) 지적 공부에 등록된 경계나 수치 지적부에 등록된 좌표를 바탕으로 하여 지적 공부에 등록될 당시의 원래 지상 경계를 찾아 지표에 나타내는 행정 처분.",
    "경계점": "필지를 구획하는 선의 굴곡점으로서 지적도나 임야도에 도해(圖解) 형태로 등록하거나 경계점좌표등록부에 좌표 형태로 등록하는 점을 말한다.",
    "경관녹지": "도시의 자연적 환경을 보전하거나 이를 개선하고 이미 자연이 훼손된 지역을 복원·개선함으로써 도시경관을 향상시키기 위하여 설치하는 녹지를 말한다.",
    "경관지구": "경관의 보전ㆍ관리 및 형성할 필요에 의해 『국토의 계획 및 이용에 관한 법률』에 따라 도시ㆍ군관리계획으로 결정ㆍ고시된 용도지구를 말하며, 자연경관지구, 시가지경관지구, 특화경관지구로 세분한다.",
    "계약금": "계약의 이행을 보장받기 위하여 계약 당사자 가운데 한쪽이 상대편에게 미리 제공하는 금액.",
    "계약당사자": "계약서에 기명하거나 날인함으로써 서로 간에 정해진 권리와 의무를 부담하는 둘 이상의 주체.",
    "계약보증금": "계약의 이행을 보장받기 위하여 계약 당사자 가운데 한쪽이 상대편에게 미리 제공하는 금액.",
    "계좌송금": "특정은행에 예금계좌를 가지고 있는 수령인에게 돈을 보내기 위하여 다른 특정 은행에 위탁하여 수령인 계좌에 예치하는 방법으로 하는 송금을 말한다. 이러한 계좌송금은 자행간 계좌송금과 타행간 계좌 송금으로 구분할 수 있다.",
    "고가도로": "시ㆍ군내 주요지역을 연결하거나 시ㆍ군 상호간을 연결하는 도로로서 지상교통의 원활한 소통을 위하여 공중에 설치하는 도로를 말한다.",
    "고도제한": "법률로써 건축물의 높이를 제한하는 일.",
    "고도지구": "쾌적한 환경 조성 및 토지의 효율적 이용을 위하여 건축물 높이의 최고한도를 규제할 필요에 의해 『국토의 계획 및 이용에 관한 법률』에 따라 도시ㆍ군관리계획으로 결정ㆍ고시된 용도지구를 말한다.",
    "고속도로": "고속국도(高速國道) 도로교통망의 중요한 축(軸)을 이루며 주요 도시를 연결하는 도로로서 자동차와 건설기계(최고속도 70킬로미터 이상, 트럭형식) 전용의 고속교통에 사용되는 도로를 말하며, 국토교통부장관이 지정ㆍ고시한다.",
    "고적지": "옛 문화를 보여 주는 건물이나 터.",
    "고층건축물": "층수가 30층 이상이거나 높이가 120미터 이상인 건축물을 말한다.",
    "골프회원권": "「체육시설의 설치ㆍ이용에 관한 법률」에 따른 회원제 골프장의 회원으로서 골프장을 이용할 수 있는 권리를 말한다.",
    "공개경쟁입찰": "입찰을 희망하는 모든 자격자가 입찰에 참가할 수 있고, 그 참가한 입찰자 가운데 가장 좋은 조건을 제시한 참가자를 선정하는 방식의 입찰.",
    "공개공지": "대지면적에서 일반이 사용할 수 있도록 설치하는 공개공지 또는 공개공간을 말한다. 도시환경을 쾌적하게 조성하기 위하여 일정 용도와 규모의 건축물은 일반이 사용할 수 있도록 소규모 휴게시설 등의 공개공지 또는 공개공간을 설치하여야 한다.",
    "공공시설": "도로, 공원, 철도, 수도 등 공공의 업무와 용도로 사용되는 시설을 말하며, 『국토의 계획 및 이용에 관한 법률』에서는 공공의 업무와 용도로 사용되는 다음의 시설을 공공시설로 규정하고 있다. 1.",
    "공공용수면": "국가, 지방자치단체 또는 대통령령으로 정하는 공공단체(한국수자원공사, 한국농어촌공사)가 소유하고 있거나 관리하는 내수면을 말한다.",
    "공공용재산": "국유재산법에서의 \"공공용재산\"이란 국가가 직접 공공용으로 사용하거나 행정재산으로 사용하기로 결정한 날부터 5년이 되는 날까지 사용하기로 결정한 재산을 말한다.",
    "공공용지": "공공건물이나 공공시설이 차지하는 터. 공공건물의 건축 면적과 정원, 녹지, 도로 면적 따위로 이루어진다.",
    "공공임대리츠": "한국 토지 주택 공사와 주택 기금이 공동 출자 하여 부동산 투자 회사를 설립한 다음, 민간 자본을 더하여 공공 임대 주택을 건설하는 사업. 임대 주택은 임차인에게 10년 동안 빌려주며 그 기간이 지나면 분양 전환권을 준다.",
    "공공택지": "국민주택건설사업 또는 대지조성사업, 택지개발사업, 산업단지개발사업, 공공주택지구조성사업, 공공지원민간임대주택 공급촉진지구 조성사업, 도시개발사업, 경제자유구역개발사업, 혁신도시개발사업, 행정중심복합도시건설사업, 공익사업 등 공공사업에 의하…",
    "공과금": "「국세징수법」에서 규정하는 체납처분의 예에 따라 징수할 수 있는 채권 중 국세, 관세, 임시수입부가세, 지방세와 이와 관계되는 체납처분비를 제외한 것을 말한다.",
    "공권력": "국가나 공공 단체가 우월한 의사의 주체로서 국민에게 명령하고 강제할 수 있는 권력.",
    "공동구": "전기ㆍ가스ㆍ수도 등의 공급설비, 통신시설, 하수도시설 등 지하매설물을 공동 수용함으로써 미관의 개선, 도로구조의 보전 및 교통의 원활한 소통을 위하여 지하에 설치하는 시설물을 말한다.",
    "공동담보": "1. 거래원 가운데 한 사람이 계약을 위반하여 생긴 손해를 공동으로 배상하는 담보. 2. 하나의 채권을 담보하기 위하여 여러 개의 물건에 담보 물권을 설정하는 일.",
    "공동인증서 재발급": "공동인증서를 저장매체에서 삭제 또는 공동인증서 암호 분실, 전자서명생성정보의 손상 등으로 기존 공동인증서의 잔여기간까지 사용가능한 새로운 공동인증서를 발급받는 것을 말한다.",
    "공동화현상": "1. 해외의 생산 활동 비중이 높아지면서 국내 생산 활동의 규모가 축소되는 일을 말한다. 무역 규모는 유지되지만 국내에서는 고용 문제가 생긴다. 2. 속이 텅 비게 되는 현상을 말한다.",
    "공매투자아카데미": "온비드 이용과 공매재테크에 도움을 드리기 위해 온비드에서 제공하는 설명회를 말한다. 공매횟수 공매횟수(公賣回數) 게재일자를 달리하여 전자자산처분시스템(온비드) 등에 당해 물건의 공매를 공고한 횟수를 말한다.",
    "공시지가": "국토 교통부 장관이 조사ㆍ평가하여 공시한 표준지의 단위 면적당 가격. 양도세ㆍ상속세 따위의 각종 토지 관련 세금의 과세 기준으로, 1989년 7월부터 시행되고 있다.",
    "공실률": "업무용 빌딩에서 비어 있는 사무실이 차지하는 비율.",
    "공업지역": "공업의 편익을 증진하기 위하여 『국토의 계획 및 이용에 관한 법률』에 따라 도시ㆍ군관리계획으로 결정ㆍ고시된 용도지역을 말하며, 전용공업지역, 일반공업지역, 준공업지역으로 세분한다.",
    "공영사업": "공공 단체가 공공의 행복과 이익을 위하여 직접 관리ㆍ경영하는 사업. 수도, 도서관, 병원, 양로원 따위가 있다.",
    "공영주차장": "공적인 기관에서 공공의 이익을 위하여 경영하거나 관리하는 주차장을 말한다.",
    "공영주택": "지방 공공 단체에서 건설하여 국민에게 싸게 팔거나 빌려주는 집.",
    "공용재산": "국가가 직접 사무용ㆍ사업용 또는 공무원의 주거용(직무 수행을 위하여 필요한 경우로서 대통령령으로 정하는 경우로 한정한다)으로 사용하거나 대통령령으로 정하는 기한까지 사용하기로 결정한 재산을 말한다.",
    "공원구역": "자연생태계와 자연 및 문화경관 등을 보전하고 지속 가능한 이용을 도모하기 위하여 자연공원으로 지정된 구역을 말한다.",
    "공원녹지": "쾌적한 도시환경을 조성하고 시민의 휴식과 정서 함양에 이바지하는 다음 각 목의 공간 또는 시설을 말한다. 가. 도시공원, 녹지, 유원지, 공공공지(公共空地) 및 저수지 나.",
    "공원마을지구": "자연공원을 효과적으로 보전하고 이용할 수 있도록 하기 위하여 공원관리청이 공원계획으로 결정한 용도지구로서 마을이 형성된 지역으로서 주민생활을 유지하는 데에 필요한 지역을 말한다.",
    "공원문화유산지구": "자연공원을 효과적으로 보전하고 이용할 수 있도록 하기 위하여 공원관리청이 공원계획으로 결정한 용도지구로서「문화재보호법」에 따른 지정문화재를 보유한 사찰(寺刹)과 전통사찰보존지 중 문화재의 보전에 필요하거나 불사(佛事)에 필요한 시설…",
    "공원자연보존지구": "자연공원을 효과적으로 보전하고 이용할 수 있도록 하기 위하여 공원관리청이 공원계획으로 결정한 용도지구로서 생물다양성이 특히 풍부한 곳, 자연생태계가 원시성을 지니고 있는 곳, 특별히 보호할 가치가 높은 야생 동식물이 살고 있는 곳,…",
    "공원자연환경지구": "자연공원을 효과적으로 보전하고 이용할 수 있도록 하기 위하여 공원관리청이 공원계획으로 결정한 용도지구로서 공원자연보존지구의 완충공간(緩衝空間)으로 보전할 필요가 있는 지역을 말한다.",
    "공유물의 분할청구": "공유자는 공유물의 분할을 청구할 수 있다. 그러나 5년내의 기간으로 분할하지 아니할 것을 약정할 수 있다.(계약을 갱신한 때에는 그 기간은 갱신한 날로부터 5년을 넘지 못한다) 분할의 방법에 관하여 협의가 성립되지 아니한 때에는 공…",
    "공유수면": "바다ㆍ바닷가 및 하천ㆍ호소(湖沼)ㆍ구거(溝渠), 그 밖에 공공용으로 사용되는 수면 또는 수류(水流)로서 국유인 것을 말한다.",
    "공유수면매립": "공유수면에 흙, 모래, 돌, 그 밖의 물건을 인위적으로 채워 넣어 토지를 조성하는 것(간척을 포함한다)을 말한다.",
    "공유자우선매수": "공유자는 매각기일까지 보증을 제공하고 최고매수신고가격과 같은 가격으로 채무자의 지분을 우선매수하겠다는 신고를 할 수 있으며, 이 경우 법원은 최고가매수신고가 있더라도 그 공유자에게 매각을 허가하여야 하는 것을 말한다.",
    "공유재산 관리": "공유재산 및 물품의 취득ㆍ운용과 유지ㆍ보존을 위한 모든 행위를 말한다.",
    "공유재산 처분": "공유재산 및 물품의 매각, 교환, 양여(讓與), 신탁, 현물 출자 등의 방법으로 공유재산 및 물품의 소유권이 해당 지방자치단체 외의 자에게 이전되는 것을 말한다.",
    "공유지분": "공동으로 소유하는 물건이나 재산 따위에 대한 각 공유자의 권리. 공유자 간의 합의나 법률의 규정에 의하여 정해지는데 그 지분이 분명하지 않은 경우, 민법에서는 각 공유자의 지분이 균등한 것으로 추정한다.",
    "공익단체": "온비드에서의 \"공익단체\"란 「사회복지사업법」에 따른 사회복지법인, 「사회적기업 육성법」에 따른 사회적기업, 「협동조합 기본법」에 따른 사회적협동조합, 「도시재생 활성화 및 지원에 관한 특별법」에 따른 마을기업, 「국민기초생활 보장법」에 따른 자활기업,…",
    "공익용산지": "임업생산과 함께 재해 방지, 수원 보호, 자연생태계 보전, 산지경관 보전, 국민보건휴양 증진 등의 공익 기능을 위하여 필요한 산지로서 다음의 산지를 대상으로 산림청장이 지정하는 산지를 말한다.",
    "공장용지": "제조업을 하고 있는 공장시설물의 부지 및 『산업집적활성화 및 공장설립에 관한 법률』 등 관련 법령에 따른 공장부지 조성공사가 준공된 토지와 이와 같은 구역에 있는 의료시설 등 부석시설물의 부지를 말한다.",
    "공정증서": "사법상 법률행위 기타 사권에 관한 사실에 관하여 공증인이 일정한 방식에 따라 작성하는 증서를 말한다. 공정증서는 소송에 있어서 강력한 증거력을 갖는다.",
    "공청회": "국회나 행정 기관에서 일의 관련자에게 의견을 들어 보는 공개적인 모임. 국민적인 관심의 대상이 되거나 사회 일반에 영향력이 큰 안건을 심의하기 전에, 국회나 행정 기관이 학자ㆍ경험자 또는 이해관계자를 참석하게 하여 의견을 듣는 공개회의이다.",
    "공한지": "1. 농사를 지을 수 있는데도 아무것도 심지 않고 놀리는 땅. 2. 집을 짓지 않은 빈터.",
    "과밀부담금": "과밀억제권역에 속하는 지역으로서 서울특별시에서 인구집중유발시설 중 업무용 건축물, 판매용 건축물, 공공 청사, 복합 건축물을 건축(신축ㆍ증축 및 공공 청사가 아닌 시설을 공공 청사로 하는 용도변경, 업무용시설이 아닌 시설에서 업무용시설등…",
    "과밀억제권역": "수도권의 인구와 산업을 적정하게 배치하기 위하여 수도권을 구분한 권역의 하나로서, 인구와 산업이 지나치게 집중되었거나 집중될 우려가 있어 이전하거나 정비할 필요가 있는 지역을 말한다.",
    "과세표준": "세법에 따라 직접적으로 세액산출의 기초가 되는 과세대상의 수량 또는 가액(價額)을 말한다.",
    "과수원": "사과ㆍ배ㆍ밤ㆍ호두ㆍ귤나무 등 과수류를 집단적으로 재배하는 토지와 이에 접속된 저장고 등 부속시설물의 부지. 다만, 주거용 건축물의 부지는 \"대\"로 한다.",
    "과실상계": "채무 불이행이나 불법 행위에 대해 채권자나 피해자에게도 과실이 있는 경우 법원이 이를 고려하여 배상액을 정하는 제도.",
    "과잉경매": "여러 개의 부동산을 매각하는 경우에 한 개의 부동산의 매각대금으로 모든 채권자의 채권액과 강제집행비용을 변제하기에 충분하면 다른 부동산의 매각을 허가하지 않는 것을 말한다.",
    "관리지역": "도시지역의 인구와 산업을 수용하기 위하여 도시지역에 준하여 체계적으로 관리하거나 농림업의 진흥, 자연환경 또는 산림의 보전을 위하여 농림지역 또는 자연환경보전지역에 준하여 관리의 필요에 의해 『국토의 계획 및 이용에 관한 법률』에 따라 도시ㆍ군관리계획…",
    "관리처분계획": "재개발 사업 시행 구역 안에 있는 종전의 토지나 건축물의 소유권과 지상권, 전세권, 임차권, 저당권과 같은 소유권 이외의 권리를 재개발 사업으로 조성된 토지와 축조된 건축 시설에 관한 권리로 변환하여 배분하는 일련의 계획.",
    "광업권": "탐사권과 채굴권을 말한다. ※ 탐사권 : 등록을 한 일정한 토지의 구역(광구)에서 등록을 한 광물과 이와 같은 광상(鑛床)에 묻혀 있는 다른 광물을 탐사하는 권리를 말한다.",
    "광역도시계획": "광역계획권의 장기발전방향을 제시하는 계획을 말한다. ※ 광역계획권 : 국토교통부장관 또는 도지사는 둘 이상의 특별시ㆍ광역시ㆍ특별자치시ㆍ특별자치도ㆍ시 또는 군의 공간구조 및 기능을 상호 연계시키고 환경을 보전하며 광역시설을 체계적으로 정비하기 위하여 필…",
    "광역시설": "기반시설 중 광역적인 정비체계가 필요한 둘 이상의 특별시ㆍ광역시ㆍ특별자치시ㆍ특별자치도ㆍ시 또는 군의 관할 구역에 걸쳐 있는 시설 또는 둘 이상의 특별시ㆍ광역시ㆍ특별자치시ㆍ특별자치도ㆍ시 또는 군이 공동으로 이용하는 시설을 말한다.",
    "광천지": "지하에서 온수ㆍ약수ㆍ석유류 등이 용출되는 용출구(湧出口)와 그 유지(維持)에 사용되는 부지를 말한다. 다만, 온수ㆍ약수ㆍ석유류 등을 일정한 장소로 운송하는 송수관ㆍ송유관 및 저장시설의 부지는 제외한다.",
    "교부청구": "국세징수법에 따라 관할 세무서장은 다음 각 호의 어느 하나에 해당하는 경우 해당 관할 세무서장, 지방자치단체의 장, 「공공기관의 운영에 관한 법률」 제4조에 따른 공공기관의 장, 「지방공기업법」 제49조 또는 제76조에 따른 지방공사 또는 지방공단의…",
    "교통시설": "교통수단의 운행에 필요한 도로ㆍ주차장ㆍ여객자동차터미널ㆍ화물터미널ㆍ철도ㆍ도시철도ㆍ공항ㆍ항만 및 환승시설 등을 말한다.",
    "교통영향평가": "사업의 시행에 따라 발생하는 교통량ㆍ교통흐름의 변화 및 교통안전에 미치는 영향을 조사ㆍ예측ㆍ평가하고 그와 관련된 각종 문제점을 최소화할 수 있는 방안을 마련하는 행위를 말한다.",
    "교통유발부담금": "교통혼잡을 완화하기 위하여 원인자 부담의 원칙에 따라 혼잡을 유발하는 시설물에 부과하는 경제적 부담을 말한다.",
    "구분건물": "1동의 건물을 구분하여 각 부분을 별개의 부동산으로 소유하는 형태를 건물의 구분소유라 하고, 구분된 건물부분을 구분건물이라 한다.",
    "구분등기": "1동의 건물에 독립하여 1개의 건물이 될 수 있는 부분이 수 개 있는 경우 그 각 부분을 양도하거나 그 부분만을 임대를 할 때에 이에 대응한 소유권이전등기나 임차권의 설정등기를 하기 위하여 그 한 동의 건물을 수개의 건물로 하는 등기를 말한다.",
    "구분소유권": "건물의 일부가 독립한 건물과 경제적으로 동일한 효용을 가지며, 사회 관념상 독립한 건물로 취급되는 경우에, 그에 대하여 독립된 소유권으로 인정하는 권리를 말한다.즉, 1동의 건물에 구조상 구분되는 2개 이상의 부분이 있을 때 그것들이 독립해서 주거,점…",
    "구분지상권": "타인 토지의 지하 또는 지상에 일정한 범위를 정하여 건물 기타 공작물을 소유하기 위해 그 구분층을 사용할 것을 내용으로 하는 지상권이다.",
    "구상권": "다른 사람을 위하여 그 사람의 빚을 갚은 사람이 다른 연대 채무자나 주된 채무자에게 상환을 요구할 수 있는 권리.",
    "국가소송": "국가가당사자(원고 또는 피고) 또는 참가인(보조참가 또는 독립당사자 참가)이 되는 소송을 말한다.",
    "국민주택규모": "주거의 용도로만 쓰이는 면적이 1호(戶) 또는 1세대당 85제곱미터 이하인 주택을 말한다. 다만 수도권을 제외한 도시지역이 아닌 읍 또는 면 지역은 1호 또는 1세대당 주거전용면적이 100제곱미터 이하인 주택을 말한다.",
    "국민주택채권": "국민주택사업에 필요한 자금을 조달하기 위하여 국민주택기금의 부담으로 발행하는 채권을 말하며, 국토교통부장관의 요청에 따라 기획재정부장관이 제1종국민주택채권, 제2종국민주택채권으로 구분하여 발행한다.",
    "국유재산 관리": "국유재산의 취득ㆍ운용과 유지ㆍ보존을 위한 모든 행위를 말하며, 총괄청(기획재정부 장관), 중앙관서의 장(「국가재정법」제6조에 따른 중앙관서의 장), 위임(조달청장 또는 지방자치단체의 장)ㆍ위탁(정부출자기업체 또는 특별법에 따라 설립된 법인으로서 대통령…",
    "국유재산 권리보전": "국유재산을 \"국\" 명의로 등기를 하여 국가의 소유권을 확보하고, 책임소재를 명확히 하기 위해 소관 중앙관서의 명칭을 \"국(중앙관서)\"과 같이 첨기 등기하고, 토지대장 소유자란을 등기부와 같이 \"국(중앙관서)\"으로 정리한 후 등기부, 토지(임야)대장(건…",
    "국채증권": "국채에 대한 권리를 표시하기 위하여 발행한 증권. 무기명 증권을 원칙으로 하나 권리자의 청구에 따라 등록 국채로 하거나 기명 증권을 발행할 수도 있다.",
    "굴삭기": "땅이나 암석 따위를 파거나, 파낸 것을 처리하는 기계를 통틀어 이르는 말.",
    "권리금": "토지 또는 건물의 임대차에 부수해서 그 부동산이 가지는 특수한 장소적 이익의 대가로서 임차인이 임대인에게 지급하는 금전.",
    "권리설정": "권리의 주체가 그 권리를 보유하면서 그 권리에 기하여 내용이 제한된 새로운 권리를 발생시키는 것을 말한다. 예컨대 소유자가 지상권이나 질권과 같은 제한물권을 설정하는 경우이다.",
    "권리소멸사실": "권리가 없어졌다는 객관적인 명제. 목적물의 멸실로 인한 소유권의 소멸 따위의 사유로 권리 자체가 완전히 없어지는 절대 소멸과 매매나 증여와 같이 권리가 이전되거나 변경되는 상대 소멸이 있다.",
    "권리증": "등기소에서 등기가 완료된 것을 증명하여 교부하는 서류. 이 서류의 소지인은 권리자로 추측된다.",
    "권리증권": "증권 인도에 따라 증권에 기재된 화물에 대한 권리가 이전됨을 약속하는 유가 증권. 예를 들면 선화 증권이 있다.",
    "권리증서": "어떤 주식을 보유한 자가 일정한 가격으로 일정한 수의 주식을 더 살 수 있도록 권리를 부여하는 증서. 주로 신주가 발행될 때 이용된다.",
    "권리질권": "부동산의 사용, 수익을 목적으로 하는 권리 외의 양도할 수 있는 재산권을 목적하는 질권을 말한다.",
    "권리질권에 관한 등기": "저당권으로 담보한 채권을 질권의 목적으로 한 때에는 그 저당권등기에 질권의 부기등기를 하여야 그 효력이 미치는 것이므로, 이때에는 그 취지의 등기를 하여야 한다.",
    "귀농어업인": "농어촌 이외의 지역에 거주하는 사람이(농업인 및 어업인이 아닌 사람) 농어업인이 되기 위하여 농어촌 지역으로 이주한 사람을 말하며, 농어촌지역으로 이주하기 직전 1년 이상 농어촌 외의 지역에 주민등록이 되어있고 농업경영체에 등록 또는 어업인에 해당하는…",
    "귀속재산": "서기 1948년 9월 11일부 대한민국정부와 미국정부간에 체결된 '재정 및 재산에 관한 최초 협정' 제5조의 규정에 의하여 대한민국정부에 이양된 일체의 재산으로 일본인 소유였던 재산, 일본법인, 일본기관소유 재산을 말한다.",
    "그린벨트": "도시의 무질서한 확산 방지와 도시의 자연환경 보전 따위를 위하여 국토 교통부 장관이 도시 개발을 제한하도록 지정한 구역.(= 개발제한구역)",
    "근린상업지역": "『국토의 계획 및 이용에 관한 법률』에 따라 도시ㆍ군관리계획으로 결정ㆍ고시된 상업지역의 하나로서 근린지역에서의 일용품 및 서비스의 공급을 위하여 필요한 지역을 말한다.",
    "근린생활시설": "건축물의 용도 구분의 하나로서 제1종 근린생활시설, 제2종 근린생활시설로 구분된다. ※ 세부 용도는 건축법 시행령 별표1 참조",
    "근저당": "장래에 생길 채권의 담보로서 저당권을 미리 설정함. 또는 그 저당권.",
    "근저당권": "계속적인 거래관계(예：당좌대월계약)로부터 발생하는 불특정 다수의 채권을 장래의결산기에 일정한 한도액까지 담보하기 위하여 설정하는 저당권을 말한다.",
    "기간시설": "도로ㆍ상하수도ㆍ전기시설ㆍ가스시설ㆍ통신시설ㆍ지역난방시설 등을 말한다.",
    "기간입찰": "경매 매각 방법의 하나. 입찰 기일을 확인하여 그 기간에 입찰표를 작성한 후 매수 신청 보증과 함께 등기 우편으로 제출하거나 집행관에게 직접 제출한다. 기간은 대개 1주일 이상 1개월 이하이다.",
    "기반시설": "교통시설, 공간시설, 유통ㆍ공급시설, 공공ㆍ문화체육시설, 방재시설, 보건위생시설, 환경기초시설로 다음의 시설(해당시설 그 자체의 기능발휘와 이용을 위하여 필요한 부대시설 및 편익시설 포함)을 말한다.",
    "기반시설부담구역": "개발밀도관리구역 외의 지역으로서 개발로 인하여 도로, 공원, 녹지 등 대통령령으로 정하는 기반시설의 설치가 필요한 지역을 대상으로 기반시설을 설치하거나 그에 필요한 용지를 확보하게 하기 위하여 『국토의 계획 및 이용에 관한 법률』제…",
    "기부물건": "온비드 이용기관회원이 공익단체회원에게 무상으로 제공하기 위해 온비드에 등록한 물건을 말한다. 기부채납 기부채납 국가ㆍ지방자치단체 외의 자가 재산의 소유권을 무상으로 국가 또는 지방자치단체에 이전하여 국가 또는 지방자치단체가 이를 취득하는 것을 말한다.",
    "기업용재산": "정부기업이 직접 사무용ㆍ사업용 또는 그 기업에 종사하는 직원의 주거용(직무 수행을 위하여 필요한 경우로 한정)으로 사용하거나 5년간 사용하기로 결정한 재산을 말한다.",
    "기일입찰": "경매 매각 방법의 하나. 정해진 매각 기일에 경매 법정에 출석하여 입찰표와 매수 신청 보증을 제출하는 방식으로 진행된다.",
    "기입등기": "새로운 등기원인에 준하여 어떤 사항을 등기부에 새로이 기입하는 등기로서, 보통 등기라고 하면 이것을 가리킨다. 소유권보존등기, 소유권이전등기, 저당권설정등기 등이 그것이다.",
}
TERM_GLOSSARY.update(ONBID_GLOSSARY_TERMS)


# 질문 답변(/api/ask)이 근거로 쓰는 온비드 공매 제도·절차 용어 설명이다. 온비드 이용안내·낙찰절차 안내·
# FAQ·입찰참가자준수규칙(2026-10-19 수집본)에서 옮겼고, 근거 원문과 위치는
# team-reports/2026-10-19-coach-onbid-terms/researcher-onbid-terms.md 에 있다(인용 137건 원자료 대조).
# text 는 그 표의 설명 칸을 글자 그대로 옮겼다(scratchpad 의 생성 스크립트로 만들었고 손으로 고치지 않았다).
# 뜻과 절차만 적는다 — 입찰 여부·법률·권리관계·수익성 판단은 담지 않는다.
# 사전(ONBID_GLOSSARY_TERMS)과 달리 손으로 고른 목록이라 2글자 용어(개찰·유찰·낙찰)도 둔다.
# scope 는 용어 탭(build_glossary)이 공고 분류에 맞춰 고를 때 쓴다. 값은 common · sale · lease ·
# 압류재산 · 국유재산 · 수탁재산 여섯 가지다(2026-10-19 용어 탭 작업 세션과 합의).
ONBID_GUIDE_TERMS: dict[str, dict[str, object]] = {
    '매각결정기일': {
        "text": "매각결정기일은 최고가 매수신청인(낙찰자)이 있을 때 매각허가 또는 불허가 결정을 선고하는 날입니다. 캠코 압류재산은 개찰일로부터 7일 이내(통상 개찰일의 다다음주 월요일 14:00, 공휴일·대체공휴일·토·일요일 제외)입니다. 정확한 날짜는 공고문이나 해당 공고의 '공고물건입찰정보'에서 확인합니다.",
        "source": '온비드 FAQ 「압류재산의 매각결정기일」 · 압류재산 인터넷공매 입찰참가자준수규칙 제12조③',
        "scope": '압류재산',
        "aliases": ('매각결정일', '매각결정일시'),
    },
    '인터넷공매': {
        "text": '인터넷공매는 한국자산관리공사가 운영하는 온비드로 하는 공매입니다. 입찰은 온비드 입찰화면에서 입찰서를 제출하는 방법으로 하고, 인증서로 입찰서에 전자서명합니다.',
        "source": '압류재산 인터넷공매 입찰참가자준수규칙 제4조5호 · 제5조②④',
        "scope": 'common',
        "aliases": ('인터넷입찰', '전자입찰'),
    },
    '인증서': {
        "text": "온비드 전자입찰에는 공동인증서나 간편인증서(개인회원만)가 필요합니다. 공동인증서는 '전자거래범용인증서'나 '온비드전용인증서'를 온비드에 등록해야 합니다. 은행용·증권용처럼 용도가 정해진 인증서는 등록할 수 없습니다. 간편인증서(무료)는 따로 등록하지 않고 바로 씁니다.",
        "source": '온비드 인증서 안내 · 온비드 이용안내 > 입찰참가 안내 STEP02',
        "scope": 'common',
        "aliases": ('공동인증서', '간편인증서', '온비드전용인증서', '전자거래범용인증서', '공인인증서'),
    },
    '입찰참가자준수규칙': {
        "text": '온비드 전자입찰에 참가해 입찰서를 제출할 때 지켜야 할 규칙입니다. 입찰서를 제출할 때 이 규칙에 동의합니다.',
        "source": '전자자산처분시스템 적정최고가입찰참가자 준수규칙 제1조 · 온비드 FAQ 「입찰서 제출 후 취소 또는 수정이 가능한가요?」',
        "scope": 'common',
        "aliases": ('준수규칙',),
    },
    '입찰참가신청': {
        "text": '입찰참가신청 절차를 거쳐 공고기관이 승인한 사람만 입찰에 참가할 수 있게 하는 방식입니다.',
        "source": '온비드 공고·물건 상세 도움말(입찰참가신청)',
        "scope": 'common',
        "aliases": (),
    },
    '공동입찰': {
        "text": "2인 이상이 함께 입찰에 참가하는 것입니다. 1인이 대표로 온비드에서 입찰서를 내고, 나머지는 '전자서명방식'이나 '서류제출방식'으로 참가합니다. 가능 여부는 공고기관이 정한 기준을 따릅니다.",
        "source": '온비드 공고·물건 상세 도움말(공동입찰) · 온비드 이용안내 > 입찰참가 안내 STEP04 · 압류재산 인터넷공매 입찰참가자준수규칙 제7조①',
        "scope": 'common',
        "aliases": ('공동명의 입찰', '공동 매수신청'),
    },
    '대리입찰': {
        "text": "회원이 입찰대리인이 되어 입찰자(본인)를 대신해 본인 명의로 입찰서를 제출하는 것입니다. 입찰서를 낸 뒤 '대리입찰신청서', '위임장' 등을 입찰마감시간 전까지 공고기관에 내야 유효한 입찰이 됩니다.",
        "source": '온비드 FAQ 「대리입찰 참가 가능 여부」 · 온비드 공고·물건 상세 도움말(대리입찰)',
        "scope": 'common',
        "aliases": ('대리 매수신청',),
    },
    '공매예정가격': {
        "text": '압류재산의 공매예정가격은 감정평가사 등이 감정평가한 금액을 기준으로 정하며, 공사가 임의로 정하지 않습니다.',
        "source": '온비드 FAQ 「공매예정가격은 어떻게 정해지나요?」',
        "scope": '압류재산',
        "aliases": (),
    },
    '일반경쟁·제한경쟁·지명경쟁': {
        "text": '국유재산 대부는 일반경쟁입찰이 원칙이고, 예외로 제한경쟁·지명경쟁·수의 방법을 허용합니다. 제한경쟁·지명경쟁은 인접 토지 소유자를 지명할 필요가 있을 때, 수의 대부 신청이 경합할 때, 대부계약자의 자격을 제한하거나 지명할 필요가 있을 때 씁니다.',
        "source": '온비드 FAQ 「국유재산을 대부받기 위하여 반드시 입찰에 참여하여야 하나요?」(분류 국유재산)',
        "scope": '국유재산',
        "aliases": ('일반경쟁', '제한경쟁', '지명경쟁'),
    },
    '최고가입찰': {
        "text": '최고가입찰 준수규칙은 입찰공고에서 정한 유효한 입찰참가자 가운데 가장 높은 가격을 낸 사람을 낙찰자로 정합니다.',
        "source": '전자자산처분시스템 최고가입찰참가자 준수규칙 제10조① · 온비드 물건상세 「입찰방식」',
        "scope": 'common',
        "aliases": ('최고가방식',),
    },
    '적정최고가입찰': {
        "text": '적정최고가입찰은 예비가격 추첨으로 정한 예정가격 이상으로 입찰한 사람 가운데, 예정가격에 가장 가까운 금액을 낸 사람을 낙찰자로 정하는 방식입니다. 예비가격은 이용기관이 정한 기준으로 고른 15개 가격입니다. 예정가격은 추첨 결과에 따라 이용기관이 정한 개수만큼의 예비가격을 산술 평균한 가격입니다.',
        "source": '전자자산처분시스템 적정최고가입찰참가자 준수규칙 제2조1~3호',
        "scope": 'common',
        "aliases": ('예비가격',),
    },
    '입찰보증금': {
        "text": '입찰보증금 납부계좌는 입찰서를 제출할 때 건별로 주어지고, 입찰 마감시간까지 내야 합니다. 압류재산(공매보증)은 공매예정가격의 10% 이상, 국유재산은 입찰금액의 5% 이상, 수탁재산은 입찰금액의 10% 이상입니다. 이용기관 물건은 기관이 정한 입찰금액의 일정률 이상입니다. 마감시간까지 내지 않으면 입찰이 무효입니다.',
        "source": '압류재산 인터넷공매 입찰참가자준수규칙 제8조①② · 국유재산 입찰참가자 준수규칙 제8조① · 인터넷공매입찰참가자준수규칙(수탁재산) 제6조① · 전자자산처분시스템 최고가입찰참가자 준수규칙 제8조① · 온비드 FAQ 「여러 개의 물건에 입찰참가시 보증금 입금방법」',
        "scope": 'common',
        "aliases": ('공매보증', '공매보증금'),
    },
    '입찰보증금 분할납부': {
        "text": '입찰보증금은 납부기한까지 전액을 한 번에 내야 합니다. 1천만 원을 넘으면 납부기한 전까지 나눠 낼 수 있습니다.',
        "source": '온비드 이용안내 > 입찰참가 안내 STEP05',
        "scope": 'common',
        "aliases": ('분할납부', '분납'),
    },
    '입찰참가수수료': {
        "text": '입찰참가수수료가 있는 물건은 입찰보증금과 수수료를 합한 금액을 한 번에 냅니다. 캠코가 집행하는 압류재산·국유재산 안내에는 입찰참가수수료가 없다고 적혀 있습니다.',
        "source": '온비드 FAQ 「보증금 외 참가수수료가 있는 경우 입금방법」 · 「입찰보증금과 수수료는 얼마인지?」',
        "scope": 'common',
        "aliases": ('참가수수료',),
    },
    '전자보증서': {
        "text": '입찰보증금을 현금 대신 보증보험증권으로 내기 위해 SGI서울보증에서 발급받는 증권입니다. 공고기관이 허용한 경우에만 쓸 수 있습니다. 온비드로 발급을 신청하는 것은 입찰마감일 전 영업일 18시 전까지만 됩니다.',
        "source": '온비드 공고·물건 상세 도움말(전자보증서) · 온비드 FAQ 「전자보증서비스 이용방법」',
        "scope": 'common',
        "aliases": ('입찰보증보험', '전자보증서비스'),
    },
    '환급계좌': {
        "text": '환급계좌는 낸 입찰보증금을 돌려받을 계좌입니다. 낙찰받지 못했거나 입찰이 취소된 경우처럼 환급 사유가 생기면 이 계좌로 돌려받습니다.',
        "source": '온비드 이용안내 > 입찰참가 안내 STEP04 · 온비드 모의입찰 입찰서 작성 화면',
        "scope": 'common',
        "aliases": ('환불계좌', '환불예금계좌'),
    },
    '입찰서 제출 뒤 취소·변경': {
        "text": '제출한 입찰서는 수정·변경·취소할 수 없습니다. 다만 같은 물건에 2회 이상 입찰서를 낼 수 있는 물건이면 같은 회차에 다시 입찰할 수 있습니다.',
        "source": '온비드 이용안내 > 입찰참가 안내 STEP04 · 온비드 FAQ 「입찰서 제출 후 취소 또는 수정이 가능한가요?」 · 전자자산처분시스템 최고가입찰참가자 준수규칙 제7조④',
        "scope": 'common',
        "aliases": ('입찰서 취소', '입찰서 수정', '입찰서 변경', '입찰 취소', '입찰 수정', '입찰 변경'),
    },
    '동일물건 2회 이상 입찰': {
        "text": '같은 회차의 같은 물건에 한 사람이 2회 이상 입찰할 수 있는지를 나타내는 항목입니다. 수탁재산은 한 사람이 여러 번 내면 가장 높은 가격의 입찰만 낙찰자 결정 대상으로 봅니다.',
        "source": '온비드 공고·물건 상세 도움말(동일물건 2회 이상 입찰) · 인터넷공매입찰참가자준수규칙(수탁재산) 제7조③',
        "scope": 'common',
        "aliases": ('2회 이상 입찰',),
    },
    '입찰 무효': {
        "text": '입찰 마감시간까지 입찰보증금을 내지 않으면 입찰이 무효입니다. 공동·대리입찰 서류를 마감 전에 내지 않거나 거짓으로 써서 낙찰받으면 낙찰이 무효입니다. 수탁재산은 보증금이 입찰금액의 10%에 못 미쳐도 무효입니다.',
        "source": '온비드 FAQ 「입찰보증금 납부시 유의사항」 · 압류재산 인터넷공매 입찰참가자준수규칙 제7조④ · 인터넷공매입찰참가자준수규칙(수탁재산) 제6조② · 온비드 FAQ 「「개인회원」의 입찰참여시 유의사항」',
        "scope": 'common',
        "aliases": ('낙찰 무효',),
    },
    '개찰': {
        "text": '개찰일시는 공고기관이 개찰을 시작하는 시각이며, 개찰이 끝난 뒤에 입찰결과를 볼 수 있습니다. 통상 캠코 국유재산은 목요일 09:30, 캠코 압류재산은 목요일 11:00에 개찰합니다. 그 밖의 이용기관 물건은 공고문에서 확인합니다.',
        "source": '온비드 이용안내 > 입찰참가 안내 STEP06 · 온비드 FAQ 「입찰 및 개찰 일정」 · 전자자산처분시스템 최고가입찰참가자 준수규칙 제9조',
        "scope": 'common',
        "aliases": ('개찰일시',),
    },
    '낙찰': {
        "text": "최고가 방식에서는 기준가격 이상으로 가장 높은 금액을 낸 유효한 입찰자가 낙찰자입니다. 기준가격은 압류재산 공매예정가격, 국유재산 대부(매각)예정가격, 수탁재산 공사 최저매매가격(공매공고가격)입니다. 이용기관 물건은 입찰공고가 정한 유효 입찰자 가운데 최고가격 입찰자입니다. 압류재산에서는 낙찰자를 '최고가 매수신청인'이라 하며, 매각결정을 거쳐 매수인이 됩니다.",
        "source": '압류재산 인터넷공매 입찰참가자준수규칙 제11조①1호 · 국유재산 입찰참가자 준수규칙 제13조①1호 · 인터넷공매입찰참가자준수규칙(수탁재산) 제9조① · 전자자산처분시스템 최고가입찰참가자 준수규칙 제10조①',
        "scope": 'common',
        "aliases": ('낙찰자', '최고가 매수신청인', '최고가 낙찰자'),
    },
    '무작위 추첨': {
        "text": '최고가 입찰자가 2인 이상이면, 온비드의 난수발생기로 입찰자마다 난수를 만들어 비교해 낙찰자를 자동으로 추첨합니다.',
        "source": '온비드 FAQ 「온비드에 설치된 난수발생기에 의한 자동추첨이란?」 · 압류재산 인터넷공매 입찰참가자준수규칙 제11조②',
        "scope": 'common',
        "aliases": ('자동추첨', '난수발생기', '동점'),
    },
    '1인 입찰': {
        "text": "캠코의 압류재산·국유재산·유입자산·국유증권은 예정가격 이상의 유효한 입찰이 있으면 그중 최고가 입찰자를 낙찰자로 정하므로 1인이 입찰해도 됩니다. 이용기관 물건은 법령과 기관 내규에 따라 다르니 물건상세의 '입찰 방법 및 입찰 제한 정보'와 공고문을 확인합니다. 2인 이상이 참가해야 유효한 입찰로 보는 물건에 1인만 참가하면 유찰됩니다.",
        "source": '온비드 FAQ 「온비드에서 1인이 입찰하면 어떻게 되나요?」 · 「공공기관에서 공고한 국유재산물건에 단독 입찰참가 하였는데 유찰된 이유」',
        "scope": 'common',
        "aliases": ('단독입찰', '혼자 입찰', '입찰 성립'),
    },
    '유찰': {
        "text": "온비드 입찰결과의 '유찰'은 내 입찰이 유찰됐다는 뜻이고, 두 경우가 있습니다. 물건은 다른 사람에게 낙찰되고 내가 떨어진 경우와, 물건 자체가 유찰돼 모든 입찰자의 입찰이 유찰된 경우입니다. 2인 이상 유효입찰자가 필요한 공매에 입찰자가 2인이 안 되거나, 입찰금액이 모두 예정가격 미만이면 물건이 유찰될 수 있습니다.",
        "source": "온비드 FAQ 「입찰결과에서 '유찰'의 의미」",
        "scope": 'common',
        "aliases": ('유찰자',),
    },
    '입찰금액 공개여부': {
        "text": "온비드는 공개여부와 상관없이 최종 낙찰자의 입찰금액을 공개합니다. '공개'면 낙찰자와 유효한 입찰자 모두의 금액이, '비공개'면 낙찰자 금액만 공개됩니다.",
        "source": '온비드 공고·물건 상세 도움말(입찰금액 공개여부)',
        "scope": 'common',
        "aliases": ('입찰금액 공개',),
    },
    '보증금 반환': {
        "text": '낙찰받지 못한 입찰자(입찰 무효·취소 포함)의 보증금은 지정한 환급계좌로 이자 없이 돌려줍니다. 개찰 완료 뒤 보통 당일 중 환불하지만, 계좌 오류나 은행 전산 사정으로 늦어질 수 있습니다.',
        "source": '압류재산 인터넷공매 입찰참가자준수규칙 제14조① · 국유재산 입찰참가자 준수규칙 제14조② · 전자자산처분시스템 최고가입찰참가자 준수규칙 제11조① · 온비드 FAQ 「유찰된 경우 환불 일시」',
        "scope": 'common',
        "aliases": ('보증금 환불', '입찰보증금 환불', '입찰보증금 반환', '공매보증 환불'),
    },
    '매각결정': {
        "text": '압류재산 공매에서 매각결정기일에 최고가 매수신청인을 매수인으로 정하는 결정입니다. 우선매수 신청, 매수인 제한 해당, 공매 취소·정지 사유 같은 사유가 있으면 하지 않습니다. 효력은 매각결정기일에 매각결정을 한 때 생깁니다.',
        "source": '압류재산 인터넷공매 입찰참가자준수규칙 제12조①③',
        "scope": '압류재산',
        "aliases": ('매각허가',),
    },
    '우선매수 신청': {
        "text": '압류 공매재산의 공유자(부부 공유 동산·유가증권은 배우자)는 매각결정기일 전까지 공매보증을 내고 우선매수를 신청할 수 있습니다. 전세사기피해주택이 공매되면 그 전세사기피해자도 같은 방식으로 신청할 수 있습니다. 우선매수 신청이 있으면 최고가 매수신청인은 매각결정기일 전까지 지위를 유지할지 신청해야 하고, 신청한 뒤에는 철회할 수 없습니다.',
        "source": '온비드 FAQ 「압류재산 우선매수 신청은 어떻게 하나요?」 · 압류재산 인터넷공매 입찰참가자준수규칙 제12조⑤',
        "scope": '압류재산',
        "aliases": ('우선매수', '공유자우선매수'),
    },
    '차순위 매수신청': {
        "text": "최고가 매수신청인 외의 매수신청인은 매각결정기일 전까지 공매보증을 내고 차순위 매수신청을 할 수 있습니다. 최고가 매수신청인이 대금을 내지 않아 매각결정이 취소되면 '최고가 매수신청가격에서 공매보증을 뺀 금액' 이상으로 사겠다는 신청입니다. 그 경우 취소한 날부터 3일(토·일·공휴일 제외) 안에 차순위 매수신청인에게 매각결정합니다. 낙찰자가 대금을 완납할 때까지 보증금 환불을 요구할 수 없고, 중간에 취소할 수도 없습니다.",
        "source": '압류재산 인터넷공매 입찰참가자준수규칙 제13조①③ · 온비드 FAQ 「차순위 매수신고시 입찰보증금은?」(분류 압류재산)',
        "scope": '압류재산',
        "aliases": ('차순위 매수신고',),
    },
    '차순위 신청': {
        "text": '최고가 낙찰자가 잔대금을 내지 않을 때 차순위 신청자가 낙찰자가 될 수 있도록, 입찰서를 낼 때 함께 신청하는 것입니다. 이용기관이 입찰공고에 적어 둔 경우에만 할 수 있습니다. 입찰서를 낸 뒤에는 취소할 수 없습니다. 압류재산은 국세징수법 절차를 따릅니다.',
        "source": '온비드 공고·물건 상세 도움말(차순위 신청) · 전자자산처분시스템 최고가입찰참가자 준수규칙 제7조의2①',
        "scope": 'common',
        "aliases": (),
    },
    '매각결정기일 연기': {
        "text": '최고가 매수신청인이나 우선매수신청인이 다른 법령상 매수 자격을 갖추지 못했다면, 매각결정기일을 1회에 한해 당초 기일부터 10일 이내로 연기할 수 있습니다. 차순위 매수신청인은 연기를 신청할 수 없습니다.',
        "source": '압류재산 인터넷공매 입찰참가자준수규칙 제12조② · 온비드 FAQ 「압류재산의 매각결정기일 연기」',
        "scope": '압류재산',
        "aliases": ('매각결정기일 연기신청',),
    },
    '매각결정통지서': {
        "text": '매각결정 뒤 받는 통지서이며, 대금 납부기한이 여기에 적혀 있습니다. 온비드의 이 서비스는 캠코 압류재산에만 있고, 다른 재산은 각 기관이 직접 발급합니다.',
        "source": '온비드 FAQ 「매각결정통지서 및 잔대금납부영수증은 어디서 출력하나요?」 · 온비드 이용안내 > 낙찰절차 안내(압류재산) STEP02',
        "scope": '압류재산',
        "aliases": (),
    },
    '대금납부기한': {
        "text": '[압류재산] 매각결정통지서에 적힌 납부기한까지 잔대금납부계좌로 냅니다. 낙찰금액이 3,000만 원 미만이면 매각결정기일로부터 7일, 3,000만 원 이상이면 30일입니다. 공매공고 시점에 따라 기한이 다르니 입찰 전에 물건정보에서 확인합니다. [국유재산 매각] 매매계약을 맺은 날부터 60일 안에 전액을 냅니다. [국유재산 대부] 낙찰일로부터 5영업일 안에 공사 지정계좌로 냅니다. [수탁·유입재산] 매매계약서에 적힌 납부기일까지 중도금과 잔대금을 냅니다. [이용기관 물건] 낙찰 뒤 계약과 대금 납부 절차는 공고기관마다 정하므로 공고문을 확인합니다.',
        "source": '온비드 이용안내 > 낙찰절차 안내(재산유형별 탭)',
        "scope": 'common',
        "aliases": ('잔대금', '잔금', '매수대금', '매각대금', '중도금', '대금 납부'),
    },
    '납부최고': {
        "text": '압류재산 매수인이 매수대금을 기한까지 내지 못하면, 납부최고일로부터 10일 이내로 기한을 다시 정합니다. 촉구를 받고도 지정 기한까지 내지 않으면 매각결정이 취소됩니다(공고문 기준).',
        "source": '온비드 FAQ 「압류재산 매수대금 납부기한을 연장해주세요」 · 온비드 압류재산 공매공고 1건(전북지역본부 2026년 제010차) 15-가④',
        "scope": '압류재산',
        "aliases": ('매수대금 납부의 촉구', '납부 촉구'),
    },
    '매각결정 취소': {
        "text": '매각결정기일 전에 체납액 납부 같은 압류 해제 사유가 생겨 공매대행의뢰기관이 공매 취소를 요청하면 매각결정이 취소될 수 있습니다. 낙찰자가 대금을 내지 않아 취소되면 차순위 매수신고인에게 새로 매각결정합니다.',
        "source": '온비드 이용안내 > 낙찰절차 안내(압류재산) STEP01 · 온비드 FAQ 「차순위 매수신고시 입찰보증금은?」',
        "scope": '압류재산',
        "aliases": (),
    },
    '보증금 귀속': {
        "text": '[압류재산] 매수대금 촉구를 받고도 내지 않아 매각결정이 취소되는 경우 등에는, 매수인이 낸 공매보증을 돌려주지 않는다고 압류재산 공고문이 적고 있습니다. [국유재산] 낙찰자가 계약을 맺지 않으면 낙찰은 무효가 되고 입찰보증금은 국고에 귀속됩니다. 계약 뒤 잔대금을 내지 않아도 계약이 해제되고 계약보증금이 국고에 귀속됩니다. [수탁재산] 낙찰자가 계약을 맺지 않으면 낙찰은 무효가 되고 입찰보증금은 매도자에게 귀속됩니다. [이용기관 물건] 기한 안에 계약을 맺지 않았을 때 입찰보증금을 어떻게 처리할지는 이용기관이 정합니다.',
        "source": '온비드 압류재산 공매공고 1건(전북지역본부 2026년 제010차) 15-나 · 국유재산 입찰참가자 준수규칙 제15조① · 제16조 · 인터넷공매입찰참가자준수규칙(수탁재산) 제11조① · 전자자산처분시스템 최고가입찰참가자 준수규칙 제13조',
        "scope": 'common',
        "aliases": ('보증금 몰수', '몰수', '국고 귀속', '매도자 귀속'),
    },
    '계약보증금': {
        "text": '낙찰자(압류재산은 최고가 매수신청인)가 낸 입찰보증금은 계약보증금이 됩니다.',
        "source": '압류재산 인터넷공매 입찰참가자준수규칙 제14조① · 국유재산 입찰참가자 준수규칙 제14조① · 인터넷공매입찰참가자준수규칙(수탁재산) 제10조①',
        "scope": 'common',
        "aliases": (),
    },
    '차액납부': {
        "text": '차액납부 대상인 최고가 매수신청인은 매각결정기일 전까지, 매수대금에서 자신이 배분받을 금액을 뺀 금액만 내겠다고 신청할 수 있습니다. 허용되면 대금납부기한을 따로 정하지 않고 배분기일에 정해진 시간 전까지 냅니다.',
        "source": '온비드 압류재산 공매공고 1건(전북지역본부 2026년 제010차) 14-가·다',
        "scope": '압류재산',
        "aliases": ('매수대금의 차액납부',),
    },
    '등기촉탁': {
        "text": '압류재산 소유권이전은 공사의 등기촉탁으로만 할 수 있고, 매수인이 직접 등기소에 촉탁서를 접수할 수 없습니다. 매수인은 필요한 서류를 갖춰 물건 담당 부점에 우편이나 방문으로 내고 등기촉탁을 의뢰합니다.',
        "source": '온비드 FAQ 「압류재산 소유권이전절차 및 유의사항」 · 온비드 이용안내 > 낙찰절차 안내(압류재산) STEP04',
        "scope": '압류재산',
        "aliases": ('소유권이전 등기촉탁',),
    },
    '명도책임': {
        "text": '압류재산 공고문은 부동산 명도책임을 매수인이 지고, 동산은 보관 중인 곳에서 현 상태로 넘긴다고 적습니다. 수탁재산은 명도책임이 물건마다 다르며, 공사가 책임지는 경우 소송 등으로 늦어지면 그 사유가 끝난 때에 명도·인도합니다.',
        "source": '온비드 압류재산 공매공고 1건(전북지역본부 2026년 제010차) 4-다 · 인터넷공매입찰참가자준수규칙(수탁재산) 제15조 · 온비드 수탁재산 공매공고 1건(2026년 제9회) 첨부',
        "scope": 'sale',
        "aliases": ('명·인도책임', '명도'),
    },
    '수의계약': {
        "text": '국유재산 대부는 일반경쟁입찰이 원칙이고 수의 방법은 예외로 허용됩니다. 한 국유재산 대부 공고는 2회 이상 유찰된 물건만 같은 조건으로 수의계약을 신청할 수 있고, 개찰일 이후부터 다음 입찰일 전날 사이에 신청한다고 적습니다. 한 수탁재산 공고는 매각되지 않은 일부 물건을 다음 공매 공고 전까지 유찰(수의)계약으로 요청할 수 있되, 위임기관과 협의해 진행한다고 적습니다.',
        "source": '온비드 FAQ 「국유재산을 대부받기 위하여 반드시 입찰에 참여하여야 하나요?」 · 온비드 국유재산 대부입찰 공고 1건(2026년 제13회) 첨부 12-가·나 · 온비드 수탁재산 공매공고 1건(2026년 제9회) 첨부 8-⑧',
        "scope": 'common',
        "aliases": ('유찰계약', '유찰(수의)계약'),
    },
    '공매재산명세서': {
        "text": '압류재산의 권리 관련 사항을 안내하는 자료입니다. 입찰시작 7일 전부터 입찰마감 전까지 물건 상세페이지 [입찰정보] 탭에서 볼 수 있습니다. 배분요구와 채권신고 현황도 여기서 확인합니다.',
        "source": '온비드 FAQ(압류재산) 2건',
        "scope": '압류재산',
        "aliases": ('공매재산명세',),
    },
    '배분요구의 종기': {
        "text": '공매공고 등기·등록 전에 등기·등록되지 않은 채권자가 배분을 받으려면, 배분요구의 종기까지 채권신고 및 배분요구서를 서면으로 내야 합니다. 개별 공매재산의 종기는 공고의 표시목록에 적혀 있습니다.',
        "source": '온비드 FAQ 「배분요구 종기일(언제까지 권리신고를 해야 하는지)」 · 온비드 압류재산 공매공고 1건(전북지역본부 2026년 제010차) 6',
        "scope": '압류재산',
        "aliases": ('배분요구 종기', '배분요구 종기일', '배분요구'),
    },
    '입찰 보류': {
        "text": '체납자가 체납액 일부를 내거나 이의신청·심사청구·소송제기 같은 사유가 생겨 공매를 보류하고 입찰도 멈춘 상태를 말합니다.',
        "source": '온비드 FAQ 「입찰 보류란?」',
        "scope": '압류재산',
        "aliases": ('공매 보류',),
    },
    '공매 취소·정지': {
        "text": '체납자 등 이해관계인이 공매와 관계된 세금을 내면 공매를 취소합니다. 일부 납부·송달불능·이의신청 같은 사유로 취소된 경우, 그 사유가 풀리면 다시 공매합니다.',
        "source": '온비드 FAQ 「압류재산의 매각절차 중지 및 취소」',
        "scope": '압류재산',
        "aliases": ('공매 취소', '공매 정지', '공매의 취소', '입찰의 취소'),
    },
    # ---- 아래 5건은 용어 탭 작업 세션(2026-10-19)이 더했다. 근거 정리본은
    # team-reports/2026-10-19-onbid-journey-conformance/researcher-onbid-journey.md 와 커뮤니티 조사
    # docs/60_본선준비/24_공매초보_어려움_커뮤니티조사_20261019.md 1-1·1-4 다. 뜻과 절차만 적고 판단은 담지 않는다.
    '최저입찰가격': {
        "text": "이 회차에 입찰할 수 있는 가장 낮은 금액입니다. 감정평가금액과 다를 수 있고, 회차가 여러 개인 공고는 회차마다 값이 다를 수 있습니다. 「비공개」로 표시되면 이용기관이 공개하지 않기로 한 것입니다(온비드 화면도 「비공개」로 표시합니다).",
        "source": '온비드 물건 상세 가격 표시 규칙(최저입찰가격 비공개 구분) · 온비드 국유재산 대부 공고 회차별 입찰일정 표',
        "scope": 'common',
        "aliases": ('최저입찰가', '최저 입찰가격'),
    },
    '감정평가금액': {
        "text": "감정평가업자가 평가한 재산의 가격입니다. 최저입찰가격과 다를 수 있고, 둘이 어떤 관계인지는 공고마다 다르므로 공고 원문에서 확인합니다.",
        "source": '온비드 자료실 용어사전 「감정가격」 · 온비드 물건 상세 감정평가금액 표시값',
        "scope": 'common',
        "aliases": ('감정평가액',),
    },
    '입찰참가자격': {
        "text": "공고가 정한 입찰 가능 조건입니다. 조건에 맞지 않으면 입찰이 무효가 될 수 있습니다. 괄호 안 표기(사업자 등)가 있으면 그 뜻은 참가자격 조항 원문과 담당기관에서 확인합니다.",
        "source": '온비드 공고문 입찰참가자격 조항 · 공공데이터 온비드 물건 입찰상세(getCltrBidInf2) 자격·지역·기타 제한 필드',
        "scope": 'common',
        "aliases": ('참가자격', '입찰자격', '입찰 자격'),
    },
    '소유권이전': {
        "text": "[압류재산] 잔대금을 낸 뒤 매수인이 서류·비용·우표를 준비해 캠코 관할 부점에 우편이나 방문으로 내고, 캠코가 등기를 촉탁합니다. 매수인이 등기소에 직접 낼 수는 없습니다. [국유재산 매각] 잔대금을 낸 뒤 이전서류를 받아 매수자가 직접 이전등기를 합니다. [수탁·유입재산] 위임기관에서 이전서류를 받아 매수자가 등기 신청합니다. [이용기관 물건] 절차와 비용은 공고문이 정합니다.",
        "source": '온비드 FAQ 「압류재산 소유권이전절차 및 유의사항」 · 온비드 이용안내 > 낙찰절차 안내(압류재산 STEP03~05 · 국유재산 매각 STEP03 · 수탁재산 STEP03 · 기타 탭)',
        "scope": 'sale',
        "aliases": ('소유권이전등기', '이전등기', '등기 이전'),
    },
    '대부료': {
        "text": "재산을 빌려 쓰는 대가로 내는 돈입니다. [국유재산 대부] 낙찰일로부터 5영업일 이내에 대부료 잔금을 공사 지정계좌에 내고, 신분증·주민등록등본·인장을 지참해 대부계약을 맺습니다. 계약을 맺지 않으면 낙찰이 무효가 되고 입찰보증금은 국고에 귀속됩니다. [이용기관 물건] 사용료·임대료의 납부 기한과 계약 절차는 공고기관마다 정하므로 공고문을 확인합니다.",
        "source": '온비드 FAQ 「국유재산 대부계약 체결 방법은?」 · 온비드 이용안내 > 낙찰절차 안내(국유재산 대부 STEP01~02 · 기타 탭) · 국유재산 입찰참가자 준수규칙 제15조①',
        "scope": 'lease',
        "aliases": ('대부료 잔금', '연간대부료'),
    },
}

# 질문 하나에 붙이는 용어 설명의 상한이다. 많이 붙이면 답보다 설명이 길어진다.
ONBID_REFERENCE_LIMIT = 3


def onbid_reference_entries() -> list[dict[str, object]]:
    """질문에서 찾을 용어 목록. 손으로 고른 절차 용어를 먼저 두고, 같은 용어는 사전에서 다시 싣지 않는다.

    사전 용어는 3글자 이상만 찾는다. 2글자(매각·임대·대부 등)는 어느 질문에나 우연히 들어맞아
    「임대료는 언제 내나요?」에도 「임대」 뜻풀이가 붙는다(ONBID_GLOSSARY_TERMS 머리 주석과 같은 이유).
    """
    entries: list[dict[str, object]] = []
    for term, item in ONBID_GUIDE_TERMS.items():
        names = (term, *item.get("aliases", ()))
        entries.append({
            "term": term, "names": names, "text": item["text"], "source": item["source"],
            "scope": item.get("scope", ""), "minLength": 1,
        })
    for term, meaning in TERM_GLOSSARY.items():
        # TERM_GLOSSARY 의 처음 9건은 캠코 회의(2026-09-07)에서 받은 설명이고 나머지는 온비드 용어사전이다.
        source = "온비드 자료실 용어사전" if term in ONBID_GLOSSARY_TERMS else "온비드 운영기관(캠코) 안내"
        entries.append({"term": term, "names": (term,), "text": meaning, "source": source, "scope": "", "minLength": 3})
    return entries


def _word_positions(question: str) -> tuple[set[int], set[int]]:
    """띄어쓰기를 지운 질문에서 낱말 자리를 모은다.

    첫째는 낱말마다 앞 문장부호를 건너뛴 첫 글자 자리, 둘째는 낱말이 시작하는 자리(낱말 경계)다.
    find_onbid_references 의 compact 와 같은 str.split() 으로 자르므로 두 자리는 compact 기준이다.
    """
    heads: set[int] = set()
    bounds: set[int] = set()
    offset = 0
    for token in (question or "").split():
        bounds.add(offset)
        # 문장부호만 있는 낱말이면 다음 낱말의 시작 자리가 들어갈 뿐이라 따로 거르지 않는다.
        heads.add(offset + re.match(r"[^\w]*", token).end())
        offset += len(token)
    return heads, bounds


def find_onbid_references(question: str, limit: int = ONBID_REFERENCE_LIMIT) -> list[dict[str, str]]:
    """질문에 나온 온비드 용어를 찾아 설명·출처·scope 를 질문 속 순서대로 돌려준다.

    띄어쓰기를 지우고 비교하므로 「매각 결정 기일」도 찾는다. 긴 이름부터 보고, 이미 고른 이름과
    자리가 겹치는 짧은 이름은 버린다. 「매각결정기일」을 찾았으면 그 안의 「매각결정」은 따로 싣지 않는다.
    겹치는 자리 말고 다른 자리에 또 나오면 그 자리를 쓴다.
    """
    compact = "".join((question or "").split())
    if not compact:
        return []
    word_starts, word_bounds = _word_positions(question)
    candidates: list[tuple[str, dict[str, object]]] = []
    for entry in onbid_reference_entries():
        for name in entry["names"]:
            key = re.sub(r"\s+", "", str(name))
            if key and len(key) >= int(entry["minLength"]):
                candidates.append((key, entry))
    # 길이가 같으면 entries 순서대로 절차 용어가 앞에 선다(안정 정렬). 그래서 사전에 같은 이름이 있으면
    # 그 사전 용어는 자리가 겹쳐 버려진다. 사전의 「공유자우선매수」·「계약보증금」은 법원 경매나 일반 사전
    # 기준이라, 온비드 공매 절차 설명과 함께 내면 서로 어긋난다.
    candidates.sort(key=lambda pair: -len(pair[0]))
    taken: list[tuple[int, int]] = []
    found: list[tuple[int, dict[str, str]]] = []
    for key, entry in candidates:
        if len(found) >= limit:
            break
        if any(item["term"] == entry["term"] for _start, item in found):
            continue
        span = None
        for match in re.finditer(re.escape(key), compact):
            start, end = match.start(), match.end()
            # 2글자 이름은 낱말 첫머리에서 시작하고 낱말 경계를 넘지 않을 때만 받는다. 낱말 가운데(「설명도」의
            # 「명도」)나 띄어쓰기를 건넌 자리(「공동 점유」의 「동점」·「두 명 도장」의 「명도」)에서 잡으면
            # 엉뚱한 설명이 붙는다(2026-10-19 리뷰 r1 P1-1 · r2 P2-a).
            if len(key) <= 2 and (start not in word_starts or any(start < b < end for b in word_bounds)):
                continue
            if any(start < t_end and t_start < end for t_start, t_end in taken):
                continue
            span = (start, end)
            break
        if span is None:
            continue
        taken.append(span)
        found.append((span[0], {
            "term": str(entry["term"]), "text": str(entry["text"]), "source": str(entry["source"]),
            "scope": str(entry["scope"]),
        }))
    return [item for _start, item in sorted(found, key=lambda pair: pair[0])]



# 용어 탭에 올리는 절차 용어 — ONBID_GUIDE_TERMS(질문창과 같은 사전) 가운데 커뮤니티 조사에서 초보자가
# 뜻을 물은 용어만 고른 목록이다(docs/60_본선준비/24_공매초보_어려움_커뮤니티조사_20261019.md 1-1~1-4).
# 사전 전부를 올리면 공통 용어만 30건이 넘어 탭이 읽히지 않는다. 뜻풀이는 사전에서 읽으므로 여기에는 키만 둔다.
# 항목의 scope 가 공고 분류와 맞을 때만 보여 준다. 사전에 실제로 쓰인 scope 값은 common · sale · lease ·
# 압류재산 · 국유재산 다섯이다(2026-10-19 실측 · 「수탁재산」 scope 항목은 아직 없다).
# 순서: 재산유형 전용 → 매각/임대 전용 → 공통. 초보자가 가장 찾는 유형별 용어(매각결정기일 · 차순위 · 명세서)가
# 공통 용어 10여 건 뒤에 묻히지 않게 한다(리뷰 r3 제안).
GLOSSARY_TAB_TERMS: tuple[str, ...] = (
    "최저입찰가격",
    "감정평가금액",
    "입찰보증금",
    "입찰참가자격",
    "입찰서 제출 뒤 취소·변경",
    "개찰",
    "유찰",
    "낙찰",
    "보증금 반환",
    "입찰 무효",
    "대금납부기한",
    "보증금 귀속",
    "소유권이전",
    "명도책임",
    "대부료",
    "매각결정기일",
    "매각결정통지서",
    "차순위 매수신청",
    "공매재산명세서",
    "배분요구의 종기",
    "등기촉탁",
    "공매 취소·정지",
)

# 사전 text 가 「[압류재산] … [국유재산 매각] … [수탁·유입재산] … [이용기관 물건] …」처럼 재산유형 머리표로
# 묶여 있으면, 공고 분류에 맞는 조각만 남긴다. 머리표가 없거나 맞는 조각이 없으면 원문 그대로다.
# 머리표는 어휘로 잠근다. 사전 text 에는 산문 대괄호(「물건 상세페이지 [입찰정보] 탭」)도 있어, 대괄호를
# 전부 머리표로 보면 그 뒤 본문이 잘려 나갈 수 있다(리뷰 r3 R3-3 · 2026-10-19 사전 50건 전수에서 머리표 7종).
GUIDE_TEXT_HEAD_RE = re.compile(r"\[(압류재산|국유재산(?: 매각| 대부)?|수탁(?:·유입)?재산|이용기관 물건)\]\s*")


def _guide_text_for(text: str, asset_type: str, disposition_label: str) -> str:
    parts = GUIDE_TEXT_HEAD_RE.split(text)
    # 머리표가 없으면 heads 가 비어 picked 도 비므로 아래 「not picked」 한 곳에서 원문으로 돌아간다.
    lead = parts[0].strip()
    heads = parts[1::2]
    bodies = [body.strip() for body in parts[2::2]]
    asset_type = asset_type or ""
    # 매각·임대 판정은 _notice_scopes 와 한 곳에서만 한다(둘이 갈리면 용어 선택과 머리표 선택이 어긋난다).
    scopes = _notice_scopes(asset_type, disposition_label)
    is_lease = "lease" in scopes
    is_sale = "sale" in scopes
    # exact 는 머리표와 글자까지 같아야 하고, prefix 는 머리표가 그 낱말로 시작하면 된다(「수탁·유입재산」 · 「이용기관 물건」).
    exact: list[str] = []
    prefix: list[str] = []
    if "압류재산" in asset_type:
        exact = ["압류재산"]
    elif "국유재산" in asset_type:
        # 「국유재산」 하나로만 묶인 글(보증금 귀속)과 매각·대부로 갈라 묶인 글(대금납부기한)이 둘 다 있다.
        # 임대와 매각 낱말이 함께 있는 라벨(「임대/매각」)은 미상과 같이 둘 다 남긴다(리뷰 r3 R3-4).
        if is_lease and not is_sale:
            exact = ["국유재산 대부", "국유재산"]
        elif is_sale and not is_lease:
            exact = ["국유재산 매각", "국유재산"]
        else:
            exact = ["국유재산 매각", "국유재산 대부", "국유재산"]
    elif "수탁재산" in asset_type:
        prefix = ["수탁"]
    elif "공유재산" in asset_type or "기타일반재산" in asset_type:
        prefix = ["이용기관"]
    picked = [body for head, body in zip(heads, bodies) if head in exact or any(head.startswith(w) for w in prefix)]
    if not picked:
        return text
    return " ".join(part for part in [lead, *picked] if part)


def _notice_scopes(asset_type: str, disposition_label: str) -> set[str]:
    """이 공고에 보여 줄 절차 용어의 scope 집합.

    매각·임대 판정은 처분방식 표기(와 압류재산 여부)만 본다. app.js 의 보드 판정은 공고명(title)도 보므로
    둘은 비슷하되 같지 않다(리뷰 r1 #4).
    """
    asset_type = asset_type or ""
    disposition_label = disposition_label or ""
    scopes = {"common"}
    if re.search(r"매각|공매", disposition_label) or "압류" in asset_type:
        scopes.add("sale")
    if re.search(r"임대|대부", disposition_label):
        scopes.add("lease")
    for name in KNOWN_ASSET_TYPES:
        if name in asset_type:
            scopes.add(name)
    return scopes


def build_glossary(asset_type: str = "", disposition_label: str = "", title: str = "") -> list[dict[str, str]]:
    """기본 용어(group=basic · ONBID_GUIDE_TERMS 가운데 GLOSSARY_TAB_TERMS 에 든 것)를 앞에,
    공고 표기에 든 사전 용어(group=match · TERM_GLOSSARY)를 뒤에 둔다."""
    scopes = _notice_scopes(asset_type, disposition_label)
    entries: list[dict[str, str]] = []
    # 재산유형 전용(0) → 매각/임대 전용(1) → 공통(2). 같은 등급 안에서는 GLOSSARY_TAB_TERMS 순서를 지킨다.
    scope_rank = {"common": 2, "sale": 1, "lease": 1}
    ordered = sorted(GLOSSARY_TAB_TERMS, key=lambda t: scope_rank.get(str(ONBID_GUIDE_TERMS.get(t, {}).get("scope")), 0))
    for term in ordered:
        item = ONBID_GUIDE_TERMS.get(term)
        if not item or item.get("scope") not in scopes:
            continue
        entries.append(
            {
                "term": term,
                "meaning": _guide_text_for(str(item["text"]), asset_type, disposition_label),
                "source": str(item.get("source", "")),
                "group": "basic",
            }
        )
    seen: set[str] = set()
    for value in (asset_type, disposition_label, title):
        for term, meaning in TERM_GLOSSARY.items():
            if term in (value or "") and term not in seen:
                seen.add(term)
                entries.append({"term": term, "meaning": meaning, "group": "match"})
    return entries


def build_notice(raw_url: str) -> dict[str, object]:
    final_url, text = fetch_onbid(raw_url)
    inputs = hidden_inputs(text)
    parsed_final = urllib.parse.urlparse(final_url)
    params = urllib.parse.parse_qs(parsed_final.query)
    page_type = "공고 상세" if "PbancDtlInqController" in final_url else "물건 상세"

    pbanc_mng_no = class_text(text, "getPbancMngNo") or inputs.get("pbancMngNo") or inputs.get("onbidPbancMngNo", "")
    onbid_pbanc_no = inputs.get("onbidPbancNo") or single_query_value(params, "onbidPbancNo")
    notice_id = pbanc_mng_no or onbid_pbanc_no
    onbid_cltr_no = inputs.get("onbidCltrno") or single_query_value(params, "onbidCltrno")
    cltr_mng_no = inputs.get("cltrMngNo") or inputs.get("cltrMngNoInq") or single_query_value(params, "cltrMngNo")
    pbct_no = inputs.get("pbctNo") or single_query_value(params, "pbctNo")
    pbct_cdtn_no = inputs.get("pbctCdtnNo") or single_query_value(params, "pbctCdtnNo")
    cltr_detail = fetch_onbid_cltr_detail(
        final_url,
        params,
        {
            "onbidCltrno": onbid_cltr_no,
            "onbidPbancNo": onbid_pbanc_no,
            "pbctCdtnNo": pbct_cdtn_no,
            "pbctNo": pbct_no,
        },
    )
    cltr_mng_no = cltr_mng_no or clean_text(str(cltr_detail.get("cltrMngNo") or ""))
    related_urls = build_related_urls(
        final_url,
        params,
        {
            "onbidCltrno": onbid_cltr_no,
            "onbidPbancNo": onbid_pbanc_no,
            "pbctNo": pbct_no,
            "pbctCdtnNo": pbct_cdtn_no,
        },
    )
    # getCltrBidInf2 는 cltrMngNo 와 pbctCdtnNo 를 둘 다 요구한다 — 하나만 보내면
    # resultCode=11 NO_MANDATORY_REQUEST_PARAMETERS_ERROR 가 온다. 그런데 공고 상세 URL 로
    # 들어오면 화면 hidden input 과 쿼리 어디에도 pbctCdtnNo 가 없어서, 이 API 가 호출 목록에
    # 들어가지도 못했다(2026-09-07 등록 이후 2026-10-18 까지 호출 0회).
    # 그 값은 fetch_onbid_cltr_detail() 이 받아 오는 cltrInfVO 에 이미 들어 있다(필드 119개
    # 중 하나 · 2026-10-18 실측). 공공데이터 호출용으로만 여기서 보충한다.
    # 관련 URL 생성에는 넣지 않는다 — 화면에서 온 값으로 만들던 기존 동작을 그대로 둔다.
    api_pbct_cdtn_no = pbct_cdtn_no or clean_text(str(cltr_detail.get("pbctCdtnNo") or ""))
    public_data = fetch_public_data_bundle(
        {
            "pbancMngNo": pbanc_mng_no,
            "cltrMngNo": cltr_mng_no,
            "pbctCdtnNo": api_pbct_cdtn_no,
        }
    )
    api_entries = [item for item in public_data.get("items", []) if isinstance(item, dict)]
    items_by_service = public_data.get("itemsByService")
    item_bid_entries = (
        items_by_service.get("item_bid_detail", []) if isinstance(items_by_service, dict) else []
    )
    item_bid_entry = item_bid_entries[0] if item_bid_entries else {}

    title = (
        class_text(text, "getPbancNm")
        or inputs.get("btbdTitlNm")
        or inputs.get("onbidCltrNm")
        or values_after_label(text, "물건명")
        or api_value(api_entries, "pbancNm", "cltrNm", "cltrHstrNm", "goodsNm", "itemNm")
        or "온비드 공고/물건"
    )

    # 온비드 좌측 내비게이션에도 "재산유형" 라벨이 있어 values_after_label이 메뉴 문구를
    # 먼저 집는다. 물건상세는 hidden input, 공고상세는 머리 배지가 정확하므로 그쪽을 먼저 본다.
    # 라벨 값은 알려진 재산유형일 때만 받는다 — 메뉴 문구가 화면 세 곳에 찍히던 경로를 막는다.
    asset_type = (
        inputs.get("scrnCltrPrptDivNm")
        or asset_type_badge(text)
        or known_asset_type(values_after_label(text, "재산유형"))
        or inputs.get("ctgrFullNm")
        or api_value(api_entries, "prptDvsnNm", "prptDivNm", "cltrPrptDivNm", "ctgrFullNm", "cltrPrptDvsnNm")
        or "재산유형 확인"
    )
    disposition = inputs.get("dspsMthodNm") or ("임대" if "대부입찰" in title else "")
    if not disposition:
        badge_text = clean_text(" ".join(re.findall(r"<li[^>]*class=(?:\"[^\"]*\bop_cm_badge\b[^\"]*\"|'[^']*\bop_cm_badge\b[^']*')[^>]*>(.*?)</li>", text[:330000], flags=re.I | re.S)))
        disposition = "임대" if "임대" in badge_text else "매각" if "매각" in badge_text else ""
    if not disposition:
        disposition = api_value(api_entries, "dpslMtdNm", "dspsMthodNm", "dpslMthdNm", "pbctMtdNm")
    disposition_label = disposition or ("매각/공매" if "압류재산" in asset_type else "처분방식 확인")

    agency = values_after_label(text, "공고기관") or api_value(api_entries, "pbancInstNm", "dpslMchnNm", "orgNm", "instNm") or "공고기관 확인"
    contact = (
        strip_placeholder_segments(values_after_label(text, "담당부점"))
        or strip_placeholder_segments(values_after_label(text, "담당기관"))
        or api_value(api_entries, "chargeDeptNm", "chrgrDeptNm", "picDeptNm", "chargerTel", "ctacTel")
        or agency
    )
    bid_method = (
        values_after_label(text, "입찰방식")
        or inputs.get("cptnMthodNm")
        or api_value(api_entries, "bidMtdNm", "biddingMtdNm", "cptnMthodNm", "bidTypeNm", "pbctMtdNm")
        or "입찰방식 확인"
    )
    bid_type = "전자입찰" if "전자입찰" in text else values_after_label(text, "입찰구분") or api_value(api_entries, "bidDvsnNm", "bidKindNm") or "입찰구분 확인"
    notice_date = values_after_label(text, "공고일") or values_after_label(text, "최초공고일자") or inputs.get("pbctBgngDt", "")[:10] or api_value(api_entries, "pbancDt", "fstPbancDt")
    cltr_bid_begin = clean_text(str(cltr_detail.get("pbctBegnDtm") or ""))
    cltr_bid_end = clean_text(str(cltr_detail.get("pbctDdlnDt") or ""))
    if inputs.get("pbctBgngDt") and inputs.get("pbctLastDdlnDt"):
        bid_period = f"{inputs['pbctBgngDt']} ~ {inputs['pbctLastDdlnDt']}"
    else:
        bid_period = values_after_label(text, "입찰기간")
    if not bid_period and (cltr_bid_begin or cltr_bid_end):
        bid_period = f"{cltr_bid_begin} ~ {cltr_bid_end}".strip(" ~")
    api_start = api_value(api_entries, "pbctBegnDtm", "bidBgngDt", "bidBgngDtm", "pbctStrtDt")
    api_end = api_value(api_entries, "pbctClsDtm", "bidClsDt", "bidClsgDtm", "pbctEndDt", "pbctLastDdlnDt")
    if not bid_period and (api_start or api_end):
        bid_period = f"{api_start} ~ {api_end}".strip(" ~")
    bid_deadline = inputs.get("pbctLastDdlnDt") or cltr_bid_end or api_end
    minimum_bid = minimum_bid_value(
        inputs,
        (
            inputs.get("lowstBidPrc")
            or values_after_label(text, "공매예정가격(원)")
            or clean_text(str(cltr_detail.get("lowstBidPrc") or ""))
            or api_value(api_entries, "minBidPrc", "lowstBidPrc", "fstBidPrc", "pbctExpcPrc", "bidPrc")
        ),
        clean_text(str(cltr_detail.get("lowstBidPrcHideDivCd") or "")),
    ) or api_value(api_entries, "lowstBidPrcIndctCont")
    appraisal = (
        inputs.get("cltrApslEvlAvgAmt")
        or values_after_label(text, "감정평가금액(원)")
        or clean_text(str(cltr_detail.get("cltrApslEvlAvgAmt") or ""))
        or api_value(api_entries, "apslAmt", "cltrApslEvlAvgAmt", "aprsPrc")
    )
    cltr_land_sqms = float(cltr_detail.get("landSqms") or 0) or None
    cltr_bld_sqms = float(cltr_detail.get("bldSqms") or 0) or None
    area = (
        values_after_label(text, "면적")
        or (f"{cltr_land_sqms}㎡" if cltr_land_sqms else "")
        or (f"{cltr_bld_sqms}㎡" if cltr_bld_sqms else "")
        or api_value(api_entries, "area", "lndArea", "bldArea", "ar")
    )
    sections = split_sections(text)
    related_docs = extract_related_docs(text, final_url)
    attachment_chunks, attachment_reads = attachment_doc_reads(related_docs)
    doc_checklist = build_doc_checklist(sections, asset_type, related_docs, attachment_chunks, contact, attachment_reads)
    required_docs = [str(item["name"]) for item in doc_checklist["items"]]
    notice_outline = extract_notice_outline(sections)
    countdown = bid_countdown(bid_period, bid_deadline)

    core_id = notice_id
    if page_type == "물건 상세" and onbid_cltr_no:
        core_id = f"{notice_id or '공고'} / 물건 {onbid_cltr_no}"

    notice: dict[str, object] = {
        "sourceUrl": final_url,
        "inputUrl": raw_url,
        "relatedUrls": related_urls,
        "mode": "실제 온비드 페이지 분석",
        "pageType": page_type,
        "noticeId": core_id,
        "title": title,
        "agency": agency,
        "assetType": asset_type,
        "disposition": disposition,
        "dispositionLabel": disposition_label,
        "bidMethod": bid_method,
        # 「입찰방법」 절의 원문 표시값을 그대로 옮긴다. 못 읽으면 빈 문자열이고 화면이 「원문 확인」을 띄운다.
        "jointBidAllowed": bid_method_flag(sections, "공동입찰"),
        # 표본 3/23 에서만 나온다. 값이 없으면 빈 문자열이고 화면은 행 자체를 만들지 않는다.
        "evictionResponsibility": eviction_responsibility(sections),
        "bidType": bid_type,
        "noticeDate": notice_date or "공고일 확인",
        "round": values_after_label(text, "회차") or "",
        "contact": contact,
        "onbidCltrno": onbid_cltr_no,
        "onbidPbancNo": onbid_pbanc_no,
        "pbancMngNo": pbanc_mng_no,
        "cltrMngNo": cltr_mng_no,
        "pbctNo": pbct_no,
        "pbctCdtnNo": pbct_cdtn_no,
        "bidPeriod": bid_period,
        "bidDeadline": bid_deadline,
        "minimumBidPrice": minimum_bid,
        "appraisalPrice": appraisal,
        "area": area,
        "relatedDocs": related_docs,
        "requiredDocs": required_docs,
        "docChecklist": doc_checklist,
        # 아래 세 값은 getCltrBidInf2 응답에서만 온다. 그 API 가 응답하지 않으면(식별자가
        # 없거나 차수가 끝난 물건) 모두 빈 값이고, 화면은 빈 값일 때 해당 블록을 그리지 않는다.
        "bidParticipationApply": build_bid_participation_apply(item_bid_entry),
        "apiDocTerms": build_bid_doc_terms(item_bid_entry),
        "bidLimits": build_bid_limits(item_bid_entry),
        "noticeOutline": notice_outline,
        "countdown": countdown,
        "glossary": build_glossary(asset_type, disposition_label, title),
    }

    price_candidates = []
    if minimum_bid:
        price_candidates.append(
            {
                "title": "최저입찰가격",
                "value": minimum_bid,
                "note": (
                    "이용기관이 공개하지 않기로 선택한 값입니다. 온비드도 「비공개」로 표시합니다."
                    if minimum_bid == PRICE_UNDISCLOSED
                    else "온비드 상세 페이지 표시값"
                ),
            }
        )
    if appraisal:
        price_candidates.append(
            {
                "title": "감정평가금액",
                "value": appraisal,
                # 공매는 최저입찰가격이 감정평가금액보다 높게도 낮게도 정해진다(2026-10-19 커뮤니티 조사 3-4).
                # 두 값의 관계는 계산하지 않고 다르다는 사실만 적는다.
                "note": "온비드 상세 페이지 표시값입니다. 최저입찰가격과 다를 수 있고, 둘의 관계는 공고 원문에서 확인하십시오.",
            }
        )
    price_candidates.extend(extract_cost_terms(sections, minimum_bid))
    if not price_candidates:
        price_candidates.append({"title": "비용 후보", "value": "공고 원문 확인", "note": "보증금, 대부료, 납부 방식은 원문 기준 확인"})

    notice["costs"] = price_candidates
    deadline_passed, deadline_stamp = bid_deadline_passed(bid_period, bid_deadline)
    notice["alerts"] = []
    if deadline_passed:
        notice["alerts"].append(
            {
                "title": "입찰 마감 지남",
                "value": f"{deadline_stamp} 마감",
                "note": "분석 시각 기준 입찰 마감일시가 지났습니다. 진행 여부는 온비드 원문과 담당기관에서 확인하십시오.",
                "status": "warn",
            }
        )
    elif countdown.get("label"):
        notice["alerts"].append(
            {
                "title": str(countdown["label"]),
                "value": f"{countdown['deadline']} 마감",
                "note": "화면 표시 전용입니다. 이 서비스는 메일·푸시 알림을 보내지 않으니 마감 일정은 직접 캘린더에 옮기십시오.",
                "status": "warn" if countdown["state"] == "urgent" else "check",
            }
        )
    notice["alerts"].extend([
        {
            "title": "입찰기간",
            "value": bid_period or bid_deadline or NOTICE_VALUE_FALLBACK,
            "note": "입찰 시작/마감 시각을 캘린더에 옮기기 전 원문을 재확인합니다.",
            "status": "warn",
        },
        {
            "title": "제출서류",
            # 첫 서류 이름 하나만 보이면 서류가 한 건뿐인 것처럼 읽힌다(2026-10-19 여정 점검 · 9건 중 1건 표시).
            "value": str(doc_checklist["headline"]),
            "note": str(doc_checklist["profile"]["detail"]),
            "status": "check",
        },
    ])
    notice["risks"] = [
        {
            "title": "공고 유형 착오",
            "reason": f"현재 페이지는 {asset_type} / {disposition_label}로 추출되었습니다.",
            "question": "내가 찾는 임대/매각/공매 목적과 이 공고 유형이 맞는가?",
            "source": "온비드 상세 페이지 > 재산유형/처분방식",
        },
        {
            "title": "서류 제출 방식 착오",
            "reason": "제출서류와 제출방법은 공고별로 달라질 수 있습니다.",
            "question": "원본 제출, 직접 제출, 공동/대리입찰 서류 조건을 확인했는가?",
            "source": "온비드 상세 페이지 > 제출서류",
        },
        {
            "title": "가격·비용 오해",
            "reason": "공매예정가격, 감정평가금액, 보증금, 대부료는 서로 다른 값입니다.",
            "question": "입찰금액 외 실제 납부해야 할 비용과 납부 일정을 확인했는가?",
            "source": "온비드 상세 페이지 > 가격/입찰정보",
        },
        {
            "title": "담당기관 확인 필요",
            "reason": "본 MVP는 입찰 여부, 법률 판단, 권리관계 판단을 제공하지 않습니다.",
            "question": "담당부점 또는 공고기관에 확인해야 할 항목을 분리했는가?",
            "source": "온비드 상세 페이지 > 공고기관/담당부점",
        },
    ]
    notice["boardTasks"] = build_tasks(notice, required_docs)
    notice["aiCoach"] = build_ai_coach(notice, required_docs)
    notice["watchlist"] = [
        {
            "notice": "비교 공고 후보",
            "type": "관심조건 검색 필요",
            "next": "지역/재산유형 조건 입력 후 후보 선택",
            "status": "미선택",
        },
        {
            "notice": "창업 공간 후보",
            "type": "관심조건 검색 필요",
            "next": "용도 제한 및 시설 상태 확인",
            "status": "담당기관 확인 필요",
        },
    ]
    notice["todayActions"] = [
        {"title": task["title"], "value": task["action"], "note": task["detail"], "status": "check"}
        for task in notice["boardTasks"][:3]
    ]
    notice["analysisMeta"] = {
        "finalUrl": final_url,
        "pageType": page_type,
        "publicData": {
            "status": public_data.get("status"),
            "message": public_data.get("message"),
            "services": public_data.get("services", []),
            "identifiers": {
                "pbancMngNo": pbanc_mng_no,
                "cltrMngNo": cltr_mng_no,
                # 실제 API 호출에 쓴 값을 적는다. 화면에서 온 pbct_cdtn_no 를 적으면
                # 보충이 동작했는지를 이 보고로 확인할 수 없다.
                "pbctCdtnNo": api_pbct_cdtn_no,
            },
        },
        "extractedFields": [key for key, value in notice.items() if isinstance(value, str) and value],
    }
    return notice


# /api/ask 오남용 방지 속도 제한. 로그인이 없는 서비스라 IP를 식별자로 쓰고,
# 메모리 내 카운터라 서버 재시작 시 리셋된다(DB 도입은 범위 밖).
ASK_RATE_LIMIT_PER_MINUTE = 5
ASK_RATE_LIMIT_PER_HOUR = 30
_ask_rate_lock = threading.Lock()
_ask_rate_log: dict[str, deque] = {}


def check_ask_rate_limit(client_ip: str) -> str | None:
    now = time.time()
    with _ask_rate_lock:
        timestamps = _ask_rate_log.setdefault(client_ip, deque())
        while timestamps and now - timestamps[0] > 3600:
            timestamps.popleft()
        minute_count = sum(1 for t in timestamps if now - t <= 60)
        if minute_count >= ASK_RATE_LIMIT_PER_MINUTE:
            return "질문이 너무 많습니다. 1분 후 다시 시도하세요."
        if len(timestamps) >= ASK_RATE_LIMIT_PER_HOUR:
            return "질문이 너무 많습니다. 잠시 후 다시 시도하세요."
        timestamps.append(now)
        return None


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        parsed = urllib.parse.urlparse(path)
        safe_path = parsed.path.lstrip("/")
        return str(ROOT / safe_path)

    def end_headers(self) -> None:
        # Cache-Control 이 없으면 브라우저가 재검증 없이 디스크 캐시를 그대로 쓴다 —
        # 코드를 고쳐도 화면이 안 바뀌는 것처럼 보이는 문제가 2026-10-01·10-04·10-08
        # 세 번 반복됐다. no-cache 는 캐시 자체는 허용하되 매번 서버에 재검증(조건부
        # GET)을 강제한다 — SimpleHTTPRequestHandler 가 If-Modified-Since 를 이미 처리한다.
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def send_json(self, status: int, payload: dict[str, object]) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/version":
            # server 는 기동 시점 판, current 는 지금 디스크의 판이다. 둘이 다르면 화면이 재시작을 알린다.
            self.send_json(200, {
                "ok": True, "server": SERVER_REVISION, "startedAt": SERVER_STARTED_AT, "current": code_revision(),
            })
            return
        if parsed.path == "/api/analyze":
            query = urllib.parse.parse_qs(parsed.query)
            raw_url = (query.get("url") or [""])[0]
            try:
                notice = build_notice(raw_url)
                self.send_json(200, {"ok": True, "notice": notice})
            except (ValueError, urllib.error.URLError, TimeoutError) as exc:
                self.send_json(400, {"ok": False, "error": str(exc)})
            except Exception as exc:
                self.send_json(500, {"ok": False, "error": f"분석 중 오류가 발생했습니다: {exc}"})
            return
        super().do_GET()

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/ask":
            try:
                length = int(self.headers.get("Content-Length", "0") or "0")
                raw_body = self.rfile.read(length) if length > 0 else b""
                payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
                question = str(payload.get("question") or "").strip()[:500]
                notice = payload.get("notice") if isinstance(payload.get("notice"), dict) else {}
                docs_raw = payload.get("docs") if isinstance(payload.get("docs"), list) else []
                docs = [str(item) for item in docs_raw][:10]
                if not question:
                    self.send_json(400, {"ok": False, "error": "질문을 입력하세요."})
                    return
                limit_message = check_ask_rate_limit(self.client_address[0])
                if limit_message:
                    self.send_json(429, {"ok": False, "error": limit_message})
                    return
                board = sanitize_board_state(payload.get("board"))
                result = answer_notice_question(notice, docs, question, board)
                self.send_json(200, {"ok": True, "result": result})
            except (ValueError, urllib.error.URLError, TimeoutError) as exc:
                self.send_json(400, {"ok": False, "error": str(exc)})
            except Exception as exc:
                self.send_json(500, {"ok": False, "error": f"질문 처리 중 오류가 발생했습니다: {exc}"})
            return
        self.send_json(404, {"ok": False, "error": "not found"})


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    server = ThreadingHTTPServer((HOST, port), Handler)
    print(f"Serving OnBid MVP on http://{HOST}:{port}/")
    server.serve_forever()


if __name__ == "__main__":
    main()
