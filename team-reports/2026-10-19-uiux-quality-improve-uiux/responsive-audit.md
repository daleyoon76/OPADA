# responsive-tester 반환물 (3팀 · 모바일 · 태블릿 · 데스크톱 · 긴 텍스트 · 작은 화면)

> 팀장 전사: responsive-tester 는 읽기 전용 역할이라 채팅 반환물을 팀장이 이 파일로 옮겼다(2026-10-19 · 반환 직후). 본문은 반환물 그대로이고, 색으로 말한 표현 세 곳(「빨간 줄」·「빨간 경고」)만 「경고 줄」로 고쳤다. 1절의 하위 불릿 몇 개는 한 줄로 합쳤다.
> 역할이 만든 캡처 328장과 측정 스크립트는 `/private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/e6ad4d9c-5c84-4401-baa3-6e11a43878f2/scratchpad/role-responsive/r2/` 에 있다(레포 밖 · 지워질 수 있다).
> 팀장 주: 1절의 `M tests/screen.spec.js` 는 팀장이 19:39 에 E2E 5건을 고친 것이다(src 는 바꾸지 않았다). 4절의 8976 서버는 팀장이 18:36 에 다시 띄운 것이고, 그때 디스크의 `src/server.py` 는 그 뒤 커밋한 `ee2ca95` 판과 같다(그 뒤로는 app.js · index.html · styles.css 만 바꿨다).

결론을 먼저 말씀드립니다.
- 가로 넘침은 360px 이상에서 0입니다. 긴 공고명과 서류명도 블록을 넘지 않습니다.
- 페이지 맨 아래에서는 「이전/다음 단계」 버튼이 가려지지 않습니다.
- 가장 큰 문제는 AI 코치 답이 열렸을 때입니다. 작은 화면의 61~76%(가로 모드는 93%)를 고정 영역이 덮습니다.
- 320px에서는 숨김 글자(sr-only) 하나 때문에 가로 넘침 26px이 납니다(SC 1.4.10 Reflow 실패). 고치는 방법은 CSS 한 줄이고, 효과를 주입 시험으로 확인했습니다.

## 1. 머리

- 판정 대상 커밋은 `ee2ca95`입니다(`git -C <워크트리> rev-parse --short HEAD`, 19:40:28 출력).
- 작업 트리 상태
  - 시작 때 없던 `M tests/screen.spec.js`(+10줄, mtime 19:39:02)가 생겼습니다. 다른 세션이 고친 것이고, 저는 워크트리에 아무것도 쓰지 않았습니다.
  - `src/`는 바뀌지 않았으므로 측정 대상은 `ee2ca95`판 그대로입니다.
- 서버는 8976을 썼습니다. 이 서버는 18:36:05에 기동됐고, 화면 머리에 경고 줄 「서버 기동 뒤 코드가 ee2ca95 로 바뀌었습니다」가 계속 보입니다(아래 4절 참고).
- 직접 찍은 화면은 모두 역할 scratch에 있습니다.
  - `role-responsive/r2/shots/`: 230장입니다. 이름은 `{폭}-{sample|seized}-{1-1~1-3|2-1~2-4|2-3-answer|2-3-collapsed|watchlist}-{vp|full}.png` 입니다. 폭은 360·390·768·1024·1440, 높이는 각각 740·844·1024·768·900입니다.
  - `role-responsive/r2/shotsx/`: 98장입니다. 이름은 `x-{W}x{H}-{2-n|ans|col}-{top|mid|bottom}.png` 이고, 320×568과 가로 모드 844×390을 더했습니다.
- packet 스크린샷 중 m-sample-2-1, m-seized-2-2를 대조용으로 봤습니다.
- 실행한 명령과 시각
  - 19:36:30~19:38:17 · `node role-responsive/resp.cjs <워크트리> r2/shots sample,seized` (넘침 · 화면 밖 요소 · 터치 대상 · 고정 영역 높이 측정. 로그 `r2/run1.log`, 수치 `r2/results-sample_seized.json`)
  - 19:38:33~19:38:46 · `node resp2.cjs` (2-1~2-4 · 답 열림 · 접힘 상태에서 가운데와 맨 아래로 스크롤해 고정 영역과 이전/다음 버튼 위치 측정. 7개 크기. 로그 `r2/run2.log`)
  - 19:39:02 · `node resp3.cjs` (320px 넘침. `r2/run3.log`)
  - 19:39:18 · `node resp5.cjs` (`.mini-step{position:relative}`를 주입해 넘침이 사라지는지 확인. `r2/run5.log`)
  - 19:39:47 · `node r2/notice.cjs` (「고지」 라벨 줄바꿈과 머리 높이)
  - 재현성: 중단된 앞 실행(18:52~18:56)의 로그와 시각을 뺀 나머지를 diff했습니다. run2는 변경 0줄이고, run1은 1줄만 달랐습니다(측정 무효인 bottom 칸 · 아래 4절).
  - `/api/ask`는 이번 실행에서 2회 불렀습니다. 중단된 앞 실행의 2회를 더해 역할 합계는 4회입니다.
  - 콘솔 오류는 sample과 seized 모두 0건입니다.

