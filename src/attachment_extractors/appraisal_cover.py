"""감정평가서 첨부에서 표지값(감정평가액·기준시점)을 규칙기반으로 뽑는 프로토타입.

"감정평가액" 라벨은 문서 안에 반복해서(대부분 매 페이지 헤더로) 나오므로, 첫 등장이
아니라 라벨 바로 뒤(30자 이내)에 실제 숫자가 붙어있는 등장만 값으로 본다. 다호실
일괄 평가서(idx15·16처럼)는 "결정된 감정평가액" 표기가 최종 합계이므로 그 라벨을
우선한다.
"""

from __future__ import annotations

import re

FINAL_AMOUNT_LABEL_RE = re.compile(r"결정된\s*감정평가액\s*\n*\s*([\d,]{4,})")
AMOUNT_NEAR_LABEL_RE = re.compile(r"감정평가액[^0-9\n]{0,30}?([\d,]{4,})")
BASE_DATE_RE = re.compile(r"기준시점[^\d]{0,60}?(\d{4})[^\d]{0,5}(\d{1,2})[^\d]{0,5}(\d{1,2})")


def extract_appraisal_cover(text: str) -> dict | None:
    """감정평가액과 기준시점을 뽑는다. 감정평가액을 못 찾으면 None(해당 문서 아님)."""
    amount: int | None = None
    final_match = FINAL_AMOUNT_LABEL_RE.search(text)
    if final_match:
        amount = int(final_match.group(1).replace(",", ""))
    else:
        near_match = AMOUNT_NEAR_LABEL_RE.search(text)
        if near_match:
            amount = int(near_match.group(1).replace(",", ""))
    if amount is None:
        return None

    base_date = None
    date_match = BASE_DATE_RE.search(text)
    if date_match:
        year, month, day = date_match.groups()
        base_date = f"{year}-{int(month):02d}-{int(day):02d}"

    return {"amount_krw": amount, "base_date": base_date}
