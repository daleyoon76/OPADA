# visual-designer 반환물 — 준비 보드 시각 품질 진단 (2026-09-22)

- 조사자: visual-designer (읽기 전용, 코드 미수정)
- 대상: `src/app.js`, `src/styles.css` (2026-09-22 12시 기준 워킹트리)
- 참고: `team-reports/2026-09-22-code-completeness-ai-coach/architecture-audit.md`,
  `.../failure-mode-round-parsing.md` — 특히 실패모드 보고서 S3(추출 실패 문구와 정상값이 같은 amber 톤)는
  이번 진단의 색상 제안과 직접 겹친다.
- 스크린샷 확인: `screenshots/validation/20_doc-checklist-extracted.png`(준비 보드 화면) 1장만 저장소에 있었다.
  "공고 가져오기" 탭(`.preview-grid`가 실제로 보이는 화면)은 스크린샷이 없어 **코드 판독 기반**이고,
  실제 렌더 확인은 아래 "스크린샷 검증 필요" 항목으로 남긴다.
- 브랜드 색상 팔레트(`--ink`/`--muted`/`--green`/`--blue`/`--amber`/`--red`/`--soft-*`)와 기본 폰트(`--font-sans`)는
  건드리지 않는 제안만 담았다.

---

## 1. 라벨-값 쌍이 쓰이는 구역 전수 조사

| 구역 | 위치(app.js) | 마크업 패턴 | 라벨 스타일 | 값 스타일 | 컨테이너 배경 |
|---|---|---|---|---|---|
| 공고 미리보기 그리드(`.preview-grid`) | 911~916, "유형" 행이 사용자가 지적한 "공고유형" 자리 | `<div><b>라벨</b><strong>값</strong></div>`, 2열 그리드 | `b`, 12px, `--muted`, margin-bottom 3px | `strong`, 14px, line-height 1.35, 색상 미지정(상속 `--ink`) | 투명(부모 패널 배경 그대로) |
| AI 코치 "탐지한 내용"(`.coach-facts`) | 946~948 | 동일 `<div><b>·<strong>` 패턴 | 동일(12px `--muted`) | `strong`, 14px, `font-weight:700` 명시, 색 `--ink` 명시 | **soft-amber 배경 + amber 테두리** |
| AI 코치 "미해결 점검"(`.coach-check`, static 안내) | 949~957 | `<article><strong>제목</strong><p>사유</p><em>행동</em></article>` | 제목이 라벨 역할(14px, bold) | 본문 `p` 12px `--muted`, `em` 12px `--green-dark` bold | **soft-neutral 배경** |
| 공고 요약 사이드바(`.fact-row`, "공고번호"·"공고기관"·"입찰방식" 등) | app.js:1540~1560(`quick-facts`), 1428~1440(입력 실패 시 대체) | `<div class="fact-row"><span>라벨</span><strong>값</strong></div>`, 세로 스택 | `span`, 12px, `--muted` | `strong`, 14px, 색 미지정 | 없음(투명) |
| 상단 상태 카드(`.status-card`, "다음 액션"·"진행률") | 1476~1491, 1410~1420 | `<div><b>라벨</b><strong>값</strong></div>` | `b`, 12px `--muted`, margin-bottom **5px** | `strong`, **16px**(다른 구역보다 큼) | 흰 배경 + 테두리 |
| 작업 목록 항목(`.task-item` 제목/설명) | 1499~1507 | `<strong>제목</strong><em>설명</em>`, **값이 위, 라벨 격 설명이 아래**(다른 구역과 순서 반대) | 없음(제목이 곧 1차 정보) | `strong` 16px / `em` 12px `--muted` | 흰 배경 |
| 서류 체크리스트 항목(`.doc-group li`) | 1180~1191 | `<strong>서류명</strong>` + `.doc-chip`(구분/부수/유효기간/제출방법/기한을 한 줄 문자열로 합쳐 칩화) | 칩 안에 라벨 접두어가 텍스트로 합쳐짐("제출 우편" 등, 별도 라벨 요소 없음) | 11px, `--muted`, pill | soft-neutral pill |
| 문서 출처 안내(`.doc-source-notice`, `.doc-head`) | 1145~1154, 1202~1207 | 배지 + `<strong>프로필 라벨</strong>` + `<p>` 설명 | `strong` 자체가 12px `--muted` 600(=사실상 라벨) | 없음(설명은 본문 `p`) | 없음 |
| 공고문 항목(`notice-outline`, `.compact-row`) | 1253~1266 | `<summary><span>항목</span><strong>제목</strong></summary>` 가로 그리드(48px+1fr) | `span` "항목"(고정 문자열, 필드명이 아님), 12px bold `--muted` | `strong` 14px | 흰 배경 |
| 용어 안내(`glossary`) | 1323~1331 | `<strong>용어</strong><p>뜻</p>` | 없음(용어=값처럼 큼) | `p` 기본 |없음 |
| 공고 상단 요약 문장(report-hero) | 1458 | `<p>${assetType} ${dispositionLabel} / ${userType} / ${focus}</p>` — **라벨 요소 자체가 없다** | 없음 | 없음, 그냥 본문 텍스트 | 없음 |

