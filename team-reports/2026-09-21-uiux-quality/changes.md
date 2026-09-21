# 변경 내역 — 관심 공고 탭 (2026-09-21)

4개 진단 역할(ux-flow-auditor·visual-designer·interaction-auditor·responsive-tester)이 지적한 것 중 P0 전부와 구현이 작은 P1 일부를 반영했다. 전체 디자인 테마(캐니언 팔레트 색상·폰트·톤앤매너)는 건드리지 않았고, 기존 CSS 변수(`--red`·`--muted`·`--line`)만 재사용했다.

## 구현한 것

1. **모바일 소제목 줄바꿈 수정** (`src/styles.css` `.watch-section-title h3`) — `flex-shrink: 0` 추가. "관심 공고"·"최근 살펴본 공고"가 375~390px에서 2줄로 깨지던 것을 고쳤다.
2. **"예시" 배지 렌더링 버그 수정** (`src/styles.css` `.watch-item span:not(.star-placeholder)` 계열) — `:not(.badge)`를 추가해 선택자 명시도 충돌을 없앴다. 카드 폭 전체를 채우던 막대가 원래 의도한 작은 pill로 돌아왔다.
3. **샘플 카드 "원문" 링크 수정** (`src/app.js` `watchItemHtml()`) — `item.sample`이면 `<a>` 링크 대신 비활성 "예시 항목(원문 없음)" 텍스트로 대체. 실제 공고와 무관한 온비드 홈페이지로 튀던 문제를 없앴다.
4. **즐겨찾기 포커스 이동 버그 수정** (`src/app.js` 클릭 위임 핸들러) — 클릭된 버튼이 속한 `.watch-section`의 인덱스를 기억해 재렌더 후 같은 위치에서 우선 포커스를 복원하도록 바꿨다. "최근 살펴본 공고"에서 즐겨찾기를 추가했는데 포커스가 "관심 공고" 섹션의 다른 카드로 튀던 접근성 결함을 고쳤다.
5. **별 placeholder 시각 구분** (`src/styles.css` `.star-placeholder`) — muted 회색조 + `opacity: 0.6`으로 바꿔 활성 별(amber)과 구분되게 했다.
6. **마감 경과 경고 강조** (`src/app.js`/`src/styles.css`) — 1차 구현(`item.next` 문자열 매칭 + `is-overdue` 클래스)은 독립 리뷰(visual-reviewer)에서 "실제 데이터 흐름에 그 문자열이 도달하지 않는 죽은 코드"로 지적받아 되돌렸다. 재구현: `currentNoticeCard()`가 카드 저장 시점에 `sampleNotice.countdown`(서버 `bid_countdown()`이 만드는 `{state, label, deadline, daysLeft}`)을 함께 저장하고, `watchItemHtml()`이 기존 `countdownBadge()`와 같은 type 매핑 규칙으로 배지를 하나 더 렌더링한다. urgent/warn 매핑 자체(마감 지남이 마감 임박보다 약하게 보이는 것)는 기존 전역 관례라 이번 범위에서 재설계하지 않았다. 재판정 결과 **GO**(상세는 `verification.md`).
7. **별표 버튼 접근성 이름 명시** (`src/app.js`) — `title`과 같은 문구로 `aria-label` 추가.
8. **원문 링크 터치 영역 확대** (`src/styles.css` `.watch-actions .text-action`) — `min-height: 32px`로 절충 확대(44px 완전 충족은 아님).

## 구현하지 않은 것 (제품 판단 또는 범위 밖으로 남김)

- 요약 숫자("관심 공고 N건")와 카드 개수(샘플 포함) 불일치 — 카피·정보 구조 변경 필요, 다음 과제.
- 별표/배지 색상 대비 부족(WCAG 약 2.0:1) — 전역 `--amber` 변경은 테마 변경 범위라 판단해 보류.
- 즐겨찾기 항목이 "관심 공고"·"최근 살펴본 공고" 두 섹션에 중복 노출되는 정보 구조 — 부제로 이미 설명돼 있어 구조 변경은 범위 밖.
- 카드 내부 텍스트 위계(제목/메타/액션 크기 차이) 승격 — 다음 과제.

## diff 요약

`git diff --stat`: `src/app.js` 23줄 변경, `src/styles.css` 33줄 변경. 상세는 이 커밋의 diff 참고.
