# slide-composer packet (2026-10-20 · 팀장 · 09:46 `date` 뒤)

## 목표
- v09 덱 `docs/60_본선준비/10_발표자료/17_발표슬라이드_v09_20261020/index.html`(지금은 v08 사본 · sha256 `e9fa1e53…4493a`)을 확정된 발표노트 v07 과 동원님 결정에 맞춰 고친다.
- 기준 서비스 판: main `2f38609`(src = develop `2c46005`). 화면 사실은 `service-facts-develop-a1e1f3a.md`(끝의 「정정」 절 포함).

## 읽을 것
1. 발표노트 v07(확정): `docs/60_본선준비/10_발표자료/16_발표평가_10분피치_초안_v07_20261020.md`
2. 종합과 결정: `team-reports/2026-10-20-slides-v09/r0-synthesis.md`(3절 고칠 것 · 6절 동원님 결정)
3. r0 반환물 넷(같은 폴더): `deck-reviewer-r0.md`(2절 대조표의 수정안 열) · `prose-editor-r0.md`(L · D 표) · `slide-designer-r0.md`(2절 배치 · 4절 P1/P2) · `story-architect-r0.md`
4. 공통 packet: `r0-packet-common.md`(금지표현 · 함정)

## 자산 (팀장이 준비 · 모두 2배율 캡처 · 개인정보 줄과 「코드 판」 줄 없음을 팀장이 눈으로 확인)
폴더: `/private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/ecae8f91-ad18-45ef-8441-2fbb81acf176/scratchpad/assets/`

| 파일 | 원본 px | 내용 | 쓸 곳 |
|---|---|---|---|
| `s4-pills-1.png` | 598×66 | 1-1 유형·목적 · 1-2 물건 URL · 1-3 분석 결과(활성) | 4장(넣을 자리가 있으면) |
| `s4-pills-2.png` | 994×66 | 2-1 공고 확인 · 2-2 🔒 입찰 전 준비 · 2-3 🔒 입찰 참여 · 2-4 ⏳ 낙찰 후 준비 | 4장(넣을 자리가 있으면) |
| `s5-docs-proxy.png` | 620×288 | 공동입찰인가요? 아니오 · 대리입찰인가요? 예 · 「0/5개 서류 준비 완료」 | 5장 |
| `s5-coach-notice.png` | 1596×138 | 「공고 원문 기반 답변」 · 「해당 공고의 입찰 마감 일시는 2026년 10월 29일 15:00입니다.」 | 5장 |
| `s5-coach-boundary-top.png` | 1596×300 | 「이 질문에는 답하지 않았습니다. …」 · 「온비드 안내 기준 용어 설명」 · 낙찰 설명 앞부분 | 5장 |
| `s5-coach-boundary.png` | 1596×342 | 위 전체(출처 줄 포함) | 5장 대안 |
| `font/Pretendard-subset.woff2` | 449,996 B | Pretendard 1.3.9 가변 글꼴 부분집합(KS X 1001 한글 2,350자 + 덱·노트 글자) · OFL | 덱 전체 |
| `font/LICENSE.txt` | | OFL 원문 | 제작 기록에 출처 표기 |

- 그림 표시 폭은 원본 px 의 0.5~1.0 배로 둔다(2배율 원본이라 CSS 1배 이상으로 보인다 · slide-designer 종료 조건). 원본보다 크게 늘리지 않는다.
- 질문 문장은 그림이 아니라 덱 글자로 그림 위에 둔다(slide-designer 2절).

## 고칠 것 (장별)
- 전체
  - Pretendard 를 `@font-face { font-family: "Pretendard"; src: url(data:font/woff2;base64,…) format("woff2"); font-weight: 45 920; }` 로 index.html 안에 넣고 글꼴 목록 맨 앞에 둔다. 단일 파일을 유지한다.
  - `.slide { word-break: keep-all; }` 를 넣는다. 링크 글자(`.link-url` 등)의 `break-all` 은 그대로 둔다.
  - 장 제목은 하나도 바꾸지 않는다(동원님 결정 「그대로 둠」).
- 1~3장: 본문 글자는 바꾸지 않는다. 전체 CSS(글꼴 · keep-all) 때문에 줄바꿈이 바뀌면 그 장의 `<br>` 만 조정한다.
- 4장(해결)
  - 단계 번호를 화면처럼 1-1~1-3 · 2-1~2-4 로.
  - 1-3 설명 「판정 · 핵심 정보 · 확인 사항 · 온비드 연결, 네 묶음」.
  - 준비 보드 머리 「준비 보드 · 4단계 (2-2·2-3은 앞 단계를 마치면 열림)」 쪽으로(prose L3).
  - 2-1 · 2-2 · 2-3 · 2-4 설명은 노트 v07 2절 「근거 2」를 줄여 한 줄씩. 2-2 에서 「만」 · 「조건화」를 쓰지 않는다.
  - AI 코치 상자: 표지 줄을 실측 세 표지 「공고 원문 기반 답변 · 온비드 규칙 기반 안내 · 온비드 안내 기준 용어 설명」으로. 안전 경계 문장은 prose L9 수정안.
  - 「절차 문제(1겹)는 … 받습니다」는 prose D1 수정안.
  - 단계 띠 그림(`s4-pills-*`)은 세로 공간이 되면 넣는다. 넘침이 생기면 넣지 않고 그 사실을 반환에 적는다.
