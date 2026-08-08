# 시각 품질 진단 — 2026-08-08

담당: visual-designer (3팀)
대상: "산만하고 불편하다" 사용자 피드백에 대한 시각적 원인 진단

## P0

- **badge 색상 남발**: report-hero에서 최대 4개 badge가 동시 출력(`app.js:1070-1072`)되고, "원문 우선"이 상시 warn색(`app.js:1133,1187`)으로 표시되어 실제 경고와 구분되지 않음.
  - 처리 상태: **이번에 report-hero badge 1개(실제 상태 badge만)로 축소, "원문 우선"은 텍스트로 강등 완료**
- **accent border 색 중복**: fit-panel(green, `styles.css:287`) / coach-panel(blue, `styles.css:439`) / coach-panel.board(green, `styles.css:537`) / report-hero(green, `styles.css:674`) / risk-card(amber, `styles.css:1115`)가 한 화면에 동시 노출되어 "무엇이 경고인지" 신호가 희석됨.
  - 처리 상태: **이번에 report-hero/coach-panel을 중립색으로 통일. 실제 경고 상태(fit-panel.mismatch, risk-card)는 색 유지(안 건드림)**
- **박스 안의 박스**: fit-facts(`styles.css:316-320`) / preview-grid(`styles.css:375-379`) / coach-facts(`styles.css:455-459`) 미니 셀에 중복 border.
  - 처리 상태: **이번에 border 제거 완료**

## P1

- **폰트 크기 난립**: 9단계 이상(25/22/19/17/16/15/14/13/12px)이 혼재.
  - 처리 상태: **이번에 24/20/16/14/12 5단계로 정리 완료**
- **font-weight 700 과다**: label, 일반 strong, a 태그까지 굵게 처리.
  - 처리 상태: **이번에 h1/h2/버튼/badge로 제한 완료**
- **pastel 배경틴트 남발**: soft-green/soft-amber/soft-blue가 기본 정보 패널에도 남용됨.
  - 처리 상태: **report-hero/coach-panel만 이번에 중립화, 나머지는 보류**

## 요약

색상/경계선/타이포그래피 과잉이 "산만함"의 시각적 근본 원인으로 진단됨. P0 3건은 모두 해결, P1 3건 중 폰트 단계·weight 정리는 완료, pastel 배경틴트는 report-hero/coach-panel 범위만 처리하고 전면 정리는 다음 이터레이션으로 보류.

## 전후 비교 참고

캡처 위치: 팀장 검증 시 사용한 Playwright 브라우저 화면(데스크톱 1280px / 모바일 390px). 별도 스크린샷 파일은 이번 세션에서 저장되지 않았음(미확인 — 파일 경로 없음). `verification.md`의 "검증 수행" 항목 참고.