## 2. 결함 표

| 번호 | 등급 | 화면·위치 | 관측 | 사용자에게 미치는 영향 | 고치는 방법(구체적) | 근거 등급 |
|---|---|---|---|---|---|---|
| R1 | P1 | 답이 열린 AI 코치(`styles.css:2256-2260` `.coach-dock .coach-ask-result:not(:empty){max-height:32vh}`) · `x-390x844-ans-mid.png` · `x-844x390-ans-bottom.png` · `1440-sample-2-3-answer-vp.png`. V9의 연장이고, 모바일 수치는 새로 잰 것입니다 | 고정 영역 높이(뷰포트 대비)는 다음과 같습니다. 320×568: 430px(76%) · 360×740: 485px(66%) · 390×844: 519px(61%) · 768: 513px(50%) · 1024×768: 441px(57%) · 1440×900: 441px(49%) · 가로 844×390: 362px(93%). 32vh 제한은 답 칸에만 걸리고, 나머지 고정 줄 약 240px이 그 위에 더해집니다. 가로 모드에서는 본문이 14~28px 띠만 보입니다. 이전/다음 버튼은 어느 스크롤 위치에서도 가려지거나 화면 밖에 있습니다(맨 아래 top=-59). 페이지 맨 위에서는 고정 영역 아래쪽이 화면 밖으로 나갑니다(360: dock bottom 887 > 740). 그래서 단계 표시와 진행률이 안 보입니다(stepVis=false) | 모바일에서 답을 읽는 동안 보드 본문을 볼 수 없습니다. 가로 모드에서는 「접기」를 누르기 전까지 다음 단계로 갈 수 없습니다 | ⑴ 답 칸 제한을 고정 영역 전체 기준으로 바꿉니다. `.board-dock{max-height:60vh; overflow-y:auto}`를 두고 답 칸은 `max-height:none`으로 둡니다. ⑵ `@media (max-width:600px)`와 `@media (max-height:500px)`에서 답이 있을 때 `.coach-context-detail`과 `.coach-suggest`를 숨깁니다(`.coach-dock.has-answer` 같은 상태 클래스). ⑶ `@media (max-height:500px)`에서는 고정 영역을 접힌 상태로 시작합니다 | [관측] run2.log answer 행 |
| R2 | P1 | 펼친 기본 고정 영역 · `x-320x568-2-1-mid.png` · `360-seized-2-1-vp.png`. 390 수치는 V4·V9와 같고, 아래는 새로 잰 크기만 적습니다 | 320: 241px(42%) · 360: 241px(33%) · 768: 230px(22%) · 1024×768: 198px(26%) · 가로 844×390: 230px(59%). 접으면 122px(360에서 16%) · 126px(가로에서 32%)로 줄어듭니다. 360×740 첫 화면에서 보드 본문이 보이는 띠는 y≈420~500, 약 80px뿐입니다(「STEP 2-1 공고 확인」 제목만 보임) | 모바일과 가로 모드에서 본문 대부분이 늘 가려집니다 | ⑴ `@media (max-width:600px), (max-height:500px)`에서 코치를 접힌 상태로 시작합니다. 펼침은 사용자가 고르게 합니다. ⑵ 펼침 상태에서도 ≤600px이면 `.coach-suggest` 줄을 숨기고, `.board-status`(진행률)를 단계 표시 줄 오른쪽에 붙여 한 줄로 만듭니다. 지금은 `styles.css:2530` column 규칙 때문에 두 줄입니다 | [관측] run2.log · run1.log dock 칸 |
| R3 | P1 | 320px · 340px 준비 보드 2-1~2-4 전부(`app.js:2513` · `2532`의 `.sr-only`가 `.mini-step` 안에 있음 · `styles.css:2129-2139` · `2167-2181`) | 문서 가로 넘침이 320에서 26px, 340에서 6px입니다. 360 이상은 0입니다. 1-x와 관심 공고는 320에서도 0입니다. 원인은 `position:absolute`인 sr-only의 기준 상자가 `.mini-step`이 아니라는 점입니다. 그래서 `overflow-x:auto` 단계 표시의 잘림을 벗어나 right=346에 놓입니다. `.mini-step{position:relative}`를 주입하면 320과 340 모두 0이 됩니다 | WCAG 2.1 SC 1.4.10 Reflow(AA) 실패입니다. 320px은 1280px 화면을 400% 확대한 것과 같습니다. 보드 전체가 옆으로 흔들립니다 | `.mini-step { position: relative; }` 한 줄을 넣습니다(`styles.css:2167` 블록) | [관측] run5.log (`base 26 → fixed 0`) |
| R4 | P2 | 고정 영역 단계 표시(360) · `360-seized-2-2-full.png`. 위쪽 단계 버튼 잘림은 V12와 같습니다 | 600px 이하에서 이미 지금 단계만 이름을 보이는데도 360에서 16~29px이 잘립니다. 2-4 알약이 오른쪽 끝에서 반쯤 끊깁니다. 위쪽 단계 버튼은 360에서 98px, 390에서 68px이 숨습니다(V12) | 「2-4가 없다」로 보입니다 | `@media (max-width:400px){ .board-dock .mini-step{padding:4px 8px} .board-dock .mini-stepper{gap:4px} }`를 넣습니다. 또는 400px 이하에서는 지금 단계의 이름도 숨깁니다 | [관측] results JSON scrollers |
| R5 | P2 | 「자주 묻는 질문」 칩 줄(`styles.css:2824-2831` `.coach-suggest{overflow-x:auto}`) | 2-3에서 숨은 폭은 360: 504/814px(62%) · 390: 474px · 768: 108px입니다. 첫 칩 하나와 낱말 중간에서 끊긴 다음 칩(「제출한…」)만 보이고, 넘길 수 있다는 단서가 없습니다. 칩 높이는 28px입니다 | 준비된 질문 대부분이 모바일에서 보이지 않습니다 | ≤600px에서 `flex-wrap:wrap`으로 바꾸고 칩을 2개까지만 보입니다. 가로 스크롤을 유지한다면 오른쪽 끝에 `mask-image: linear-gradient(to right, #000 85%, transparent)` 페이드를 넣습니다 | [관측] results JSON scrollers |
| R6 | P2 | 앱 머리와 고지 띠(≤600px) · `360-sample-2-1-vp.png`. V4의 원인 중 하나로 덧붙입니다 | 360·390에서 `.app-header`는 216px입니다(1440은 107px). 고지 띠 아래 끝은 y=367로, 360×740 높이의 50%입니다. 머리에는 코드 판과 경고 줄이 두 줄로 있습니다 | 보드에서 첫 화면 본문이 약 80px만 남습니다(R2와 겹침) | ≤600px에서 코드 판 줄(`app.js:3255` 근처 출력)을 숨기거나 `<details>`로 접습니다. 「실증 MVP」 카드는 제목 옆 머리표 한 줄로 줄입니다 | [관측] notice.cjs 출력 |
| R7 | P2 | 「고지」 라벨 · V10과 같습니다 | 360·390에 더해 768에서도 「고/지」 두 줄입니다(strong 폭 12~20px, 높이 42px). 1024 이상은 한 줄입니다 | 태블릿에서도 깨져 보입니다 | V10의 수정 그대로입니다(`flex:none; white-space:nowrap`). 768에서도 고쳐졌는지 확인합니다 | [관측] notice.cjs 출력 |
| R8 | P2 | 터치 대상 · results JSON의 `lt24` · `lt44` | **24px 미만**은 다음과 같습니다. 서류 체크리스트 「원문 근거」 summary 17px(seized 2-2 10개 · 2-4 8개) · 「서류 준비 체크리스트」 · 「자세히」 summary 18px(2-x 전부) · 발급처 링크 14px(seized 2-4 7개 · 「정부24」는 32×14) · `a.text-action` 15px. **44px 미만**은 보드 대상의 100%입니다(2-1 35/35 · seized 2-2 64/64). 1-x는 7/9~11/11입니다. 구성은 주 버튼 40px · 단계 알약 32px · 칩 28px · 할 일 체크 label 25px입니다 | 모바일에서 서류 행 접기와 발급처 링크를 누르기 어렵습니다. summary는 위아래 간격으로 SC 2.5.8 Spacing 예외에 들 수 있습니다[추론]. 링크는 「근거 … · 링크」 문장 속이라 Inline 예외에 들 수 있습니다[추론]. 44px(SC 2.5.5 · AAA)는 전부 미달입니다 | `.doc-group summary, .task-detail > summary { padding:6px 0; min-height:32px; }` · ≤600px에서 `.mini-step, .seg-option, .small-button { min-height:40px }` · `.task-check { min-height:40px }` · `.doc-howto a { display:inline-block; padding:5px 0 }` | [관측] 측정 · [추론] 예외 판정 |
| R9 | P2 | 긴 한국어 제목과 값의 줄바꿈 · `360-seized-1-3-full.png` · `x-320x568-2-1-mid.png` | 넘침은 0입니다(contentOverflow 0 · 화면 밖 0 · 모든 크기). 다만 낱말 중간에서 끊깁니다. 360 seized 1-3 「선 / 샤인빌」 · 「마 / 감」, 320 sample 2-1 「696- / 1연구B동」입니다 | 주소와 지번이 끊겨 읽기 어렵습니다 | `.report-hero h3, .fact-value, .info-row strong { word-break: keep-all; overflow-wrap: anywhere; }`(긴 영문이나 번호 대비로 anywhere를 함께 둡니다) | [관측] 캡처 |

