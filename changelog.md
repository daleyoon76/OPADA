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

## 2026-09-02

- 화면에 표시되는 재산유형이 온비드 내비게이션 문구("중메뉴 펼치기")로 채워지던 파싱 결함을 근본 수정 — 라벨 기반 HTML 스크래핑보다 상세 페이지 hidden input(`scrnCltrPrptDivNm`)을 우선 참조하도록 변경. 압류재산·기타일반재산·파산자산 4건으로 회귀 0건 확인.
- 온비드 물건상세를 GET으로 여는 파라미터 조합을 확정 — `onbidCltrno`·`cltrHisNo`·`pbctCdtnNo`·`onbidPbancNo`·`pbctNo` 5개 전부 필요(누락 시 온비드가 500 반환). 시연용 실 URL 확보 절차가 성립했다.
- 공공데이터 API 6종의 활용신청 경로를 엔드포인트명 대조로 확정하고, 캠코로부터 서비스별 일 허용 건수 100,000건을 확인.

<!-- arch-review: 2026-09-02: 파싱 소스 우선순위 변경 -->