**핵심 관측**: 같은 "라벨-값" 개념이 최소 **5가지 서로 다른 마크업/스타일 조합**으로 구현돼 있다
(세로 스택 12/14px, 세로 스택 12/16px, 가로 그리드 48px+1fr, 제목-설명 역순 16/12px, 라벨 없는 평문).
이것이 사용자가 지적한 3번 "UI 객체가 중구난방"의 구체적 근거다.

---

## 2. 구역별 차이 상세 — 통일 방법

- **폰트 크기**: 값 크기가 14px(`preview-grid`/`coach-facts`/`fact-row`)와 16px(`status-card`/`task-item` 제목)로 이원화돼 있다.
  이유가 있는 차이(카드형 헤드라인 값은 16px, 인라인 사실 값은 14px)로 보이지만 지금은 문서화 없이 섞여 있어
  "왜 이 값만 크지?"라는 인상을 준다.
  → **제안**: 두 단계를 의도적으로 이름 붙인다. `--field-value-size: 14px`(사실 나열), `--field-headline-size: 16px`
  (그 화면에서 지금 가장 중요한 값 1~2개, 예: 다음 액션·진행률·작업 제목)만 쓰기로 규칙화.
- **라벨 색·크기는 이미 통일돼 있다**: `--muted`/12px는 `preview-grid`·`coach-facts`·`status-card`·`fact-row`가 전부 같다.
  깨진 것은 라벨이 아니라 **컨테이너·정렬 방향**이다.
- **정렬 방향 불일치**: `task-item`만 "값(제목)이 위, 부연설명이 아래"로 다른 모든 구역(라벨이 위, 값이 아래)과 반대다.
  `task.title`은 원래 "작업 이름"이라 헤드라인으로 취급하는 게 맞지만, 그 아래 `task.action`(`<em>`)은 사실상
  "이 작업에서 확인할 값"에 가까워 다른 구역의 "라벨" 역할과 헷갈릴 수 있다. 구조 변경(재설계)은 이번 범위 밖이므로
  스타일만 맞추자면 `task-check em`의 색/크기(12px `--muted`)는 이미 다른 라벨과 톤이 같아 큰 위화감은 없다.
- **여백 불일치**: 라벨-값 사이 여백이 3px(`preview-grid`/`coach-facts`)와 5px(`status-card`)로 다르다. 사소하지만
  같은 리듬을 쓰면 스캔이 편해진다. → 3px로 통일 제안(더 촘촘한 쪽에 맞춤, 라벨-값 결속감이 더 강함).
- **공통 템플릿 제안** (신규 클래스, 기존 클래스 대체가 아니라 새 컴포넌트로 도입 후 점진 적용 권장):
  ```
  .field-row        { display:block; }             /* 또는 그리드 컨테이너가 감싸는 한 칸 */
  .field-row .field-label { display:block; color:var(--muted); font-size:12px; font-weight:700; margin-bottom:3px; }
  .field-row .field-value { display:block; font-size:14px; line-height:1.35; color:var(--ink); font-weight:700; }
  .field-row.is-headline .field-value { font-size:16px; }
  ```
  `preview-grid div`, `coach-facts div`, `fact-row`, `status-card`를 이 세 클래스 조합으로 재작성하면
  마크업이 통일되고, 값 크기 차이는 `.is-headline` 한 modifier로 명시적 예외가 된다.
  (코드 수정은 이번 역할 범위 밖 — 구현자에게 넘길 스펙으로만 남긴다.)

---

## 3. static(고정 가이드) vs variable(공고별 값) 색 구분 제안

