# interaction-auditor 진단 — 관심 공고 탭 (2026-09-21)

대상: `renderWatchlist()`·`watchItemHtml()`·`toggleFavoriteNotice()`·클릭 위임(`app.js:1787` 부근). hover/focus/loading/error/empty/disabled 상태와 별표 토글 입력 UX만.

## 상태 매트릭스 (요약)

- 즐겨찾기 버튼(진짜, `showFavorite:true`): hover(기본 커서만) / focus(브라우저 기본 아웃라인) / active(즉시 토글, 로딩 없음) / aria-pressed 정상 토글 — 확인됨.
- 샘플 placeholder(`<span aria-hidden>`): 클릭 자체가 불가능한 게 의도이나 시각적으로 활성 별과 구분 안 됨 — 확인됨.
- "관심 공고" 섹션 empty state: 코드상 도달 불가(항상 샘플 3건으로 채워짐) — 실측 확인됨.
- "최근 살펴본 공고" 섹션 empty state: 정상 작동 — 확인됨.

## P0 — 포커스가 엉뚱한 곳으로 이동 (키보드/스크린리더 심각)

재현: "최근 살펴본 공고"에만 있는 공고의 별표를 눌러 즐겨찾기에 **추가**하면, 같은 `data-favorite-id`를 가진 버튼이 "관심 공고" 섹션에도 새로 생겨 화면에 두 개가 동시에 존재한다(`document.querySelectorAll('[data-favorite-id="…"]')` length 2). 기존 `document.querySelector('[data-favorite-id="…"]')?.focus()`(`app.js:1791`)는 문서 순서상 첫 번째 요소로 포커스를 보내므로, 사용자가 "최근 살펴본 공고"(y≈842px)에서 클릭했는데 포커스는 "관심 공고" 섹션의 새로 생성된 다른 카드(y≈100px)로 튄다. 키보드 사용자는 방향을 잃고, 스크린리더 사용자는 조작하지 않은 카드의 내용을 듣게 된다(WCAG 2.4.3 Focus Order 위반 소지). "관심 공고"에서 해제할 때는 중복이 하나로 줄어 우연히 드러나지 않아 QA에서 놓치기 쉽다.

## P1

- **샘플 placeholder가 활성 별과 시각적으로 동일.** `.star-placeholder`는 `.star-button.is-on`과 거의 같은 amber 테두리·색을 쓴다. 유일한 차이는 `cursor: auto`뿐이라 마우스 사용자도 알아채기 어렵고, 클릭해도 이벤트 위임 셀렉터에 걸리지 않아 아무 피드백 없이 무반응이다.
- **"관심 공고" 빈 상태 문구가 실질적으로 죽은 코드.** `savedItems`는 실제 즐겨찾기 + 항상 샘플 3건이라 진짜 즐겨찾기가 0건이어도 `savedItems.length`는 항상 3 이상.

## P2

- 별표 버튼의 접근성 이름이 `title` 속성이 아니라 버튼 내부 별 글리프(★/☆)에 의존한다.
- `.star-button`에 커스텀 hover/focus 스타일이 없어 브라우저 기본 아웃라인에만 의존한다.
- 즐겨찾기 해제로 카드가 사라질 때 `aria-live` 알림이 없다.

## 검증 방법

Playwright(chromium)로 로컬 서버(8975)에 접속해 localStorage에 recent/favorites를 시딩, 별표 클릭 전/후 `document.activeElement` 좌표·섹션·`data-favorite-id` 개수를 비교. `getComputedStyle`로 `.star-placeholder` vs `.star-button.is-on` 대조.

## 반영 여부 (2026-09-21 구현·리뷰 후 갱신)

- 포커스 이동 버그: 구현함 — 클릭된 버튼이 속한 섹션 인덱스를 기억해 재렌더 후 같은 인덱스에서 우선 포커스 복원, 없으면 문서 전체 폴백
- 샘플 placeholder 시각 구분: 구현함 — muted 회색조 + opacity 0.6으로 활성 별과 구분
- 별표 aria-label: 구현함
- hover/focus 커스텀 스타일, aria-live: 미구현 — 다음 과제로 남김
