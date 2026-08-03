# 3팀 검증 기록

## 통과 항목

- `node --check app/app.js` 통과
- `python -m py_compile app/server.py` 통과
- Chrome headless CDP로 입력 화면, 임대 준비 보드, 매각 준비 보드 확인
- 사용자-facing bad string scan false:
  - `로컬 분석 API`
  - `Local MVP`
  - `Vertex AI`
  - `Gemini AI`
  - `API 키 없음`
  - `API 상태 확인`
  - `AI 준비 코치`
  - `AI 코치`
  - `질문과 근거`
  - `0/0`
  - `NaN`

## 캡처

- `screenshots/validation/33_input-clean-user-language.png`
- `screenshots/validation/36_board-ai-value-final-check.png`
- `screenshots/validation/38_sale-board-ai-priority-check.png`

## 남은 확인

- 실제 제출 DOCX/HWP에 이미지 삽입 후 줄바꿈, 캡션, 이미지 크기 확인 필요.
