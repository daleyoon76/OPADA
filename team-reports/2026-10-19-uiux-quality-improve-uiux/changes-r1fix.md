# 재판정 r1 반영 구현 반환물 (frontend-implementer · P1-1 · P2-1 · P2-3)

> 팀장 전사: frontend-implementer 가 채팅으로만 반환해 팀장이 이 파일로 옮겼다(2026-10-19 · 반환 직후). 본문은 반환물 그대로이고, 하위 불릿 일부만 한 줄로 합쳤다.
> 팀장 대조: 반환물의 diff 지문 `app.js a50a9ac6` · `styles.css 5e393a41` 와 numstat(19/8 · 2/2 · 33/0)은 팀장이 다시 잰 값과 같다. 1절의 `??` 두 파일(verification-r1.md · mutation-coverage.md)은 팀장이 쓴 것이다.
> 역할의 측정 스크립트·변이·로그·캡처는 `/private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/e6ad4d9c-5c84-4401-baa3-6e11a43878f2/scratchpad/role-impl/` 에 있다(레포 밖).

세 건 모두 고쳤고, 커밋하지 않았습니다.
- 재판정 6절 종료 조건을 통과합니다. 390 접힘 · 펼침 모두 고정 영역 안에 「이 물건」 힌트가 보이고, 답이 열린 390×844 는 48% 입니다.
- E2E 는 37 passed 이고 깨진 테스트는 없습니다.
- 서류 구획 함수(renderDocChecklist 등 5개)는 diff 에서 0건으로, 건드리지 않았습니다.

## 1. 바꾼 것

| 항목 | 위치 | 이유 |
|---|---|---|
| P1-1 | `renderBoardCoach` 의 `.coach-context` 를 두 span 으로 나눔 · styles.css 끝 규칙 | 긴 쪽은 「「제목」 정보를 알고 답합니다」, 짧은 쪽은 「이 물건 정보를 알고 답합니다」입니다. ≤600px 에서는 짧은 쪽만 머리 줄 아래 한 줄(말줄임)로 보입니다. 접힘 · 펼침 모두 보이고 title 속성에 기대지 않습니다. 옛 규칙 `.coach-context { display:none }` 은 `.coach-dock-head .coach-context` 로 이겼습니다. |
| P2-1 | `getBidQualificationTask` 에 `valueLabel` · `needsCheck` 를 더하고 `action` 을 실제 내용으로 · `renderTaskItem` 이 두 칸을 읽음 | 값은 「자격 제한: 사업자만 입찰 가능 외 1건」(첫 항목 40자 + 외 N건)입니다. 라벨은 「공공데이터에서 확인된 값」이고, 칸이 없는 다른 할 일은 기존 라벨 그대로입니다. 「확인 필요」는 `aiMatch || task.needsCheck` 일 때 붙고, 미완료면 늘 붙습니다. |
| P2-3 | `getFitMessage` 입력 분기의 `notTriedYet` · `renderUrlStepFeedback` · css `.fit-panel.is-neutral` · `runAnalysis` 빈 칸 경로 | 판정은 칸이 비었고 `#notice-url` 에 `aria-invalid="true"` 가 없을 때 「안내」(neutral · 띠 없음 · 흰 바탕)입니다. 빈 칸으로 「분석하기」를 누르면 「입력 필요」(warn)로 바뀝니다. 그러려고 빈 칸 경로에서 `aria-invalid` 를 다시 그리기 **전에** 붙이도록 순서를 바꿨습니다. |
| 캐시 | `index.html` | `uiux-r7` |

`git diff --numstat`(05bf12b 기준): `19 8 src/app.js` · `2 2 src/index.html` · `33 0 src/styles.css`
- `git diff src/app.js | shasum` 앞 8자는 `a50a9ac6`, `git diff src/styles.css | shasum` 앞 8자는 `5e393a41` 입니다(21:56:04).

## 2. 검증 표

측정은 실서버 19325 의 sample 로 했습니다. 실제 `/api/ask` 는 0회입니다.

