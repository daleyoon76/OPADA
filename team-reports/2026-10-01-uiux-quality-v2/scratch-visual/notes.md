# visual-designer 작업 노트 (2026-10-01) — AI 가이드형 재설계 초안 검증

## 실측 대비비 (WCAG 2.x, python3 상대휘도 공식 직접 계산)
- amber(#f5901e) on soft-amber(#fde8d0): 1.98:1
- amber(#f5901e) on white(#ffffff): 2.36:1
- amber(#f5901e) on bg(#fdf5ee): 2.19:1
- amber(#f5901e) on panel(#fffaf5): 2.28:1
- muted(#8b5a40) on soft-amber(#fde8d0): 4.85:1
- muted(#8b5a40) on white(#ffffff): 5.78:1
- muted(#8b5a40) on bg(#fdf5ee): 5.36:1
- muted(#8b5a40) on panel(#fffaf5): 5.57:1

## amber 텍스트가 실제 쓰이는 자리 (src/styles.css grep)
- .badge.warn (L1200-1203): color amber on soft-amber bg → 1.98:1. 서류 체크리스트 attachment_only/not_in_notice/not_found 전부 이 클래스(docChecklistStatusBadge, app.js).
- .primary.is-caution (L178-182): color amber on 흰 배경 → 2.36:1.
- .copy-feedback.is-warn (L991): color amber, 배경 백색류 추정.
- .star-button.is-on (L1155-1157): color amber on soft-amber → 1.98:1 (to-do.md 기존 등재 항목, 별표 활성).
- renderCoachPanel() 의 coach-head 배지: `badge(coachMode, llmConnected ? "safe" : "warn")` (src/app.js ~966) — LLM 미연결(규칙 기반 폴백)이면 badge.warn 사용 → 1.98:1.

## 신규 mockup에서 amber 쓰인 자리 (grep "amber" on mockup html)
- 단 1곳: `.mock-ask-promoted { border: 1px dashed var(--amber) }` — 텍스트 아님, 테두리(장식/비텍스트 UI 경계).
- `.mock-panel-reco`는 color: var(--muted) — amber 아님. font-size 11px.

## 신규 강조 메커니즘의 실제 색상 (코치 강조 vs 다음 액션 강조 충돌 여부)
- renderTaskAiNudge()의 배지: `badge("확인 필요 항목", "safe")` → green/safe 계열, amber 아님.
- .task-ai-nudge 컨테이너: border #c8d1a0(올리브그린), bg #f3f6e8(연두) — amber 아님.
- .coach-panel.board: border-left var(--line)(연한 크림), bg #fffcf8 — 신규 배경색 추가 없음, 문구만 교체.
- → "다음 액션" 강조와 "코치 패널" 강조는 서로 다른 색상군(그린 계열)을 쓰고 있어, amber 과포화로 인한 "전부 강조=무강조" 충돌은 이 두 메커니즘 사이에서는 발생하지 않음. (기존 to-do.md 등재 우려와 달리 실측상 색 충돌은 없음 — 다만 아래 "진짜 문제" 참조)

## 진짜 발견: 대시드 amber 테두리의 위계 역전
- 기존 스타일시트 전체에서 dashed 테두리는 단 1곳(L1166, --line 색상)뿐. 모든 카드(report-hero, status-card, task-item, coach-panel)는 옅은 --line 또는 border 없음으로 톤을 낮춘 solid 테두리.
- mock-ask-promoted만 "dashed + amber(채도 높은 주황)" 조합 — 스타일시트에 전례 없는 조합이라 페이지에서 가장 눈에 띄는 요소가 됨.
- 그런데 Mermaid 플로우(19_...md)의 의도는 "코치가 먼저 말을 건다"(Coach가 1순위)이고 Ask 카드는 "상시 노출되는 보조 유틸리티"다. 코치 패널은 옅은 좌측 라인 하나뿐이라 시각적으로 가장 약한데, 의도상 보조적인 Ask 카드가 테두리 스타일 때문에 가장 강한 시각 신호를 가짐 → 의도한 위계와 실제 시각적 위계가 뒤집힘.
- 이 테두리는 텍스트가 아니라 비텍스트 UI 경계라 WCAG 1.4.11(3:1) 직접 적용 대상은 아님(판단 대상 텍스트 없음, 카드 식별에 테두리만 의존하지 않음 — 제목 bold 15px·"신규 위치" 태그로도 식별 가능). 색 대비 "실패"로 보지 않지만 위계 설계 결함으로 본다.

## 기존 평면적 위계 패턴 반복 여부
- .task-ai-nudge strong(12px, 신규 제목) vs .task-ai-nudge p(12px, var(--muted), 본문) — 제목·본문 폰트 크기가 동일(12px), font-weight(strong vs normal)만 다름. 관심 공고 카드에서 지적된 "제목/본문/메타 구분 약함" 패턴과 동일.
  - 이번 설계 의도(19_...md)가 "표시를 더 크게 키운다"고 명시했으므로, 구현 시 이 지점을 키우지 않으면 같은 결함을 반복.
- mock-ask-promoted는 b(15px bold) vs p(12px muted)로 크기 차이가 있어 위계가 상대적으로 명확 — 평면적 패턴 아님.
- .support-panel summary(16px bold) 옆에 .mock-panel-reco(11px muted)를 한 줄에 붙임 — 11px는 일반 가독성 하한(보통 12px) 미달 권고 위반 소지. 16px bold와 11px가 한 줄에 같이 있어 크기 낙차가 크고 좁아 보임(가독성·탭 타겟 측면에서도 작은 보조 텍스트가 큰 제목에 바싹 붙어 시선 분산).

## coach-head 배지 노출 증가 영향
- 코치 패널이 "먼저 말을 거는" 주연출로 격상되면서, 그 머리에 붙는 badge.warn(규칙기반 폴백 시 amber-on-soft-amber, 1.98:1)의 노출 비중도 함께 올라감. 문구 교체만으로는 이 기존 결함이 고쳐지지 않고, 오히려 더 많이 보이게 됨.
