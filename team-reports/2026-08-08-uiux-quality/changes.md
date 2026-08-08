# 변경 내역 — 2026-08-08

담당: frontend-implementer (구현), 팀장(리뷰 후 1건 추가)
대상 파일: `src/app.js`, `src/styles.css`, `src/index.html`(버전 쿼리만)

## 구현된 변경

1. `badge("원문 우선","warn")` 3곳을 `<span class="small-text">`로 강등, report-hero badge 4개 → 1개(실제 상태 badge만)로 축소.
2. `.report-hero` / `.coach-panel` / `.coach-panel.board`의 accent border+배경을 중립색(`border-left: 3px solid var(--line)`, `#fbfcfb`)으로 통일. `.fit-panel.mismatch`/`.check`, `.risk-card`는 상태색 유지(안 건드림).
3. `.fit-facts div` / `.preview-grid div` / `.coach-facts div`의 border/background 제거.
4. `sampleNotice.watchlist` 항목에 `sample: true` 추가, `watchItemHtml()`에서 샘플이면 "예시" badge 표시.
5. `.two-col`의 `grid-template-columns`를 `1.05fr/0.95fr` → `1.6fr/0.9fr`로 변경.
6. 폰트 5단계(h1 24 / h2 20 / 강조값 16 / 본문 14 / 메타 12px)로 정리. label·a 태그 `font-weight` 700 → 500(버튼/badge/h1/h2는 700 유지).
7. `resetTaskState()`에 `confirm("진행 상황을 초기화할까요?")` 가드 추가.
8. 죽은 변수 `analysisTimer` 제거, 모듈 스코프 `analysisRequestId` 카운터 도입. `runAnalysis()`에서 요청마다 캡처해 응답 처리 전 최신 요청인지 확인. "샘플 불러오기" 클릭 시 카운터 증가로 진행 중 요청 무효화.
9. `@media(max-width:900px)` 모바일 스택 규칙에 `.preview-grid`, `.coach-facts` 추가.
10. (visual-reviewer 리뷰 후 팀장이 추가) `.badge`에 `flex-shrink:0`/`white-space:nowrap`, `.preview-top`/`.coach-head`/`.ai-ready-summary div`에 `flex-wrap:wrap` 추가. "AI 분석 완료" 등 배지가 모바일 폭에서 여러 줄로 쪼개지던 기존 결함(P1)을 수정.

## 버전

`src/index.html`의 `styles.css`/`app.js` 쿼리스트링을 `20260808-visual-cleanup` → `20260808-visual-cleanup2`로 갱신(캐시 무효화).

## 이번 범위에서 보류한 것 (다음 이터레이션 후보)

- 공고유형 3중 반복 통합 (`ux-audit.md` P0-2)
- 준비 보드 6단 구획 재배치 (`ux-audit.md` P1-3)
- select 위치 이동 (`ux-audit.md` P1-1)
- AI 안내 메시지 4중 통합 (`ux-audit.md` P1-2)
- 체크박스/별표 포커스 관리 (`state-matrix.md` 상호작용 P1)
- 별표 버튼 터치 타깃 확대 (`state-matrix.md` 상호작용 P2)
- pastel 배경틴트 전면 정리 (`visual-audit.md` P1)
