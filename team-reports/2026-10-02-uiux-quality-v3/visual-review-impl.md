# 3팀 UIUX품질팀 — 실제 코드 반영 독립 검토 (visual-reviewer)

- 작성: 2026-10-02
- 담당: visual-reviewer (읽기 전용, 저자=frontend-implementer 와 분리된 독립 검토)
- 판정 대상: `git diff`(워킹 디렉터리, 미커밋) — `src/app.js`(+20/-3) · `src/index.html`(+17/-8, 실질은 순서 이동) · `src/styles.css`(+26/-1)
- 대상 저장소: `~/Documents/Dev/Hometest_op-test`(워크트리 `test`)
- 코드 수정 없음. grep·curl·독립 playwright 스크립트로 직접 재현만 함.

## 결론부터 — 최종 판단

**조건부 GO.** 네 가지 항목 + is-done 버그 수정의 실제 코드는 네 소스 문서(ux-audit·visual-audit·v3 재판정·22번 목업) 의도와 일치하고, 내가 독립적으로 재현한 데스크톱·모바일 스크린샷에서 회귀를 찾지 못했다.
다만 **"e2e 17/17 재검증" 주장은 이 diff에 대한 증거로 쓸 수 없다** — 아래 🔴 참조. 코드는 GO, 이 e2e 재검증 서술은 정정 없이 그대로 인용·발행하면 안 된다(NO-GO).

## 넘침·겹침 (고정 축 — PPT 아닌 웹 UI지만 Core Workflow 상 동일 기준 적용)

- 텍스트 넘침: 0건 관측(데스크톱 6장 + 내가 재현한 데스크톱 1280px·모바일 375px 스크린샷 총 8장 육안 확인).
- 요소 겹침: 0건 관측(같은 8장). `scripts/slide-overlap.js` 류의 사각형 자동측정 도구는 이 저장소에 없음(PPT 전용 스크립트라 미적용) — **육안 확인만**이고 자동측정 0건이라는 점을 미검증으로 남긴다.

## 항목별 판정

### 1. 코치 패널 1인칭 문구 — GO
- `renderCoachPanel`은 `src/app.js` 전체에서 호출부 1곳(`app.js:1495`, `{ board: true }`)뿐임을 `grep -n "renderCoachPanel("`로 직접 확인. 패킷의 주장과 일치.
- 즉 `options.board ? "" : ...` 헤드라인 분기(옛 977행대)는 **데드 코드**가 맞다. 이 diff가 그 안의 리터럴 문구를 바꿨지만(`"AI가 미해결 항목만 골랐습니다."` → `"제가 미해결 항목만 골랐습니다."`), 분기 자체는 이 diff 이전부터 도달 불가능했고 이번 diff가 새로 죽은 코드를 만든 것이 아니다. Karpathy 가이드라인("관련 없는 데드 코드는 언급하되 삭제하지 마라")대로 언급만 하고 넘긴다. 🔵
- N5 스코프 주장도 `tests/screen.spec.js`를 직접 읽어 확인: `aiClaimHits(page, "#analysis-result")`(line 627), N5 테스트 2건(line 702, 708) 모두 `#analysis-result`만 본다. `#board-coach`는 어떤 e2e 테스트에서도 locator로 등장하지 않음(`grep -rln "board-coach" tests/` 결과 0건). 패킷 주장과 일치.
- 실제 렌더 문구(`boardLead`, 살아있는 코드)는 연결 시 "제가 체크리스트를 먼저 훑어서...", 미연결 시 "정해진 규칙으로 체크리스트를 먼저 훑어서..."로 "AI"라는 단어 자체를 쓰지 않는다 — 내용상 "AI가 했다" 주장을 하지 않음. 내 모바일 스크린샷(아래)에서 미연결 상태 실제 렌더로 재확인.
- 🟡 **새로 발견(이 diff 범위 밖, 손대지 않은 기존 코드)**: 같은 패널 안 `factsHtml` 블록의 라벨이 `"AI가 탐지한 내용"`(`app.js:988`, 고정 문자열, llmConnected 분기 없음)으로 하드코딩돼 있다. `AI_CLAIM_PHRASES` 목록에는 없어 N5 테스트에 걸리지 않지만, 바로 옆 배지(`coachMode`: "규칙 기반 누락 점검")와 모순되는 문구다. 이번 diff가 만든 결함은 아니지만, 이번 diff가 이 패널을 주 동선(1인칭 톤 + 더 눈에 띄는 노출)으로 격상시켜 **노출 빈도를 올렸다** — visual-audit.md가 이미 "`.badge.warn` 노출 빈도 증가"를 정보성으로 적어 둔 것과 같은 계열의 리스크다.
  - 다음 사람이 이 증상을 만나면: `app.js:988` 바로 위에 `// TODO: llmConnected 분기 없음 — "AI가"를 "규칙이"로 바꿔야 N5 원칙과 일치` 주석 1줄을 남기는 편이 추적 문서보다 낫다(이번엔 코드 수정 권한이 없어 주석도 직접 달지 못함 — frontend-implementer에게 위임).
  - 비용: 분기 추가 자체는 5분 미만(코드 변경 범위가 이번 4항목 밖이라 별도 커밋 권장).

