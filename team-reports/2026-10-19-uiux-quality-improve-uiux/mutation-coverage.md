# 3팀 diff 조건 조각 × 변이 대조 (1340f55..0b0e4a6 · src/app.js)

> 팀장 작성(2026-10-19). 조각 목록은 `python3 ~/.claude/scripts/mutation-fragments.py 1340f55..0b0e4a6 -- src/app.js` 출력이다.
> 변이 출처: A m1~m14(changes-A.md) · B 9행(changes-B.md) · C 7행(changes-C.md · 팀장 1행 포함) · D 7행(changes-D.md) · 「사본 X1~X7」은 팀장이 0b0e4a6 `git archive` 사본(19331)에서 구현자 프로브로 돌린 추가 변이다(21:36~21:4x · 결과 원문 `scratchpad/mutx/result.txt`).
> styles.css 의 규칙은 조각 도구가 뽑지 않는다. CSS 판정은 각 묶음의 계산 스타일 측정(대비 · 넘침 · 높이)과 재판정 r1 종료 조건이 맡는다.

| # | 조각 | 위치 | 결과 | 근거 |
|---|---|---|---|---|
| 1 | `(saved === true \ | \ | 잡힘 | 사본 X1(저장값 우선 줄 삭제) · d.cjs 390 저장값 펼침이 접힘으로 뒤집힘 |
| 2 | `JS 연산자 === true` | src/app.js:467 | 변이 없음 | #1 과 같은 줄의 한쪽 비교 · X1 이 줄 전체를 끔 · 한쪽만 바꾼 변이는 없음 |
| 3 | `JS 연산자 === false` | src/app.js:467 | 변이 없음 | #2 와 같음 |
| 4 | `JS 연산자 ?` | src/app.js:1285 | 변이 없음 | 데이터 형식 가드(Array.isArray) · 판정이 아님 |
| 5 | `(!restricted.length) return null;` | src/app.js:1287 | 잡힘 | B 「자격 제한 조건」 조기 반환 삭제 |
| 6 | `JS 연산자 ?` | src/app.js:1319 | 잡힘 | 사본 X2(맨 앞에 붙이기 삭제) · b.cjs 2-1 할 일 목록에서 빠짐 |
| 7 | `(!window.confirm("2-1~2-4 할 일 체크와 서류 체크를 모두 지웁니다. 되돌릴 수 없습니다. 계속할까요?")) {` | src/app.js:1350 | 변이 없음 | 확인창(window.confirm) 분기 · 문구만 B 에서 바꿈 |
| 8 | `JS 연산자 ?` | src/app.js:1413 | 변이 없음 | 안내 문구 선택 삼항 · B 4 전후 화면 비교로 관측만 |
| 9 | `JS 연산자 ?` | src/app.js:1427 | 변이 없음 | 안내 문구 선택 삼항 · B 2 전후 관측만 |
| 10 | `JS 연산자 ?` | src/app.js:1439 | 변이 없음 | 안내 문구 선택 삼항 · B 4 전후 관측만 |
| 11 | `JS 연산자 ?` | src/app.js:1576 | 변이 없음 | 머리표 이름 선택(badgeLabel) · B 2 전후 관측만 |
| 12 | `JS 연산자 ?` | src/app.js:1679 | 변이 없음 | is-collapsed 클래스 · D 기본 접힘 변이(getInitialCoachCollapsed)가 상태를 뒤집지만 이 렌더 조각 자체는 미변이 |
| 13 | `JS 연산자 ?` | src/app.js:1679 | 안 잡힘 | 사본 X3(렌더 때 has-answer 삭제) · 안 잡힘. setCoachAnswer 가 같은 클래스를 다시 맞추는 경로가 있어 동치로 보임[추론] |
| 14 | `JS 연산자 ?` | src/app.js:1681 | 변이 없음 | 머리표 문구 선택(llmConnected) · 기존 동작 |
| 15 | `JS 연산자 ?` | src/app.js:1681 | 변이 없음 | 머리표 tone 선택 · C tone 변경의 한 곳 · 미변이 |
| 16 | `JS 연산자 ?` | src/app.js:1682 | 변이 없음 | title 속성 문구 |
| 17 | `JS 연산자 ?` | src/app.js:1682 | 변이 없음 | 힌트 문구 선택(제목 유무) |
| 18 | `JS 연산자 ?` | src/app.js:1699 | 변이 없음 | 답 지우기 줄 초기 hidden · #21 이 같은 일을 함 |
| 19 | `(result) result.innerHTML = coachAnswerHtml;` | src/app.js:1715 | 안 잡힘 | A m2(변수에서 되살리기 → DOM 복사) · 안 잡힘. 응답 시점 재조회(m1)가 같은 일을 함 |
| 20 | `(result) result.innerHTML = html;` | src/app.js:1734 | 잡힘 | A m1(옛 요소에 쓰기) |
| 21 | `(tools) tools.hidden = !html;` | src/app.js:1738 | 잡힘 | 사본 X4(답 지우기 줄 항상 숨김) · d.cjs clearVisible false |
| 22 | `(askButton) {` | src/app.js:1750 | 변이 없음 | 요소 존재 가드 |
| 23 | `JS 연산자 ?` | src/app.js:1752 | 잡힘 | A m8(429 잠금 시작 삭제) · 버튼 글자 「1분 뒤 다시」가 사라짐 |
| 24 | `(result) {` | src/app.js:1758 | 변이 없음 | 요소 존재 가드 |
| 25 | `(askInFlight) result.setAttribute("aria-busy", "true");` | src/app.js:1759 | 잡힘 | A m14(aria-busy if false) |
| 26 | `JS 연산자 .length > 0` | src/app.js:1788 | 잡힘 | 사본 X5(onBoard 를 true 로) · 공고 가져오기에서 --dock-h 16px |
| 27 | `JS 연산자 ?` | src/app.js:1789 | 잡힘 | #26 과 같은 변이 · 같은 줄의 결과 선택 |
| 28 | `(!input \ | \ | 변이 없음 | 요소 존재 가드 |
| 29 | `(isCoachAskLocked()) return;` | src/app.js:1955 | 잡힘 | A m5(진입부 잠금 판정 삭제) |
| 30 | `(requestId !== askRequestId) return;` | src/app.js:1994 | 잡힘 | A m6(응답 직후 번호 비교 if false) |
| 31 | `(response.status === 429) startAskCooldown();` | src/app.js:1995 | 잡힘 | A m8(429 잠금 시작 삭제) |
| 32 | `JS 연산자 >= 500` | src/app.js:1999 | 안 잡힘 | B 「5xx 판정」 삭제 · 안 잡힘. 서버 500 문구가 정규식에도 걸림 |
| 33 | `(systemFailure) console.warn("AI 코치 질문 실패", response.status, payload.error);` | src/app.js:2000 | 변이 없음 | console.warn 기록 · 화면 영향 없음 |
| 34 | `JS 연산자 ?` | src/app.js:2001 | 잡힘 | B 「질문 시스템 실패」 systemFailure=false |
| 35 | `(requestId !== askRequestId) return;` | src/app.js:2006 | 잡힘 | A m6 과 같은 비교의 catch 쪽 · m6 이 잡힘[추론: 같은 변수 비교] |
| 36 | `(requestId === askRequestId) {` | src/app.js:2011 | 잡힘 | A m7(finally 번호 비교 if true) |
| 37 | `JS 연산자 ?` | src/app.js:2054 | 변이 없음 | 링크 표시 조건(sourceUrl 유무) · B 10 전후 관측만 |
| 38 | `JS 연산자 ?` | src/app.js:2148 | 변이 없음 | 안내 문구 조건(profile.code B) · B 7 관측만 |
| 39 | `JS 연산자 ?` | src/app.js:2384 | 변이 없음 | 머리표 문구(제한 있음/없음) · 기존 의미 |
| 40 | `JS 연산자 ?` | src/app.js:2384 | 변이 없음 | 머리표 tone · C 의 safe 변경 · 미변이 |
| 41 | `JS 연산자 ?` | src/app.js:2462 | 변이 없음 | 첨부 안내 버튼 표시 조건(profile.code B) · B 7 관측만 |
| 42 | `JS 연산자 ?` | src/app.js:2617 | 잡힘 | C 「마감 D-n tone」 neutral→safe |
| 43 | `JS 연산자 ?` | src/app.js:2617 | 잡힘 | #42 와 같은 줄 |
| 44 | `JS 연산자 ?` | src/app.js:2689 | 잡힘 | C 「진행 중 아이콘 없음」 ""→"▶" · 아이콘 렌더 조건이 함께 바뀜 |
| 45 | `JS 연산자 ?` | src/app.js:2702 | 잡힘 | C getStageIcon 변이 |
| 46 | `JS 연산자 ?` | src/app.js:2702 | 잡힘 | #45 와 같은 줄 |
| 47 | `JS 연산자 ?` | src/app.js:2702 | 잡힘 | #45 와 같은 줄 |
| 48 | `JS 연산자 ?` | src/app.js:2716 | 잡힘 | C getStageIcon 변이 · 위쪽 단계 버튼 렌더 |
| 49 | `JS 연산자 ?` | src/app.js:2897 | 변이 없음 | 해당 묶음 0개 안내 선택 · B 「해당 묶음 필터」 변이가 앞 단계를 끔 · 이 삼항 자체는 미변이 |
| 50 | `JS 연산자 ?` | src/app.js:2928 | 잡힘 | C 할 일 「확인 필요」 tone warn→safe |
| 51 | `(hidden) byId("board-stage1-extra").hidden = true;` | src/app.js:2976 | 잡힘 | 사본 X7(빈 보드에서 공고 자료 숨김 삭제) · b.cjs 빈 보드 문구에 공고 자료가 섞임 |
| 52 | `(neverAnalyzed) {` | src/app.js:3001 | 잡힘 | B 빈 상태 조건 = false |
| 53 | `JS 연산자 ?` | src/app.js:3052 | 변이 없음 | 입력 상태 문구 선택 · B 1 보강 관측만 |
| 54 | `JS 연산자 ?` | src/app.js:3052 | 변이 없음 | #53 과 같은 줄 |
| 55 | `JS 연산자 ?` | src/app.js:3088 | 변이 없음 | 목적 불일치일 때만 본문 · 기존 동작 |
| 56 | `JS 연산자 ?` | src/app.js:3157 | 잡힘 | B 완료 조건(stage.done 삭제) |
| 57 | `JS 연산자 ?` | src/app.js:3342 | 변이 없음 | 관심 공고 마감 tone · C 변경 · 미변이 |
| 58 | `JS 연산자 ?` | src/app.js:3342 | 변이 없음 | #57 과 같은 줄 |
| 59 | `JS 연산자 ?` | src/app.js:3347 | 변이 없음 | 관심 공고 머리표 선택(예시/마감) |
| 60 | `JS 연산자 ?` | src/app.js:3347 | 변이 없음 | #59 와 같은 줄 |
| 61 | `JS 연산자 ?` | src/app.js:3348 | 잡힘 | C 관심 공고 반복 제거(notice!==title 제거) |
| 62 | `JS 연산자 ?` | src/app.js:3349 | 변이 없음 | 관심 공고 meta 반복 제거(next!==type) · 미변이 |
| 63 | `JS 연산자 ?` | src/app.js:3349 | 변이 없음 | #62 와 같은 줄 |
| 64 | `JS 연산자 ?` | src/app.js:3351 | 변이 없음 | 예시 항목 링크 선택 · 기존 동작 |
| 65 | `JS 연산자 ?` | src/app.js:3355 | 변이 없음 | 빈 text 줄 생략 |
| 66 | `JS 연산자 ?` | src/app.js:3356 | 변이 없음 | 빈 meta 줄 생략 |
| 67 | `(analysisError) focusNoticeUrlAsInvalid();` | src/app.js:3442 | 잡힘 | D 분석 실패 포커스(focusNoticeUrlAsInvalid 삭제) |
| 68 | `JS 연산자 >= 500` | src/app.js:3460 | 안 잡힘 | #32 와 같은 5xx 판정(분석 쪽) · B 「5xx 판정」 안 잡힘 |
| 69 | `(!serverSide) return message \ | \ | 잡힘 | B 「서버 오류 문구 판정」 /$^/ · 같은 함수의 앞 갈래[추론] |
| 70 | `(busy) analyzeButton.setAttribute("aria-busy", "true");` | src/app.js:3472 | 안 잡힘 | 사본 X6(분석하기 aria-busy if false) · p3.cjs 비교에서 안 잡힘[관측] · A 반환물의 LOCK 줄은 analyzeBusy 를 찍었으나 사본 비교 정규화에서 걸러졌을 수 있음[추론] |
| 71 | `(!window.confirm("지금 공고를 관심 공고에 저장하고 새 물건 분석을 시작할까요?")) {` | src/app.js:3514 | 변이 없음 | 확인창 분기 · 문구만 B 에서 바꿈 |
| 72 | `(event.target.closest("[data-goto-input]")) {` | src/app.js:3717 | 변이 없음 | 빈 보드 「공고 가져오기로」 클릭 처리 · B 1 관측(누르면 wizard-step-profile)만 |
| 73 | `JS 연산자 ?` | src/app.js:3720 | 변이 없음 | #72 와 같은 처리의 단계 선택 |
| 74 | `(event.target.closest("[data-goto-attachments]")) {` | src/app.js:3723 | 변이 없음 | 「2-1 첨부파일 보기」 클릭 처리 · B 7 관측만 |
| 75 | `JS 연산자 ?` | src/app.js:3750 | 변이 없음 | 저장 피드백 문구 선택 |
| 76 | `(event.target.closest("[data-coach-clear]")) {` | src/app.js:3771 | 변이 없음 | 「답 지우기」 클릭 처리 · D 관측(결과 0자 · 포커스 이동)만 |
| 77 | `(dockForHeight && window.ResizeObserver) new ResizeObserver(updateDockHeightVar)` | src/app.js:3806 | 잡힘 | D --dock-h 갱신(ResizeObserver 등록 삭제) |
| 78 | 이동 `const result = byId("coach-question-result");` | src/app.js:1813→1733 | 잡힘 | A m1(결과 요소를 옛 위치에서 잡기) · 이동 줄의 경계 변이 |
| 79 | 이동 `: `<p class="small-text">이 공고에서 낙찰 후 서류를 찾지 못했습니다. 공고 원문과 첨부` | src/app.js:2713→2898 | 변이 없음 | 문구 위치 이동(낙찰 후 서류 없음 문장) · 미변이 |

집계(표의 결과 열 기준): 잡힘 31 · 안 잡힘 5 · 변이 없음 43 · 합계 79

- 안 잡힘 5건(#13 · #19 · #32 · #68 · #70) 가운데 #13 · #19 는 다른 경로가 같은 일을 하는 동치 후보[추론]이고, #32 · #68 은 서버 500 문구가 정규식에도 걸리는 이중 판정이다. #70(분석하기 aria-busy)은 화면 읽기용 속성이라 시각 동작에 영향이 없고, 비교 스크립트가 그 값을 걸렀는지 확인하지 않았다[미확인].
- 변이 없음 행의 대부분은 문구 · 머리표 이름 선택 삼항이다. 그 결과는 각 묶음 반환물의 전후 화면 비교로 관측했고, 변이로 증명하지는 않았다.
