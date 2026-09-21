# visual-reviewer 재판정 — 마감 경고 재구현 (2026-09-21 11:40 KST)

판정 대상: 1차 판정(`visual-reviewer-r1.md`)의 유일한 조건("항목 2가 죽은 코드")을 해소하기 위한 재구현 diff.

## 판정: GO

### 항목 2(마감 경과 강조) — 해결 확인

- 서버: `src/server.py:1854-1875` `bid_countdown()`이 마감 지난 공고에 대해 정확히 `{"state":"closed","label":"입찰 마감 지남",...}`을 반환함 `[관측]`.
- 배선: `bid_countdown()` 결과가 `notice["countdown"]`으로 응답 객체에 실제 포함됨(`server.py:2155,2197`) `[관측]`.
- 클라이언트 저장 경로: `replaceNotice(payload.notice)`(`app.js:1670-1674,1711`)가 `Object.assign`으로 `sampleNotice`에 `countdown`까지 복사 → `currentNoticeCard()`(`app.js:620`)가 `sampleNotice.countdown`을 카드에 실어 저장 → `watchItemHtml()`(`app.js:1605-1615`)이 `item.countdown`으로 배지 렌더. 도달 불가능한 죽은 코드 아님을 정적 추적으로 확인 `[관측]`.
- `isOverdue`/`is-overdue` 문자열은 `src/app.js`, `src/styles.css` 전체에서 grep 0건 — 지적된 죽은 코드가 실제로 제거됨 `[관측]`.
- 실제 렌더 검증(Playwright, `localStorage`에 `onbid-public-asset-doc-agent-recent-v1` 직접 주입): `state:"closed"` → `badge warn :: 입찰 마감 지남`, `state:"urgent"` → `badge urgent :: 마감 D-1` 로 실제 DOM에 렌더됨을 직접 재현·대조. 제공된 참고 스크린샷(`/tmp/opada-watchlist-shots/08-countdown-render-check.png`)과 독립 재현본(리뷰어가 별도 데이터로 캡처)이 동일한 배지 색상·라벨 매핑을 보임 `[관측, 독립 재현]`.
- 모바일 375px에서도 배지가 겹침·탈출 없이 title/type 블록 아래로 자연 줄바꿈됨을 확인 `[관측]`.
- CSS `watch-item span:not(.star-placeholder):not(.badge)` 수정은 필수였음 — 없었다면 새 배지가 `display:block; color:muted` 규칙에 먹혀 알약(pill) 대신 회색 블록 텍스트로 보였을 것. 구현자가 이를 선제 방지한 점은 양성 신호.

### 범위 판단(4번, urgent/warn 매핑 미변경)

기존 `countdownBadge()` 관례를 그대로 재사용한 것은 타당함. 전역 재설계는 이번 요청(관심 공고 탭에 마감 정보 부재) 범위 밖이며, 새 회귀를 만들지 않음.

### 새로 만든 문제

없음. `favorite` 표기 저장 방식(`getFavoriteNoticeIds()` 별도 키)을 리뷰어 테스트에서 오해해 `0건`으로 나온 것은 리뷰어의 테스트 스크립트 오류이며 구현 결함 아님 — 참고 스크린샷(정상 favorite 키 사용)에서 `2건`으로 정상 집계됨을 대조 확인.

### 게이트 3종 재실행 결과 (리뷰어가 직접 실행)

- 순수 함수: 251/251 통과
- 화면 문자열: 20/20 통과
- e2e: 17/17 통과 (선언 16/16 · 미실행 축 2개는 S8/S9로 이번 변경과 무관 · countdown 배지 자체는 자동 게이트 커버리지 없음 — 리뷰어의 수동 Playwright 검증이 유일한 근거)

### 미검증 (비용/경계)

- countdown 배지에 대한 자동화된 e2e 축 부재 — 회귀 방지용 스펙 1개 추가는 15분 내 가능하나 코드 수정이라 리뷰어 권한 밖, 팀장 판단 필요.
- `/api/analyze`를 실제 온비드 URL로 라이브 호출해 `countdown` 필드가 실전 응답에도 뜨는지는 정적 추적만 했고 실제 크롤링은 안 함 — ngrok 라이브 호출은 승인 경계(외부 네트워크 호출)로 남김. (팀장 후속: 이후 팀장이 직접 curl로 라이브 호출해 `countdown` 필드 포함을 확인함 — `verification.md` 참고.)