## 3. 잘 된 것 (바꾸지 말 것)

- 페이지 맨 아래로 스크롤하면 고정 영역이 버튼 아래에 놓입니다. 그래서 7개 크기 × 펼침 · 접힘 모두에서 이전/다음 버튼이 가려지지 않습니다(`coveredAtCenter:false`). 예외는 R1의 답 열림 가로 모드 하나입니다.
- 360px 이상에서는 1-1~1-3 · 2-1~2-4 · 관심 공고 모두 문서 가로 넘침 0, 블록 밖 글자 0입니다. 압류재산의 긴 주소와 긴 발급처도 마찬가지입니다.
- 「접기」 하나로 고정 영역이 122~126px까지 줄어 빠져나갈 길이 있습니다.

## 4. 확인하지 못한 것

- 실기기 iOS Safari와 Android Chrome은 보지 못했습니다. 주소창이 줄고 늘 때 `vh`와 sticky가 어떻게 움직이는지 미확인입니다. Chromium 에뮬레이션(hasTouch 없음)만 썼습니다.
- 키보드 포커스가 고정 영역 뒤로 숨는지(SC 2.4.11 Focus Not Obscured)는 재지 않았습니다. R1과 R2 높이를 보면 위험이 높다고 추정합니다[추론].
- 브라우저 확대 200%·400%, 다크 모드와 고대비, VoiceOver의 sr-only 낭독은 보지 않았습니다.
- demo1 공고는 측정하지 않았습니다(packet 지시대로 sample과 seized만).
- `resp.cjs`의 「맨 아래」 판정은 무효이고, 버튼 가림 판정은 `resp2.cjs` 값만 썼습니다.
  - 이유: `styles.css:31`의 `scroll-behavior: smooth` 때문에 `scrollTo`가 즉시 움직이지 않았습니다.
  - 그래서 `r2/shots/*-bottom-vp.png`는 맨 아래 화면이 아닙니다.