| 검사 | 고치기 전 (05bf12b) | 고친 뒤 | 시각 |
|---|---|---|---|
| `node --check` | (해당 없음) | exit 0 | 21:55:48 |
| `test_docs_extraction.py` | (미실행) | `462/462 통과 · 연기 7개 · 축 43개 중 단정이 한 번도 안 돈 축 0개` | 21:56:04 |
| `test_screen_strings.py` (금지표현) | (미실행) | `20/20 통과 · 연기 1개 · 축 5개 중 미실행 0개` | 21:56:04 |
| E2E 전체 (19324) | 37 passed (팀장 21:41) | `37 passed (1.1m)` · 실행 상태 passed | 21:51:31~21:52:38 |
| **r1 6절: 390 2-1 접힘** · 고정 영역 안 힌트 | **[] (0개)** | `["이 물건 정보를 알고 답합니다 (w134)"]` | 21:49:23 / 21:50:21 |
| **r1 6절: 390 2-1 펼침** | **[] (0개)** | 같은 힌트 1개 | 같음 |
| 1280 접힘 · 펼침 | 제목 힌트 1개 | 제목 힌트 1개 (데스크톱은 그대로) | 같음 |
| **r1 6절: d.cjs 「R answer 390x844」** | (묶음 D 61→48%) | 맨 위 · 가운데 · 맨 아래 **48 · 48 · 48%** (405px) | 21:50:33 |
| 같은 실행의 다른 크기 | | 360×740 48% · 844×390 48% · 1440×900 40% · 390 접힘 136px(16%, 힌트 한 줄만큼 110px 에서 늘어남) · I6 가림 0 · 0 · 기본 접힘 4건 모두 기대대로 | 같음 |
| P2-1 2-1 「입찰 자격 확인」 카드 | 라벨 「공고 원문에서 확인된 값」 · 값 「자격 제한 · 기타 제한」 · 머리표 `분석 직후` 만 | 「공공데이터에서 확인된 값」 · 「자격 제한: 사업자만 입찰 가능 외 1건」 · `확인 필요=warn` · `분석 직후=warn` | 21:49:23 / 21:50:21 |
| P2-1 다른 카드 | 「공고 원문에서 확인된 값 \| 확인 필요, …」 | 같음 (변화 없음이 맞음) | 같음 |
| P2-3 1-2 첫 진입 | `fit-panel mismatch` · `warn 입력 필요` · 주황 띠 · 연주황 바탕 | `fit-panel is-neutral` · `neutral 안내` · 띠 `rgb(240,213,192)` · 흰 바탕 | 같음 |
| P2-3 빈 칸으로 분석 뒤 | `warn 입력 필요` (첫 진입과 구분 없음) | `fit-panel mismatch` · `warn 입력 필요` · `aria-invalid=true` | 같음 |
| 페이지 오류 | 0 | 0 | 21:51:23 |

- 전후 캡처는 뷰포트 기준이고 판마다 5장씩입니다. 폴더 `role-impl/shots-E/` · 이름 `{before|after}-{390-2-1-collapsed | 390-2-1-open | 1280-2-1-collapsed | 1280-2-1-open | 390-1-2-empty-analyze}.png`

## 3. 돌연변이 표 (6행 · 잡힘 6 / 안 잡힘 0)

| 조각 | 위치 | 변이 | 결과 |
|---|---|---|---|
| P1-1 좁은 화면 힌트 표시 | css `.coach-dock-head .coach-context` | `display: block` 을 `none` 으로 (숨김 되살리기) | 잡힘 (390 접힘 · 펼침 모두 `[]`) |
| P2-1 라벨 칸 | `renderTaskItem` | `task.valueLabel ||` 무시 | 잡힘 (라벨이 「공고 원문에서 확인된 값」) |
| P2-1 머리표 조건 | `renderTaskItem` | `|| task.needsCheck` 제거 | 잡힘 (머리표가 `분석 직후` 만) |
| P2-3 첫 진입 조건 (false) | `getFitMessage` `notTriedYet` | `= false` | 잡힘 (첫 진입이 `warn 입력 필요`) |
| P2-3 첫 진입 조건 (true) | 같은 줄 | `= true` | 잡힘 (빈 칸 분석 뒤에도 `neutral 안내`) |
| P2-3 aria-invalid 순서 | `runAnalysis` 빈 칸 경로 | `focusNoticeUrlAsInvalid()` 를 `renderAll()` 뒤로 | 잡힘 (빈 칸 분석 뒤 `neutral 안내` · 순서가 판정에 필요함을 확인) |

- 변이는 매번 trap 으로 복원했고, 복원 뒤 세 파일이 고친 판 사본과 `cmp` 로 같았습니다.

## 4. 하지 못한 것 · 남은 위험

- **좁은 화면 힌트에서 공고 제목을 뺀 것**은 지시대로입니다. 그래서 390 에서는 어느 물건인지가 머리 줄에 나오지 않습니다. 보드 위 공고 머리 카드에는 제목이 있습니다.
- **P2-3 의 상태 판정을 DOM 속성(`aria-invalid`)에 맡겼습니다.** 입력하면 그 속성이 풀리므로, 입력했다가 다시 비우면 「안내」(중립)로 돌아갑니다. [추론] 「아직 시도하지 않음」과 같은 상태로 보는 것이 맞다고 판단했습니다.
- **값 40자 자르기**는 sample 의 첫 항목이 짧아 실제로는 걸리지 않았습니다. 긴 첫 항목인 공고로는 화면을 보지 않았습니다.
- **844×390 페이지 맨 위**에서 답이 열린 상태의 단계 표시가 화면 밖인 것은 묶음 D 보고와 같습니다(그대로 남음).
- **포트 상태**: 8976 은 건드리지 않았습니다(21:55 기준 PID 48677). 19324 · 19325 는 종료했습니다(LISTEN 0).

## 5. 서버 문자열이라 못 고친 문구 · 6. 깨진 테스트

없습니다(37 passed).

작업 시간은 21:48부터 21:56까지 약 8분입니다.
