# UI/UX 변경 기록

작성일: 2026-07-04

## 변경 파일

- `90_MVP개발/app/index.html`
- `90_MVP개발/app/styles.css`
- `90_MVP개발/app/app.js`
- `90_MVP개발/screenshots/*.png`

## 주요 변경

1. `준비 보드` 화면을 정보 카드 나열에서 체크 가능한 작업판으로 변경했다.
2. 상단 메트릭을 `자동 분석`, `다음 액션`, `진행률` 3개로 줄였다.
3. `오늘 할 일` 카드는 체크박스 task list로 바꾸고, 세부 설명은 접힌 상태로 이동했다.
4. 마감·비용 요약과 관심 공고 준비상태는 기본 접힘 보조 섹션으로 낮췄다.
5. 사용자 유형별 task 필터를 적용했다.
6. 진행률, localStorage 저장, 초기화, 분석 중 disabled, focus 이동, focus-visible 스타일을 추가했다.
7. 우측 CTA 문구를 `서류 준비처 보기`, `문의 질문 확인`, `준비 리포트 저장`으로 바꿨다.

## 스크린샷

- `90_MVP개발/screenshots/01_input.png`
- `90_MVP개발/screenshots/03_report-dashboard.png`
- `90_MVP개발/screenshots/02_structured-data.png`
- `90_MVP개발/screenshots/04_risk-evidence.png`
- `90_MVP개발/screenshots/05_pdf-preview.png`

검증용 모바일 캡처는 `90_MVP개발/screenshots/validation/`에 보관했다.

## 18:04 추가 변경

1. `공고 분석`과 `준비 보드 만들기`를 분리했다.
   - 분석 성공 전에는 `준비 보드 만들기` disabled.
   - 분석 성공 후에는 입력 화면에서 분석 미리보기를 먼저 보여준다.
2. 분석 미리보기에 `현재 분석 페이지`, `공고보기`, `물건상세` 링크를 추가했다.
3. Vertex AI 기반 `AI 준비 코치`를 추가하고, 화면에는 다음 행동 3개와 담당기관 확인 질문 2개만 노출한다.
4. 안전 표현 후처리를 추가해 입찰 권유/가격 결정/법률 판단으로 읽히는 문구를 줄였다.
5. `관심 공고` 탭을 `관심 공고`와 `최근 살펴본 공고` 2개 섹션으로 분리했다.
6. 분석 성공 시 최근 공고를 저장하고, 별표 클릭 시 관심 공고에도 표시되도록 했다.
7. 신청서용 최신 검증 캡처를 갱신했다.

## 18:04 스크린샷

- `90_MVP개발/screenshots/validation/16_input-analysis-preview-vertex-ai.png`
- `90_MVP개발/screenshots/validation/15_url-preview-prepare-vertex-ai.png`
- `90_MVP개발/screenshots/validation/17_watchlist-recent-favorite.png`