- 8976 서버는 18:36:05에 6cd8487 + 미커밋 변경으로 기동됐습니다.
  - `git diff 6cd8487 ee2ca95 -- src/server.py`는 238줄입니다.
  - 고정 안내 답(「온비드 규칙 기반 안내」)이 나오는 것으로 보아 그 미커밋 변경에 포함됐다고 추정하지만, 메모리의 server.py가 ee2ca95와 같은지는 미확인입니다[추론].
  - 시연 전에 서버를 다시 시작하지 않으면 머리의 경고 줄이 모든 화면에 보입니다[관측].
- 범위 밖이라 판정하지 않은 것이 하나 있습니다. seized(영등포 공동주택) 2-2 「제출서류 확인」 값이 「농지취득자격증명 / 농지대장」으로 나옵니다. 파싱이 맞는지는 다른 역할에서 확인해야 합니다.

## 5. 재판정 종료 조건

- 같은 `resp5.cjs` 방식으로 8976(또는 새 판 서버)에서 sample 2-1~2-4를 320×568로 엽니다.
- `document.documentElement.scrollWidth - innerWidth`가 **0**이면 닫습니다.
- 같은 측정에서 390×844 2-3 답 열림 상태의 `.board-dock` 높이가 **뷰포트의 50% 이하**여야 합니다.
- 기준선 `ee2ca95`에서 돌리면 26과 61%가 나와 실패합니다(19:39 실측).

임시 파일은 역할 scratch에만 만들었습니다. 워크트리에서 제가 만든 `??`는 0개입니다.
