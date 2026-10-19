# 묶음 A 구현 반환물 (frontend-implementer · I1 · I2 · I3)

> 팀장 전사: frontend-implementer 가 채팅으로만 반환해 팀장이 이 파일로 옮겼다(2026-10-19 · 반환 직후 · 파일 작성 뒤 20:17:49 `date` 출력). 본문은 반환물 그대로다.
> 팀장 대조: 반환물의 diff 지문 `1fd73e46` 은 팀장이 다시 잰 `git diff src/app.js | shasum` 앞 8자와 같다. triage.md 변경은 팀장이 19:51 에 더한 5절이다.
> 역할의 재현 스크립트·변이 파일·로그는 `/private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/e6ad4d9c-5c84-4401-baa3-6e11a43878f2/scratchpad/role-impl/` 에 있다(레포 밖).

세 건 모두 고쳤습니다. 수정한 파일은 `src/app.js` 하나이고, 커밋하지 않았습니다. 고치기 전 판(1340f55)에서 실패하던 재현이 고친 판에서는 모두 통과합니다. 전체 E2E 는 고치기 전과 똑같이 8건이 실패하므로 이번 변경 때문에 생긴 실패는 없습니다.

## 1. 바꾼 함수와 이유 · `git diff --stat`

- **상태 변수 추가** (`coachAnswerHtml` · `askInFlight` · `askRequestId` · `askCooldownUntil` · `askCooldownTimer`): 코치 영역은 다시 그릴 때마다 통째로 바뀌므로, 답과 잠금 상태를 화면 요소가 아니라 변수에 둡니다.
- **`renderBoardCoachKeepingState`**: 결과 영역을 화면에서 복사하지 않고 `coachAnswerHtml` 에서 되살립니다. 그다음 `applyCoachAskControls()` 로 잠금과 버튼 글자를 다시 맞춥니다.
- **새 함수 7개**
  - `escapeHtml`: 서버 오류 문구가 태그가 아니라 글자로 보이게 합니다. app.js 에 비슷한 함수가 없어서 새로 만들었습니다.
  - `setCoachAnswer`: 답을 변수에 보관하고, 쓰는 순간에 결과 요소를 다시 찾아 씁니다(I1 ⑴).
  - `isCoachAskLocked`: 「진행 중이거나 429 직후」인지 판정합니다.
  - `applyCoachAskControls`: 질문하기 버튼 · 칩의 잠금, 버튼 글자, 결과 영역의 `aria-busy` 를 상태 변수대로 맞춥니다.
  - `clearCoachAnswer`: 요청 번호를 올리고, 진행 중 표시를 풀고, 답을 비웁니다.
  - `startAskCooldown`: 429 를 받으면 60초 동안 버튼을 「1분 뒤 다시」로 잠급니다.
  - `setAnalysisInputsBusy`: 분석 중에 `#notice-url` · `#load-sample` · `#analyze` 를 막고 `#analyze` 에 `aria-busy` 를 붙입니다.
- **`askNoticeQuestion`**
  - 결과 요소를 처음에 잡아 두지 않습니다.
  - 맨 앞에서 잠금을 확인합니다. 버튼 · 칩 · Enter 세 경로가 모두 이 함수로 오므로 한 곳에서 막힙니다.
  - `askRequestId` 로 낡은 응답을 버립니다. 판정은 응답 직후 · catch · finally 세 곳에 있습니다.
  - 429 면 잠금을 시작하고, `payload.error` 는 이스케이프해서 넣습니다.
- **`runAnalysis`**
  - 요청 전에 `requestedInput` 을 잡아 둡니다. 요청 URL과 `analyzedInputValue` 기록 둘 다 이 값을 씁니다.
  - 분석 중에는 입력을 잠그고, 성공하면 코치 답을 비웁니다.
  - 기존 `analysisRequestId` 흐름은 그대로 두었습니다. finally 에서 잠금을 푸는 것도 최신 요청일 때만입니다.
- **`restartWizardToProfile`**: 잠금 해제와 `clearCoachAnswer()` 를 넣었습니다. 분석 중에 돌아오면 그 응답의 finally 가 잠금을 풀지 않기 때문입니다. `startNewAnalysis` 는 이 함수를 부르므로 같이 처리됩니다.
- **샘플 불러오기 핸들러**: `byId("analyze").disabled = false` 줄을 `setAnalysisInputsBusy(false)` 로 바꾸고 `clearCoachAnswer()` 를 넣었습니다.

