"""첨부 원문에서 자격요건 수치 조건을 규칙기반으로 뽑는 프로토타입.

"참가자격/신청자격/자격요건" 절을 앵커로 잡고, 그 구간에서 숫자+단위+이상/이내류
어미가 함께 있는 구절을 후보로 본다. 단위 목록은 이번 10건 표본에서 실제로 나온
것만 담았다(면·년·개월·인·분의N·%·원 단위).
"""

from __future__ import annotations

import re

SECTION_ANCHOR_RE = re.compile(r"참가\s*자격|신청\s*자격|자격\s*요건")
WINDOW_CHARS = 1200

# 숫자 + 단위 + (이상/이내/이하/미만 등 어미, 선택). "분의"는 어미 없이도 그 자체로
# 조건이다(예: "3분의 1 이상").
NUMBER_CONDITION_RE = re.compile(
    r"(?:최근\s*)?\d+\s*(?:년|개월|면|인|개소|백만원|억원|만원|원|%|퍼센트)"
    r"(?:\s*(?:이상|이내|이하|미만))?"
    r"|\d+\s*분의\s*\d+\s*(?:이상|이내|이하|미만)?"
)


def extract_qualification_numbers(text: str) -> list[str]:
    """참가자격 절 근처에서 숫자 조건 구절을 뽑는다. 못 찾으면 빈 리스트."""
    items: list[str] = []
    seen: set[str] = set()
    for anchor in SECTION_ANCHOR_RE.finditer(text):
        window = text[anchor.end() : anchor.end() + WINDOW_CHARS]
        for match in NUMBER_CONDITION_RE.finditer(window):
            value = re.sub(r"\s+", "", match.group(0))
            if value not in seen:
                seen.add(value)
                items.append(value)
    return items
