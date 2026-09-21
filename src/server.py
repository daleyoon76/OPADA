from __future__ import annotations

import html
import http.cookiejar
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


HOST = "127.0.0.1"
PORT = 8975
ROOT = Path(__file__).resolve().parent
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
        "detail": "이용기관이 직접 작성하는 공고라 본문은 요약만 두고 목록을 첨부 공고문에 담는 경우가 많습니다. 아래 첨부파일을 함께 확인하십시오.",
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

# 이 절/문장이 입찰 전 준비물인지 낙찰 후 계약 서류인지 표시한다.
# 표본 6건의 목록이 계약 단계 서류였다(표본조사 §4-7).
CONTRACT_STAGE_RE = re.compile(r"계약\s*(?:체결|시|을)|낙찰\s*(?:자|후|일)|사용\s*허가\s*(?:신청|일)|매매계약")

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
}


def find_doc_names(line: str) -> list[str]:
    names: list[str] = []
    masked = line
    for label, pattern in DOC_NAME_PATTERNS:
        for match in re.finditer(pattern, masked):
            name = label or clean_text(match.group(0))
            if name and name not in names:
                names.append(name)
            masked = masked[: match.start()] + ("\x00" * (match.end() - match.start())) + masked[match.end() :]
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


def extract_doc_items(
    sections: dict[str, str],
    attachment_chunks: list[tuple[str, str]] | None = None,
) -> list[dict[str, object]]:
    """공고문·제출서류 절과 첨부 텍스트에서 조건별 서류 항목을 뽑는다.

    한 줄이 조건 문구만 담고 서류명이 없으면 그 조건을 다음 하위 항목들에 물려준다.
    새 상위 번호(1. / 가.)가 조건 없이 나오면 물림을 끊는다.
    첨부는 label 이 DOC_SEARCH_SECTIONS 밖의 값("첨부:파일명")이라 sourceSection 으로
    본문/첨부 출처를 구분할 수 있다.
    """
    items: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    chunks = [(title, sections.get(title, "")) for title in DOC_SEARCH_SECTIONS]
    chunks.extend(attachment_chunks or [])
    for title, chunk in chunks:
        if not chunk:
            continue
        # 첨부는 온비드 공고 절과 문장 구조가 다르다(표·서식·PDF 텍스트화 결과라 「제출」·「지참」
        # 같은 동사가 그 줄에 없을 때가 많다). DOC_REQUEST_RE 게이트를 그대로 걸면 실측
        # 재현율이 어휘 그대로 매칭한 것보다 낮아진다(2026-09-12 측정 · 배선 38% vs 첨부모의 59%).
        # 그래서 첨부 줄은 서류명이 잡히면 그 자체로 요구로 본다 — 조건 태깅(carried 로직)은 그대로 살린다.
        is_attachment = title not in DOC_SEARCH_SECTIONS
        carried: list[dict[str, str]] = []
        # 「라. 계약체결시 필요서류」처럼 단계를 밝히는 줄은 제목뿐이고, 그 아래 표 행(「개인
        # 주민등록초본, 인감증명서…」)에는 단계 단어가 없다. 조건 물림과 같은 구조라 같은
        # 방식으로 물린다 — 안 물리면 표 아래 항목이 전부 기본값 「입찰 전」으로 오분류된다
        # (2026-09-12 · #15 실측).
        carried_stage = False
        for raw_line in block_text(strip_tooltips(chunk)).split("\n"):
            line = raw_line.strip()
            # 1200자 상한은 «지저분한 HTML»을 걸러내려는 것이다(공고 절 기준). PDF/HWP 첨부는
            # 줄바꿈 없이 문서 전체가 한 줄로 텍스트화될 때가 있어(실측 최대 89,290자) 상한을
            # 그대로 걸면 그 안의 서류명이 통째로 빠진다(2026-09-12 · 32건 실측). 첨부는 상한을 안 건다.
            if not line or (len(line) > 1200 and not is_attachment):
                continue
            conditions = [item for item in find_conditions(line) if not item["negative"]]
            names = find_doc_names(line)
            if not names:
                if conditions and DOC_REQUEST_RE.search(line):
                    carried = conditions
                elif LINE_RESET_RE.match(line):
                    carried = []
                if CONTRACT_STAGE_RE.search(line):
                    carried_stage = True
                elif LINE_RESET_RE.match(line):
                    carried_stage = False
                continue
            carried_applies = bool(carried) and bool(SUB_ITEM_RE.match(line))
            # 첨부는 조건 물림 구조(번호·하위항목 서식)가 공고 절과 다르게 깨져 있어, 조건을
            # 잘못 붙이면(엉뚱한 줄의 「법인」이 따라붙는 등) 맞는 항목을 조건 불일치로 놓친다.
            # 조건 없이 "공통"으로 두는 편이 실측상 더 맞다(2026-09-12 · 배선 47%→59%로 상승 확인).
            active = [] if is_attachment else (conditions or (carried if carried_applies else []))
            # 「업종·자격 요건」 축은 `등록증`·`면허` 같은 서류명 토큰으로 잡히므로
            # 그것만으로 제출 요구를 증명하지 못한다. authorizing 축에서 뺀다.
            authorizing = [item for item in conditions if item["key"] != "license"]
            if not authorizing and not carried_applies and not DOC_REQUEST_RE.search(line) and not is_attachment:
                # 조건 문맥도 제출 동사도 없으면 단순 언급이다(예: 「부동산의 표시는
                # 등기사항증명서 기준」). 서류 요구로 세지 않는다. 첨부는 위에서 게이트를 뺐다.
                continue
            extras = doc_extras(line)
            stage = "낙찰 후·계약 시" if (CONTRACT_STAGE_RE.search(line) or carried_stage) else "입찰 전"
            labels = [item["label"] for item in active] or ["공통"]
            for name in names:
                key = (name, " · ".join(labels))
                if key in seen:
                    continue
                seen.add(key)
                howto, howto_url = DOC_HOWTO.get(name, ("", ""))
                items.append(
                    {
                        "name": name,
                        "conditions": labels,
                        "conditionKeys": [item["key"] for item in active],
                        "copy": extras.get("copy", ""),
                        "validity": extras.get("validity", ""),
                        "method": extras.get("method", ""),
                        "due": extras.get("due", ""),
                        "count": extras.get("count", ""),
                        "stage": stage,
                        "howto": howto,
                        "howtoUrl": howto_url,
                        "sourceSection": title,
                        "evidence": line[:300],
                    }
                )
    return items


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
) -> dict[str, object]:
    profile = doc_source_profile(asset_type)
    items = extract_doc_items(sections, attachment_chunks)
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