### 2. task-ai-nudge 강조 + is-done 버그 — GO
- `.task-ai-nudge strong`: 12px→14px, visual-audit.md P1 권고와 일치.
- `.task-item.is-done .task-ai-nudge { display: none; }` 신규 — 기존 `.task-item.is-done { background: ... }` 패턴(line 846)을 그대로 따른 CSS 전용 처리. `grep -n "is-done" src/app.js`로 렌더 조건(`task-summary.state[task.id] ? "is-done" : ""`) 자체는 손대지 않았음을 확인 — "CSS 숨김 방식, 렌더 조건은 그대로" 주장과 일치.
- `_tmp-task-list.png`(체크 전) ↔ `_tmp-task-list-after-check.png`(1번째 항목 체크 후) 비교: 체크된 항목의 "확인 필요 항목" 박스만 사라지고, 아래 미체크 항목들의 박스는 그대로 남아 있음을 직접 확인. 의도대로 동작.

### 3. 질문-답변 위젯 독립 카드 — GO (경미한 신규 관찰 1건 P2)
- `renderCoachAskCard()`가 `renderCoachAsk()`를 감싸 "AI 코치" 배지 + "AI 코치에게 물어보기" 제목을 추가하고, `renderCoachPanel` 내부 호출은 제거됨. `renderReport()`에서 `#board-coach-ask`에 별도 렌더 — diff와 일치.
- `grep -n "board-coach-ask" src/styles.css` 결과 0건 — 컨테이너(`#board-coach-ask`/`.board-coach-ask`)에 의도치 않은 스타일 없음. `.coach-ask-card`만 스타일을 가짐 — 패킷이 설명한 "컨테이너 무스타일/콘텐츠만 스타일" 패턴(`#board-coach`와 동일)이 실제로 지켜짐을 확인.
- `_tmp-coach-ask-card.png` + 내가 재현한 `_tmp-board-full.png` 상당 화면에서 실선 `var(--line)` 테두리로 렌더됨을 확인 — visual-audit.md P0가 지적한 `.mock-ask-promoted`의 점선 amber 테두리는 쓰이지 않음. amber 관련 새 사용처 0건(`grep` 결과 diff 안에 `amber` 토큰 없음).
- 🟡 **새로 발견**: `renderCoachAskCard()`의 배지는 `badge("AI 코치", "safe")`로 **고정**돼 있고 `llmConnected` 인자를 받지 않는다. 같은 파일의 `renderCoachPanel`은 `coachMode`를 llmConnected로 분기하는데, 이 카드는 LLM 미연결 상태에서도 항상 "AI 코치"라는 라벨을 쓴다. 다만 이는 ux-audit.md 원문이 "승격 카드에도 코치와 같은 라벨(「AI 코치에게 물어보기」 등)을 넣어 같은 화자임을 유지"라고 **그대로 지시한 문구**라 이 diff의 일탈이 아니라 원 audit 자체의 사각지대다. 실제 질문 제출 시 응답(`renderQuestionAnswer`, 기존 코드)은 `answer.connected`가 false면 "AI 연결 안 됨" 배지로 정직하게 꺾인다(`app.js:1030-1034`) — 사용자가 실제로 질문해 보면 바로 드러나므로 기만으로 보기는 어렵다. P2로 다음 iteration 백로그에 남기는 것을 권고.

### 4. 접힌 패널 재배치 + 기본 펼침 — GO
- `src/index.html`의 `<summary>` 순서를 직접 추출(`grep -n "<summary>"`)해 확인: 마감·비용 요약 → 담당기관에 물어볼 문장 모음 → 공고 첨부파일 → 공고문 항목 보기 → 용어 안내 → 참고자료 → 근거와 안전 경계. 패킷이 설명한 순서, 22번 목업(`217~222행`)의 순서와 모두 일치.
- 앞 두 패널에만 `open` 속성 — 목업과 일치.
- 화살표 안내 문구 미추가 — ux-flow-auditor의 "구현하지 않는다" 판정을 그대로 존중했음을 diff에서 확인(추가된 텍스트 없음).
- `_tmp-support-grid.png`에서 3열 그리드 마지막 행이 "근거와 안전 경계" 1칸만 채워진 비대칭이 그대로 보임 — v3 재판정이 P2·범위 밖으로 남긴 것과 일치, 이번에 손대지 않음을 확인.

