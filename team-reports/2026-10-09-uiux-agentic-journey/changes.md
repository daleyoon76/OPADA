# OPADA 준비 보드 — 단계 잠금 버그 수정 변경 내역

> 반환자: ux-scribe (3팀 UIUX품질팀).
> 이전 세션(`adaf4bf`, WIP 커밋 — ux-flow-auditor·visual-designer 설계, frontend-implementer 구현)이 만든 것과
> 이번 세션이 고친 것을 분리해 적는다. 이번 세션 자체의 커밋 해시는 아직 없음(미커밋, 팀장이 일괄 커밋 예정).

## 이전 세션(`adaf4bf`)이 이미 만든 것 — 이번 세션은 건드리지 않음

- 단계 구성(`PREP_STAGES`, `src/app.js` 442행), 단계 잠금 파생 계산(`getPrepStageStatus`, 866행).
- 메인 task 체크박스(`data-task-id`) 잠금 — `renderTaskItem`(1554행), `disabled aria-disabled aria-describedby` 부여(1568~1570행).
- 단계 스테퍼(`renderPrepStageStepper`, 1504행), 단계 헤딩(`renderStageHeading`, 1527행).
- 질문-답변 온보딩(`renderExperienceQuestion` 등) 및 "자세히" `<details>` 기본 열림/닫힘 전환 로직.
- 서류 체크리스트 렌더 자체(`renderDocChecklist`, 당시 매개변수 없음) — **잠금 처리가 빠진 채로** 구현돼 있었음(이번 세션이 고친 버그의 원인).

## 이번 세션이 고친 것

### 1. 버그 수정 — 서류 체크박스 잠금 누락

**문제**: 2단계(서류 준비) 잠김 상태에서 메인 task 체크박스(`data-task-id`)만 잠기고, 그 하위 서류 체크리스트 체크박스(`data-doc-name`, 8~16종)는 그대로 클릭 가능했다.

**수정 파일**: `src/app.js`

- `renderDocChecklist()` → `renderDocChecklist(locked)`로 매개변수 추가(1267행).
  - 체크박스 렌더 템플릿에 `locked`일 때 `disabled aria-disabled="true" aria-describedby="stage-lock-msg-2"` 부여(1291~1296행).
  - `<li>`에 `locked`일 때 `is-locked` 클래스 부여(1290~1291행) — 아래 2번 CSS와 연동.
- `renderReport()` 안 호출 순서 변경(1700~1703행).
  - 기존에는 `renderDocChecklist()`를 먼저 호출한 뒤 `getPrepStageStatus()`를 나중에 계산했다 — 즉 `documents` task의 잠금 상태를 알기 **전에** 체크리스트를 이미 렌더하고 있었다.
  - 수정 후: `stageStatus`를 먼저 계산 → `getTaskStageNum("documents")`로 서류 task가 속한 단계 번호(2)를 구함 → 그 단계의 `locked` 값을 `renderDocChecklist(documentsStageLocked)`에 전달.
  - `aria-describedby="stage-lock-msg-2"`는 `documents`가 항상 2단계(`PREP_STAGES` 고정 구성)이므로 고정 문자열로 넣었다 — 메인 task 체크박스 쪽(`lockMsgId`, 1564행)처럼 동적으로 구하지 않은 점은 이번 수정의 단순화이며, 단계 구성이 바뀌면 함께 손볼 지점이다.

### 2. 시각 피드백 보강 — 잠긴 서류 체크박스 hover 처리

**문제**: interaction-auditor 점검에서 서류 체크박스가 기능적으로(`disabled`) 잠겨도 hover 시 cursor가 `pointer`로 남고 흐림 처리가 없다는 지적이 나왔다.

**수정 파일**: `src/styles.css` (1430행대, 기존 `.task-row.is-locked-row` 패턴 바로 아래 추가)

```css
.doc-group li.is-locked {
  opacity: 0.55;
}

.doc-group li.is-locked .doc-check,
.doc-group li.is-locked .doc-check input {
  cursor: not-allowed;
}
```

- 기존 `.task-row.is-locked-row`(메인 task 체크박스 잠금 시각 처리)와 동일한 패턴을 서류 체크박스 쪽에 맞췄다.
- 기능은 1번 수정의 `disabled` 속성으로 이미 막혀 있으므로, 이 CSS는 시각 신호만 보강한다(코드 주석으로 명시, `src/styles.css` 1430~1433행).

## 이번 세션에서 새로 만들지 않은 것

- 질문-답변 온보딩 기능 자체 — 이전 세션(`adaf4bf`)이 이미 구현. 이번 세션은 `visual-reviewer`가 실동작(선택 전 열린 `<details>` 10개 → "몇 번 해봤어요" 선택 후 5개)만 재확인했다.
- `lowstBidPrcHideDivCd`, AI 판단 금지 원칙, 금지 문구 규칙 — 이번 diff가 건드리지 않음(`visual-reviewer` GO 판정 근거).
