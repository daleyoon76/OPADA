# UX 전면 재설계 4단계(전체 phase 4/5) — 준비 보드 3단계(입찰참여) 내부 로직 2026-10-13

솔로 작업(서브에이전트 병렬 호출 없이 직접 설계·구현·검증 수행). `agentic-journey` 브랜치, 워크트리 `Hometest_op-agentic`.

## 범위

준비 보드 3단계(입찰참여) 내부 로직만. 1·2단계와 마법사 화면은 이번에 손대지 않았다. 설계된 마지막 기능 phase이며, phase5(전체 흐름 통합 검증)는 포함하지 않는다.

## 구현 방식

- **"담당기관에 물어볼 질문 정리" 제거** — `src/server.py`의 `build_tasks()`에서 `id: "agency"` task를 삭제했다. 이 task는 `PREP_STAGES`(`src/app.js`)의 3단계(`taskIds: ["price", "agency"]`)에 묶여 있었으므로, 서버가 더 이상 이 id를 돌려주지 않으면 화면에서도 자동으로 사라진다. `PREP_STAGES`의 3단계 `taskIds`도 `["price"]`로 맞췄다.
- **입찰 참여 정보 리스트** — `renderBidParticipationInfo()`(`src/app.js`) 신설. 새 추출 로직을 만들지 않고 이미 계산된 값만 재사용한다.
  - 입찰기간·최저입찰가격은 1·3단계 task(`bid-period`·`price`)의 `.action` 값을 그대로 가져온다(서버의 `build_tasks()`가 이미 `notice.bidPeriod`/`notice.minimumBidPrice` 기준으로 계산해 둔 값).
  - 입찰 장소는 `notice.bidType`이 "전자입찰"이면 "온비드 전자입찰"로, 그 외(미확인 포함)는 "원문 확인 필요"로 표시한다. `bidType`은 기존 `build_notice()`가 이미 추출하던 필드다.
  - 개찰일시는 `notice`에 그 값을 담는 필드 자체가 없어(원문이 자바스크립트로 지연 채우는 "입찰일정 및 장소" 표 문제와 별개로, 단일 개찰일시 필드 추출이 아예 없었다) 행을 만들지 않았다. 사용자 지시의 "있으면"을 "없으면 행 자체를 생략"으로 해석했다 — 다른 세 항목처럼 "원문 확인 필요"로 채우면 마치 그 필드가 존재하는 것처럼 보일 수 있어, 더 보수적인 쪽을 택했다.
  - 마크업은 기존 `.fact-list`/`.fact-row`(이미 "공고 요약" 패널이 쓰던 클래스)를 그대로 재사용했다 — 새 CSS 없음.
- **AI 질문창** — `renderBidAskBox()`/`askBidParticipationQuestion()`(`src/app.js`) 신설. **새 엔드포인트를 만들지 않고 기존 `/api/ask`(2026-09-21 신설, `question_prompt()`/`sanitize_ai_text()`/`answer_notice_question()`)를 그대로 재사용했다** — 이미 공고 사실(notice)·준비 보드 상태(board) 두 근거로만 답하고 "입찰 참여 권유·가격 결정 권유·수익성 판단·법률/권리관계 판단은 하지 않는다"는 안전 지시가 박혀 있어, 요청받은 안전 경계와 정확히 일치했다.
  - 공고 핵심 맥락(title·assetType·dispositionLabel·bidMethod·bidPeriod·bidDeadline·minimumBidPrice·appraisalPrice·agency·contact)에 더해, 2단계에서 답한 공동입찰/대리입찰 여부(`getDocConditionAnswers()`)를 "공동입찰 예정"/"공동입찰 아님" 문장으로 요약해 `jointBidAnswer`/`proxyBidAnswer` 필드로 함께 보낸다.
  - 서버 `question_prompt()`의 `notice` 딕셔너리에 이 두 필드를 추가했다(`src/server.py`) — 사용자가 2단계에서 고른 선택이지 원문 추출값이 아니라는 점을 주석으로 남겼다.
  - 응답 렌더링은 기존 `renderQuestionAnswer()`를 그대로 재사용한다("AI 연결 안 됨"/"담당기관 문의 필요"/"공고 원문 기반 답변"/"준비 보드 기반 안내" 네 분기 전부 포함).
  - fetch 실패(네트워크 오류 등)는 catch 블록에서 "지금은 답변을 가져올 수 없습니다. 담당기관에 문의하세요."로 안내한다.
  - 2단계의 "공동입찰인가요?"/"대리입찰인가요?" 질문처럼, 3단계가 잠겨 있어도(1·2단계 미완료) 정보 리스트와 질문창은 항상 보인다 — "잠긴 상태에서도 자세히·원문 링크는 항상 보인다"는 기존 원칙(ux-audit §⑴)과 같은 이유다.
- `tests/screen.spec.js`의 `stagedNotice()` 픽스처와 "준비 단계 스테퍼" 세 테스트에서 "agency" task 참조를 전부 제거했다(실행하지는 않았다 — 아래 "검증" 참고).

## 검증

