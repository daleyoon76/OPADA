# 변경 내용 — 캠코 데모 핵심 플로우 UI 다듬기 (2026-11-05)

frontend-implementer 역할. P0와 작은 P1만 고쳤다. 화면 재배치·새 플로우 설계 같은 큰 구조 변경은
하지 않았다(색·간격·캐시버스터 문자열만).

## 변경 파일
- `src/index.html` — 정적 자원 캐시버스터 `?v=20261029-item-search-r2` → `?v=20261105-uiux-fix`
  (styles.css·app.js 2곳).
- `src/styles.css` — 3곳
  1. `.board-top-stepper:empty` 바로 아래 `.report-hero:empty { display: none; }` 추가.
  2. 2738행 근처 `.post-award-caution, .post-award-process` 통합 규칙에서 `.post-award-caution`을
     빼 `.post-award-process`만 남김(원인 주석 추가).
  3. 828행 `.post-award-caution` 선택자를 `.info-row.post-award-caution`(복합 클래스)로 올리고
     `border: 0` 뒤 `border-left: 3px solid #c9a08f`를 둬 `.info-row` 기본 테두리를 명시적으로 이김.

## 왜 (요약, 상세 근거는 ux-audit.md·verification.md)
1. 10-30에 app.js를 수정한 커밋 4개가 캐시버스터 문자열을 안 올려, 캐시된 브라우저가 구버전을 볼
   위험이 있었다.
2. 분석 전 준비 보드 탭에 `#report-hero`가 빈 채로 렌더링돼 테두리 있는 빈 박스가 보였다.
3. 2-4단계(낙찰 후 준비)의 "함께 확인" 경고가 2026-10-19 리팩터링과 `.info-row` 기본 스타일에
   덮여 일반 안내문과 구분이 안 됐다 — "단계 판정 오분류의 안전망이라 묻히면 안 된다"는 원래 설계
   의도(app.js 주석)와 어긋났다.

## 건드리지 않은 것
- AI 검색·AI 코치·서류 추출 등 백엔드 로직(`src/server.py`) — 전혀 수정하지 않았다.
- `#view-print`(인쇄용 화면)·관심 공고 탭(`#view-watchlist`) — 범위 밖으로 판단해 손대지 않았다
  (ux-audit.md 참고).
- 동원님 결정 대기 항목(상가 표지 물건 제외 여부·"1-2 물건 URL" 안내 문구 등) — 그대로 둔다.
