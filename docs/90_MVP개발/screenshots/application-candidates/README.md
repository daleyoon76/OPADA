# 신청서용 MVP 스크린샷 후보

작성일: 2026-07-05

## 권장 사용 순서

DOCX 본문에는 원본 PNG보다 `submission-crops/`의 크롭본을 우선 사용한다. 원본은 전체 화면 증빙용으로 보관한다.

1. `01_url_analysis_ready.png`
   - 캡션: 온비드 공고/물건 URL을 붙여넣으면 공고번호·물건번호·일정·가격/보증금·원문 링크를 분석하고, 준비 보드 생성 가능 여부를 먼저 보여준다.
   - DOCX 권장 파일: `submission-crops/01_url_analysis_ready_crop.png`

2. `02_ai_priority_board_lease.png`
   - 캡션: 임대/대부 공고에서는 AI가 `내 업종으로 실제 사용 가능한지`, `현장 상태와 인수 범위`, `대부료 외 반복 비용`처럼 초보자가 놓치기 쉬운 빈칸을 우선 체크리스트로 연결한다.
   - DOCX 권장 파일: `submission-crops/02_ai_priority_board_lease_crop.png`

3. `03_ai_priority_board_sale.png`
   - 캡션: 매각/공매 공고에서는 `공동/대리입찰 서류`, `직접제출 마감`, `보증금·잔금·추가 비용`처럼 유형별로 다른 준비 빈칸을 우선 표시한다.
   - DOCX 권장 파일: `submission-crops/03_ai_priority_board_sale_crop.png`

4. `04_watchlist_recent_favorite.png`
   - 캡션: 분석한 공고는 최근 살펴본 공고에 남고, 별표를 누르면 관심 공고에도 저장되어 여러 공고의 준비 상태를 이어서 관리할 수 있다.
   - DOCX 권장 파일: `submission-crops/04_watchlist_recent_favorite_crop.png`

## 본문 연결 문장

본 MVP는 단순 공고 요약이나 일회성 보고서 생성이 아니라, 온비드 공고 URL을 사용자가 실행 가능한 준비 보드로 바꾸는 데 초점을 맞췄다. AI는 원문에 이미 표시된 값을 반복하지 않고, 사용자가 실제 준비 전에 놓치기 쉬운 확인 항목을 찾아 체크리스트 우선순위와 담당기관 문의 문장으로 연결한다.

## 제외 후보

- `37_board-empty-tasks-final-guard.png`: 회귀 검증용 빈 상태 캡처이므로 신청서 본문에는 넣지 않는다.
- 과거 `vertex` 명칭이 들어간 validation 캡처: 최신 화면과 문구가 달라 제출용 후보에서 제외한다.
