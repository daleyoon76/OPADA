# responsive-tester 진단 — 관심 공고 탭 (2026-09-21)

검증 경계: Playwright(chromium)로 375/390/768/1280px 4개 뷰포트를 스크린샷·DOM 측정(`getBoundingClientRect`, `scrollWidth` vs `clientWidth`)으로 확인.

## P0 — 없음

가로 스크롤(`scrollWidth > clientWidth`)은 4개 뷰포트 전부 `false`, 텍스트 겹침·조작 불가 요소는 관측되지 않았다.

## P1

- **375px·390px에서 `.watch-section-title h3` 두 개("관심 공고", "최근 살펴본 공고")가 2줄로 깨지고 CJK 글자 단위로 고아 줄이 생긴다.** "관심 공고" → "관심 공" / "고", "최근 살펴본 공고" → "최근 살펴" / "본 공고". DOM 측정으로 375·390px에서만 `h3.height=48`(2줄), 768·1280px에서는 `height=24`(1줄) 확인. 원인은 `.watch-section-title { display:flex }`가 `@media (max-width:900px)` 예외 목록에 없어, 좁은 폭에서 `<p>` 설명 문구와 flex 공간을 다투다 `h3`가 최소폭 이하로 눌리는 것.
- **"원문" 링크(`.text-action`)의 실제 히트 영역이 24×21px로 44px 터치 타겟 기준에 못 미친다.** 옆 배지와 `gap:4px`뿐이라 모바일에서 오탭 위험. 뷰포트 차등은 아니지만 모바일에서 실질 위험이 커 P1으로 분류.

## P2

- 768px(태블릿)에서 `.watch-item`이 900px 이하 미디어쿼리로 1열로 강제돼, 706px의 넓은 패널 폭을 못 쓰고 여백이 헐렁하다. 붕괴는 아니고 태블릿 전용 배치 검토 여지.
- "예시" 배지가 전체 폭 띠처럼 표시되는 현상은 375/768/1280 전부 동일 재현(visual-designer 진단과 같은 원인).

## 확인하지 못한 것

- 실제 터치 디바이스(iOS/Android) native 탭 판정, VoiceOver/TalkBack 접근성 트리는 미확인(Playwright chromium 데스크톱 엔진 기준).
- `#watchlist-title`(Step 3 상단 h2)은 4개 뷰포트 모두 1줄 유지 — 기존에 우려했던 줄바꿈은 이 h2가 아니라 하단 섹션 소제목 h3 2개에서 발생함을 정정.

## 반영 여부 (2026-09-21 구현·리뷰 후 갱신)

- 모바일 소제목 줄바꿈: 구현함 (`h3 { flex-shrink: 0 }`)
- 원문 링크 터치 타겟: 부분 구현 — `min-height: 32px`로 절충(44px 완전 충족 아님), visual-reviewer 재확인 요청
- 태블릿 여백: 미구현 — 다음 과제로 남김
