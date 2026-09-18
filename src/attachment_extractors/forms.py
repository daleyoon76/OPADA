"""첨부 원문에서 빈칸 서식(존재확인용)을 규칙기반으로 뽑는 프로토타입.

"정보 추출"이 아니라 "이 서식이 첨부에 있는가"만 보는 존재확인이다. 서식명 어휘가
짧은 한 줄(제목처럼)로 등장하고, 그 뒤 가까운 구간에 빈칸 서식의 전형적 흔적
("년   월   일" 같은 빈 날짜칸, "(인)" 서명란, "귀하"로 끝나는 수신처)이 있으면
서식으로 본다. 어휘만 보고 판단하면(예: 본문 중 "위임장을 제출하십시오" 같은 단순
언급) 실제 첨부된 서식이 아닌 경우까지 오탐한다.
"""

from __future__ import annotations

import re

FORM_NAME_RE = re.compile(
    r"^(?:\[[^\]]{0,10}\]\s*)?"
    r"([가-힣·\s]{2,20}(?:확인서|동의서|신청서|서약서|협정서|접수조서|선임계|인감계|각서|계약서|입찰서))\s*$"
)

# hwp5html은 표 셀 제목을 글자 사이마다 공백을 끼워 렌더링할 때가 있다
# (예: "종   람   확   인   서"). 위 정규식은 이 경우 못 잡으므로, 실패하면 그 줄에서
# 공백을 전부 없앤 버전으로 한 번 더 시도한다.
FORM_NAME_COMPACT_RE = re.compile(
    r"^(?:\[[^\]]{0,10}\])?"
    r"([가-힣·]{2,20}(?:확인서|동의서|신청서|서약서|협정서|접수조서|선임계|인감계|각서|계약서|입찰서))$"
)

# 서식명 줄 뒤 이 길이(문자수) 안에서 빈칸 흔적을 찾는다.
EVIDENCE_WINDOW_CHARS = 400

BLANK_EVIDENCE_RE = re.compile(r"년\s*[.]?\s*월\s*[.]?\s*일|\(\s*인\s*\)|귀하\s*$")


def extract_forms(text: str) -> list[str]:
    """빈칸 서식으로 추정되는 항목명을 뽑는다. 못 찾으면 빈 리스트."""
    names: list[str] = []
    seen: set[str] = set()
    lines = text.split("\n")
    offset = 0
    line_offsets = []
    for line in lines:
        line_offsets.append(offset)
        offset += len(line) + 1

    for line, start in zip(lines, line_offsets):
        stripped = line.strip()
        match = FORM_NAME_RE.match(stripped)
        if not match:
            match = FORM_NAME_COMPACT_RE.match(re.sub(r"\s+", "", stripped))
        if not match:
            continue
        name = re.sub(r"\s+", "", match.group(1))
        if name in seen:
            continue
        window = text[start : start + EVIDENCE_WINDOW_CHARS]
        if BLANK_EVIDENCE_RE.search(window):
            seen.add(name)
            names.append(name)
    return names
