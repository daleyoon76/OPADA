# AI 질문 응답에 "공매 절차 일반 지식" 갈래 추가 (2026-10-14)

`/api/ask`가 질문을 `notice`·`board`·`none` 세 갈래로만 분류해, 공고 하나에 매이지 않는
일반적인 공매·입찰 절차 질문("전자입찰이면 서류 제출 이후 결과를 기다리면 되나요?")이
전부 `none`(담당기관 문의 필요)으로 처리되던 문제를 고쳤다. 실제 데모에서 사용자가 이
질문을 넣어 겪은 문제다.

## 새 갈래

- 이름: **`general`**
- 선택 이유: 이 공고에 한정되지 않은 온비드 공매·입찰 절차에 대한 공개된 일반 지식을
  뜻하는 범용적인 영어 단어다. 기존 두 갈래(`notice`·`board`)가 이미 코드 전체에서
  영어 단수 명사를 쓰고 있어 같은 관례를 따랐다. `procedure`도 검토했지만 `board`의
  "절차"(준비 순서)와 뜻이 겹쳐 혼동을 줄 수 있어 제외했다.
- 화면 배지 문구: **"공매 절차 일반 안내"** (기존 "공고 원문 기반 답변"·"준비 보드 기반
  안내"와 구분되는 짧은 라벨)

## 변경 범위

1. **`src/server.py:1768`** — `ANSWER_TYPES`에 `"general"`을 추가해 네 값으로 늘렸다.
2. **`src/server.py` `question_prompt()`** — instruction에 `(3) general` 분류 설명을
   추가하고 기존 `(3) none`을 `(4) none`으로 옮겼다. `general`은 notice·board 데이터
   없이도 공매 절차 일반 지식만으로 확실히 답할 수 있을 때만 쓰고, 이 공고에만 해당하는
   사실이나 notice에 없는 물건 특정 내용은 `general`로 답하지 않도록 명시했다. 기존
   안전 경계 문장("입찰 참여 권유, 가격 결정 권유, 수익성 판단, 법률/권리관계 판단은
   하지 않는다")은 "어느 갈래로도"를 붙여 네 갈래 전체에 적용되게 했고, "모르는데
   지어내지 않는다" 원칙도 `general`에 동일 적용되는 문장을 추가했다.
3. **`normalize_question_answer()`** — 별도 수정 없음. `answer_type not in ANSWER_TYPES`
   판정이 튜플 멤버십만 보므로 `general`을 추가한 것만으로 자동으로 통과한다. `board`
   전용 가드(보드 데이터 없이 온 board 답변은 none으로 버림)는 `general`에는 해당하지
   않는 조건이라 그대로 뒀다.
4. **`src/app.js` `renderQuestionAnswer()`** — `answerType === "general"`일 때
   "공매 절차 일반 안내" 배지를 쓰도록 분기를 추가했다. 기존 "준비 보드 기반 안내"/
   "공고 원문 기반 답변"과 "담당기관 문의 필요"/"AI 연결 안 됨" 분기는 그대로 뒀다.
5. **`tests/test_docs_extraction.py`·`tests/test_screen_strings.py`** — 두 파일 모두
   기존 분류·배지 가정을 확인했으나, `notice`·`board`·`none` 세 값만 참조하고 있어
   고칠 필요가 없었다. 건드리지 않았다.

## 완료 조건 검증 — 실제 LLM 호출

응답 경로를 먼저 확인했다: `GOOGLE_CLOUD_PROJECT_ID`가 설정돼 있고 `gcloud auth
application-default print-access-token`이 실제로 토큰을 내므로, 아래 네 테스트는 모두
**Vertex AI 경로**(`vertex_answer_question`)로 응답을 받았다. Gemini API 키 경로는
폴백으로만 쓰인다.

검증은 포트 19876에 테스트 전용 서버를 띄워 진행했다. 포트 18982의 실서비스는 건드리지
않았고, 검증이 끝난 뒤 19876 서버는 종료했다.

### 1. 일반 절차 질문이 답변되는가

사용자가 데모에서 직접 겪은 그 질문을 **브라우저로 샘플 공고를 불러온 뒤 실제 AI
질문창에 입력해 전송**해 확인했다.

- 질문: "전자입찰이면 서류 제출 이후 결과를 기다리면 되나요?"
- 배지: **공매 절차 일반 안내**
- 답변: "전자입찰의 경우, 서류 제출 후에는 별도의 서류 제출 없이 온라인으로 개찰 결과를
  기다리시면 됩니다."
- `answerType`: `general`

같은 질문을 `/api/ask`에 직접 호출해도 동일하게 분류됐다(`answerType: "general"`,
"전자입찰의 경우, 서류 제출 후에는 시스템에서 자동으로 입찰이 등록되며, 별도의 결과
통보를 기다리기보다는 개찰 결과 확인을 통해 입찰 결과를 알 수 있습니다.").

### 2. 안전 경계가 그대로인가

- 질문: "이 공고에 입찰하면 낙찰될 가능성이 높을까요?"
  → `answerType: "none"`, `answerable: false`, `answer: ""` (담당기관 문의 필요)
- 질문: "적정 가격이 얼마인가요?"
  → `answerType: "none"`, `answerable: false`, `answer: ""` (담당기관 문의 필요)

두 질문 모두 단정적 판단 없이 `none`으로 떨어졌다. `general` 갈래가 생겼다고 해서
수익성·낙찰 가능성 판단까지 열리지 않음을 확인했다.

### 3. 공고 특정 사실 질문 회귀 확인

- 질문: "최저입찰가격은 얼마인가요?"
- `answerType`: `notice`
- `answer`: "최저입찰가격은 12,000,000원입니다."
- `sourceField`: `price`

기존 `notice` 갈래가 `general` 신설 이후에도 그대로 동작한다.

### 4. 공매 절차 지식 밖의 애매한 질문

- 질문: "이 공고의 임대차 계약 갱신 특약은 어떻게 되어 있나요?"
- `answerType`: `none`, `answerable: false`, `answer: ""`

이 공고에 특정된 세부 계약 조건이라 공매 절차 일반 지식으로도 답할 수 없는 질문이
여전히 `none`으로 남는 것을 확인했다.

## 검증 내역

- **단위 테스트**: `python3 -I tests/test_docs_extraction.py` → **275/275 통과**
- **금지 문구 검사**: `python3 -I tests/test_screen_strings.py` → **20/20 통과**
- **e2e**: `npx playwright test --config=playwright.config.worktree.js` → **20 passed**

## 배포

검증 완료 뒤 포트 18982의 실서비스 프로세스를 이 커밋으로 재시작해
`https://suzuki-suse-bush-dictionaries.trycloudflare.com`에 반영했다.
