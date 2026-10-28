#!/usr/bin/env python3
"""물건 목록 전체를 캐시(data/cltr_cache.json)에 하루 1회 받아 두는 배치 스크립트.

cron·launchd 로 하루 1회 돌린다(등록은 아직 하지 않았다 — handoff.md 참고).
수동 실행: python3 scripts/refresh_cltr_cache.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import server  # noqa: E402


def main() -> int:
    cache = server.refresh_cltr_cache(force=True)
    if cache.get("refreshError"):
        print(f"갱신 실패: {cache['refreshError']}")
        return 1
    print(f"물건 {len(cache.get('items', []))}건 캐시 갱신 완료: {cache.get('fetchedAt')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
