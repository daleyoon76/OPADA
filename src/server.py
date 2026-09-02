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


def extract_required_docs(text: str) -> list[str]:
    idx = text.find("제출서류")
    if idx < 0:
        return []
    chunk = text[idx : idx + 9000]
    table_match = re.search(r"<table\b.*?</table>", chunk, flags=re.I | re.S)
    if table_match:
        chunk = table_match.group(0)
    rows = re.findall(r"<tr\b.*?</tr>", chunk, flags=re.I | re.S)
    docs: list[str] = []
    for row in rows:
        cells = [clean_text(cell) for cell in re.findall(r"<td\b[^>]*>(.*?)</td>", row, flags=re.I | re.S)]
        cells = [cell for cell in cells if cell]
        if cells:
            if len(cells) >= 4 and cells[0] == cells[1]:
                docs.append(f"{cells[0]} - {cells[2]} - {cells[3]}")
            else:
                docs.append(" / ".join(cells[:4]))
    return docs[:6]


def extract_related_docs(text: str) -> list[str]:
    idx = text.find("관련문서")
    if idx < 0:
        return []
    chunk = text[idx : idx + 7000]
    names = [clean_text(item) for item in re.findall(r"<span[^>]*class=(?:\"[^\"]*\btxt01\b[^\"]*\"|'[^']*\btxt01\b[^']*')[^>]*>(.*?)</span>", chunk, flags=re.I | re.S)]
    return [name for name in names if name][:6]


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
    cltr_mng_no = ids.get("cltrMngNo", "")
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
    is_sale = "매각" in disposition or "압류" in notice.get("assetType", "")
    price_label = "공매예정가격" if is_sale else "입찰보증금/대부료"
    price_value = notice.get("minimumBidPrice") or notice.get("bidDeposit") or "공고 원문 확인"
    docs_detail = " / ".join(docs[:2]) if docs else "공고 원문 제출서류 표 확인"
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
            "detail": "가격, 보증금, 대부료, 납부 방식은 입찰 판단에 영향을 주지만 본 MVP는 수익성 판단을 제공하지 않습니다.",
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
            "detail": "공동입찰, 대리입찰, 법인/개인 여부에 따라 제출서류와 제출방법이 달라질 수 있습니다.",
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
    docs_summary = " / ".join(docs[:2]) if docs else "제출서류 표 확인"
    docs_text = " ".join(docs)
    is_sale = "매각" in disposition or "공매" in disposition or "압류" in asset_type
    has_direct_submit = "직접제출" in docs_text
    has_proxy_or_joint = "공동" in docs_text or "대리" in docs_text
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
        unresolved_checks.insert(
            0,
            {
                "title": "제출서류 표를 찾지 못함",
                "reason": "자동 추출에서 제출서류가 비어 있어 원문 탭이나 첨부 공고문 확인이 필요합니다.",
                "action": "공고보기 링크에서 제출서류/첨부파일을 먼저 확인합니다.",
                "source": "자동 추출 결과",
            },
        )
        ask_agency.insert(0, "이 공고의 제출서류 목록과 제출 방법이 별도 첨부파일에 있는지 확인할 수 있나요?")

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
    minimum_bid = (
        inputs.get("lowstBidPrc")
        or values_after_label(text, "공매예정가격(원)")
        or api_value(api_entries, "minBidPrc", "lowstBidPrc", "fstBidPrc", "pbctExpcPrc", "bidPrc")
    )
    appraisal = inputs.get("cltrApslEvlAvgAmt") or values_after_label(text, "감정평가금액(원)") or api_value(api_entries, "apslAmt", "cltrApslEvlAvgAmt", "aprsPrc")
    area = values_after_label(text, "면적") or api_value(api_entries, "area", "lndArea", "bldArea", "ar")
    related_docs = extract_related_docs(text)
    required_docs = extract_required_docs(text)

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
    }

    price_candidates = []
    if minimum_bid:
        price_candidates.append({"title": "공매예정가격", "value": minimum_bid, "note": "온비드 상세 페이지 표시값"})
    if appraisal:
        price_candidates.append({"title": "감정평가금액", "value": appraisal, "note": "온비드 상세 페이지 표시값"})
    if not price_candidates:
        price_candidates.append({"title": "비용 후보", "value": "공고 원문 확인", "note": "보증금, 대부료, 납부 방식은 원문 기준 확인"})

    notice["costs"] = price_candidates
    notice["alerts"] = [
        {
            "title": "입찰기간",
            "value": bid_period or bid_deadline or "원문 기준 확인",
            "note": "입찰 시작/마감 시각을 캘린더에 옮기기 전 원문을 재확인합니다.",
            "status": "warn",
        },
        {
            "title": "제출서류",
            "value": required_docs[0] if required_docs else "제출서류 표 확인",
            "note": "공동/대리입찰 여부와 제출방법에 따라 준비 시간이 달라집니다.",
            "status": "check",
        },
    ]
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