### 범위 밖 미침범 확인 — GO
- `git diff --name-only`: `src/app.js`·`src/index.html`·`src/styles.css` 3개 파일만 변경. 다른 파일(특히 `src/server.py`의 `local_ai_coach` 판정 로직, 계정/결제 관련 파일, `playwright.config.js`) 변경 0건을 `git status --short`로 확인.
- CSS 색상 토큰: diff 안에 새 hex/변수 선언 없음(`var(--line)`, `var(--panel)` 재사용만) — "색상 팔레트 전체 손대지 않음" 주장과 일치.
- 취소선(strikethrough), support-grid 3열 그리드 자체의 구조 변경 — diff에 없음, 스크린샷에서도 비대칭 그대로 — P2 보류 상태 유지 확인.

## 🔴 반드시 고쳐야 할 것 — "e2e 17/17 재검증" 주장의 증거 능력

**관측 사실**: `tests/screen.spec.js:162`와 `tests/public-data-status.spec.js:8`이 둘 다 `page.goto("http://127.0.0.1:8975/")`를 **하드코딩**하고 있다. `playwright.config.js`의 `use.baseURL`이나 `webServer`가 어떤 포트를 쓰든, 이 두 파일에서 파생되는 **모든** 테스트(N0~N6, S1~S9, public-data-status 1건 = 17개 중 17개 전부)는 실제로는 항상 **127.0.0.1:8975로 네비게이션**한다.

- `lsof -p 86154`로 그 포트의 프로세스 cwd가 `/Users/user/Documents/Dev/Hometest_op`(다른 워크트리, `-test` 아님)임을 직접 확인했다 — 패킷이 설명한 "다른 워크트리 서버가 점유" 진단은 **정확**하다.
- 그러나 내가 `playwright.config.js`의 `webServer` 포트만 바꿔(18976) 재현했을 때도 **같은 함정**에 걸렸다: webServer는 내 워크트리 코드로 18976에서 새로 뜨지만, 테스트 자체는 여전히 8975로 네비게이션해 **다른 워크트리의 구 코드**를 테스트했다.
- `curl`로 두 포트의 `index.html`을 직접 비교해 증명: `127.0.0.1:18977`(이 워크트리, 내 서버)에는 `id="board-coach-ask"`가 있고 패널 순서가 diff대로지만, `127.0.0.1:8975`(점유 중인 다른 워크트리)에는 `board-coach-ask`가 **없고** 패널 순서도 구버전이다.
- 즉 **implementer가 설명한 "playwright.config.js 포트만 18975로 바꿔 재검증"은 이 두 테스트 파일에 대해서는 문제를 해결하지 못한다.** webServer 디렉티브는 "어떤 프로세스를 띄우고 준비될 때까지 기다릴지"만 제어하고, 실제 브라우저가 어디로 접속하는지는 테스트 소스에 적힌 리터럴이 결정한다. 내가 동일한 방법으로 재현했을 때도 16/17 통과(1건은 N6 타임아웃, 8975 쪽 프로세스 상태에 따라 달라지는 노이즈로 추정 — 미확인)가 나왔는데, 이 결과는 **이 diff와 무관한 다른 워크트리의 코드를 테스트한 결과**라 증거로 쓸 수 없다.
- **이 diff(항목 1~4)를 다루는 e2e 테스트는 애초에 0건이다.** `grep -rln "board-coach\|task-ai-nudge\|support-grid\|coach-ask\|renderCoachPanel\|is-done" tests/` 결과 0건 — N0~N6·S1~S9·public-data-status 테스트 전부 `#analysis-result`·`#task-list`·`#doc-checklist` 등 분석 직후 화면만 다루고, 준비 보드(`#board-coach` 등)는 어떤 자동화 테스트도 보지 않는다.

**배제한 가설**: "내 재현 환경(포트 18976)이 잘못됐다" — 아니다. `curl`로 18977(동일 워크트리, 다른 임시 포트)을 직접 떠서 diff가 실제로 반영된 HTML을 받았음을 확인했고, 테스트가 그 포트가 아니라 8975로 가는 것이 원인임을 소스 리터럴로 특정했다.

**다음 probe**: `tests/screen.spec.js`·`tests/public-data-status.spec.js`의 하드코딩된 `8975`를 `playwright.config.js`의 `baseURL`(상대경로 `page.goto("/")`) 또는 `page.goto(testInfo.project.use.baseURL)`로 바꾸는 것이 근본 수정이다. 이번 diff 범위(UI 4항목) 밖이라 이 보고서에서는 고치지 않았고, frontend-implementer에게 별도 후속 작업으로 넘긴다.

