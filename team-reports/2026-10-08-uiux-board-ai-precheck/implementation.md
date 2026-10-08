# 3팀(UIUX품질팀) frontend-implementer 구현 결과 — 준비 보드 AI 사전 확인 노출

- 날짜: 2026-10-08
- 작업자: frontend-implementer(이 세션이 직접 구현, Agent 도구로 재위임하지 않음)
- 워크트리: `~/Documents/Dev/Hometest_op`(main, 유일한 워크트리)
- 커밋: `a02f8a1`

## 배경

동원님이 준비 보드 "할 일" 카드 스크린샷을 보고, "공고 유형 확인"·"입찰기간 확인" 같은 카드가
"다시 확인하세요"라고만 하고 AI가 이미 비교·추출한 결과를 보여주지 않는다고 지적했다. 네 가지를
요청했다 — ① AI 사전 확인 결과 노출 ② 불확실한 항목의 담당기관 질문 초안 자동 생성 ③ 최저입찰가격
필드명 조사 ④ 자세히 블록을 2열 표로 정리.

## 1. AI 사전 확인 결과를 "할 일" 카드에 노출 — 완료

- `src/app.js`에 `getAiPrecheckForTask(task, fit)` 함수를 신설했다(`getFitMessage()` 뒤,
  `renderAnalysisResult()` 앞). `getFitMessage()`·`getApplicableTasks()` 자체의 판정 로직은
  건드리지 않고, 그 결과를 "보여주는" 자리만 넓혔다.
- `task.id === "notice-type"` 카드: `fit.type`(match/mismatch/check)에 따라 자세히 블록에
  "AI 사전 확인" 문장을 넣는다.
  - match: "선택한 검토 목적과 공고 유형을 비교했을 때 맞는 것으로 보입니다. 원문·담당기관 확인을
    우선합니다."
  - mismatch: "선택한 검토 목적과 공고 유형이 다른 것으로 보입니다. {fit.body} 원문·담당기관
    확인을 우선합니다."
  - check(창업 목적): "{fit.body} 원문·담당기관 확인을 우선합니다."
- `task.id === "bid-period"`·`"price"` 카드: `task.action !== NOTICE_VALUE_FALLBACK`로 추출
  성공/실패를 가른다.
  - 추출 성공: "공고 원문에서 {값}로 확인된 것으로 보입니다. 원문·담당기관 확인을 우선합니다."
  - 가격이 "비공개"(known-pitfalls.md 「가격 표시」 — `minimum_bid_value()`가 명시적으로 돌리는
    정상 값)인 경우는 별도 문구: "공고 원문에서 가격이 비공개로 설정된 것으로 보입니다. …"
  - 추출 실패: "원문에서 값을 찾지 못했습니다. 직접 확인해 주세요."
- 전부 "~로 보입니다"로 헤지하고 "원문·담당기관 확인을 우선합니다"를 끝에 붙였다. "일치합니다"·
  "확인됐습니다" 같은 단정 표현은 쓰지 않았다. `tests/test_screen_strings.py`의 금지표현 목록
  (자동 입찰·낙찰 가능성 예측 등 14종)과도 겹치지 않는다 — G2 축 20/20 통과로 확인했다.

## 2. 담당기관 질문 초안 자동 생성 — 완료

같은 `getAiPrecheckForTask()`가 `draft` 필드로 함께 낸다. 불일치·추출 실패 상태에만 넣고, 일치/
추출 성공 항목에는 `draft: null`로 비워 불필요한 질문을 만들지 않는다.

- 공고 유형 불일치: "제가 고른 용도와 공고 유형이 다르게 보이는데, 이 공고로 진행해도 되는지 확인
  부탁드립니다."(동원님이 준 예시 문장 그대로)
- 공고 유형 "확인 필요"(창업 목적): "이 물건을 제가 고른 용도로 사용할 수 있는지 담당기관에 확인
  부탁드립니다."
- 입찰기간 추출 실패: "이 공고의 입찰기간(입찰 시작·마감 일시)은 언제인가요?"
- 최저입찰가격 추출 실패: "이 공고의 최저입찰가격(또는 임대료 기준가)은 얼마인가요?"(동원님이 준
  예시 문장 그대로)

화면에는 "AI가 짚은 질문" 라벨로 들어간다(`src/app.js` task-list 렌더 구간).

## 3. 최저입찰가격 표시 조사 — 조사 완료, 코드 변경 없음

- 샘플 공고(국유재산 대부입찰, `onbidPbancNo=887390`)로 `/api/analyze`를 직접 호출해
  `bidPeriod`·`minimumBidPrice`·`appraisalPrice`가 전부 빈 문자열임을 재확인했다(팀장 실측과
  일치).
- 온비드 원문 HTML을 직접 받아(`curl`, 641,154바이트) "임대료"·"예정가격"·"저감예정가격"·
  "월임대료"·"감정가" 키워드를 전수 검색했다 — **0건**. "대부료"는 6건 있었지만 전부 납부 방법을
  설명하는 안내 문구(연간대부료 50만원 초과 시 분납 등)이지 실제 가격 값이 아니었다.
- "최저입찰가격" 라벨은 원문에 7건 있었는데, 전부 `<th>`/`<span class="txt01">` 같은 **표 머리글**
  이거나, `item.lowstBidPrc`·`item.lowstBidPrcHideDivCd`를 참조하는 **JS 코드**(`document.
  createElement`로 `<td>`를 동적 생성)였다. 즉 실제 값은 서버가 받는 정적 HTML에 없고, 브라우저가
  별도 데이터(`item` 객체, 회차별 AJAX 응답으로 추정)로 자바스크립트가 채운다.
