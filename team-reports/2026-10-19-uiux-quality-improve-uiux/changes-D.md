# 묶음 D 구현 반환물 (frontend-implementer · 고정 영역 · 작은 화면 · 포커스 8항목)

> 팀장 전사: frontend-implementer 가 채팅으로만 반환해 팀장이 이 파일로 옮겼다(2026-10-19 · 반환 직후). 본문은 반환물 그대로이고, 하위 불릿 일부만 한 줄로 합쳤다.
> 팀장 대조: 반환물의 diff 지문 `app.js 0f5270d5` · `styles.css f502351f` 와 numstat(67/6 · 2/2 · 147/0)은 팀장이 다시 잰 값과 같다.
> 역할의 측정 스크립트·변이·로그·캡처는 `/private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/e6ad4d9c-5c84-4401-baa3-6e11a43878f2/scratchpad/role-impl/` 에 있다(레포 밖).

8항목을 모두 반영했고, 커밋하지 않았습니다.
- responsive-audit 5절 종료 조건을 통과합니다. 답이 열린 390×844 에서 고정 영역이 61% → **48%** 입니다.
- 포커스 가림(I6)은 0건이고, 단계 이동 뒤 포커스는 `report-title` 로 갑니다.
- E2E 는 기준선과 같은 8 failed · 29 passed 이고, 새로 깨진 테스트는 없습니다.
- 다른 세션이 맡은 서류 구획 함수(renderDocChecklist · renderDocFlatSection · isUnclassifiedDoc · 첨부 안내)는 건드리지 않았습니다. diff 에서 그 이름으로 grep 하면 0건입니다.

## 1. 바꾼 것

| 항목 | 위치 | 이유 |
|---|---|---|
| 1 R1·V9 | css `.board-dock` (flex 세로 · max-height 60vh, 좁거나 낮은 화면 48vh · overflow-y auto) · `.board-coach` 를 스크롤 칸으로 · 답 칸의 32vh 해제 · `has-answer` 일 때 칩 줄 숨김 · app.js `setCoachAnswer` 가 `has-answer` 와 「답 지우기」를 함께 맞춤 · `[data-coach-clear]` | 상한을 답 칸이 아니라 고정 영역 전체에 둡니다. 스크롤은 코치 쪽 한 곳에서만 생기고 단계 표시는 늘 보입니다. 「답 지우기」를 누르면 `clearCoachAnswer()` 를 부르고 포커스를 질문 입력칸으로 옮깁니다. |
| 2 R2·V9 | `getInitialCoachCollapsed` · `COACH_CONTEXT_DETAIL` · 참고 항목 줄 삭제 · 그 문장을 `.coach-context` title 과 sr-only `#coach-context-help`(입력칸 aria-describedby)로 이동 · ≤600px 단계 표시와 진행률 한 줄 | 저장값이 없으면 `(max-width:600px), (max-height:500px)` 에서 접힌 상태로 시작합니다. 한 줄로 두려고 ≤600px 에서는 진행률 라벨과 막대를 숨기고 「0/5 완료」만 보입니다. |
| 3 I6 | `updateDockHeightVar` · ResizeObserver · `setView` 끝에서 호출 · css `html { scroll-padding-bottom: var(--dock-h, 0px) }` | Tab 으로 옮긴 포커스가 고정 영역 뒤로 들어가지 않게 합니다. |
| 4 R5 | ≤600px 칩 flex-wrap · 3번째부터 숨김 · 데스크톱 mask-image 페이드 | 좁은 화면에서는 줄바꿈해 두 개만 보이고, 데스크톱은 한 줄 끝을 흐리게 합니다. |
| 5 R8·I11 | ≤600px `.mini-step` · `.seg-option` · `.small-button` · `.coach-toggle` · 칩 · `.task-check` min-height 40px · summary padding 6px 0 / min-height 32px · `.coach-ask-result` overflow-wrap anywhere | 단계 버튼은 옛 규칙 `.wizard-progress .mini-step` 이 더 구체적이라 같은 세기로 다시 적었습니다. |
| 6 R6 | ≤600px `.code-revision:not(:has(.code-revision-warn))` 숨김 · 머리 여백과 「실증 MVP」 카드 축소 | 코드 판 줄은 재시작 · 미커밋 경고가 있을 때만 보입니다. |
| 7 I7 | 단계 이동 핸들러 `focusReportTitle()` · 간단히/자세히는 같은 `data-guide-level` 로 복귀 · 분석 성공은 1-3 h2 · 실패는 `#notice-url` 에 `aria-invalid="true"` · 입력하면 해제 | 위 · 아래 · 페이지 이동 · 완료 행 버튼이 모두 같은 핸들러를 탑니다. |
| 8 | (변경 없음) | 390px 점검 결과 넘침 · 겹침이 없었습니다(아래 표). |

