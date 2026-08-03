# Architecture — Hometest_op

## 1. 디렉토리 구조

```
Hometest_op/
├── src/
│   ├── server.py       # 백엔드. 표준 라이브러리 HTTP 서버, 유일한 API(/api/analyze) + 정적 파일 서빙
│   ├── app.js           # 프론트엔드 로직. #input/#report/#watchlist 화면 전환, localStorage 관심공고
│   ├── index.html       # 단일 페이지 셸
│   └── styles.css       # 스타일
├── tests/
│   └── public-data-status.spec.js  # Playwright e2e. 127.0.0.1:8975 대상 실사용 시나리오 검증
└── docs/                # KAMCO Startup TechBlaze 제출 전 과정 문서 (원문 공고~본선준비, MVP 개발 기록)
```

## 2. 각 파일의 역할

| 파일 | 역할 |
| --- | --- |
| `src/server.py` | 온비드 URL 검증(`validate_onbid_url`) → 원문 크롤링(`fetch_onbid`) → 필드 추출(`clean_text`, `hidden_inputs`, `class_text`, `values_after_label`, `extract_required_docs`, `extract_related_docs`) → 공공데이터 보강(`fetch_public_data_bundle`) → 체크리스트 생성(`build_tasks`) → AI 코치(`build_ai_coach`) → JSON 응답(`build_notice`) |
| `src/app.js` | `#input`(공고 가져오기) / `#report`(준비 보드) / `#watchlist`(관심 공고) 세 화면 렌더링과 상태 전이, `/api/analyze` 호출, localStorage 기반 최근 살펴본 공고·관심 공고 저장 |
| `src/index.html` | 세 화면의 DOM 셸. `app.js`가 여기에 렌더링 |
| `tests/public-data-status.spec.js` | 실제 온비드 URL로 분석 → 준비 보드 생성 → 공공데이터 API 상태 문구 확인까지의 크리티컬 패스 e2e |

## 3. 데이터 흐름 (사용자 요청 → 응답)

1. 사용자가 `#input` 화면에서 온비드 공고/물건 URL 입력 → `app.js`가 `GET /api/analyze?url=...` 호출
2. `server.py Handler.do_GET`이 `/api/analyze`만 가로채고 나머지는 정적 파일 서빙(`translate_path`)
3. `build_notice(raw_url)`:
   - `validate_onbid_url` → `fetch_onbid`로 원문 HTML 가져옴 (short URL은 최종 URL로 추적)
   - 원문에서 공고/물건 필드 추출, `build_related_urls`로 연관 URL 구성
   - `ONBID_API_SERVICE_KEY`가 있으면 `fetch_public_data_bundle`이 `PUBLIC_DATA_ENDPOINTS` 6종을 호출해 필드 보강 (키 없거나 403/`NODATA_ERROR`여도 원문 분석 결과는 유지)
   - `build_tasks`가 필요서류·준비 빈칸을 체크리스트로 변환
   - `build_ai_coach`가 `local_ai_coach` → (`GEMINI_API_KEY` 있으면) `gemini_ai_coach` → (없으면 gcloud 토큰으로) `vertex_ai_coach` 순으로 AI 우선 액션/확인 문장 생성
4. JSON 응답을 `app.js`가 받아 `#report` 화면(준비 보드)을 렌더링, `#watchlist`에 자동 저장

## 4. 외부 서비스 연동 포인트

| 서비스 | 위치 | 필수 여부 |
| --- | --- | --- |
| 온비드 공개 페이지 | `fetch_onbid` | 필수 (기본 경로) |
| 공공데이터포털 온비드 API 6종 | `PUBLIC_DATA_ENDPOINTS`, `fetch_public_data_bundle` | 선택 (`ONBID_API_SERVICE_KEY`) |
| Gemini API | `gemini_ai_coach` | 선택 (`GEMINI_API_KEY`/`GOOGLE_API_KEY`) |
| Vertex AI | `vertex_ai_coach`, `vertex_access_token` | 선택 (gcloud 토큰) |

## 5. 공유 타입/유틸리티

단일 파일 구조라 별도 공유 모듈은 없다. `server.py` 안에서 관심사별로 함수가 분리되어 있으며(원문 파싱 / 공공데이터 호출 / AI 코치 / HTTP 핸들러), 새 기능도 같은 파일 안에 같은 방식으로 함수 단위로 추가한다.