- 단위 테스트 `tests/test_docs_extraction.py`: 275/275 통과(변경 전후 동일)
- 금지 문구 검사 `tests/test_screen_strings.py`: 20/20 통과
- 전용 포트 19004에 직접 서버를 띄우고, 실제 온비드 공고(`onbidPbancNo=887390`, phase2·3과 같은 샘플)를 분석해 1·2단계를 완료 처리한 뒤 3단계를 실제 브라우저(OpenClaw browser 도구)로 확인했다.
  - **"담당기관에 물어볼 질문 정리" 부재**: 3단계 할 일 카드가 "최저입찰가격 확인" 하나만 뜨는 것을 DOM에서 확인했다.
  - **정보 리스트**: "입찰 참여를 위해 챙겨야 할 정보입니다" 아래 입찰기간("2026-06-01 10:00 ~ 2026-06-04 17:00")·입찰 장소("온비드 전자입찰")·최저입찰가격("660000")이 실제로 뜨는 것을 확인했다.
  - **AI 질문창 실제 호출 — 사실 질문**: "최저입찰가격은 얼마인가요?"를 입력해 전송 → "공고 원문 기반 답변 / 최저입찰가격은 660,000원입니다."를 받았다. 숫자를 "660,000원"으로 자연스럽게 포맷한 문장은 규칙 기반이 아니라 모델이 생성한 응답임을 보여준다.
  - **AI 질문창 실제 호출 — 모호한 질문**: "입찰보증금은 어떻게 내나요?"는 "담당기관 문의 필요"로 분류됐다(`answerType: none`) — `connected: true`인데 `answerable: false`인 분기이므로, 이 역시 실제로 모델 응답을 받은 뒤 내린 판정이다.
  - **안전 경계 — 낙찰 가능성·적정가**: "이 가격이면 낙찰 가능성이 높을까요? 적정 가격인지 알려주세요"를 입력 → "담당기관 문의 필요 / 이 질문은 공고 원문만으로 답하기 어렵습니다. 담당기관에 문의하세요."로 응답했다. 단정적인 낙찰·적정가 판단을 하지 않았다.
  - **API 키/Vertex 둘 다 없는 상황**: 이 기기에는 다른 프로젝트(`Bizketch`)의 `.env.local`에 `GOOGLE_CLOUD_PROJECT_ID`가 있고 gcloud ADC도 연결돼 있어, `GEMINI_API_KEY` 없는 사본 디렉터리에서 띄워도 Vertex 경로로 실제 연결됐다(`secret_value()`의 다른 프로젝트 공유 fallback 때문 — 기존 동작, 이번에 건드리지 않았다). 그래서 `python3 -I`로 `server.gemini_api_key`/`server.vertex_config`를 직접 몽키패치해 `answer_notice_question()`을 호출, `{"connected": False, "answerable": False, "answerType": "none", "answer": "", "sourceField": ""}`가 돌아오는 것을 확인했다. `/api/ask` 핸들러는 이 경우에도 예외 없이 `200 {"ok": true, "result": ...}`를 반환한다(코드 확인).
  - **네트워크 요청 실패**: 19004 서버 프로세스를 잠깐 종료한 뒤 질문을 보내 "지금은 답변을 가져올 수 없습니다. 담당기관에 문의하세요."가 뜨는 것을 확인했다. 브라우저 콘솔 에러는 의도한 `ERR_CONNECTION_REFUSED`(`/api/ask`)와 기존부터 있던 무관한 `favicon.ico` 404 외 0건 — 화면이 깨지지 않았다.
  - **모바일(390px)**: 정보 리스트·AI 질문창·네트워크 실패 안내 문구 모두 줄바꿈 없이 정상 표시되는 것을 스크린샷으로 확인했다.
  - 작업 중 생성된 임시 파일 없음(`git status --short`로 확인, `src/app.js`·`src/server.py`·`tests/screen.spec.js` 수정만 남음). API 키 재현용으로 만든 `/tmp/opada-noapikey*` 사본·프로세스는 검증 직후 정리했다.

## 다음 phase(phase5: 전체 흐름 통합 검증)에 넘길 메모

- `tests/screen.spec.js`(e2e 17/17 게이트)는 phase1부터 `playwright.config.js`의 `baseURL`이 8975(메인 워크트리) 전용으로 고정돼 있어 이번에도 전체 실행을 하지 않았다 — "agency" task 참조 제거는 코드만 맞춰 뒀고 실행으로 확인하지는 못했다. phase1 handoff의 "다음 시작점"에 적힌 "이 워크트리 전용 포트로 돌릴 별도 playwright config 마련"이 아직 해소되지 않았다 — phase5에서 전체 흐름을 통합 검증할 때 함께 처리하는 것을 권한다.
- 입찰 참여 정보 리스트의 "개찰일시"는 이번에 실제로 표시된 적이 없다(해당 필드 추출 자체가 없어서). 개찰일시를 보여줘야 한다는 요구가 다시 나오면, 새 추출 로직(온비드 "입찰일정 및 장소" 표 파싱)이 필요하다 — known-pitfalls.md의 "회차(여러 입찰 차수)가 있는 공고는 입찰기간·최저입찰가격을 못 읽습니다" 항목과 같은 뿌리의 문제라, 가볍게 붙이지 말고 별도 작업으로 다뤄야 한다.
- `src/app.js`의 `aiTaskSignals`(line 484 부근)에는 여전히 `"agency"`·`"agency-question"` id를 참조하는 매칭 규칙이 남아 있다. `"agency"` task 자체가 사라졌으므로 이 규칙은 이제 아무것도 매칭하지 않는 죽은 참조이지만, 범위 밖 정리로 보고 이번에는 건드리지 않았다. 동작에 영향은 없다(단순히 매칭되지 않을 뿐).
- `/api/ask`를 이제 두 곳(기존 "AI 코치에게 물어보기" 전역 패널, 신설 3단계 "AI 질문창")이 함께 호출한다. 두 UI 모두 같은 엔드포인트·같은 안전 지시를 공유하므로 서버 쪽 프롬프트를 고칠 때는 두 UI 모두에 영향이 간다는 점을 염두에 둘 것.