def attachment_doc_chunks(attachments: list[dict[str, str]]) -> list[tuple[str, str]]:
    """첨부 목록을 내려받아 텍스트화하고, extract_doc_items 가 쓸 (label, text) 쌍으로 낸다."""
    chunks: list[tuple[str, str]] = []
    for doc in attachments[:ATTACHMENT_MAX_COUNT]:
        url = doc.get("downloadUrl", "")
        if not url:
            continue
        try:
            data = fetch_attachment_bytes(url)
        except Exception:  # noqa: BLE001 — 첨부 하나 다운로드 실패가 전체를 막지 않는다
            continue
        if not data or len(data) > ATTACHMENT_MAX_BYTES:
            continue
        text = attachment_text(data)
        if text.strip():
            chunks.append((f"첨부:{doc.get('name', '')}", text))
    return chunks


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
                "note": f"온비드 원문 표시값입니다. 기준이 되는 최저입찰가격은 {minimum_bid_display or '원문 확인'}입니다.",
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
                    "note": "온비드 원문 표시값입니다.",
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


def minimum_bid_value(inputs: dict[str, str], raw_value: str) -> str:
    hide_code = (inputs.get("lowstBidPrcHideDivCd") or "").strip()
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


def public_data_service_key() -> str:
    for name in ("ONBID_API_SERVICE_KEY", "DATA_GO_KR_SERVICE_KEY", "PUBLIC_DATA_SERVICE_KEY"):
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return ""


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
    model = os.environ.get("VERTEX_GEMINI_MODEL", os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")).strip()
    return {"project": project, "location": location, "model": model or "gemini-2.5-flash-lite"}


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
    }


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
    price_value = notice.get("minimumBidPrice") or notice.get("bidDeposit") or "공고 원문 확인"
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
            "action": notice.get("bidPeriod") or "입찰기간 원문 확인",
            "due": notice.get("bidDeadline") or "입찰 전",
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
                "최저입찰가격이 「비공개」이면 이용기관이 공개하지 않기로 선택한 것입니다. 보증금은 이 값에 이용기관이 정한 비율을 곱해 정해집니다."
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
        {
            "id": "agency",
            "title": "담당기관에 물어볼 질문 정리",
            "action": notice.get("contact") or notice.get("agency") or "담당기관 확인",
            "due": "입찰 전",
            "detail": "AI가 법률·권리관계 판단을 대신하지 않고, 사용자가 담당기관에 확인해야 할 문장으로 분리합니다.",
            "question": "서류 제출 방식, 낙찰 후 절차, 비용 납부 방식 중 내가 담당기관에 확인할 항목을 정리합니다.",
            "source": "온비드 상세 페이지 > 공고기관/담당부점",
            "cta": "온비드 원문",
            "url": final_url,
            "defaultDone": False,
        },
    ]
    return tasks


