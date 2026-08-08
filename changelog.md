# Changelog

(아래 기준에 해당하는 항목만 누적 기록. 작업 일지가 아님)
(기준: 마일스톤/Phase 완료, 이슈 Close, 기능 전면 구현, 아키텍처·DB 결정, 반복 버그 근본 수정, 성능·보안 개선)

## 2026-08-03

- KAMCO Startup TechBlaze 모집부문1 예선(서류) `선정` — 10월 결선 발표평가 대상 확정.
- `supporting-programs` 레포에서 KAMCO Startup TechBlaze MVP를 `Hometest_op` 독립 레포로 분리 (서류 합격에 따른 분리).
- Harness 세팅 완료: `CLAUDE.md`/`architecture.md`/`plan.md`/`to-do.md`/`spec-sync-rules.md` 구성, `plan.md`는 `docs/60_본선준비` 계획 반영.

<!-- arch-review: 2026-08-03: 초기 세팅 -->

## 2026-08-08

- 온비드 물건상세 URL에 필수 파라미터가 없을 때 500 에러를 그대로 노출하던 문제를 근본 수정 — 사전 검증으로 400 + "공유하기 → URL 복사" 안내 메시지로 전환.
- 3팀(UIUX품질팀) 소집해 MVP 화면 전면 정리: notice-fit/analysis-preview 패널 통합으로 정보 중복 제거, badge/강조색 체계 재정립, 포커스 관리·요청 경합 등 상호작용 버그 수정, 관심 공고 화면 실제/예시 데이터 시각적 구분.

<!-- arch-review: 2026-08-08: UI/UX 전면 정리 -->
