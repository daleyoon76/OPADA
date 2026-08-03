# 2팀 코드 완성도 검토

일시: 2026-07-05

## 닫은 리스크

| 등급 | 리스크 | 조치 |
| --- | --- | --- |
| P1 | `AI 준비 코치`, `AI 코치` 사용자-facing 잔존 | 앱/서버 문구를 `AI 우선 확인`, `AI가 ... 문장으로 분리`로 변경 |
| P1 | `boardTasks=[]`에서 `0/0` 또는 `NaN` 노출 가능 | `formatProgress()` 추가, 빈 체크리스트 상태 추가 |
| P1 | AI 매칭이 임대 샘플에만 맞을 가능성 | 매각/공매 short URL로 별도 Chrome CDP 검증 |
| P2 | 보드 상단 AI 요약 2개, 체크리스트 배지 3개 불일치 | 보드 상단 AI 요약도 3개로 맞춤 |

## 검증

- `node --check app/app.js` -> pass
- `python -m py_compile app/server.py` -> pass
- Chrome headless CDP:
  - 임대/대부 URL: `AI 우선 액션=내 업종으로 실제 사용 가능한지`
  - 매각/공매 URL: `AI 우선 액션=공동/대리입찰 서류가 나에게 필요한지`
  - `boardTasks=[]`: `체크리스트 대기`, `hasBadProgress=false`

## 남은 리스크

- AI 우선 매칭은 휴리스틱이다. 실제 서비스에서는 LLM 응답에 task target 후보를 명시시키거나 서버에서 task id를 함께 생성하는 방식으로 강화할 수 있다.