- 5장(데모 시연)
  - 제목 「데모 시연」과 라이브 링크 글자는 그대로 둔다(동원님: 같은 주소에 main 배포).
  - 시연 단계는 노트 v07 3절 「화면에 올릴 시연 단계」 4줄.
  - v08 스크린샷 2장과 가짜 브라우저 창 점 · 그림자 · 고정 높이 프레임을 없애고, 위 자산 셋(서류 변화 · 공고 사실 답 · 거절 답)으로 바꾼다. 캡션은 화면 이름 그대로(「2-2 입찰 전 준비」 · 「2-3 입찰 참여 · AI 코치」).
- 6장(시스템 구조 · 제목 그대로)
  - 노트 v07 4절대로 3층 도식 내용을 바꾼다.
    - 외부 데이터: 「온비드 공개 페이지」(공고·물건 상세와 첨부 공고문 · 기본 경로) · 「물건상세 화면 데이터」(정적 HTML 에 없는 회차별 값) · 「공공데이터포털 API」(인증키가 있을 때 빈 값을 채우는 보조 경로)
    - 화살표 이름표: 「원문 우선 · 빈 값 보충」 쪽
    - 서버: 분석 서버(첨부 공고문 HWP·PDF 읽기 포함) · AI 계층(근거: 공고 사실 · 준비 보드 · 온비드 안내 설명 / 자주 묻는 질문은 모델 없이 온비드 규칙 안내). 「/api/ask」 경로 글자와 「Gemini/Vertex」는 쓰지 않고 「AI 모델」.
    - 클라이언트: 「브라우저 단일 페이지 앱」 · 「관심 공고 · 체크 진행을 브라우저에 저장(로그인 없음)」. 「SPA」 · 「내 보관함」 · 「LLM」 · 「파싱」 · 「내부 JSON」 · 「교차」를 쓰지 않는다.
  - 차별점 띠: 근거 표지 문장(노트 v07 4절 후보 · 「답마다」 금지).
- 7장(사업화 · 제목 그대로 · 수치 그대로)
  - 「SOM · 초기 3년 목표」 → 「SOM · 시장침투율 1% 기준 연 매출」
  - 「SAM · 유효 시장」 → 「SAM · 시장침투율 3% 목표 연 매출」 · 값 표기 「연 매출 약 6억 7,200만 원 …」(prose D15)
  - 「건별 리포트」 → 「3건 이용권」
  - 각주에 기준 시점: 「온비드 월평균 입찰참가자 약 14,000명(2023~2025 월평균)」 · 「등기부등본 700~1,000원(인터넷등기소 열람·발급 수수료 · 2026년 기준)」. 「응찰인 10배」는 prose D14 수정안. 「재설계」 · 「재계산」은 prose D13.
  - 「등기부등본 발급 비용과 비슷한 수준」 문구는 동원님이 지정한 표현이라 그대로 둔다(`docs/60_본선준비/23_사업화_재설계_20261016/notes.md` 18행).
- 8장(향후 계획 · 제목과 두 단계 그대로)
  - 백로그 「내 보관함」 줄 → prose L18 수정안. 「그 외 백로그」 → 「그 밖의 개선 과제」.
- 9장: 바꾸지 않는다.

## 금지
- 수정 가능 파일: v09 `index.html` 과 새 제작 기록 `17_발표슬라이드_v09_20261020/notes.md`(v08 `notes.md` 형식을 참고해 새로 씀)뿐이다.
- v08 폴더 · 노트 v06/v07 · 코드 · 다른 문서는 고치지 않는다. 브랜치를 바꾸지 않는다. 앱을 기동하지 않는다.
- 금지표현(공통 packet) · 엠대시 · 겹화살괄호 0.
- 개인 작업 폴더: `/private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/ecae8f91-ad18-45ef-8441-2fbb81acf176/scratchpad/role-composer/` 만 쓴다.

## 검증 (반환 전에 직접 실행하고 출력 줄을 붙인다)
1. `python3 ~/.claude/scripts/slide-render.py <덱> --out role-composer/render` 로 9장 전부 렌더하고 PNG 를 눈으로 본다.
2. `python3 ~/.claude/scripts/slide-measure.py <덱> --print`: 화면 · 인쇄 모두 겹침 · 고아 줄 · 장 벗어남 · 상자 이탈 0.
3. slide-designer 종료 조건: `python3 /private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/ecae8f91-ad18-45ef-8441-2fbb81acf176/scratchpad/role-design/final-check.py <덱>` → PASS exit 0.
4. deck-reviewer 종료 조건: `python3 -I /private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/ecae8f91-ad18-45ef-8441-2fbb81acf176/scratchpad/role-deck/exitcond.py <덱>` → 0 · exit 0.
5. prose-editor 종료 조건: `prose-editor-r0.md` 6절의 `grep -cE …` → 0. 같은 절의 `grep -c '판정 · 핵심 정보'` 는 2 이상(4장 · 5장).
6. story-architect 종료 조건: `grep -cE '교차 대조한 뒤에만|1~3단계 순차|Gemini/Vertex' <덱>` → 0.
7. 금지표현 · 엠대시 검사: `python3 -I /private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/ecae8f91-ad18-45ef-8441-2fbb81acf176/scratchpad/role-deck/forbid.py <덱>`.

## 시간 예산
- 40분. 못 끝낸 것은 「미완」으로 적고 반환한다.

## 반환 형식(채팅 · 팀장이 파일로 옮김)
1. 착수 · 반환 시각(`date`)과 반환 시 덱 sha256
2. 장별로 바꾼 것(전 → 후)과 바꾸지 않은 것
3. 자산 배치 표(파일 · 장 · 표시 크기 · 표시 폭/원본 폭)
4. 검증 1~7 의 명령과 출력 줄
5. 넣지 못한 것과 이유 · 팀장 판단이 필요한 것