지시와 다르게 한 점이 둘 있습니다.
- 429 뒤 60초 동안은 자주 묻는 질문 칩도 막습니다. 막지 않으면 칩을 눌러도 아무 반응이 없습니다.
- 「질문하기」 버튼의 선택자를 `#board-coach [data-ask-question]` 로 좁혔습니다.

```
 src/app.js                                         | 133 ++++++++++++++++++---   (119+ / 14-)
 .../2026-10-19-uiux-quality-improve-uiux/triage.md |   8 +-
```
- triage.md 변경은 제 것이 아닙니다. 첫 `git diff --stat`(19:52, 제가 고치기 전)에 이미 있었고, 건드리지 않았습니다.
- 지금 판의 `git diff src/app.js | shasum` 앞 8자는 `1fd73e46` 입니다.
- 진단은 「20줄 안팎」으로 봤지만 실제로는 119줄이 늘었습니다. 대부분 주석과 상태 함수입니다.

## 2. 검증 표

재현 스크립트는 scratch 로 복사해 고쳐 썼습니다.
- 공통: 포트를 19310 으로 바꿨습니다.
- p2: 연타 2번째 클릭과 Q2 클릭에 `force:true` 를 붙였습니다(잠긴 버튼을 Playwright 가 기다려 주면 연타가 재현되지 않습니다. 고치기 전 판에서는 버튼이 열려 있어 동작이 같습니다). 429 단계는 맨 뒤로 옮겼습니다(고친 판에서는 60초 잠금 때문에 뒤 단계가 멈춥니다). 오류 문구 이스케이프를 보는 ESC 단계를 넣었습니다.
- p3: 분석 중 잠금 상태를 찍는 LOCK 줄, 「막힘」을 기록하는 fill, 값만 바꾸는 M-js 단계를 넣었습니다.
- p7(새로 작성): 새 분석으로 넘어갈 때 답이 남는지 보는 R1~R5 입니다. 가짜 응답만 씁니다.

| 검사 | 고치기 전 결과 (1340f55) | 고친 뒤 결과 | 시각 |
|---|---|---|---|
| `node --check src/app.js` | (해당 없음) | exit 0 | 19:58:56 |
| `test_docs_extraction.py` | (미실행) | `462/462 통과 · 연기 7개 · 축 43개 중 단정이 한 번도 안 돈 축 0개` | 19:58:56 |
| `test_screen_strings.py` | (미실행) | `20/20 통과 · 연기 1개 · 축 5개 중 미실행 0개` | 19:59:13 |
| p2 G 체크박스 누른 뒤 | `result= "답변을 찾는 중입니다..."` | `result= "공고 원문 기반 답변\n\nMOCK-ANSWER-1 …"` | 19:55:00 / 19:56:57 |
| p2 H 단계 이동 뒤 | `"답변을 찾는 중입니다..."` | `"공고 원문 기반 답변\n\nMOCK-ANSWER-1 …"` | 같음 |
| p2 F 연타 3번 | `btnDisabled:false … busy:null,chipDisabled:false … requests sent by 3 activations: 3` | `btnDisabled:true … busy:"true",chipDisabled:true … requests sent by 3 activations: 1` | 같음 |
| p2 order | `reqs 2 … final(input=Q2): "…MOCK-ANSWER-1"` (Q2 답을 Q1 답이 덮음) | `reqs 1` (Q2 는 나가지 않고, 답은 Q1 것 하나) | 같음 |
| p2 ESC | `<b id="xss">굵게</b>` · `tag:true` | `&lt;b id="xss"&gt;…` · `tag:false` | 같음 |
| p2 429 버튼 | `{"t":"질문하기","d":false,"chips":[false,false,false]}` | `{"t":"1분 뒤 다시","d":true,"chips":[true,true,true]}` | 같음 |
| p2 429 뒤 다시 그림 | `{"t":"질문하기","d":false,…}` | `{"t":"1분 뒤 다시","d":true,…}` | 같음 |
| p2 429 직후 Enter | `reqs: 1` | `reqs: 0` | 같음 |
| p2 J 한글 조합 중 Enter | (고치기 전 출력 미확인) | `requests: 0` | 19:56:57 |
| p3 LOCK 분석 중 | `urlDisabled:false,sampleDisabled:false,analyzeBusy:null` | `urlDisabled:true,sampleDisabled:true,analyzeBusy:"true"` | 20:07:05 / 19:58:23 |
| p3 M 분석 중 URL 고침 | `filled` → `prepareDisabled:false`, 결과는 「성남시 분당구…」 | `blocked` (입력이 잠겨 고칠 수 없음) | 같음 |
| p3 M-js 값만 바꿈 | `{"prepareDisabled":false}` | `{"prepareDisabled":true}` | 같음 |
| p3 성공 · 실패 뒤 잠금 | (고치기 전에는 잠금 없음) | 둘 다 `urlDisabled:false,sampleDisabled:false,analyzeBusy:null,analyzeDisabled:false` | 19:58:23 |
| p7 R4 답을 받은 뒤 다시 분석 | `after= "공고 원문 기반 답변 MOCK-ANSWER-4"` (옛 답이 남음, 이번에 새로 확인) | `after= ""` | 20:07:05 / 20:14:12 |
| p7 R5 옛 답이 새 질문 중에 도착 | `btnDisabled:false` · `busy null` | `btnDisabled:true` · `busy true` | 20:14:58 / 20:14:12 |
| p7 R1~R3 | `after= ""` (고치기 전에도 통과) | `after= ""` | 같음 |
| p6 실서버(질문 1회) | `shown= "답변을 찾는 중입니다..."` (3007ms) | `shown= "담당기관 문의 필요\n\n이 질문은 공고 원문만으로 답하기 어렵습니다. …"` (979ms) | 19:55:32 / 19:58:45 |
| E2E `-g "매각결정기일"` | (고친 뒤에만 실행) | `No tests found` | 19:59:18 |
| E2E `-g "AI 코치 질문"` | (미실행) | `1 passed (5.0s)` | 19:59:34 |
| E2E 전체 | `8 failed · 29 passed (2.7m)` | `8 failed · 29 passed (2.6m)` | 20:02:54 / 19:59:53 |

