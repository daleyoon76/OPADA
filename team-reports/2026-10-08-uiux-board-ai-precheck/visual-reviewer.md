# 3팀(UIUX품질팀) visual-reviewer 독립 재검토: 할 일 카드 AI 사전 확인·질문 초안

- 날짜: 2026-10-08
- 역할: visual-reviewer(이 세션이 직접 수행, `Agent` 도구로 재위임하지 않음)
- 워크트리: `~/Documents/Dev/Hometest_op`(main, 유일한 워크트리)
- 판정 대상 커밋: `a02f8a1`(frontend-implementer 구현). HEAD는 `970a47b`(그 바로 다음 커밋이고, 구현 보고서의 커밋 해시 오기를 정정한 docs 전용 커밋이라 코드 변경은 없다. `git show 970a47b --stat`로 확인)
- sha256(착수 직후, `a02f8a1` 기준 작업트리): `src/app.js` `48cef7ec726e3f43191ddd31995a00643c161d5be64df2a6d69077c9eb2a26cc` · `src/styles.css` `b70da83fa81d2081da30e79f259637c22919723df50bcb74636669f77d92a1a6` · `src/server.py` `3cd866946ba1edd98da72c07a598e5f7d7468a2816e986677da742b22b6ee114`

## 판정: 조건부 GO (안전 경계 P1 1건을 이 세션이 직접 수정한 뒤 GO)

## 항목별 판정표

| 항목 | 구현 보고 주장 | 이 세션의 독립 확인 방법 | 판정 |
|---|---|---|---|
| ① AI 사전 확인 노출 | `<details>`에 헤지 문장 노출 | Playwright로 실제 서버(8975) 구동, 3개 분기(match/mismatch/check) 라이브 렌더 확인 | ✅ 확인됨(라벨은 아래 안전 경계 항목에서 수정) |
| ② 질문 초안 자동 생성 | 불일치·추출 실패에만 생성 | 같은 Playwright 세션에서 match 시 질문 없음, mismatch/추출실패 시 질문 있음을 직접 관측 | ✅ 확인됨 |
| ③ 2열 표 레이아웃 | 데스크톱·모바일 안 깨짐 | 1280px·390px 스크린샷 직접 캡처, 긴 라벨("대부료 외 반복 비용" 등) 줄바꿈 확인 | ✅ 확인됨 |
| ④ 최저입찰가격 코드 변경 없음 | `server.py` 미변경 | `git diff a02f8a1~1 a02f8a1 -- src/server.py` 빈 출력 직접 확인 | ✅ 확인됨. 단 코드 변경이 0건이라는 사실만 확인했고, 조사 결론 자체는 재현 시도했으나 외부 사이트 접근 실패로 미확인(아래 참고) |
| 회귀 | 기존 기능 안 깨짐 | `npm run test:unit` 275/275+20/20, `npx playwright test` 17/17 재실행 | ✅ 확인됨 |

## 안전 경계 검토 결과 (가장 중요)

### P1: "AI" 라벨이 100% 규칙 기반 콘텐츠에 무조건 붙어 있었음. 이 세션이 직접 수정함

