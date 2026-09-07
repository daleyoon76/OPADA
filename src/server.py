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
PUBLIC_DATA_ENDPOINTS = {
    "notice_list": "http://apis.data.go.kr/B010003/OnbidPbancListSrvc2/getPbancList2",
    "real_estate_list": "http://apis.data.go.kr/B010003/OnbidRlstListSrvc2/getRlstCltrList2",
    "real_estate_detail": "http://apis.data.go.kr/B010003/OnbidRlstDtlSrvc2/getRlstDtlInf2",
    "item_bid_detail": "http://apis.data.go.kr/B010003/OnbidCltrBidDtlSrvc2/getCltrBidInf2",
    "notice_detail": "http://apis.data.go.kr/B010003/OnbidPbancDtlnfSrvc2/getPbancDtlInf2",
    "notice_bid_detail": "http://apis.data.go.kr/B010003/OnbidPbancBidDtlSrvc2/getPbancBidInf2",
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
    ("컨소시엄 협정서", r"컨소시엄\s*협정서"),
    ("농지취득자격증명", r"농지\s*취득\s*자격\s*증명(?:서)?"),
    ("농지대장", r"농지\s*대장"),
    ("토지이용계획 확인원", r"토지\s*이용\s*계획\s*확인(?:원|서)"),
    ("사업자등록증", r"사업자\s*등록증(?:명)?"),
    ("국세 및 지방세 완납증명서", r"국세\s*(?:및|과|,)\s*지방세\s*완납\s*증명서?"),
    ("국세완납증명서", r"국세\s*완납\s*증명서?"),
    ("지방세완납증명서", r"지방세\s*완납\s*증명서?"),
    ("4대보험 가입확인서", r"(?:4대\s*보험|국민연금)[^\n]{0,20}가입\s*확인서"),
    ("영업신고증", r"영업\s*신고증"),
    ("청렴계약이행서약서", r"청렴\s*계약\s*이행\s*서약서"),
    ("계약이행보증보험증권", r"계약\s*이행\s*보증\s*보험\s*증권"),
    ("전자보증서", r"전자\s*보증서"),
    ("보증보험증권", r"보증\s*보험\s*증권"),
    ("확약서", r"확약서"),
    ("운영계획서", r"(?:시설\s*)?운영\s*계획서"),
    ("사업계획서", r"사업\s*계획서"),
    ("제안서", r"제안서"),
    ("입찰참가신청서", r"입찰\s*참가\s*신청서"),
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


def extract_doc_items(sections: dict[str, str]) -> list[dict[str, object]]:
    """공고문·제출서류 절에서 조건별 서류 항목을 뽑는다.

    한 줄이 조건 문구만 담고 서류명이 없으면 그 조건을 다음 하위 항목들에 물려준다.
    새 상위 번호(1. / 가.)가 조건 없이 나오면 물림을 끊는다.
    """
    items: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for title in DOC_SEARCH_SECTIONS:
        chunk = sections.get(title, "")
        if not chunk:
            continue
        carried: list[dict[str, str]] = []
        for raw_line in block_text(strip_tooltips(chunk)).split("\n"):
            line = raw_line.strip()
            if not line or len(line) > 1200:
                continue
            conditions = [item for item in find_conditions(line) if not item["negative"]]
            names = find_doc_names(line)
            if not names:
                if conditions and DOC_REQUEST_RE.search(line):
                    carried = conditions
                elif LINE_RESET_RE.match(line):
                    carried = []
                continue
            carried_applies = bool(carried) and bool(SUB_ITEM_RE.match(line))
            active = conditions or (carried if carried_applies else [])
            # 「업종·자격 요건」 축은 `등록증`·`면허` 같은 서류명 토큰으로 잡히므로
            # 그것만으로 제출 요구를 증명하지 못한다. authorizing 축에서 뺀다.
            authorizing = [item for item in conditions if item["key"] != "license"]
            if not authorizing and not carried_applies and not DOC_REQUEST_RE.search(line):
                # 조건 문맥도 제출 동사도 없으면 단순 언급이다(예: 「부동산의 표시는
                # 등기사항증명서 기준」). 서류 요구로 세지 않는다.
                continue
            extras = doc_extras(line)
            stage = "낙찰 후·계약 시" if CONTRACT_STAGE_RE.search(line) else "입찰 전"
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
) -> dict[str, object]:
    profile = doc_source_profile(asset_type)
    items = extract_doc_items(sections)
    table_rows = extract_docs_table(sections)
    generic_only = bool(table_rows) and all(row["generic"] for row in table_rows)

    groups: dict[str, dict[str, object]] = {}
    for item in items:
        label = " · ".join(item["conditions"])
        group = groups.setdefault(label, {"condition": label, "items": []})
        group["items"].append(item)

    if items:
        status = "extracted"
        headline = f"공고 원문에서 서류 {len(items)}건을 찾았습니다. 확인하셨습니까?"
    elif profile["code"] == "C":
        status = "not_in_notice"
        headline = "이 공고에서는 서류 목록을 찾지 못했습니다."
    elif attachments:
        status = "attachment_only"
        headline = "본문에서 서류 목록을 찾지 못했습니다. 첨부 공고문을 확인하십시오."
    else:
        status = "not_found"
        headline = "이 공고에서는 서류 목록을 찾지 못했습니다."

    notes: list[str] = []
    if generic_only:
        notes.append(
            "온비드 제출서류 표의 서류명 칸은 구분명(예: 공동입찰서류)이라 실제 준비할 서류명이 아닙니다."
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


def api_header(payload: object) -> dict[str, object]:
    if not isinstance(payload, dict):
        return {}
    response = payload.get("response")
    if isinstance(response, dict) and isinstance(response.get("header"), dict):
        return response["header"]
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
    # 근거는 `docChecklist["items"]` 뿐이다. 온비드 제출서류 표(`tableRows`)의 제출방법 칸을
    # 근거로 삼으면, 서류를 한 건도 못 뽑아 「못 뽑았습니다」를 띄운 공고에서 바로 다음 줄이
    # 「직접제출 서류」의 존재를 전제한다(표본 09·10·18·21·22·23 실측).
    has_direct_submit = any(item.get("method") for item in checklist_items)
    has_proxy_or_joint = bool({"proxy", "joint"} & condition_keys)
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
                    "reason": f"원문에는 `{docs_summary}`가 보이지만, 단독 전자입찰이면 일부 서류가 불필요할 수 있습니다.",
                    "action": "내 입찰 방식이 단독/공동/대리 중 무엇인지 정하고 필요한 서류만 남깁니다.",
                    "source": "제출서류 표",
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
    # 먼저 집는다. 상세 페이지 hidden input이 정확하므로 그쪽을 먼저 본다.
    asset_type = (
        inputs.get("scrnCltrPrptDivNm")
        or values_after_label(text, "재산유형")
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
    doc_checklist = build_doc_checklist(sections, asset_type, related_docs)
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


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    server = ThreadingHTTPServer((HOST, port), Handler)
    print(f"Serving OnBid MVP on http://{HOST}:{port}/")
    server.serve_forever()


if __name__ == "__main__":
    main()
