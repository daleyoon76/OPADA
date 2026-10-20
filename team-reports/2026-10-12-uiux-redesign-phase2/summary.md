# UX 전면 재설계 2단계 — 준비 보드 1단계(공고확인) 내부 로직 2026-10-12

솔로 작업(서브에이전트 병렬 호출 없이 직접 설계·구현·검증 수행). `agentic-journey` 브랜치, 워크트리 `Hometest_op-agentic`. 커밋 `17d1733`.

## 범위

준비 보드 1단계(공고확인) 카드 그룹 내부 로직만. 2단계(서류준비)·3단계(입찰참여) 내부 로직, 1단계 밖의 화면(마법사 1p~3p·전환화면)은 이번에 손대지 않았다 — phase1(`a1d3ccd`)에서 이미 만든 구조 그대로 쓴다.

## 구현 방식

- 새 판정 로직을 만들지 않고 두 가지 기존 값을 재사용했다.
  - **입찰기간 만료**: 서버 `bid_countdown()`(`src/server.py`)가 이미 계산해 보내는 `sampleNotice.countdown.state === "closed"`.
  - **목적/형태 불일치**: 기존 `getFitMessage()`의 `type === "mismatch"` 분기(수정 없음).
- `getStage1RestartWarning(fit)` — 위 두 값만 보고 `{expired, mismatched, reasons}` 또는 `null`을 돌려준다. `renderReport()`가 이미 blockingMessage(URL 미입력·분석 실패·URL 변경 후 미분석)를 먼저 걸러낸 뒤에만 호출되므로 그 세 가지는 다시 보지 않는다.
- `renderStage1RestartWarning(warning)` — `null`이면 빈 문자열(배너 자체를 안 만든다). 있으면 `.fit-panel.mismatch`(기존 경고 박스 스타일 재사용)에 사유 문장과 "처음으로 돌아가시겠어요?" 버튼(`data-restart-wizard`)을 담은 HTML을 돌려준다.
- `renderReport()`의 단계별 카드 그룹 렌더링 루프에서 `stage.num === 1`일 때만 이 배너를 카드들 위에 끼워 넣었다(`src/app.js` 1828~1846행 근처).
- `restartWizardToProfile()` — 버튼 클릭 핸들러. `replaceNotice()`로 공고 데이터를 초기 샘플로 되돌리고, URL 입력칸을 비우고, `analyzedInputValue`·`analysisError`·`boardGenerated`·`currentStage`를 초기화한 뒤 `setView("input")` → `setInputStep("profile")`로 1p로 보낸다. `load-sample` 버튼이 쓰는 기존 초기화 패턴을 그대로 따랐다.

## 검증

- 단위 테스트 `tests/test_docs_extraction.py`: 275/275 통과(변경 전후 동일)
- 금지 문구 검사 `tests/test_screen_strings.py`: 20/20 통과
- 전용 포트 19002에 직접 서버를 띄우고 실제 브라우저(OpenClaw browser 도구)로 세 가지 케이스를 확인했다.
  - **만료**: 기본 샘플 URL(`onbidPbancNo=887390`)을 실제로 분석했더니 입찰기간(2026-06-04 마감)이 이미 지난 실제 데이터였다. 목적(임대/대부)은 일치하는 상태에서 1단계에 "입찰기간이 이미 지났습니다(2026-06-04 17:00 마감)." 경고와 "처음으로 돌아가시겠어요?" 버튼만 뜨는 것을 확인했다.
  - **불일치**: 같은 공고를 목적만 "매각/공매 공고 검토"로 바꿔 재분석했더니 만료+불일치 두 사유가 배너에 함께 뜨는 것을 확인했다(실제 코드가 `reasons` 배열에 두 문장을 모두 담는 경로라 자연스럽게 같이 검증됐다).
  - **정상**: 브라우저 콘솔에서 `sampleNotice.countdown`을 열린 상태로, `asset-focus`를 "lease"(기본 샘플과 일치)로 맞추고 `renderReport()`를 다시 호출해 `document.querySelector('.stage1-restart-warning')`가 `null`임을 확인했다 — 정상 케이스에서는 배너 자체가 DOM에 생기지 않는다. 실제 UI 플로우로는(샘플이 늘 만료 상태라) 재현이 안 돼 이 한 건만 콘솔 개입으로 보강했다.
  - "처음으로" 버튼을 실제로 클릭해 1p(유형·목적 선택 화면)로 돌아가고 URL 입력칸이 비는 것을 확인했다.
  - 데스크톱(1280px)·모바일(390px) 모두 배너 레이아웃이 깨지지 않았다. 콘솔 오류는 `favicon.ico` 404(기존부터 있던 무관한 것) 외 0건.
  - 2단계·3단계는 계속 잠긴 상태 그대로였다 — 이번 변경이 범위 밖에 영향을 주지 않았다.

## 다음 phase(2단계 서류준비: 공동입찰/대리입찰 질문 + 보관함)에 넘길 메모

- 기본 샘플 공고(`onbidPbancNo=887390`)가 이미 만료 상태라는 점은 다음 phase 작업에서도 그대로 쓸 수 있다 — 별도 픽스처 없이 "만료 케이스"를 바로 재현한다. 반대로 "만료 아님" 케이스를 실제 UI로 재현하려면 현재 날짜 기준으로 마감이 남은 다른 온비드 URL을 찾아야 한다(이번에는 브라우저 콘솔 개입으로 대체).
- `restartWizardToProfile()`은 프로필 선택값(`user-type`·`asset-focus`)은 그대로 두고 공고 데이터·URL만 초기화한다. "완전히 리셋"을 프로필 선택까지 지우는 뜻으로 받아들이면 동작이 달라지니, 다음 phase에서 비슷한 리셋 버튼을 또 만들 때는 이 선택을 참고한다.
- `getStage1RestartWarning()`은 `renderReport()`의 blockingMessage 분기 뒤에서만 호출된다는 전제가 있다 — 이 함수를 다른 자리(예: 2단계·3단계 카드)에서 재사용하려면 `fit.inputBlocked`가 항상 false라는 전제가 깨지므로 그 조건을 다시 넣어야 한다.