- 지시와 형태가 다른 점이 셋 있습니다. ⑴ 「+16px」를 `--dock-h` 값 안에 넣었습니다(보드에서는 높이+16, 그 밖에서는 `0px`). 지시하신 `calc(var(--dock-h) + 16px)` 꼴이면 다른 화면에서 scroll-padding 이 16px 로 남아 「0 이어야 한다」와 어긋납니다. ⑵ 종료 조건(50% 이하)을 맞추려고 좁거나 낮은 화면의 상한을 60vh 가 아니라 48vh 로 두었습니다. ⑶ 빈 URL 로 「분석하기」를 누른 경우에도 URL 칸 포커스와 `aria-invalid` 를 붙였습니다. state-matrix 5절 「빈 URL 에 aria-invalid 가 없고 포커스가 버튼에 남는다」를 같이 닫으려는 것입니다.
- 데스크톱 칩 페이드는 넘칠 때만이 아니라 늘 걸립니다. CSS 만으로는 넘침을 알 수 없습니다.
- 캐시 번호는 index.html 두 곳을 `uiux-r6` 로 올렸습니다.

`git diff --numstat`(827f983 기준): `67 6 src/app.js` · `2 2 src/index.html` · `147 0 src/styles.css`
- `git diff src/app.js | shasum` 앞 8자는 `0f5270d5`, `git diff src/styles.css | shasum` 앞 8자는 `f502351f` 입니다(21:31:27).
- `git status --short` 는 ` M` 세 파일과 `?? node_modules` 뿐이고, 새 `??` 는 0개입니다.

## 2. 검증 표

측정은 실서버 19317 의 sample 로 했습니다. 질문 답은 가짜 긴 답이라 실제 `/api/ask` 는 0회입니다.

| 검사 | 고치기 전 (827f983) | 고친 뒤 | 시각 |
|---|---|---|---|
| `node --check` | (해당 없음) | exit 0 | 21:31:10 |
| `test_docs_extraction.py` | (미실행) | `462/462 통과 · 연기 7개 · 축 43개 중 단정이 한 번도 안 돈 축 0개` | 21:31:27 |
| `test_screen_strings.py` (금지표현) | (미실행) | `20/20 통과 · 연기 1개 · 축 5개 중 미실행 0개` | 21:31:27 |
| E2E 전체 (19318) | 8 failed · 29 passed (팀장 21:13) | `8 failed · 29 passed (2.4m)` · 실패 이름 8개와 오류 줄 6줄이 묶음 B 실행과 같음 | 21:22:31~21:24:57 |
| **390×844 2-3 답 열림 고정 영역** (맨 위 · 가운데 · 맨 아래) | **61 · 61 · 61%** (519px) · 맨 위에서 단계 표시 안 보임 | **48 · 48 · 48%** (405px) · 단계 표시 셋 다 보임 | 21:20:41 / 21:22:20 |
| 360×740 | 66% (485px) · 맨 위 단계 표시 안 보임 | 48% (355px) · 셋 다 보임 | 같음 |
| 844×390 | 93% (362px) · 맨 위 단계 표시 안 보임 | 48% (187px) · **맨 위만 여전히 안 보임** (가운데 · 맨 아래는 보임) | 같음 |
| 1440×900 | 40% (364px) | 40% (364px) (답이 상한에 닿지 않아 같음) | 같음 |
| 답 칸 이중 스크롤 · 가로 넘침 (390) | sh 428 > ch 270 · sw 451 > cw 340 | sh 446 = ch 446 · sw 340 = cw 340 | 같음 |
| 답 열림 390 | `has-answer` 없음 · 칩 줄 보임 · 참고 항목 줄 있음 | `has-answer` · 칩 줄 숨김 · 「답 지우기」 보임 · 참고 항목 줄 없음 | 같음 |
| 답 지우기 | (버튼 없음) | 결과 0자 · `has-answer` 해제 · 포커스 `coach-question-input` | 같음 |
| `--dock-h` | 미설정 | 보드 126px(접힘)과 422px(답 열림 · 고정 영역 405+16) · 공고 가져오기와 관심 공고에서는 `0px` (scroll-padding-bottom 0px) | 같음 |
| **I6 2-1 에서 Tab 45번 · 완전히 가려진 포커스** | 1280 **6건** · 390 **10건** (+ 일부 가림 2) | 1280 **0** · 390 **0** (일부 가림 0) | 같음 |
| **포커스** (위 단계 · 아래 단계 · 페이지 이동 · 간단히/자세히) | 넷 다 `BODY` (1280 · 390) | `report-title` ×3 · `detail` (1280 · 390) | 같음 |
| 분석 성공 · 실패 · 빈 URL | `BODY` · `BODY` (aria-invalid 없음) · `analyze` | 1-3 `H2` · `notice-url` + `aria-invalid=true` (입력하면 해제) · `notice-url` + `true` | 같음 |
| **기본 접힘** (390 저장값 없음 · 390 저장값 「펼침」 · 1280 저장값 없음 · 844×390 저장값 없음) | 펼침 · 펼침 · 펼침 · 펼침 | **접힘 · 펼침 · 펼침 · 접힘** | 같음 |
| 단계 표시와 진행률 (390) | 두 줄 · 64px | 한 줄 · 40px | 같음 |
| 칩 (390) | 4개 · 가로로 숨은 폭 474px | 2개 · 0 | 같음 |
| 머리 높이 390 (경고 없음 · 경고 있음 · 가짜 `/api/version`) | 180 · 198px | 104px(코드 판 숨김) · 144px(경고가 있어 보임) · 1280 은 107px 그대로 | 21:20:04 |
| 터치 대상 최소 높이 390 (단계 · 두 칸 · 작은 버튼 · 접기 · 칩 · 체크 · 자세히) | 32 · 32 · 34 · 28 · 28 · 25 · 18 | 40 · 40 · 40 · 40 · 40 · 40 · 32 | 21:22:20 |
| 8 390 묶음 B 요소 (빈 보드 · 완료 행 · 첨부 버튼 · 2-4 이동 줄) | right 359 · 359 · 327 · 359 / 겹침 0 / 넘침 0 | 같음 (문제 없음 · 수정 안 함) | 같음 |
| 페이지 오류 | 0 | 0 | 같음 |