- **발견**: `getAiPrecheckForTask()`가 반환하는 `precheck`/`draft` 문장은 `getFitMessage()`(클라이언트 if/else)와 `task.action`(서버 `build_tasks()`)에서만 오고, 어디에도 LLM 호출이 없다(`src/server.py`·`src/app.js` 전수 확인 결과 `llm`/`Vertex` 참조 0건). 그런데 렌더링 시 라벨이 **무조건** `AI 사전 확인`·`AI가 짚은 질문`으로 붙어 있었다. `coach?.llmStatus`를 전혀 참조하지 않는다.
- **왜 문제인가**: 같은 파일(`src/app.js:995-996`)에 이미 명시된 설계 원칙이 있다. *"모델에 붙지 않았으면 「AI 가 했다」고 말하지 않는다. 색만 바꾸면 색을 못 보는 사람에게는 같은 화면이고, 색을 보는 사람에게도 문구가 사실과 어긋난 채 남는다."* 이 원칙에 따라 `renderBoardCoach()`(996행)·`renderAnalysisResult()`(1105행)는 `llmConnected ? "AI ..." : "규칙 기반 ..."`로 분기하고, `askAgency` 질문 문구도 2026-10-04 visual-reviewer r2(P2-A)에서 같은 이유로 조건부 문구로 수정된 전례가 있다(1622행 주석에 그 경위가 그대로 남아 있다). 이번 신설 함수는 이 전례와 같은 부류인데 llmStatus 분기 자체가 없었다. 조건부가 아니라 **항상** 규칙 기반인데도 **항상** "AI" 딱지가 붙어 있었다.
- **왜 자동 검사가 못 잡았나**: `tests/screen.spec.js`의 N5("LLM 에 붙지 않았으면 「AI 가 했다」는 문구를 세우지 않는다")는 두 가지 이유로 이번 사례를 놓쳤다. 첫째, 스캔 범위가 `#analysis-result`로 한정돼 있어 할 일 카드(`#task-list`)를 보지 않는다. 둘째, `AI_CLAIM_PHRASES`가 `["AI 분석 완료", "AI 누락 점검", "AI가 미해결 항목만 골랐습니다", "AI가 먼저 볼 빈칸"]` 하드코딩 목록이라 이번에 추가된 새 문구가 애초에 목록에 없다. `tests/test_screen_strings.py`의 금지표현 목록(FORBIDDEN)에도 "AI" 단독 패턴은 없다(CLAUDE.md의 「완전 자동」·「Vertex AI」·「Gemini AI」처럼 구체적 과장 표현만 금지 대상이다). 즉 두 안전망 모두 이 부류를 겨냥하지 않았다. 게이트의 결함이 아니라 **적용 범위 밖**이었다.
- **수정**: `src/app.js` 1552~1553행의 두 `<dt>` 라벨을 `AI 사전 확인` → `규칙 기반 사전 확인`, `AI가 짚은 질문` → `담당기관에 물어볼 질문`으로 바꿨다. 조건부(llmStatus 분기)가 아니라 **무조건 규칙 기반 문구**로 고정했다. 이 함수는 llmStatus와 무관하게 항상 규칙 기반이라, "연결되면 AI, 아니면 규칙 기반"으로 분기하는 기존 패턴(996·1105행)을 그대로 가져오면 오히려 "연결 시에는 실제로 AI가 만들었다"는 잘못된 인상을 준다. 내용 문장(precheck/draft 값) 자체는 건드리지 않았다. 거기엔 애초에 "AI"라는 말이 없었다.
- **재확인**: 라벨 수정 후 `npm run test:unit`(275/275+20/20)과 `npx playwright test`(17/17)를 재실행해 전부 그대로 통과함을 확인했다. Playwright로 두 라벨이 실제 화면에 바뀐 텍스트로 나오는지도 스크린샷으로 직접 재확인했다(`screenshots/notice-type-card-startup-desktop-zoom.png`·`price-card-mobile-zoom.png`).
- **커밋**: 이 보고서와 같은 커밋.

### 판정 로직 문구 자체: 확정 판단 없음 확인

- precheck 문장 5종(match·check·mismatch·추출성공·추출실패·비공개가격)을 전부 `grep`과 Playwright 라이브 렌더로 원문을 직접 읽었다. 전부 "~로 보입니다"·"~로 확인된 것으로 보입니다"로 헤지하고 "원문·담당기관 확인을 우선합니다"로 끝난다. "일치합니다"·"확인됐습니다" 같은 단정 표현은 없다.
- `tests/test_screen_strings.py`의 FORBIDDEN 14종(자동 입찰·입찰 대행·낙찰 가능성 예측 등)과 이 5개 문장을 교차 대조했고, 겹치는 단어가 없음을 직접 `hits()` 호출로 재확인했다(아래 「검증」 참고).

## 기능 재검증 (직접 라이브 확인)

포트 8975(기존 상주 서버, PID 15027. `lsof -i :8975`로 재확인했고 구현자 보고의 PID와 동일)에 Playwright로 직접 접속해 확인했다. 서버(`server.py`)는 건드리지 않았으므로 재시작이 필요 없고, 디스크의 `app.js`/`styles.css` 수정이 요청마다 바로 반영된다(`SimpleHTTPRequestHandler`).

- **match(목적 일치, focus=lease)**: notice-type 카드에 "규칙 기반 사전 확인: 선택한 검토 목적과 공고 유형을 비교했을 때 맞는 것으로 보입니다. 원문·담당기관 확인을 우선합니다."가 노출됐고, 질문 초안은 **없었다**(의도대로).
- **mismatch(focus=sale)**: "규칙 기반 사전 확인: 선택한 검토 목적과 공고 유형이 다른 것으로 보입니다. ..."와 "담당기관에 물어볼 질문: 제가 고른 용도와 공고 유형이 다르게 보이는데, 이 공고로 진행해도 되는지 확인 부탁드립니다." 둘 다 노출됐다.
- **check(창업 목적, focus=startup)**: "규칙 기반 사전 확인: 창업 공간으로 활용 가능한지는 용도, 사용 제한, 시설 상태, 담당기관 확인이 필요합니다. ..."와 질문 초안이 함께 노출됐다. 데스크톱 1280px 확대 스크린샷으로 레이아웃을 확인했다(`screenshots/notice-type-card-startup-desktop-zoom.png`).
- **추출 실패(bid-period·price, 샘플 공고 기준)**: "규칙 기반 사전 확인: 원문에서 값을 찾지 못했습니다. 직접 확인해 주세요."와 각각 다른 질문 초안("입찰기간은 언제인가요?"/"최저입찰가격은 얼마인가요?")이 노출됐다. 모바일 390px 확대 스크린샷으로 긴 라벨("대부료 외 반복 비용")의 줄바꿈을 확인했고(`screenshots/price-card-mobile-zoom.png`), 표는 깨지지 않았다.
- **콘솔 에러**: desktop(lease)·desktop(sale)·mobile(390) 세 세션 모두 `page.on("console"/"pageerror")` 0건.
- **가로 스크롤**: 390px에서 `document.documentElement.scrollWidth > clientWidth`가 `false`로 나와 넘침이 없음을 확인했다.
- **비공개 가격 분기(`task.action === "비공개"`)**: 샘플 공고가 이 상태가 아니라서 라이브로 재현하지 못했다. 코드 로직(`src/app.js:918-923`)과 `PRICE_UNDISCLOSED` 상수(`src/server.py:812`)를 읽는 수준으로만 확인했다. **미검증(코드 읽기 수준)**.

