"""첨부 원문에서 '제N조' 조 경계 후보를 규칙기반으로 뽑는 프로토타입.

의도적으로 순수 정규식만 쓴다(줄 시작 앵커링이나 연속성 검증 같은 후처리를 넣지
않았다) — 템플릿(00_첨부추출_템플릿_20260917.md §4.6·§6)이 지적한 대로 순수
정규식만으로는 법령 인용문 속 "제N조"(예: 「건축법」 제59조)까지 함께 잡혀
정밀도가 떨어지는지를 이번 측정에서 그대로 드러내기 위함이다. 제목 괄호가
붙은 경우만 후보로 본다("제N조" 뒤에 괄호 제목이 없으면 각주·목차 번호 등
비조문 잡음이 더 많이 섞여 실측 정밀도가 오히려 더 나빠졌다).
"""

from __future__ import annotations

import re

ARTICLE_RE = re.compile(r"제(\d+)조(?:의(\d+))?\s*[\(（]([^\)）]{1,30})[\)）]")


def extract_clause_boundaries(text: str) -> list[dict]:
    """'제N조(제목)' 패턴을 전부 후보로 뽑는다. 조문/인용 구분 없이 그대로 반환한다."""
    items: list[dict] = []
    for match in ARTICLE_RE.finditer(text):
        items.append(
            {
                "article": int(match.group(1)),
                "sub": int(match.group(2)) if match.group(2) else None,
                "title": re.sub(r"\s+", "", match.group(3)),
            }
        )
    return items
