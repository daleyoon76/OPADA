# Handoff — Hometest_op

(각 세션 종료 시 아래 형식으로 항목 추가. 최대 10개 유지, 초과 시 가장 오래된 항목 삭제)

---
## [하네스 세팅] 2026-08-03 21:20 KST

### 완료
- `My AI Harness_20260511.md` 가이드 Part 3(신규 프로젝트) 기준 하네스 세팅
- `CLAUDE.md`, `architecture.md`, `plan.md`, `to-do.md`(마일스톤 1 P0 태스크), `known-pitfalls.md`, `spec-sync-rules.md` 작성/재구성
- `plan.md`/`to-do.md`는 `docs/60_본선준비/00_본선준비_계획_20260803.md`(예선 선정 확정, 본선 P0/P1/P2) 내용을 그대로 반영
- `package.json` + `playwright.config.js` 추가 (e2e 도구 선언, `npm install` 미실행 상태)
- `/handoff` 슬래시 스킬은 전역에 이미 존재해 별도 생성하지 않음

### 미완료
- 메모리 인덱스(`~/.claude/projects/.../memory/MEMORY.md`) — 이 프로젝트 디렉토리에서 첫 세션을 열어야 실제 프로젝트 ID 경로가 확정됨. 지금은 생성하지 않음.
- `.husky/pre-commit` 강제 검증 훅 — 린터/테스트 러너 미설정으로 보류 (가이드 원칙: 훅보다 러너가 먼저)
- `npm install` 미실행 (Playwright 브라우저 다운로드 필요, 자동 실행하지 않음)

### 다음 세션 시작점
- `to-do.md`의 P0-2(MVP 라이브 시연 확보)부터 진행 권장 — 발표자료(P0-1)보다 먼저 동작 여부를 확인해야 재작성 방향이 흔들리지 않음

### 불안정 영역
- 없음

---
## [프로젝트 분리] 2026-08-03 21:04 KST

### 완료
- KAMCO Startup TechBlaze 서류 합격 이후 `supporting-programs/07_KAMCO_Startup_TechBlaze`를 `Hometest_op` 독립 레포로 분리
- `docs/`에 원본 07 폴더 전체를 그대로 이관, `90_MVP개발/app/*`은 `src/`로, `90_MVP개발/tests/*`는 `tests/`로 추출
- `__pycache__/`, 잔여 `*.log` 운영 로그 파일은 이관하지 않고 제외
- `git init` 완료, `main` 브랜치로 정리

### 미완료
- 첫 커밋 (이유: 사용자 확인 후 진행)

### 다음 세션 시작점
- 원격 레포 생성 여부, `supporting-programs`에서 원본 폴더 제거 여부 결정

### 불안정 영역
- 없음
