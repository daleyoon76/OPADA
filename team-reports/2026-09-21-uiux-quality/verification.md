# 검증 기록 — 관심 공고 탭 (2026-09-21)

## 게이트 3종 (변경 전 → 변경 후, 회귀 0)

- 순수 함수: 251/251 통과 · 연기 6개 · 축 28개 중 미실행 0개 (변경 전후 동일)
- 화면 문자열: 20/20 통과 · 연기 1개 · 축 5개 중 미실행 0개 (변경 전후 동일)
- e2e(playwright): 17/17 통과 · 축 16개 중 실행 14개 (변경 전후 동일, S8·S9는 이번 변경과 무관한 기존 미실행 축)
- ⚠️ countdown 배지에 대한 자동화된 e2e 축은 없다. 아래 수동 Playwright 검증이 유일한 근거다(visual-reviewer 재판정에서 지적).

## 라이브 검증

- 실제 온비드 URL(`onbidCltrno=1837008`, 부산광역시 금정구 서동 37-17 교육연구시설)로 `/api/analyze` 직접 호출 → 응답에 `notice.countdown = {"state":"open","label":"마감 D-233","deadline":"2027-05-12 17:00","daysLeft":233}` 포함 확인(curl 실측).
- 같은 공고를 Playwright로 분석 → 관심 공고 탭에서 즐겨찾기 추가 → "마감 D-233" 초록 배지가 카드에 렌더됨을 스크린샷으로 확인(`/tmp/opada-watchlist-shots/06-live-after-star.png`, 레포 밖 임시 경로).
- localStorage에 `state:"closed"`(입찰 마감 지남)·`state:"urgent"`(마감 D-2)·`state:"open"`(마감 D-15) 세 가지를 직접 주입해 배지 색상·라벨이 각각 warn/urgent/safe로 올바르게 갈리는 것을 확인(`/tmp/opada-watchlist-shots/08-countdown-render-check.png`).
- 콘솔 에러 0건(모든 라이브·주입 검증 공통, Playwright `console`/`pageerror` 리스너로 수집).
- 모바일 375px에서 소제목("관심 공고"·"최근 살펴본 공고") 줄바꿈이 사라진 것을 DOM 높이 측정(`h3.getBoundingClientRect().height` = 24px, 단일 줄)으로 확인.
- 즐겨찾기 포커스 이동 — "최근 살펴본 공고" 섹션에서 별표를 눌러 추가했을 때 `document.activeElement`가 같은 섹션(index 1)의 같은 버튼에 남는 것을 확인(이전에는 index 0의 다른 카드로 튀었다).

## 독립 리뷰 (visual-reviewer, 저자=검증자 금지 원칙에 따라 팀장이 직접 구현하지 않고 리뷰 역할에 위임)

- 1차 판정(2026-09-21 11:29): **조건부 GO** — 9개 항목 중 7개(3·4·5·6·7·8·9-부분)는 실측 재현으로 확인, 항목 1(요약 숫자/카드 개수 불일치)은 미구현으로 정직하게 확인, 항목 2(마감 경과 강조)는 "실제 데이터 흐름에 도달하지 않는 죽은 코드"로 NO-GO 조건 지적.
- 항목 2 재구현 후 재판정(2026-09-21 11:40): **GO** — 서버 `bid_countdown()` → 응답 `notice.countdown` → `replaceNotice()`로 `sampleNotice.countdown` 갱신 → `currentNoticeCard()`가 카드에 실어 저장 → `watchItemHtml()`이 배지 렌더, 전체 경로를 정적 추적 + Playwright 독립 재현으로 확인. 죽은 코드(`isOverdue`/`is-overdue` 문자열) 잔존 0건(grep). 게이트 3종 리뷰어가 직접 재실행해 동일 수치 확인.

## 검증 경계 (구현됨 / 로컬 검증됨 / 미검증 3분할)

- **구현됨**: diff 전체(`src/app.js` +19줄/-4줄, `src/styles.css` +25줄/-4줄, 최종 기준).
- **로컬 검증됨**: 게이트 3종, localStorage 직접 주입 렌더링, 포커스 이동, 모바일 줄바꿈, 콘솔 에러 0건.
- **라이브 검증됨**: 실제 온비드 공고 1건으로 분석→관심 공고 등록→countdown 배지 렌더 전 과정.
- **미검증**: countdown 배지의 자동화된 e2e 회귀 축 부재(수동 검증만 존재) · 별표/배지 색상 대비(WCAG 2.0:1 추정, 수치 미측정) · 마감이 실제로 지난 공고로의 라이브 재현(온비드에서 마감 지난 공고 URL을 확보하지 못해 localStorage 주입으로 대체) · 태블릿(768px) 여백 · 요약 숫자와 카드 개수 불일치(미구현).

## 임시 파일 정리

- 캡처·검증에 쓴 임시 `.js` 스크립트는 전부 `_tmp_*.js` 이름으로 레포 루트에 만들었다가 실행 직후 삭제했다. 최종 `git status --short`에는 `src/app.js`·`src/styles.css`(수정)와 `team-reports/2026-09-21-uiux-quality/`(신규) 외 `??` 잔존 없음(확인 시각 2026-09-21 11:40).
- responsive-tester가 별도로 만들었던 레포 내 임시 파일 5개(`tmp-debug*.js` 등)는 해당 에이전트가 본인 작업이 아님을 밝히며 남겨뒀었으나, interaction-auditor 완료 시점 확인에서 이미 삭제되어 있었다(`git status --short` 재확인, 어느 세션이 지웠는지는 불명확하나 현재 잔존 없음).
