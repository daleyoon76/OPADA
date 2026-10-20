<!-- slide-designer 다듬기 2차 반환 (2026-10-20 10:09 반환) · 팀장이 서브에이전트 최종 반환 원문을 그대로 옮김(전사 스크립트) -->

5장 오른쪽 그림 둘을 w640 판으로 바꿨습니다. 아래 그림은 `-def` 판이 장에 들어가지 않아 `-head` 판을 넣었습니다. 바뀐 렌더는 5장 하나이고, 검증 1~5는 모두 통과했습니다.

## 시각과 해시
- 착수: 10:08:10 KST. 덱 sha256 `e886546995bd39831c0c12bcbd1e14be8f2e848baaea92fb44d04c97329c3cfa`로, 지시하신 값과 같습니다.
- 반환: 10:09:05 KST. 덱 sha256 `d73bb9774d013f69ea2bdc116e164964396245ea8ffa29abcd6871ec6616d6fb`
- 수정한 파일은 v09 `index.html` 하나입니다. `git status --short` 는 9줄로 전과 같습니다.

## 바꾼 것 (5장만)
- **오른쪽 위**: `s5-coach-notice-w640.png` 로 바꿨습니다. 표시 크기는 786×79 이고, alt 는 내용이 같아서 그대로 두었습니다.
- **오른쪽 아래**: `s5-coach-boundary-head-w640.png` 로 바꿨습니다. 표시 크기는 786×72 입니다.
  - alt 는 「이 질문에는 답하지 않았고 질문에 나온 용어의 온비드 설명만 보여 드린다는 안내와 온비드 안내 기준 용어 설명 표지」로 바꿨습니다.
- **`-def` 를 넣지 않은 이유**: 시험 사본에 넣어 재 보니 장 벗어남이 1건 나왔습니다 [관측].
  - 측정 출력은 `[5, "B:실제 화면 · 2-3 입찰", "장 아래로 나감", 8]` 입니다. 캡션이 장 아래로 8px 나갑니다.
  - `-def` 는 높이가 183px 이고 `-head` 보다 111px 깁니다.
- CSS 는 바꾸지 않았습니다. 틀 · 열 폭 · 간격은 앞 라운드 값 그대로입니다.

## 그림 판독 계산

| 그림 | 원본 | 표시 폭 | 표시/원본 | 표시 배율 | 앱 12px 글자 |
|---|---|---|---|---|---|
| notice-w640 | 1132×114 | 786 | 0.694 | 1.39 | 12.5pt |
| boundary-head-w640 | 1132×104 | 786 | 0.694 | 1.39 | 12.5pt |
| docs-proxy(그대로) | 620×288 | 310 | 0.500 | 1.00 | 9.0~9.75pt |

- 새 그림의 글자 높이는 21~22px 로, 앞 판의 12px 글자와 같았습니다 [관측]. 그래서 앱 글자 크기는 그대로 12px 로 계산했습니다.
- 개인정보 · 출처 줄 · 「코드 판」 줄은 그림에 없었습니다(눈으로 확인).

## 검증 1~5 (덱 `d73bb977…`)
1. `slide-render.py` 출력: 「렌더 9장 → render2 (덱 sha256 d73bb9774d01 · Google Chrome 155.0.8059.85 · 1600x900)」
   - 5장은 원래 크기로 봤습니다.
   - 나머지 8장은 직전 렌더와 PNG 해시가 같습니다(5장만 다름).
2. `slide-measure.py --print` (exit 0)
   - 「화면 1600x900: 겹침 0건 · 고아 줄 0건 · SVG 작은 글자 0건 · 장 벗어남 0건 · 상자 이탈 0건」
   - 「인쇄(@media print→all): 겹침 0건 · 고아 줄 0건 · SVG 작은 글자 0건 · 장 벗어남 0건 · 상자 이탈 0건」
3. `final-check.py` (exit 0)
   - 「모수 173 · 대비 미달 0 · 보류 장 미달 0 · Q&A 변형 0」
   - 「낱말 중간 줄바꿈 0」
   - 「그림 3 · 축척 벗어남 0」
   - 「PASS」
4. `exitcond.py`: `0 []`, exit 0
5. 장별 14pt 미만 요소 수: 1:5/8 · 2:3/14 · 3:5/17 · 4:33/36 · 5:20/23 · 6:24/25 · 7:27/28 · 8:9/16 · 9:4/6
   - 직전과 같습니다. 그림 속 글자는 이 probe 가 세지 않습니다.

## 팀장 판단이 필요한 것
- **왼쪽 서류 그림만 9pt 로 남았습니다.** 같은 줄의 코치 그림은 12.5pt 라 두 그림의 글자 크기가 눈에 띄게 다릅니다.
  - 서류 그림도 좁은 폭으로 다시 찍으면 맞출 수 있습니다 [추론].
  - 열 폭이 310 에 묶여 있으므로, 원본 CSS 폭이 약 223px 이하여야 같은 1.39배가 됩니다.
- **5장 아래에 세로 약 50px 가 비어 있습니다.** `-def` 를 넣으려면 약 60px 를 더 만들어야 해서 쓰지 못했습니다.
  - 질문 글자를 24px 에서 줄이면 공간이 생기지만, 앞 라운드에서 올린 것을 되돌리는 일이라 하지 않았습니다.

## 파일
- 덱: `/Users/user/Documents/Dev/Hometest_op/docs/60_본선준비/10_발표자료/17_발표슬라이드_v09_20261020/index.html`
- 이번 렌더: `/private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/ecae8f91-ad18-45ef-8441-2fbb81acf176/scratchpad/role-design2/render2/`
- 직전 렌더: `/private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/ecae8f91-ad18-45ef-8441-2fbb81acf176/scratchpad/role-design2/render/`
- 착수 사본: `/private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/ecae8f91-ad18-45ef-8441-2fbb81acf176/scratchpad/role-design2/before2.html`
- `-def` 시험 사본: `/private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/ecae8f91-ad18-45ef-8441-2fbb81acf176/scratchpad/role-design2/try-def.html`
- 편집 스크립트: `/private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/ecae8f91-ad18-45ef-8441-2fbb81acf176/scratchpad/role-design2/edit2.py`
