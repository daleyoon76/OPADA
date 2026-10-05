# 3팀 UIUX품질팀 — 시각 디자인 진단 (AI 가이드형 재설계 초안)

- 작성: 2026-10-01
- 담당: visual-designer (읽기 전용 진단, 소집=3팀 팀장)
- 대상: `docs/60_본선준비/19_AI가이드형_UX_재설계_플로우_20261001.md`, `docs/60_본선준비/mockups/20_AI가이드형_준비보드_초안_20261001.html`
- 작업 노트: `team-reports/2026-10-01-uiux-quality-v2/scratch-visual/notes.md`
- 코드 수정 없음 (`src/app.js`·`src/index.html`·`src/styles.css` 읽기만 함)

## 네 가지 제안 판정

| 제안 | 판정 | 근거 |
|---|---|---|
| 1. 코치 패널 1인칭 톤 교체 | 그대로 구현 | 색상·레이아웃 변경 없는 순수 문구 교체. 단, 패널이 더 자주 노출되는 주연출이 되면서 `coach-head`의 `badge(coachMode, llmConnected ? "safe" : "warn")`가 LLM 미연결 시 쓰는 `.badge.warn`(amber on soft-amber, 기존 결함) 노출 빈도가 간접적으로 올라간다는 점은 인지 필요. |
| 2. 다음 액션 AI 우선순위 강조 | 이렇게 수정해서 구현 | `renderTaskAiNudge()`는 그린 계열(`#c8d1a0`/`#f3f6e8`)이라 amber와 충돌 없음. 다만 `.task-ai-nudge strong`(제목)과 `p`(본문)가 둘 다 12px라 위계가 평면적 — 기획 문서가 "더 크게 키운다"고 명시했으므로 `strong`을 14px 안팎으로 올려야 의도가 실현됨. |
| 3. 질문-답변 위젯 독립 카드 승격 | 이렇게 수정해서 구현 | `.mock-ask-promoted`의 `border: 1px dashed var(--amber)`는 스타일시트 전체에서 전례 없는 조합(dashed 테두리는 L1166 `--line` 색 1곳뿐)이라 페이지에서 가장 눈에 띄는 요소가 됨. 코치 패널(옅은 좌측 라인)이 1순위여야 하는데 보조 유틸리티인 Ask 카드가 가장 강한 시각 신호를 가져 위계가 뒤집힘. solid `1px solid var(--line)` 계열로 교체 권고, 승격 표현은 "신규 위치" 배지·카드 위치만으로 충분. 제목(15px bold)/본문(12px muted) 크기 차는 적절하므로 유지. |
| 4. 접힌 패널 딥링크 힌트 | 이렇게 수정해서 구현 | `.mock-panel-reco`는 `var(--muted)`(amber 아님)이고 흰 배경 대비 5.78:1로 문제없음. 다만 11px는 가독성 하한(통상 12px) 미달이고 `<summary>`(16px bold) 바로 옆이라 크기 낙차가 큼. 12~13px로 상향하고 가능하면 summary 줄에서 분리 권고. |

## amber 대비 재계산 (직접 계산, python3 WCAG 2.x 상대휘도 공식)

| 조합 | 대비비 | 3:1 | 4.5:1 |
|---|---|---|---|
| amber(#f5901e) on soft-amber(#fde8d0) | 1.98:1 | 미달 | 미달 |
| amber on white(#ffffff) | 2.36:1 | 미달 | 미달 |
| amber on bg(#fdf5ee) | 2.19:1 | 미달 | 미달 |
| amber on panel(#fffaf5) | 2.28:1 | 미달 | 미달 |
| muted(#8b5a40) on soft-amber | 4.85:1 | 통과 | 통과(근소) |
| muted on white | 5.78:1 | 통과 | 통과 |
| muted on bg | 5.36:1 | 통과 | 통과 |
| muted on panel | 5.57:1 | 통과 | 통과 |

- `to-do.md`의 기존 등재치(약 2.0:1, "재검증 안 함")는 이번 실측 1.98:1과 거의 일치 — **재확인**이지 재인용이 아님.
- **악화 여부 판정**: mockup 전체에서 amber가 실제로 쓰인 자리는 `.mock-ask-promoted`의 `border: 1px dashed var(--amber)` 단 한 곳이며 텍스트가 아닌 비텍스트 테두리다. 카드 식별이 테두리 색에만 의존하지 않고(bold 제목·"신규 위치" 태그로도 식별 가능) WCAG 1.4.11(3:1) 직접 위반으로 보지 않는다. 새 강조 메커니즘(`task-ai-nudge`, 코치 패널 톤 교체)은 그린 계열을 쓰므로 **이번 설계가 amber 텍스트 대비 문제를 새로 만들거나 악화시키지 않는다.** 기존 실패 지점(`.badge.warn`, `.primary.is-caution`, `.copy-feedback.is-warn`, `.star-button.is-on`, 서류 체크리스트 상태 배지)은 그대로 남아 있고, 범위 밖 별도 이슈로 유지.

## 우선순위

- P0(구현 전 수정 필요): `.mock-ask-promoted`의 dashed amber 테두리 → solid `--line` 계열로 교체.
- P1: `.task-ai-nudge strong`의 제목 크기 확대(설계 의도 반영 누락 방지).
- P2: `.mock-panel-reco`의 11px → 12~13px 상향 및 summary 줄에서 분리.
- 정보성(새 결함 아님, 기존 등재분 확인): `coach-head`의 `badge.warn` 노출 빈도 증가 — 별도 이슈로 추적.

## 다음 검증 필요 항목 (스크린샷 기준, 이번 소집 범위 밖)

- `.mock-ask-promoted` solid 테두리 교체 후 실제 렌더에서 코치 패널 대비 시각적 비중이 의도대로 역전되는지.
- `.task-ai-nudge` 제목 크기 조정 후 task-item 카드 내 줄바꿈·좁은 뷰포트 밀도.
- `.mock-panel-reco` 폰트 크기 조정 후 summary 줄의 실제 줄바꿈 여부(모바일 폭).

## 참조 코드 위치

- `src/styles.css`: L1-21(토큰), L447-589(coach-panel), L783-940(task-item/task-ai-nudge), L994-1020(support-panel), L1185-1225(badge), L1311(small-text)
- `src/app.js`: L755-765(`getApplicableTasks`/`aiMatch`), L946-1000(`renderCoachPanel`/`renderCoachAsk`), L1090-1100(`renderTaskAiNudge`)
