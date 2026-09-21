# visual-reviewer 1차 판정 — 관심 공고 탭 diff (2026-09-21 11:29 KST)

판정 대상: 당시 워킹트리 미커밋 diff(`src/app.js`, `src/styles.css`, 9개 항목 반영분).

## 판정 대상 확인

`git -C /Users/user/Documents/Dev/Hometest_op diff src/app.js src/styles.css` 실측 완료. 변경은 `src/app.js`(+15/-4), `src/styles.css`(+29/-4)만 해당. 테마 축은 grep으로 재확인 — `--red`(#991b1b), `--muted`(#8b5a40), `--line`(#f0d5c0), `--amber`(#f5901e) 기존 변수만 재사용했고 새 색상 발명 없음. 폰트/톤앤매너 변경 없음. **테마 훼손 없음.**

## 항목별 판정

- **1 (0건/카드 3장 모순) — 미해결, 재현: 스크린샷 `/tmp/opada-watchlist-shots/06-live-after-star.png`에서 "관심 공고 1건" 아래 카드 3장 그대로 노출. 구조 변경 없음. e2e 게이트 자체가 이를 `P0-6 … 축 없음 — 이 게이트는 이것을 보지 못한다`로 명시해 미검증 상태를 프로젝트 스스로 선언 중. 배지 가독성 개선(4번)으로 "예시"임은 더 잘 보이나 숫자-카드 불일치는 그대로.
- **2 (마감 경과 경고 무게) — 🔴 미해결, 사실상 무증명 코드.** `item.next`의 모든 작성 지점을 추적함(app.js:382/388/394/615/1549, server.py `build_tasks` 1243-1418) — 어느 경로도 "마감 지남" 문자열을 만들지 않는다. 실제 "입찰 마감 지남"은 `countdownBadge()`(app.js:1274-1278, closed→`type:"warn"`, 일반 경고와 같은 무게)와 `notice.alerts`(원문 목록)에서만 나오며 둘 다 이번 diff가 손대지 않았다. Playwright로 `localStorage`에 `next:"입찰 마감 지남 (테스트 주입)"`을 인위 주입해 재현 — CSS 자체는 작동(`color: rgb(153,27,27)`, `font-weight:700`)하지만, 실사용 흐름에서 그 값이 절대 도달하지 않는다. 테스트 스위트(`tests/`)에도 `is-overdue`/`마감 지남` 관련 검증 0건. **원래 P0은 미해결이며, "구현함" 표기는 정정 필요.**
- **3 (샘플 "원문" 링크 오도) — 해결.** 재현: 온비드 실공고 스크린샷과 정적 확인 모두 `<span class="text-action is-disabled">예시 항목(원문 없음)</span>`로 링크 자체가 제거됨. 클릭 유도 요소 없음.
- **4 (배지 막대화) — 해결.** Playwright 스크린샷(`06-live-after-star.png`)에서 "예시" 배지가 정상 pill로 렌더. `.watch-item span:not(.star-placeholder):not(.badge)` 선택자로 배지가 규칙 범위 밖으로 확인됨.
- **5 (모바일 제목 줄바꿈) — 해결.** Playwright 375px 스크린샷·DOM 측정(`getBoundingClientRect().height`) 모두 "관심 공고"/"최근 살펴본 공고" h3 높이 24px(단일 줄) 확인.
- **6 (포커스 복원) — 해결, 실제 클릭 재현함.** Playwright로 두 번째 섹션("최근 살펴본 공고")의 즐겨찾기 버튼을 클릭 → 재렌더 후 `document.activeElement`가 동일 섹션(index 1, "최근 살펴본 공고")의 같은 버튼으로 확인. 섹션에서 사라지는 폴백 경로도 코드상 안전(널 병합 후 `document.querySelector` 폴백).
- **7 (샘플 별과 활성 별 구분 안 됨) — 해결.** CSS 계산값 대조: `.star-placeholder` 이전엔 `border:#f0c68a; color:var(--amber)`로 `.is-on`과 테두리·색이 사실상 동일했으나, 수정 후 `border:var(--line); color:var(--muted); opacity:0.6`으로 명확히 분리됨.
- **8 (aria-label 부재) — 해결.** diff에서 `title`과 동일 문구로 `aria-label` 추가 확인(정적).
- **9 (44px 터치 타겟) — 부분 개선, P1로 계속 열어둘 것.** Playwright 실측 `getBoundingClientRect()` 결과 32.2×32px. WCAG 2.5.5(AA는 미대상이지만 실무 44px 기준)에는 여전히 미달. "완화됐다"는 정확하나 "해결"은 아님.

## 새로 만든 문제

- 🔴 **P0**: 항목 2가 "구현함"으로 분류돼 있으나 실제로는 도달 불가능한 조건을 검사하는 죽은 코드다. 다음 사람이 이 상태를 보고 "이미 고쳐졌다"고 오판할 위험이 있다 — `watchItemHtml()`의 `isOverdue` 옆에 "이 조건은 현재 데이터 흐름상 도달하지 않음(countdownBadge()가 실제 위치)" 주석 1줄을 남기거나, 원래 위치(`countdownBadge()`의 closed→warn 매핑)를 고치는 재작업이 필요.
- 🟡 P2: `<span aria-disabled="true">`는 비인터랙티브 요소에 붙어 의미상 불필요(해가 되진 않음).
- 그 외 회귀 없음. 게이트 재실행: 순수 함수 251/251, 화면 문자열 20/20, e2e 17/17 — 모두 diff 적용 상태에서 독립 재확인함(리뷰어가 직접 실행).

## 검증 누락

- 별표 active 색상 대비(WCAG 2.0:1 추정) 범위 판단은 재검증하지 않음 — 전역 `--amber` 변경 소요라 3팀 판단(범위 밖)에 동의하나, 수치 자체는 미측정. 비용: contrast 계산 5분, 대비 미달 확정 시 전역 반영은 승인 경계.
- 항목 2를 실제 코드로 고치는 안(예: `countdownBadge()` closed 상태를 `warn` 대신 `urgent`류로 격상)은 검토하지 않음 — 구현 범위이므로 팀장 판단 대상.

## 최종 판단

**조건부 GO.** 9개 중 7개(3,4,5,6,7,8,9-부분)는 실측 재현으로 확인됐고 회귀·테마 훼손 없음. 다만 항목 2는 "구현함"이 사실과 다르므로, 그 상태 표기를 정정(또는 실제 위치로 재작업)한 뒤 머지할 것을 조건으로 건다. 정정 없이 그대로 "9개 중 8개 완료"로 보고하면 허위 완료 보고에 해당한다.