- **비용/경계**: 테스트 파일 2곳의 리터럴 치환 + 로컬 재실행, 약 10~15분. 코드 수정 권한은 이 역할에 없으므로(읽기 전용) 직접 고치지 않았다. 팀장 승인 후 frontend-implementer가 수정.

## 내가 독립 재현한 검증 (재현 로그)

1. **단위 테스트**: `npm run test:unit` 직접 재실행 → `251/251 통과 · 연기 6개 · 축 28개 중 미실행 0개`, `20/20 통과 · 연기 1개 · 축 5개 중 미실행 0개`. 포트/서버 의존 없는 순수 함수 테스트라 이 diff를 정확히 반영한다 — implementer 주장과 일치, **유효한 증거**.
2. **e2e**: 위 🔴 참조. 내 재현에서 16/17(1건 타임아웃) — implementer의 17/17과 다른 수치이나, 둘 다 8975(다른 워크트리)를 테스트한 결과라 이 수치 자체가 이 diff에 대해 무의미하다. 수치 불일치 원인은 "공유 리소스 상태 비결정성"으로 설명 가능하나 **미확정**.
3. **데스크톱 풀보드 스크린샷**(1280px, 내 자체 fixture로 재현): board-coach(규칙 기반 미연결 문구 실제 렌더 확인) → coach-ask-card(AI 코치 배지 + 실선 테두리) → board-status 순서, support-grid 7패널 순서·앞 2개 open 확인. 제공된 6장과 별개로 내가 직접 띄운 서버에서 재확인.
4. **모바일 뷰포트 스크린샷**(375px, 내가 직접 playwright 스크립트 작성): `.support-grid`가 1열로 reflow, coach 패널과 coach-ask-card가 겹침·잘림 없이 순서대로 쌓임, 텍스트 넘침 없음을 확인 — **제공된 6장에는 모바일 스크린샷이 없어 이 부분은 내가 새로 메운 검증 공백**.
5. **공유 자원 안전**: 8975 프로세스(PID 86154)를 시작·종료 전후로 `lsof` 대조해 내가 건드리지 않았음을 확인. 임시 파일·임시 서버(18976·18977·18978)·임시 config는 작업 종료 시 전부 제거, `git status --short`로 diff 대상 3개 파일 외 변경 없음 재확인.

## 검증 누락

- 🟡 자동 겹침 측정 도구(사각형 좌표 기반) 미적용 — 이 저장소에 PPT용 `slide-overlap.js` 같은 도구가 없어 육안 확인만 했다. 비용: 전용 스크립트 작성 시 30분 이상, 이번 UI 규모엔 과함 — 생략 타당하나 "자동측정 0건"은 명시해 둔다.
- 🟡 질문-답변 카드의 **실제 질문 제출 흐름**(버튼 클릭 → `/api/ask` 호출 → 응답 렌더)은 스크린샷·내 재현 모두 **정적 렌더만** 확인했고 동작 자체는 누르지 않았다. 이 diff가 `renderCoachAsk()` 내부 마크업은 그대로 재사용했다고 주장하므로 로직 변경 가능성은 낮으나, 실클릭 재현은 하지 않았다. 비용: 10분 내 가능(위 모바일 스크립트에 버튼 클릭 추가), 승인 경계는 없음 — 원하면 추가 수행 가능.
- 🔵 LLM 연결 상태(`llmConnected: true`) 쪽 렌더는 스크린샷·내 재현 모두 **미연결** 상태만 보여준다. 코드상 삼항 분기라 로직은 명확하나, 연결 상태의 실제 화면은 아무도 스크린샷으로 남기지 않았다. 비용: fixture의 `llmStatus`를 `"connected"`로 바꿔 5분 내 재현 가능.

## 최종 판단 (재확인)

- **코드(항목 1~4 + is-done 버그)**: GO. 네 소스 문서 의도와 일치, 회귀 0건 관측(데스크톱·모바일), 범위 밖 미침범 확인.
- **"e2e 17/17 재검증" 서술**: NO-GO로 정정 필요 — 이 diff의 증거가 아니다. 커밋 메시지나 사용자 보고에 이 수치를 인용하면 안 된다(P-35 "미실측 지표는 제목에서 빼거나 「기대값」으로 적는다"에 해당 — 이 경우는 "기대값"도 아니고 "측정 대상이 다른 수치"라 더 나쁘다). `npm run test:unit`의 251/251·20/20만 이 diff의 유효한 자동 검증 증거로 인용할 것.
- 커밋 전 권고: 커밋 메시지에 "e2e 17/17 통과" 문구를 넣지 말 것. 대신 "단위 테스트 251/251+20/20 통과, e2e는 하드코딩 포트 문제로 이 diff에 대해 미검증(후속 과제)"로 적는 것을 권고.