def local_ai_coach(notice: dict[str, object], docs: list[str]) -> dict[str, object]:
    asset_type = str(notice.get("assetType") or "재산유형 확인")
    disposition = str(notice.get("dispositionLabel") or "처분방식 확인")
    bid_period = str(notice.get("bidPeriod") or notice.get("bidDeadline") or "입찰기간 원문 확인")
    price = str(notice.get("minimumBidPrice") or notice.get("bidDeposit") or "가격/보증금 원문 확인")
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
        {"label": "공고 유형", "value": f"{asset_type} / {disposition}"},
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
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite").strip() or "gemini-2.5-flash-lite"
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
        with urllib.request.urlopen(request, timeout=30) as response:
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
    coach["model"] = config["model"]
    return coach


def build_ai_coach(notice: dict[str, object], docs: list[str]) -> dict[str, object]:
    coach = vertex_ai_coach(notice, docs) or gemini_ai_coach(notice, docs)
    if coach:
        return coach
    rule_based = local_ai_coach(notice, docs)
    rule_based["llmStatus"] = "rule_based"
    return rule_based


def question_prompt(notice: dict[str, object], docs: list[str], question: str) -> dict[str, object]:
    return {
        "role": "온비드 공공자산 입찰 준비 코치",
        "instruction": (
            "사용자가 이 공고에 대해 직접 질문했다. 아래 notice 필드와 requiredDocs 안에서 "
            "확실히 답할 수 있으면 answerable을 true로 하고, 근거가 된 값 그대로 answer에 담는다. "
            "notice 필드만으로 답할 수 없거나 추측·해석이 필요하면 answerable을 false로 하고 "
            "answer는 빈 문자열로 둔다. 모르는데 지어내지 않는다. "
            "입찰 참여 권유, 가격 결정 권유, 수익성 판단, 법률/권리관계 판단은 하지 않는다. "
            "'보장', '추천', '수익성' 같은 표현을 쓰지 않는다. "
            "답은 한국어 1~2문장으로 짧게 쓴다. 반드시 JSON 객체만 반환한다."
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
        },
        "question": question,
        "schema": {
            "answerable": True,
            "answer": "공고 내용에 근거한 답변 또는 빈 문자열",
            "sourceField": "근거로 쓴 notice 필드 이름 또는 빈 문자열",
        },
    }


def vertex_answer_question(notice: dict[str, object], docs: list[str], question: str) -> dict[str, object] | None:
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
            {"role": "user", "parts": [{"text": json.dumps(question_prompt(notice, docs, question), ensure_ascii=False)}]}
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
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read().decode(response.headers.get_content_charset() or "utf-8", errors="replace")
        parsed = parse_gemini_json(json.loads(raw))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None
    return sanitize_ai_text(parsed) if parsed else None


