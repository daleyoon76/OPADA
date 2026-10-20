# 재판정 packet r2 (deck-reviewer · prose-editor 병렬 · 2026-10-20 · 팀장 · 10:27:43 `date` 뒤)

## 판정 대상 (고정)
- 덱 sha256 `e97b139a8ed99b497798b6505d9e4199b35afc0a749f98ac392b465a1930c93b` · 사본 `/private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/ecae8f91-ad18-45ef-8441-2fbb81acf176/scratchpad/review-target/index-e97b139a.html`
- r1 판정 대상 사본(비교용): 같은 폴더 `index-3952a97d.html`. base64 를 뺀 diff 는 30줄이다(`diff <(sed 's/data:[^"]*//g' A) <(sed 's/data:[^"]*//g' B) | grep -c '^[<>]'` · 10:27 팀장 실행).
- 노트 v07 r2: sha256 앞 24자 `74e1b46603499766e222611a` · 사본 `notes-v07-r2.md`
- 제작 기록 `17_발표슬라이드_v09_20261020/notes.md` sha256 앞 24자 `a0ca401f98050a2d275b21e2`
- 렌더(9장): `/private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/ecae8f91-ad18-45ef-8441-2fbb81acf176/scratchpad/role-design2/render4/`
- 커밋으로 고정하지 않은 이유는 r1 packet 과 같다(main 커밋이 라이브 경고를 다시 띄움).

## 무엇이 바뀌었나
- 반영 목록(팀장): `team-reports/2026-10-20-slides-v09/fix-r2-list.md`(덱 15행 · 노트 4건 · 미룬 것 2건과 이유)
- 실행 기록: `composition-log-r2.md`(composer 2차 · 10:22~10:25) · `design-review-r4.md`(designer 4차 · 4장 띠 `<br>` · 5장 간격 · 10:25~10:27)
- 첫 packet(기준 판 · 결정 · 함정 · 고정 질문)은 `final-review-packet.md` 그대로다. 시간 예산 15분 · 역할 전용 scratch 는 r1 과 같은 폴더(`role-deck-final/` · `role-prose-final/`)를 쓴다.

## 함정 발췌 (r1 과 같음)
- 금지표현 · 엠대시 · 겹화살괄호 0 · 서비스 주장은 코드보다 넓게 쓰지 않는다(이번 1번 행이 그 수정) · 스크린샷 개인정보 0 · zsh 함정 · 브랜치 전환과 앱 기동 금지.

## 고정 질문
1. r1 의 당신 지적마다 처분(닫힘 · 남음 · 미룸 동의/이의)
2. 이번 수정이 새로 만든 결함이 있는가(특히 6장 차별점 문장 · 6장 공공데이터 2줄 · 7장 각주 3줄 · 5장 「시연 순서」)
3. 처방마다 기대는 것 1개
4. 당신의 r1 종료 조건을 이 판에 돌린 결과와, 최종 커밋에서 확인할 종료 조건 1개
5. 판정: GO / 조건부 GO / NO-GO

## 변이 조각 표
- 조각 표 생략: 이번 diff 는 슬라이드 HTML 의 문장 · `<br>` · CSS 간격 30줄뿐이고, 판정 코드(정규식 · `if`/`and`/`or` 조건)를 새로 넣거나 고친 것이 없다. 검사 스크립트(`exitcond-r1.py` 등)는 리뷰어가 만든 것이고 이번 수정에서 바꾸지 않았다. (팀장 · 10:28 · prose-editor 착수 뒤 이 절만 덧붙임)
