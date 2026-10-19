# UX 전면 재설계 1단계 — 입력~분석 마법사화 2026-10-12

솔로 작업(서브에이전트 병렬 호출 없이 직접 설계·구현·검증 수행). `agentic-journey` 브랜치, 워크트리 `Hometest_op-agentic`.

## 범위

입력~분석 단계를 4개 화면으로 분리했다. main 워크트리(`Hometest_op`)는 건드리지 않았다.

1. **1p** — 사용자 유형·검토 목적 선택 (`#wizard-step-profile`)
2. **2p** — 온비드 URL 입력, "다음"으로 분석 실행 (`#wizard-step-url`)
3. **3p** — 분석 결과 확인 (`#wizard-step-result`)
4. **전환 화면** — "준비보드를 만들어드려요" 메시지 900ms 노출 후 기존 준비 보드로 자동 진입 (`#wizard-step-transition`)

기존 순차 단계 준비 보드(공고확인→서류준비→입찰참여)와 1단계/2단계/3단계 내부 로직은 손대지 않았다 — 이번 범위 밖.

## 구현 방식

- 여러 HTML 파일로 쪼개지 않고, 기존 SPA 구조 안에서 `inputStep` 상태(`profile`/`url`/`result`/`transition`)로 화면 전환 단위를 분리했다(`src/app.js`의 `renderWizardStep()`/`setInputStep()`). `currentView`("input"/"report"/"watchlist")는 그대로 두고 그 안의 하위 화면만 바꾼다.
- 기존 `#notice-url`·`#analyze`·`#prepare`·`#user-type`·`#asset-focus` 등의 id·이벤트 배선은 그대로 재사용했다 — 위치만 각 하위 화면으로 옮겼다.
- 3p 분석 결과 화면 — 사용자 피드백("분석결과 박스 안의 객체 배치나 구조가 너무 정신없다")에 따라, 서로 다른 배경·테두리를 가진 상자(`.fit-panel`·`.doc-source-notice`·`.ai-ready-summary`)를 겹겹이 쌓던 구조를 "핵심 정보"·"확인 사항"·"온비드 연결" 세 묶음(`.result-section`)으로 재편했다. 데이터·판정 로직(`getFitMessage()` 등)은 그대로 쓰고 배치만 바꿨다.
- 2p의 URL 미입력·형식 오류·분석 실패 안내는 `#url-step-feedback`으로 분리해 3p 결과 영역과 섞이지 않게 했다.
- 전환 화면은 `window.setTimeout(900ms)` 로 자동 진행한다(클릭 한 번 더 요구하는 멈춤 지점이 아니다).

## 되돌아본 것

- `tests/screen.spec.js`의 `analyzeWith()` 헬퍼가 `#notice-url`을 직접 채우는데, 이제 그 필드는 1p를 지나야 보인다. 헬퍼에 `#profile-next` 클릭 한 줄을 추가해 8개 호출부를 한 번에 고쳤다. 다만 이 e2e 스위트(`playwright.config.js`)는 `baseURL` 8975(메인 워크트리) 전용으로 고정돼 있어 이번 세션에서 전체 실행은 하지 않았다 — `tests/screen.spec.js`의 더 세밀한 회귀(예: 전환 화면 타이밍 관련 단언)는 다음에 이 워크트리 전용 설정으로 한 번 더 돌려 보는 것을 권한다.
- `renderDocSourceNotice()`가 반환하는 요소에 `doc-source-notice` 클래스를 레이아웃용이 아니라 e2e 셀렉터 전용으로 남겨 뒀다(S1 배지 색 단언이 그 클래스를 쓴다).
- 마법사 내부 "Step 1/2/3" 표기가 상위 탭(공고 가져오기=Step1, 준비 보드=Step2, 관심 공고=Step3)과 번호가 겹쳐서, "Step 1-1"/"Step 1-2"/"Step 1-3"로 고쳤다.

## 검증

- 단위 테스트 `tests/test_docs_extraction.py`: 275/275 통과(변경 전후 동일)
- 금지 문구 검사 `tests/test_screen_strings.py`: 20/20 통과
- 전용 포트 19001에 직접 서버를 띄워 실제 브라우저(OpenClaw browser 도구)로 1p→2p→3p→전환화면→준비보드 전체 흐름을 끝까지 눌러 확인(데스크톱 1280px·모바일 390px 둘 다). 콘솔 오류는 `favicon.ico` 404(기존부터 있던 무관한 것) 외 0건.
- 브라우저 `history.back()`과 전체 새로고침 모두 JS 오류 없이 정상 동작 확인(상태는 각 화면이 독립적으로 다시 렌더되는 방식이라 깨지지 않는다 — 단, 마법사 내부 진행 상태 자체는 URL 해시에 반영되지 않으므로 새로고침하면 1p로 돌아간다. 의도된 동작이다).

## 다음 phase(공고확인 단계 내부 로직)에 넘길 메모

- 1단계(공고확인) 내부 유효성 검사(입찰기간 만료, 목적 불일치 피드백 + 재시작 분기)는 이번에 손대지 않았다 — `getFitMessage()`가 이미 "mismatch"/"check" 판정을 내고 있으니 그 분기를 재사용하면 될 것으로 보인다.
- 전환 화면의 900ms는 임의로 정한 값이다. 실제 사용자 테스트에서 너무 짧거나 길면 조정이 필요하다.
- `tests/screen.spec.js`를 이 워크트리 전용 포트로 돌릴 수 있는 별도 playwright config(또는 `--config` 오버라이드)를 마련하면, 다음 phase부터는 e2e 게이트(17/17)도 정식으로 돌릴 수 있다.