**정확한 대응관계부터 확인**: 사용자가 예로 든 "내 업종으로 실제 사용 가능한지"는 `src/server.py:1404`의
`unresolvedChecks[].title`이다 — `is_sale` 분기에 따라 딱 두 가지 문구 세트 중 하나가 고정 출력되는
**정적 안내 문구**이고(공고 내용과 무관, 매각/임대 여부로만 갈림), `renderCoachPanel`의 `.coach-check` 카드로 렌더된다.
반면 "공고유형 국유재산/임대"는 `.preview-grid`의 "유형" 행(`assetType`/`dispositionLabel`, 공고마다 실제로 바뀌는 값)이다.
**즉 이 둘은 같은 라벨-값 쌍의 두 파트가 아니라, 화면의 서로 다른 두 구역이다.** 사용자가 원하는 것은
"이 화면 전체에서 어디가 항상 같은 안내이고 어디가 이 공고만의 실제 값인지"를 색으로 구분하는 것으로 읽힌다.

**좋은 소식**: 이 구분은 이미 부분적으로 코드에 존재한다.
- `.coach-check`(정적 안내, static) — `background: var(--soft-neutral)` 이미 사용 중.
- `.coach-facts`(공고별 추출값, variable) — `background: var(--soft-amber)` 이미 사용 중.

**문제는 이 구분이 AI 코치 패널 안에서만 적용되고, 그 밖(미리보기 그리드, 공고 요약 사이드바, 상태 카드,
서류 칩)에는 전혀 적용되지 않는다는 점**이다. 그 결과 화면 대부분에서 static과 variable이 똑같은 무색(기본 `--ink`)
텍스트로 보인다.

**제안 (기존 팔레트 안에서만)**:
1. **variable(공고별 값)** — 모든 라벨-값 쌍(`preview-grid`, `fact-row`, `status-card`의 값, `doc-chip`)에
   `.coach-facts`가 이미 쓰는 배경/테두리 톤(`--soft-amber` 계열)을 **약하게** 확장한다. 단, 카드 전체를 amber로
   채우면 화면 전체가 경고색 범벅이 되므로(과한 카드 남용 위험), **라벨 왼쪽에 2px 폭의 `--amber` 좌측 보더 하나만**
   붙이는 절제된 방식을 권한다. 예: `.field-row.is-fact { border-left: 2px solid var(--amber); padding-left: 8px; }`.
   이렇게 하면 "이 값은 이 공고에서 읽은 것"이라는 신호를 새 색 추가 없이 준다.
2. **static(고정 안내)** — `.coach-check`가 이미 쓰는 `--soft-neutral` 배경을 그대로 유지하고,
   이 톤을 "공고와 무관한 일반 안내" 전용 배경으로 **문서화**한다(예: 상단 고지 배너, 서류 발급처 기본 문구,
   `notice-outline`의 안내 문장, `glossary` 설명). 새 스타일 작성은 필요 없다 — 이미 쓰는 색을 "이런 뜻"이라고
   이름 붙이기만 하면 된다.
3. **주의 — 실패모드 보고서 S3와의 충돌 지점**: 위 1번을 그대로 적용하면 "추출 성공값"과 "추출 실패 대체 문구"
   (예: "입찰기간 원문 확인")가 **똑같은 amber 좌측 보더**를 받게 된다. 이는 팀장이 이미 결정한
   "추출 실패 시 문구를 실제 값과 시각적으로 구분되게 표시"와 정면으로 부딪힌다.
   → **실패 대체 문구는 이 amber 강조에서 제외**하고 대신 `--muted` 색 + 기울임 없는 보통 굵기(현재 `strong`이
   임의로 bold를 상속하는 것을 `font-weight:400`으로 낮춤)로 "이건 값이 아니라 안내"라는 3번째 톤을 쓰는 것을
   권장한다. 정확한 문구 자체는 다른 역할(카피) 소관이므로 여기서는 "색·굵기 처리 방향"만 제안한다.

---

## 4. "공고유형" 류 라벨-값 위계를 명확히 하는 구체 스타일

현재 `.preview-grid`(및 동형인 `.coach-facts`, `.fact-row`)의 문제:
- 라벨(`b`, 12px `--muted`)과 값(`strong`, 14px, 색 미지정)의 **크기 차이가 2px뿐**이라 계층감이 약하다.
- 값 자체가 `${assetType} / ${dispositionLabel}`처럼 **서로 다른 두 사실을 슬래시 하나로 이어 붙인 한 덩어리
  문자열**이라, "이게 두 값인지 한 값인지" 읽는 사람이 매번 파싱해야 한다.

**제안**:
1. 값 크기를 14px → **15px**로, `font-weight`를 상속에 맡기지 말고 **명시적으로 700**으로 고정한다(현재는 브라우저
   기본 bold에 의존 — 폰트가 `Outfit`/`Pretendard`로 폴백되는 상황에서 `strong`의 실제 굵기가 폰트마다 미묘하게
   달라질 수 있다).