def gemini_answer_question(notice: dict[str, object], docs: list[str], question: str) -> dict[str, object] | None:
    api_key = gemini_api_key()
    if not api_key:
        return None
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite").strip() or "gemini-2.5-flash-lite"
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{urllib.parse.quote(model, safe='')}:generateContent?key={urllib.parse.quote(api_key, safe='')}"
    request_body = {
        "contents": [
            {"role": "user", "parts": [{"text": json.dumps(question_prompt(notice, docs, question), ensure_ascii=False)}]}
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


def answer_notice_question(notice: dict[str, object], docs: list[str], question: str) -> dict[str, object]:
    # 모델에 붙지 않았으면 「AI 가 확인했다」고 말하지 않는다(coach 의 llmStatus 와 같은 원칙).
    result = vertex_answer_question(notice, docs, question) or gemini_answer_question(notice, docs, question)
    if isinstance(result, dict) and isinstance(result.get("answerable"), bool):
        return {
            "connected": True,
            "answerable": bool(result.get("answerable")),
            "answer": str(result.get("answer") or "").strip(),
            "sourceField": str(result.get("sourceField") or "").strip(),
        }
    return {"connected": False, "answerable": False, "answer": "", "sourceField": ""}


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


def build_glossary(*values: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    seen: set[str] = set()
    for value in values:
        for term, meaning in TERM_GLOSSARY.items():
            if term in (value or "") and term not in seen:
                seen.add(term)
                entries.append({"term": term, "meaning": meaning})
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
    public_data = fetch_public_data_bundle(
        {
            "pbancMngNo": pbanc_mng_no,
            "cltrMngNo": cltr_mng_no,
            "pbctCdtnNo": pbct_cdtn_no,
        }
    )
    api_entries = [item for item in public_data.get("items", []) if isinstance(item, dict)]

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
        values_after_label(text, "담당부점")
        or values_after_label(text, "담당기관")
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
    if inputs.get("pbctBgngDt") and inputs.get("pbctLastDdlnDt"):
        bid_period = f"{inputs['pbctBgngDt']} ~ {inputs['pbctLastDdlnDt']}"
    else:
        bid_period = values_after_label(text, "입찰기간")
    api_start = api_value(api_entries, "pbctBegnDtm", "bidBgngDt", "bidBgngDtm", "pbctStrtDt")
    api_end = api_value(api_entries, "pbctClsDtm", "bidClsDt", "bidClsgDtm", "pbctEndDt", "pbctLastDdlnDt")
    if not bid_period and (api_start or api_end):
        bid_period = f"{api_start} ~ {api_end}".strip(" ~")
    bid_deadline = inputs.get("pbctLastDdlnDt") or api_end
    minimum_bid = minimum_bid_value(
        inputs,
        (
            inputs.get("lowstBidPrc")
            or values_after_label(text, "공매예정가격(원)")
            or api_value(api_entries, "minBidPrc", "lowstBidPrc", "fstBidPrc", "pbctExpcPrc", "bidPrc")
        ),
    ) or api_value(api_entries, "lowstBidPrcIndctCont")
    appraisal = inputs.get("cltrApslEvlAvgAmt") or values_after_label(text, "감정평가금액(원)") or api_value(api_entries, "apslAmt", "cltrApslEvlAvgAmt", "aprsPrc")
    area = values_after_label(text, "면적") or api_value(api_entries, "area", "lndArea", "bldArea", "ar")
    sections = split_sections(text)
    related_docs = extract_related_docs(text, final_url)
    attachment_chunks = attachment_doc_chunks(related_docs)
    doc_checklist = build_doc_checklist(sections, asset_type, related_docs, attachment_chunks)
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
        price_candidates.append({"title": "감정평가금액", "value": appraisal, "note": "온비드 상세 페이지 표시값"})
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
            "value": bid_period or bid_deadline or "원문 기준 확인",
            "note": "입찰 시작/마감 시각을 캘린더에 옮기기 전 원문을 재확인합니다.",
            "status": "warn",
        },
        {
            "title": "제출서류",
            "value": required_docs[0] if required_docs else str(doc_checklist["headline"]),
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
                "pbctCdtnNo": pbct_cdtn_no,
            },
        },
        "extractedFields": [key for key, value in notice.items() if isinstance(value, str) and value],
    }
    return notice


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        parsed = urllib.parse.urlparse(path)
        safe_path = parsed.path.lstrip("/")
        return str(ROOT / safe_path)

    def send_json(self, status: int, payload: dict[str, object]) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
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
                result = answer_notice_question(notice, docs, question)
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
