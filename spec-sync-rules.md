# 스펙 동기화 규칙 — Hometest_op

| 수정 내용 | 업데이트 대상 |
| --- | --- |
| `PUBLIC_DATA_ENDPOINTS` 추가/변경 | `docs/90_MVP개발/04_공공데이터_API_연동메모_20260704.md`, `README.md` |
| `#input`/`#report`/`#watchlist` 화면 흐름 변경 | `README.md` 화면 섹션, `docs/60_본선준비/10_발표자료/` |
| AI 코치 로직(`local_ai_coach`/`gemini_ai_coach`/`vertex_ai_coach`) 변경 | `docs/90_MVP개발/06_MVP_지속개선루프_20260705.md`, `known-pitfalls.md` |
| 금지표현/포지션 문구 변경 | `CLAUDE.md` 금지표현 절, `docs/60_본선준비/00_본선준비_계획_20260803.md` §6, `docs/40_제출준비/` 원고 |
| API 라우팅(`/api/analyze` 등) 변경 | `architecture.md` 데이터 흐름 절, `tests/public-data-status.spec.js` |

## 스펙 파일 ↔ 컴포넌트 ↔ 이슈 매핑

| ID | 문서 | 코드 | 비고 |
| --- | --- | --- | --- |
| P-01 | `docs/02_Spec/spec.md` | `src/server.py` `build_notice()` | 핵심 분석 파이프라인 |
| P-02 | `docs/90_MVP개발/04_공공데이터_API_연동메모_20260704.md` | `src/server.py` `PUBLIC_DATA_ENDPOINTS`, `fetch_public_data_bundle()` | 공공데이터 6종 보조 경로 |
| P-03 | `docs/60_본선준비/00_본선준비_계획_20260803.md` §6 | `src/app.js`, `src/index.html` 문구 | 금지표현 체크 |