- I6 기준선이 진단 원문(1280 16건 · 390 18건)과 다릅니다. 측정 판(1340f55 → 827f983)에서 2-1 구성이 바뀌었고, 판정 방식도 제가 쓴 「요소 상자 전체가 고정 영역 안」입니다. 제 기준선 6 / 10 은 같은 스크립트로 잰 값입니다.
- 전후 캡처는 뷰포트 기준이고 판마다 9장씩입니다. 폴더 `role-impl/shots-D/` · 이름 `{before|after}-{390-2-1 | 390-2-3-answer | 390-2-3-collapsed | 1280-2-1 | 1280-2-1-collapsed | 1440-2-3-answer | 390-empty-board | 390-done-row | 390-2-4-nav}.png`

## 3. 돌연변이 표 (7행 · 잡힘 7 / 안 잡힘 0)

| 조각 | 위치 | 변이 | 결과 |
|---|---|---|---|
| 2 기본 접힘 조건 | `getInitialCoachCollapsed` 마지막 줄 | `return false` | 잡힘 (390 · 844×390 저장값 없음이 펼침) |
| 1 has-answer 조건 | `setCoachAnswer` | `toggle("has-answer", false)` | 잡힘 (답 열림인데 칩 줄이 보임) |
| 3 --dock-h 갱신 | init 의 ResizeObserver | 등록 줄 삭제 | 잡힘 (답 열림 뒤에도 `126px`, 실제 405) |
| 7 단계 이동 포커스 | 단계 이동 핸들러 | `focusReportTitle()` 삭제 | 잡힘 (위 · 아래 · 페이지 이동 모두 `BODY`) |
| 7 간단히/자세히 포커스 | 안내 수준 핸들러 | `.focus()` 삭제 | 잡힘 (`BODY`) |
| 7 분석 실패 포커스 | `runAnalysis` finally | `focusNoticeUrlAsInvalid()` 삭제 | 잡힘 (`BODY` · aria-invalid 없음) |
| 7 분석 성공 포커스 | `runAnalysis` try | `resultTitle.focus` 삭제 | 잡힘 (`BODY`) |

- 변이는 매번 trap 으로 복원했고, 복원 뒤 세 파일을 `cmp` 로 확인했습니다.
- 변이 흔적 grep(`return false;`)의 4건은 827f983 에도 있는 기존 줄입니다(같은 grep 이 827f983 판에서도 4건).

## 4. 하지 못한 것 · 남은 위험

- **844×390 페이지 맨 위**: 답이 열린 상태에서 단계 표시가 여전히 화면 밖입니다. 이 화면 크기는 이제 기본 접힘으로 시작해서 펼치고 답을 연 경우에만 납니다. [추론] sticky 요소가 자기 컨테이너 위쪽보다 더 올라가지 못하는 제약입니다. 머리 · 탭 · 고지가 먼저 자리를 차지해, 고정 영역이 자연 위치에서 다 올라오지 못합니다.
- **R8 의 발급처 링크 패딩**(`.doc-howto a`)은 이번 지시 목록에 없어서 넣지 않았습니다. 서류 구획은 다른 세션 범위입니다.
- **R1 의 320 · 768 · 1024**: 이번에는 재지 않았습니다(지시받은 크기만 측정).
- **화면 읽기 프로그램**: 포커스 이동 뒤 실제로 어떻게 읽히는지 듣지 않았습니다. 속성과 `activeElement` 만 확인했습니다.
- **실제 모델 답**: 고정 영역 측정은 가짜 긴 답(약 600자 + 긴 URL)으로 했습니다.
- **포트 상태**: 8976 은 건드리지 않았습니다(21:31 기준 PID 26234). 19317 · 19318 은 종료했습니다(LISTEN 0).

## 5. 서버 문자열이라 못 고친 문구

없습니다.

## 6. 깨진 테스트

없습니다. E2E 실패 8건은 묶음 B 실행과 이름 집합이 같습니다. 줄 번호만 2줄 밀렸는데, 팀장이 묶음 C 뒤에 테스트를 고쳤기 때문입니다. 오류 줄도 같습니다.

작업 시간은 21:14부터 21:31까지 약 17분입니다.
