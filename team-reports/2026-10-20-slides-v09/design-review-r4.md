<!-- slide-designer 다듬기 4차 반환 (2026-10-20 10:27 반환) · 팀장이 서브에이전트 최종 반환 원문을 그대로 옮김(전사 스크립트) -->

두 곳 모두 고쳤고, 장 벗어남 없이 검증 1~5가 통과했습니다. 덱 sha256 은 착수 때 `e0dd7290f25f991aeab451f0c05e66e62f12f041f71cfae6b776e8942ce894fc`, 반환 때 `e97b139a8ed99b497798b6505d9e4199b35afc0a749f98ac392b465a1930c93b` 입니다.

## 시각
- 착수: 10:25:49 KST. 해시는 지시하신 값과 같았습니다.
- 반환: 10:27:18 KST
- 수정한 파일은 v09 `index.html` 하나입니다. `git status --short` 는 9줄로 전과 같습니다.

## 바꾼 것
- **4장 머리 띠**: 「단계별 준비 보드가,」 뒤에 `<br>` 하나를 넣었습니다. 글자는 바꾸지 않았습니다.
  - 지금은 첫 줄이 「…1겹(절차가 낯섦)은 단계별 준비 보드가,」, 둘째 줄이 「2겹(챙길 것을 가려내기 어려움)은 공고 분석 결과가 돕습니다.」입니다.
  - 띠는 두 줄 그대로라 높이가 같습니다.
- **5장 「시연 순서」 위 간격**: `.demo-top-row` 의 `margin-bottom` 을 10px 에서 16px 로 바꿨습니다.
  - 기준은 다른 장 소제목 위 간격 16px 입니다. 7장은 `.biz-row1` 아래, 4장은 `.solve-top` 아래가 16px 입니다.
  - 이 클래스는 5장에서만 씁니다(HTML 에서 1회).
  - 그 대신 5장 아래 여백이 6px 줄었습니다. 렌더에서 캡션 아래 끝(slide 661)이 본문 끝(666)까지 5px 남습니다.
  - 꼬리말과는 약 20px 떨어져 있습니다. 겹침과 장 벗어남은 0건입니다.

## 검증 (덱 `e97b139a…`)
1. `slide-render.py` 출력: 「렌더 9장 → render4 (덱 sha256 e97b139a8ed9 · Google Chrome 155.0.8059.85 · 1600x900)」
   - 4 · 5장은 원래 크기로 눈으로 봤습니다.
   - 착수 판 렌더와 비교하면 4 · 5장만 다르고 나머지 7장은 PNG 해시가 같습니다.
2. `slide-measure.py --print` (exit 0)
   - 「화면 1600x900: 겹침 0건 · 고아 줄 0건 · SVG 작은 글자 0건 · 장 벗어남 0건 · 상자 이탈 0건」
   - 「인쇄(@media print→all): 겹침 0건 · 고아 줄 0건 · SVG 작은 글자 0건 · 장 벗어남 0건 · 상자 이탈 0건」
3. `final-check.py` (exit 0)
   - 「모수 174 · 대비 미달 0 · 보류 장 미달 0 · Q&A 변형 0」
   - 「낱말 중간 줄바꿈 0」
   - 「그림 3 · 축척 벗어남 0」
   - 「PASS」
4. `exitcond.py`: `0 []`, exit 0
5. `exitcond-r1.py`: `r0 0 [] · r1 0 []`, exit 0

## 파일
- 덱: `/Users/user/Documents/Dev/Hometest_op/docs/60_본선준비/10_발표자료/17_발표슬라이드_v09_20261020/index.html`
- 수정 후 렌더: `/private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/ecae8f91-ad18-45ef-8441-2fbb81acf176/scratchpad/role-design2/render4/`
- 수정 전 렌더: `/private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/ecae8f91-ad18-45ef-8441-2fbb81acf176/scratchpad/role-design2/r4b/`
- 착수 사본: `/private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/ecae8f91-ad18-45ef-8441-2fbb81acf176/scratchpad/role-design2/before4.html`
- 편집 스크립트: `/private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/ecae8f91-ad18-45ef-8441-2fbb81acf176/scratchpad/role-design2/edit4.py`
