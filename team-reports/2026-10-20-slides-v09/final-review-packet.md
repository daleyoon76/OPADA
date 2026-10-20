# 최종 리뷰 packet r1 (prose-editor · deck-reviewer 병렬 · 2026-10-20 · 팀장 · 10:12:26 `date` 뒤)

## 판정 대상 (움직이지 않게 고정)
- 덱: `docs/60_본선준비/10_발표자료/17_발표슬라이드_v09_20261020/index.html` sha256 `3952a97dd8f18b457f75c3009894308fb8492f30312037ebd150a17b3ffbd140`
  - 같은 바이트 사본: `/private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/ecae8f91-ad18-45ef-8441-2fbb81acf176/scratchpad/review-target/index-3952a97d.html`
- 발표노트 v07(동원님 확정 뒤 라이브 실측 한 줄 추가): `docs/60_본선준비/10_발표자료/16_발표평가_10분피치_초안_v07_20261020.md` sha256 앞 20자 `d7512c5d62d016391061` · 사본 같은 폴더 `notes-v07.md`
- 렌더(9장 · slide-designer 3차 · 1600×900): `/private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/ecae8f91-ad18-45ef-8441-2fbb81acf176/scratchpad/role-design2/render3/`
- 커밋으로 고정하지 않은 이유: main 에 커밋하면 라이브 화면 머리에 「서버 기동 뒤 코드가 바뀌었습니다」 경고가 다시 뜬다(`live-check-c520e34.md` 재확인 절). 대신 사본과 해시로 고정한다. 판정 중에 팀장 · 다른 역할은 덱을 고치지 않는다.

## 기준과 결정
- 서비스 기준 판: main `c3cb905`(라이브와 같은 판 · src 는 develop `2c46005` 와 같음). 코드는 `git show c3cb905:src/<파일>` 로 읽는다.
- 서비스 사실: `team-reports/2026-10-20-slides-v09/service-facts-develop-a1e1f3a.md`(끝 「정정」 절 포함) · 라이브 실측: `live-check-c520e34.md`
- 동원님 결정: `r0-synthesis.md` 6절(6장 표현 셋 바꿈 · 제목 그대로 · 7장 이름표 · 기준 시점 · keep-all · Pretendard 내장 · 노트 v07 확정)
- 작업 기록: `composition-log.md`(composer) · `design-review.md` · `design-review-r2.md` · `design-review-r3.md`(designer)
- 팀장이 채택한 packet 밖 변경: composer 의 배치 셋(4장 표지 줄 위치 · 5장 링크 이름표 · 5장 간격)과 글자 둘(4장 「공고 가져오기 · 3단계」 · 6장 「브라우저 저장소」)
- 이미 결정된 것은 `r0-packet-common.md` 「이미 결정된 것」 절과 위 6절이다. 되살리지 않는다.

## 함정 발췌
- 금지표현(띄어쓰기 변형 포함) · 엠대시 · 겹화살괄호 0. 권장 문장은 `r0-packet-common.md`.
- 서비스 주장은 코드보다 넓게 쓰지 않는다(「교차 대조」 사례). 공공데이터 API 는 인증키가 있을 때만 쓰는 보조 경로이고, 라이브는 키가 있어 2-1 할 일이 3개다.
- 스크린샷에 담당자 이름 · 전화번호 · 「코드 판」 줄이 없어야 한다.
- zsh: `$var:` 수정자 · `==` · 맞는 파일 없는 glob 주의. 브랜치를 바꾸지 않는다. 앱을 기동하지 않는다.

## 고정 질문 (두 역할 모두 답한다)
1. 의도대로 고쳐졌는가(r0 지적 처분 대조)와 별개로, 이 덱이 결선 청중(캠코 심사위원) 앞에서 맞는 상태인가.
2. 지적마다 그 처방이 기대는 것(도구 · 화면 · 노트 줄 · 다음 단계) 1개.
3. 최종 커밋에서 확인할 종료 조건 1개와, 그 조건을 지금 판에 돌린 결과.

## 산출물 × 게이트
| 산출물 | 게이트 | 이번 라운드 |
|---|---|---|
| 덱 글자 | prose-editor | r1 |
| 덱 서비스 주장 · 수치 · 금지표현 · 시각 · 노트 대응 | deck-reviewer | r1 |
| 그림 속 개인정보 | 팀장 눈 확인(완료) · deck-reviewer 렌더 확인 | r1 |
| 제작 기록 `notes.md` | deck-reviewer 훑기 | r1 |
