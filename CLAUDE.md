# Hometest_op — OnBid Public Asset Doc Agent

## 프로젝트 개요

- 한 줄 설명: KAMCO Startup TechBlaze 모집부문1 제출용 온비드 공공자산 공고 해석/준비 보조 MVP. 2026-08-03 예선(서류) 선정, 10월 결선 발표평가 준비 중.
- 기술 스택: Python 표준 라이브러리 HTTP 서버(`src/server.py`, 외부 의존성 없음) + Vanilla JS/HTML/CSS(`src/app.js`, `src/index.html`, `src/styles.css`), Playwright e2e(`tests/`)
- 주요 외부 서비스: 온비드 공개 페이지(원문 크롤링, 기본 경로), 공공데이터포털 온비드 API 6종(`ONBID_API_SERVICE_KEY`, 보조 경로), AI 코치(Gemini API `GEMINI_API_KEY`/`GOOGLE_API_KEY` 또는 gcloud Vertex 토큰, 선택)

## 인프라 URL 구분 (절대 혼동 금지)

| 구분 | URL | 설명 |
| --- | --- | --- |
| 로컬 서버 | `http://127.0.0.1:8975/` | `python src/server.py` 실행 후 접근하는 유일한 서비스 접점 |
| 온비드 원문 | `https://www.onbid.co.kr/...` | 공고/물건 원문. 기본 분석 경로 |
| 공공데이터포털 API | `https://apis.data.go.kr/B010003/...` | `PUBLIC_DATA_ENDPOINTS` 6종. 인증키 있을 때만 보조 호출 |

이 프로젝트는 사내망/외부망 구분이나 배포 플랫폼이 없다. 로컬 실행이 전부이며, 위 표 이상으로 URL을 늘리지 않는다.

## 발표·시연 금지표현 (가드레일)

`docs/60_본선준비/00_본선준비_계획_20260803.md` §6 기준. 발표자료·시연 멘트·외부 공유 문서에서 아래 표현을 쓰지 않는다:

자동 입찰 · 입찰 대행 · 낙찰 가능성 예측 · 투자수익률 판단 · 법률 자문 · 권리분석 대체 · PDF 리포트 · Q&A · 공고 해석 리포트 · Vertex AI/Gemini AI · Local MVP/로컬 분석 API · 완전 자동

권장 문장: "본 서비스는 입찰 여부, 법률 판단, 투자수익률, 낙찰 가능성을 제공하지 않으며, 온비드 원문과 담당기관 확인을 우선하는 준비 보조 도구입니다."

## 행동 규칙 (가드레일)

- 사실만 말하라. 구현되지 않은 것을 구현됐다고 하지 마라.
- 코드를 수정하기 전에 반드시 현재 코드를 읽어라.
- 추측하지 마라. 모르면 모른다고 하라.
- 한 번에 하나의 작업에만 집중하라.
- AI 코치 로직(`local_ai_coach`/`gemini_ai_coach`/`vertex_ai_coach`)에 입찰 여부·법률·권리관계·수익성 판단을 추가하지 마라 — 신청서 단계부터 유지된 의도적 제외 범위다.

## 작업 흐름 규칙 (상태 전이)

- 작업 시작 전: `plan.md`와 `to-do.md`를 읽고 현재 위치를 파악하라.
- `to-do.md`의 현재 마일스톤 항목이 모두 [x]이면: `plan.md`의 다음 마일스톤으로 이동하라.
- 마일스톤 완료 시: `architecture.md`와의 정합성 체크를 수행하라.
- e2e 테스트 실패 시: 코드 수정 전에 실패 원인을 `to-do.md` 또는 세션 내에 먼저 기록하라.

## 구현 중 체크포인트 (중간 검증)

- 새 파일 생성 시: `architecture.md`의 디렉토리 구조와 일치하는지 확인
- `src/server.py`의 라우팅(`/api/analyze`)이나 `PUBLIC_DATA_ENDPOINTS` 변경 시: `spec-sync-rules.md` 매트릭스에 따라 관련 문서도 갱신
- 10개 이상의 파일 수정 후: `git diff --stat`으로 변경 범위 요약, 의도와 일치하는지 자기 검증

## 세션 종료 규칙 (컨텍스트 브리징)

- 작업 종료 전 반드시 `handoff.md`에 이 세션 내용 추가 (기존 항목 유지, 10개 초과 시 가장 오래된 항목 삭제)
- 각 항목에 작업 영역 태그와 시간 포함
- 항목 내용: 완료한 것 / 미완료 + 이유 / 다음 시작점 / 불안정 영역
- 마일스톤 완료 시 `changelog.md`에 항목 추가 (누적)

## 실패 패턴 참조

- 작업 전 `known-pitfalls.md` 확인
- 같은 유형 버그 2회 이상 시 `known-pitfalls.md`에 기록

## 외부 SSOT 동기화

- `spec-sync-rules.md` 참조 — 코드 변경 시 관련 문서(`docs/`)도 함께 갱신
- `PUBLIC_DATA_ENDPOINTS`, 화면 상태 문구, 금지표현 목록은 이 프로젝트의 외부 SSOT다. 임의로 다른 표현이나 엔드포인트를 만들지 않는다.

## 병렬 작업 시 스코프

- 단일 개발자 프로젝트다. 별도 worktree/브랜치 전략이 필요 없으며 `main` 브랜치만 사용한다.
- 병렬 세션을 여는 경우에만 세션 시작 시 구두로 수정 가능/읽기 전용/금지 경로를 지정한다.