2. 라벨은 12px 유지하되 `letter-spacing: 0.01em`을 추가해 라벨이 "캡션"처럼 더 작고 가벼워 보이게 한다(크기를
   더 줄이면 가독성이 떨어지므로 크기 대신 자간으로 위계 차이를 보강).
3. 값 내부의 복합 사실(`assetType`/`dispositionLabel`)은 슬래시 대신 **가운데 점(`·`) + 8px 여백**으로 분리하고,
   `dispositionLabel`(공고유형)을 시각적 1순위로 둔다면 그 부분만 `color: var(--ink)`, 나머지(`assetType`)는
   `color: var(--muted)`로 톤을 낮추는 것도 검토 가능하다(단, 이 경우 어느 쪽이 "제목"이고 어느 쪽이 "보조 정보"인지는
   제품 판단이 필요 — 이번 역할은 처리 방법만 제안한다).
4. 위 3번의 대안으로, 값을 한 줄 텍스트 대신 **두 개의 작은 칩**(`.doc-chip`과 같은 pill 스타일 재사용)으로 쪼개는
   방법도 있다: `<span class="value-chip">국유재산</span><span class="value-chip">임대</span>`. 기존 `.doc-chip`
   pill 스타일을 재사용하면 새 CSS 없이 "값이 여러 개"라는 사실이 형태로도 드러난다.

---

## 5. 발표자료 품질 게이트 결과

이 항목은 슬라이드/PPT 전용 게이트로, 본 화면(웹 앱)에는 해당하지 않는다. **N/A로 표시한다.**
다만 게이트의 취지(같은 역할 반복 컴포넌트의 텍스트 크기·여백 통일)는 §1~2에서 웹 화면 버전으로 그대로 적용했다.

---

## 6. 우선순위

- **P0** — variable(공고별 값) 구역이 화면 전체에서 5가지 스타일로 흩어져 있다(§1). 통일 템플릿(§2)을 만들지 않으면
  이후 카피/상태 필드가 추가될 때마다(예: `confirmedFacts.status`, architecture-audit.md 제안) 또 새로운 6번째
  변종이 생긴다. 구현 전에 스펙을 먼저 고정할 것을 권한다.
- **P0** — static/variable 색 구분(§3)은 이미 존재하는 `--soft-neutral`/`--soft-amber` 패턴을 코치 패널 밖으로
  확장하기만 하면 되므로 비용 대비 효과가 크다. 단, 실패 대체 문구와의 충돌(§3-3)을 반드시 함께 처리해야 한다 —
  이 둘을 분리해서 순서대로 넣으면(예: variable 강조 먼저, 실패 톤 나중) 중간 상태에서 "실패 문구가 성공값처럼
  강조된 화면"이 잠깐 배포될 위험이 있다.
- **P1** — "공고유형" 라벨-값 위계(§4)는 사용자가 명시적으로 지적한 항목이라 우선순위가 높지만, 구조 변경 없이
  스타일만으로 상당 부분 해결 가능하다.
- **P2** — `notice-outline`의 "항목"이라는 고정 라벨(§1)은 실제 필드명을 담지 못해 정보성이 낮다. 급하지 않다.

---

## 7. 스크린샷 검증 필요 항목

- `.preview-grid`가 실제로 보이는 "공고 가져오기"/분석 결과 탭 화면 캡처 — 이번 조사는 코드 판독만으로 "유형"
  행의 실제 렌더 간격·줄바꿈 여부를 추정했다. **미확인**.
- `.coach-facts`(AI가 탐지한 내용) 패널에서 추출 성공값과 "원문 확인" 실패 대체 문구가 실제로 같은 amber 톤으로
  나란히 보이는지 — 실패모드 보고서 S3의 반증 관측과 동일한 요청이며, idx1 URL로 재현 가능하다고 그쪽 보고서에
  적혀 있다.
- (해결됨) `.fact-row` 렌더 위치는 app.js:1540~1560으로 확인했다 — 스크린샷의 "공고번호"·"공고기관" 행과
  일치한다. 남은 미확인은 모바일 1열 전환 시 줄바꿈뿐(아래 항목).
- 모바일 폭(`@media max-width:900px`)에서 `.preview-grid`/`.coach-facts`가 1열로 바뀔 때 §4 제안(칩 분리 등)이
  줄바꿈과 충돌하지 않는지 — responsive-tester 영역으로 넘긴다.
