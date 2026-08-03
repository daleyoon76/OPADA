# Known Pitfalls — Hometest_op

## 실행 환경
- `src/server.py`는 표준 라이브러리만 사용하는 순수 Python HTTP 서버입니다 (외부 의존성 없음). `python src/server.py`로 바로 실행됩니다.
- macOS 환경에서의 기동·온비드 분석·AI 호출은 2026-08-03 기준 미검증입니다 (기존 실행 확인 기록은 Windows 경로 기준). 다른 OS에서 처음 돌릴 때는 먼저 기동 확인부터 하세요.

## 외부 API
- 공공데이터포털 인증키(`ONBID_API_SERVICE_KEY`)가 없으면 온비드 공개 원문 분석만 동작합니다. 승인 직후 일부 API가 403/`NODATA_ERROR`를 반환할 수 있으나 원문 분석 결과는 계속 표시됩니다 — API 실패를 전체 실패로 착각하지 마세요.
- AI 코치는 `local_ai_coach` → `gemini_ai_coach`(`GEMINI_API_KEY`/`GOOGLE_API_KEY`) → `vertex_ai_coach`(gcloud 토큰) 순으로 폴백합니다. 인증키/토큰이 없어도 `local_ai_coach`로 동작은 계속됩니다.
- 시연용 샘플 URL은 입찰기간 종료 후 온비드 페이지가 사라지거나 상태가 바뀔 수 있습니다. 결선 시점 직전에 유효한 URL로 다시 확인하세요.

## 문구/표현
- 발표자료·시연 멘트에는 `CLAUDE.md`의 금지표현 12종을 쓰지 않습니다. 신청서 단계부터 유지된 규칙이며, 어겨진 이력이 있어 재작성 시 재검사가 필요합니다.