- 이것은 새로운 필드명 문제가 아니라 `known-pitfalls.md`의 "🔴 회차(여러 입찰 차수)가 있는 공고는
  입찰기간·최저입찰가격을 못 읽습니다"와 **같은 원인**이다 — "입찰일정 및 장소"를 회차별 표로
  JS가 채우는 구조. 그 항목은 이미 "어느 회차를 보여줄지부터 제품 판단이 필요해 손대지 않았다"로
  범위 밖 확정돼 있다.
- **결론: 코드를 건드리지 않았다.** 다른 필드명으로 바꿔서 해결될 문제가 아니고, 기존에 범위 밖으로
  확정된 회차 이슈의 재현이다. `src/server.py`의 `minimum_bid_value()`·`build_tasks()`는 수정하지
  않았다.

## 4. "자세히" 블록 2열 표 정리 — 완료

- `src/app.js` task-list 렌더(`<details><summary>자세히</summary>…`) 안의 `<p><b>라벨</b>:
  내용</p>` 패턴 전부를 `<dl class="detail-grid">`의 `<dt>`/`<dd>` 쌍으로 바꿨다. 대상: 이유
  (`aiMatch.check.title`/`reason`), 먼저 할 일, AI 사전 확인·AI가 짚은 질문(이번에 추가), 문의
  문장, 상세 설명, 근거.
- `src/styles.css`에 `.task-item .detail-grid`(`display: grid; grid-template-columns: 84px
  1fr;`)와 `dt`/`dd` 스타일을 신설했다. 기존 `.fact-row`는 라벨·값이 세로로 쌓이는 다른 패턴이라
  고치지 않고 그대로 뒀다.
- 라벨 열은 고정폭(84px)이되 `nowrap`을 쓰지 않아, 긴 라벨(`aiMatch.check.title`처럼 9자
  넘는 문장형 라벨)도 줄바꿈만 되고 표가 깨지지 않는다.
- 데스크톱(1280px)·모바일(390px) 스크린샷으로 확인(아래 참고).

## 테스트 결과

- 워크트리: `~/Documents/Dev/Hometest_op`(main, 유일한 워크트리) · 포트: 8975(기존 상주
  launchd 서버, PID 15027, 2026-10-04 18:22 기동 — `SimpleHTTPRequestHandler`가 `src/app.js`·
  `src/styles.css`를 요청마다 디스크에서 다시 읽으므로 재시작 없이 이번 수정이 그대로 반영됨을
  확인했다. `server.py`는 건드리지 않아 재시작이 필요 없다).
- `npm run test:unit` → **275/275**(`test_docs_extraction.py`, 축 30개 전부 커버) +
  **20/20**(`test_screen_strings.py`, 금지표현 G2 포함).
- `npx playwright test` → **17/17**(`screen.spec.js`·`public-data-status.spec.js`), 포트
  8975 재사용(`reuseExistingServer: true`).
- 실제 서버(8975)에 Playwright로 직접 접속해 샘플 공고 분석 → 준비 보드 생성 → "자세히" 전개까지
  라이브 확인(`node` 스크립트, 레포에 커밋하지 않음). 시나리오 3종:
  - 데스크톱(1280×900) · 내 검토 목적 "임대/대부"(일치) — "AI 사전 확인"에 일치 문구, 입찰기간·
    최저입찰가격 카드에 "원문에서 값을 찾지 못했습니다" + "AI가 짚은 질문" 노출 확인.
  - 데스크톱(1280×900) · 내 검토 목적 "매각/공매"(불일치) — "AI 사전 확인"에 불일치 문구 +
    "제가 고른 용도와 공고 유형이 다르게 보이는데…" 질문 초안 노출 확인.
  - 모바일(390×844) · "임대/대부"(일치) — 2열 표가 깨지지 않고 줄바꿈되는 것 확인.
  - 콘솔 에러 0건(별도 확인, `page.on("console"/"pageerror")`).
- 2026-10-02 라운드의 "잘못된 서버 기준 e2e 보고" 전례를 피하려고, 이번 서버 PID(15027)·cwd
  (`/Users/user/Documents/Dev/Hometest_op`)·기동 시각을 `lsof`/`ps`로 먼저 실측하고 작업했다.

## 스크린샷

`team-reports/2026-10-08-uiux-board-ai-precheck/screenshots/`(이 디렉터리는 레포 `.gitignore`의
`screenshots/` 규칙으로 커밋되지 않는다. 이 세션이 로컬에 남긴 파일이며, 메인 세션이 동원님께
전달할 때는 경로를 직접 안내해야 한다):

- `desktop-lease-match.png` — 1280×900, 목적 일치
- `desktop-sale-mismatch.png` — 1280×900, 목적 불일치(불일치 질문 초안 포함)
- `mobile-390-lease-match.png` — 390×844, 목적 일치

## 범위 밖 확인

- `renderBoardCoach()`(코치 패널), 질문-답변 카드, `support-tablist` 구조는 건드리지 않았다
  (`git diff`로 확인 — 변경 파일은 `src/app.js`·`src/styles.css` 둘뿐이고, 코치 패널·질문-답변
  관련 함수는 diff에 없다).
- `:root` 색상 팔레트·전역 토큰은 바꾸지 않았다.
- `getFitMessage()`·`getApplicableTasks()`의 판정 로직(언제 match/mismatch/check가 되는지,
  어느 task가 몇 번째로 오는지)은 그대로다 — 새 함수는 그 결과값만 읽는다.

## 저자=검증자 금지 — 다음 단계

이 보고서와 diff는 전부 이 세션(frontend-implementer 역할, 저자)이 작성했다. 독립 재검토는
`visual-reviewer`가 커밋 `a02f8a1` 기준으로 맡는다. 재판정 packet에는 이 문서의 스크린샷 3장과
`git show a02f8a1 --stat`를 함께 넘길 것을 권한다.