- E2E `-g "매각결정기일"` 이 0건인 이유: 그 낱말은 테스트 「본문」에만 있고 이름에는 없습니다. `coach-question-input` 을 쓰는 테스트는 `screen.spec.js:945` 하나뿐이고, 이름 「AI 코치 질문」으로 돌리면 `1 passed (5.0s)` 입니다. 그래도 실행 상태는 failed 입니다. gate-reporter 가 `-g` 로 거른 실행을 「모수 어긋남 1/36」으로 일부러 실패 처리하기 때문입니다.
- E2E 전체의 실패 8건은 고치기 전 판과 테스트 이름 집합(`SAME FAILURE SET`)과 오류 줄(`SAME ERROR LINES`)이 모두 같습니다. 예: S11 `limitsStage` 기대 0, 실제 -1. 기존 실패이고 묶음 A 범위 밖입니다.
- 실제 `/api/ask` 호출은 p6 두 번으로 총 2회입니다. E2E 코치 테스트는 fetch 를 가짜로 바꿔서 0회입니다.

## 3. 돌연변이 표 (변이 14개 · 잡힘 10 / 안 잡힘 4)

각 변이 파일은 대상 줄이 정확히 1곳임을 assert 로 확인한 뒤 만들었습니다. 돌릴 때는 고친 판과 다른지 `cmp` 로 확인했고, trap 으로 되돌렸습니다. 끝난 뒤 `cmp src/app.js app.fixed.js` 가 같았고, 변이 흔적을 grep 하면 0건입니다.