검증 방법: 이 세션이 `tests/_reviewer-adhoc-*.spec.js`(임시, 커밋하지 않고 검증 후 삭제)를 작성해 `npx playwright test`로 직접 구동했다. 스크린샷 8장은 `screenshots/`(gitignore 대상이라 로컬에만 남는다)에 있다.

## 회귀 확인

- `renderBoardCoach()`·질문-답변 카드·`support-tablist`: `git diff a02f8a1~1 a02f8a1` 전체를 눈으로 읽어 해당 함수 호출부 변경이 없음을 직접 확인했다(변경 파일은 `app.js`·`styles.css` 둘뿐이다).
- 기존 `<p><b>라벨</b>: 내용</p>` 패턴 잔존 여부: `grep -n '<p><b>' src/app.js` 결과 0건으로, 전환 누락이 없다.
- `npm run test:unit`: **275/275**(`test_docs_extraction.py`) + **20/20**(`test_screen_strings.py`). 라벨 수정 전후 둘 다 재실행했고 동일하게 통과했다.
- `npx playwright test tests/screen.spec.js tests/public-data-status.spec.js`: **17/17**. 라벨 수정 전후 둘 다 재실행했고 동일하게 통과했다.

## 확인 못 한 것

- **최저입찰가격 조사 결론(④번 항목의 "조사 완료" 부분)**: 온비드 원문 HTML을 직접 `curl`로 재현 시도했으나 HTTP 500(세션·리퍼러 없는 단순 요청을 서버가 거부하는 것으로 추정)만 받아 재현에 실패했다. 코드를 건드리지 않았다는 사실(④의 핵심 주장)은 `git diff`로 확정했지만, "JS가 비동기로 채우는 구조"라는 조사 결론 자체는 이 세션이 독립적으로 재확인하지 못했다. 코드 변경이 0이므로 이 부분이 틀렸어도 안전·기능 리스크는 없다.
- **가격 "비공개" 분기의 라이브 렌더**: 위 참고. 코드 읽기로만 확인했다.
- **`tests/test_screen_strings.py` 중첩 템플릿 리터럴 사각지대**: `to-do.md`에 P2로 등재했다(아래 참고). 고치지는 않았다. 이번 diff가 만든 새 문제가 아니라 "먼저 할 일" 라벨에 이미 있던 기존 사각지대에 신설 라벨 2개가 추가로 들어간 것이고, 범위를 넓히면 별도 작업이 된다.
- **동시 사용자·다른 브라우저**: 단일 Playwright 세션으로만 확인했다. 동시성 이슈는 이 기능 자체에 해당 사항이 없다(순수 렌더 함수).

## 고친 것 요약

| 파일 | 변경 | 이유 |
|---|---|---|
| `src/app.js` (1552~1553행) | `AI 사전 확인`→`규칙 기반 사전 확인`, `AI가 짚은 질문`→`담당기관에 물어볼 질문` | 안전 경계 P1. LLM 미연결 상태에서도 무조건 "AI" 라벨이 붙던 문제를 수정했다. 내용 문장(판단 로직)은 변경하지 않았다 |
| `to-do.md` | P2 2건 등재([등록 2026-10-08]) | 중첩 템플릿 리터럴 검사 사각지대, 새 기능 자동 테스트 공백 |

## 다음 단계 제안 (P2, 고치지 않음, to-do.md 참고)

1. `tests/test_screen_strings.py`의 `js_strings()`를 중첩 백틱 인식 파서로 교체하거나, 라벨 상수를 분리한다.
2. `getAiPrecheckForTask()`의 6개 분기(match/check/mismatch/추출성공/추출실패/비공개가격)를 겨냥한 `screen.spec.js` 축을 신설한다.
