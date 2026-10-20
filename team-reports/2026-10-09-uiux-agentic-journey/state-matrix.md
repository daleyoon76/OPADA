# OPADA 준비 보드 — 단계 잠금 UI 상태 매트릭스

> 반환자: ux-scribe (3팀 UIUX품질팀). 이번 세션(버그 수정·검증) 산출물 정리.
> 범위: "공매 절차 순차 안내" 단계 잠금의 요소 × 상태 조합. 기능 설계 자체는 `ux-audit.md` §⑴·§⑸, 시각 설계는 `visual-audit.md` §⑵를 참고.
> 코드 근거: `src/app.js`(`PREP_STAGES` 442행, `getPrepStageStatus` 866행, `renderDocChecklist` 1267행, `renderTaskItem` 1554행, `renderPrepStageStepper` 1504행, `renderStageHeading` 1527행), `src/styles.css`(1430행대).

## 전제: 단계 구성

| 단계 | task id | 포함 요소 |
|---|---|---|
| 1단계 · 공고 확인 | `notice-type`, `bid-period` | 메인 task 체크박스 2개 |
| 2단계 · 서류 준비 | `documents` | 메인 task 체크박스 1개 + 서류 체크리스트 하위 체크박스(`data-doc-name`) 8~16종 |
| 3단계 · 입찰 참여 | `price`, `agency` | 메인 task 체크박스 2개 |

잠김 여부는 `getPrepStageStatus()`가 매 렌더마다 체크 상태에서 파생 계산한다. 별도 localStorage 플래그 없음(`ux-audit.md` §⑴ "완료·열림 조건" 참고).

## 요소 × 상태 매트릭스

| 요소 | 상태 | `disabled` | 시각 처리 | 확인 방법 |
|---|---|---|---|---|
| 메인 task 체크박스(`data-task-id`) | 잠김 (이전 단계 미완료) | 있음, `aria-disabled="true"` | 부모 `.task-row`에 `is-locked-row` 클래스 | 브라우저 DOM에서 `disabled` 속성 조회 |
| 메인 task 체크박스 | 풀림 (이전 단계 완료) | 없음 | `is-locked-row` 없음 | 1단계 체크 후 2단계 체크박스 클릭 가능 확인 |
| 메인 task 체크박스 | 되돌리기 후 재잠김 | 있음(재부여) | `is-locked-row` 재부여, 체크값은 보존 | 1단계 체크 해제 → 2단계 체크박스 `disabled` 복귀, `checked` 값은 유지 |
| 메인 task 체크박스 | 완료 | 없음(그 자체가 풀림 상태) | `is-done`(부모 `.task-item`) | 체크 후 카드에 "완료" 배지 노출 |
| 서류 체크박스(`data-doc-name`) | **잠김** (2단계 잠김) | **이번 세션 수정 전: 없음(버그) → 수정 후: 있음**, `aria-disabled="true"` `aria-describedby="stage-lock-msg-2"` | **수정 전: 없음(버그) → 수정 후**: 부모 `<li>`에 `is-locked` 클래스, `opacity: 0.55`·`cursor: not-allowed` | 2단계 잠김 상태(1단계 미완료)에서 서류 체크박스 16개 전부 `disabled` 조회(포트 18981 실측) |
| 서류 체크박스 | 풀림 (2단계 잠김 해제) | 없음 | `is-locked` 없음, 기존 흐림 해제 | 1단계 완료 후 서류 체크박스 16개 전부 클릭 가능 확인 |
| 서류 체크박스 | 되돌리기 후 재잠김 | 있음(재부여) | `is-locked` 재부여, 체크값은 보존 | 1단계 되돌리기 → 서류 체크박스 `disabled` 복귀, 기존 체크값 유지 확인 |
| 서류 체크박스 | 완료(개별 항목 체크) | 잠김 여부에 따름(완료는 잠김과 별개 축) | `is-checked` 클래스 | 체크 시 항목에 `is-checked` 부여 — 잠김과 무관하게 적용되는 별도 클래스 |
| 단계 헤딩(`renderStageHeading`) | 잠김 | 해당 없음(헤딩은 체크박스가 아님) | `.stage-group-heading.is-locked`, 🔒 아이콘, "N단계를 마치면 열립니다" 문구(`#stage-lock-msg-N`) | 2단계 잠김 상태에서 헤딩 텍스트·아이콘 확인 |
| 단계 헤딩 | 풀림(진행중) | 해당 없음 | `.is-active`, ▶ 아이콘, "진행중" 배지 | 1단계 완료 후 헤딩 전환 확인 |
| 단계 헤딩 | 완료 | 해당 없음 | `.is-done`, ✅ 아이콘, "완료" 배지 | 해당 단계 task 전부 체크 후 확인 |
| 단계 스테퍼(`renderPrepStageStepper`) | 잠김 | 해당 없음 | 🔒, "잠김, N-1단계를 마치면 열립니다" | 스테퍼 3칸 중 잠긴 칸 라벨 확인 |
| 단계 스테퍼 | 풀림(진행중) | 해당 없음 | ▶, `aria-current="step"` | 진행중 칸의 `aria-current` 속성 조회 |
| 단계 스테퍼 | 되돌리기 후 재잠김 | 해당 없음 | 🔒로 재전환 — "완료"로 잘못 표시하지 않음(`ux-audit.md` §⑴ 주석 근거) | 1단계 되돌리기 후 2단계 칸이 ✅가 아니라 🔒로 바뀌는지 확인 |
| 단계 스테퍼 | 완료 | 해당 없음 | ✅, "완료" | 해당 단계 전부 체크 후 확인 |

## 잠김과 무관하게 항상 열람 가능한 요소 (설계 의도, 이번 세션에서 변경 없음)

- `<details>`(원문 근거·"자세히" 상세 설명), "온비드 원문" 링크, "담당기관에 물어볼 질문" 문구, 공고 원문에서 확인된 값.
- `ux-audit.md` §⑴ "잠긴 단계의 표시" 근거: 상단 고지("원문과 담당기관 확인을 우선합니다") 약속을 어떤 화면 상태에서도 지켜야 하므로, 체크=완료 표시만 잠그고 정보 열람은 잠그지 않는다.
- 코드 주석(`src/app.js` 1552~1553행)으로 이 의도가 명시돼 있고, interaction-auditor가 실제 동작과 일치함을 확인했다([관측], `verification.md` 참고).

## 미확인 범위

- 모바일 좁은 뷰포트(375px)에서 `is-locked` 흐림 처리의 실제 렌더 — 이번 세션은 데스크톱 해상도에서만 `disabled` 속성과 클래스 부여를 확인했다.