| 조각 | 위치 | 변이 | 결과 |
|---|---|---|---|
| m1 I1 응답 시점에 요소 다시 찾기 | `askNoticeQuestion` 성공 경로 | 처음에 잡아 둔 옛 요소에 쓰기 | 잡힘 (G · H 가 「찾는 중」으로 돌아감) |
| m2 I1 변수에서 되살리기 | `renderBoardCoachKeepingState` | 화면 요소의 innerHTML 복사로 되돌림 | **안 잡힘** (p2 · p7 모두 통과) |
| m3 I2 `requestedInput` 기록 | `runAnalysis` 성공 | `getNoticeInput()` 로 되돌림 | 잡힘 (M-js `prepareDisabled:false`) |
| m4 I2 URL 입력 잠금 | `setAnalysisInputsBusy` | `notice-url.disabled = false` | 잡힘 (LOCK `urlDisabled:false` · M `filled`) |
| m5 I3 진입부 잠금 판정 | `askNoticeQuestion` 맨 앞 | 판정 줄 삭제 | 잡힘 (F `2`건 · 429 직후 Enter `1`건) |
| m6 I3 번호 비교(응답 직후) | `askNoticeQuestion` | `if (false) return` | 잡힘 (R2 · R3 에 옛 답 MOCK-ANSWER-2·3 표시) |
| m7 I3 번호 비교(finally) | `askNoticeQuestion` finally | `if (true)` | 잡힘 (R5 `btnDisabled:false` · `busy null`) |
| m8 429 잠금 시작 | `askNoticeQuestion` | `startAskCooldown()` 삭제 | 잡힘 (`"질문하기","d":false` · Enter `1`건) |
| m9 다시 그린 뒤 잠금 유지 | `renderBoardCoachKeepingState` | `applyCoachAskControls()` 삭제 | 잡힘 (다시 그린 뒤 `"질문하기","d":false`) |
| m10 오류 문구 이스케이프 | `askNoticeQuestion` | `escapeHtml` 제거 | 잡힘 (ESC `tag:true`) |
| m11 처음으로 돌아갈 때 비우기 | `restartWizardToProfile` | `clearCoachAnswer()` 삭제 | **안 잡힘** |
| m12 샘플 불러올 때 비우기 | 샘플 불러오기 핸들러 | `clearCoachAnswer()` 삭제 | **안 잡힘** |
| m13 분석 성공 때 비우기 | `runAnalysis` 성공 | `clearCoachAnswer()` 삭제 | 잡힘 (R4 에 옛 답 MOCK-ANSWER-4 가 남음) |
| m14 결과 영역 `aria-busy` | `applyCoachAskControls` | `if (false)` | 잡힘 (F `busy:null`) |

- m11 · m12 가 안 잡힌 이유 [추론]: R1~R3 는 모두 마지막에 다시 분석하므로, `runAnalysis` 성공 때의 비우기(m13)가 같은 일을 대신합니다. 두 경로만 따로 필요한지는 증명하지 못했습니다.
- m2 가 안 잡힌 이유 [추론]: m1 의 「응답 시점에 다시 찾기」만으로도 G · H 가 닫힙니다. 변수에서 되살리기가 따로 필요하다는 것은 재현으로 증명하지 못했습니다. 지시대로 코드는 남겼습니다.
- (표 머리의 「안 잡힘 4」는 표의 「안 잡힘」 3행(m2 · m11 · m12)과 다르다. 팀장 대조 결과 실제는 잡힘 11 / 안 잡힘 3 이다.)

## 4. 하지 못한 것 · 남은 위험

- **확인하지 못한 화면 크기와 모양**: 390px 모바일에서 「1분 뒤 다시」로 버튼 폭이 바뀌어 줄이 흔들리는지 보지 않았습니다. 잠긴 칩과 잠긴 URL 입력칸의 모양을 캡처로 확인하지 않았습니다. `styles.css:175` 에 `button:disabled` 규칙만 있습니다.
- **실제 429** 는 보지 못했습니다. 가짜 응답으로만 확인했습니다.
- **분석 중 「처음으로 돌아가시겠어요?」를 누르는 경로**는 실행하지 않았습니다. 그 버튼이 분석 중에 화면에 나오는지 미확인입니다. 이 경로의 잠금 해제는 코드로만 넣었습니다.
- **화면 읽기 프로그램**: 다시 그릴 때 결과 영역 innerHTML 을 다시 넣는 것이 다시 읽히는지 듣지 않았습니다. 고치기 전 코드도 같은 방식이었습니다.
- **8976 서버에서 하는 재판정 종료 조건**(state-matrix 10절)은 돌리지 않았습니다. 같은 p6 를 19310 에서 고친 판으로 돌린 결과는 위 표에 있습니다.
- **정리 상태**: 19310 서버는 종료했습니다(LISTEN 0). 19311 은 Playwright 가 직접 띄우고 닫았습니다(LISTEN 0). `git status --short` 에 새 `??` 는 없습니다.
- **후속 제안**: p7 의 R4 · R5 와 p2 의 F · 429 장면을 `screen.spec.js` 에 고정하는 것이 좋겠습니다(이번 범위에서 `tests/` 는 수정 금지였습니다). 리뷰 전에 이 diff 를 WIP 커밋으로 고정해 주십시오.

작업 시간은 19:50부터 20:15까지 약 25분입니다.
