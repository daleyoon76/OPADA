# visual-reviewer — 준비 보드 간결형 r2 (재판정)

- 대상: `e08a1f9`(r1 지적 반영). r1 원문: `visual-reviewer-board-compact-r1.md`
- 팀장 확인: 같은 HEAD 에서 아래 종료 조건을 18:29:53~18:30:18 KST 에 실행해 `exit=0` 을 받았다. `git diff e08a1f9 --stat -- src` 는 0줄.
- 아래는 리뷰어 반환물 원문이다(HTML 엔티티만 원래 기호로 되돌렸다).

---

**r2 판정: GO**

r1의 P1 두 건과 반영한 P2 두 건이 8976 화면에서 모두 닫혔습니다. 새 회귀는 없고, 판정을 막는 결함도 없습니다.

**머리**
- HEAD: `e08a1f912c29fdc0c1908971f6579210a02a0648`. test 워크트리 HEAD도 같습니다.
- 8976이 새 코드를 서빙하는지: `curl`로 `board-compact-r1` 캐시 키를 확인했습니다.
- sha256 (착수 직후 측정)
  - `src/app.js` = `f7b4cbf2abde2a93638208010cd9189aa4c53b743a7122a3d2fadc70aa9ce21e`
  - `src/styles.css` = `a075db6bf506a0c8f315a922dc3101733c40cc754958cce0510f096c6040a33b`
  - `src/index.html` = `3918a6c222976b39e3f5432af90e928e8a7833c5c65f2e74b9c3fd7c8d802f38`
- 작업 트리와 HEAD의 `src` 차이: `git diff e08a1f9 -- src | wc -l` = 0입니다.
- r2 실측 위치: `.../scratchpad/visual-reviewer/`
  - 스크립트: `review-r2.js`, `tabs-r2.js`
  - 결과: `r2/out.json`, `r2/*.png`
- 팀장이 덮어쓴 r1 `out.json`은 쓰지 않았습니다. 제가 직접 다시 돌린 값만 적었습니다.

## 지적 목록

**P0, P1: 없음.**

**P2-A. 「물어볼 문장」 탭의 askAgency 행을 펼치면 같은 안내문만 3번 나옵니다** [관측 `r2/mob-question-tab.png`, app.js:1568-1575]
- 질문 문장 전체가 이미 summary에 있습니다.
- 그래서 펼치면 「AI 코치가 이 공고에 맞춰 정리한 문장입니다…」만 보입니다.
- 또 이 문장은 llmStatus를 보지 않습니다. 규칙 기반 상태에서도 「AI 코치가 정리한」이라고 말합니다.
  - `renderBoardCoach` 주석의 원칙 「모델에 붙지 않았으면 AI가 했다고 말하지 않는다」와 어긋납니다.
  - 다만 헤더 「AI 코치에게 물어보기」도 이미 규칙 모드에서 같은 이름을 쓰고 있어서 P2로 둡니다.
- 권고: askAgency 행은 `<details>`가 아닌 평문 행으로 두거나, 문구를 llmStatus에 따라 나눕니다.

**P2-B. 매칭 품질 문제: 「입찰기간 확인」 할 일에 「현장 상태와 인수 범위」 확인 항목이 붙습니다** [관측 `r2/mob-task2-open.png`]
- 「먼저 할 일」 줄이 새로 보이면서 어긋남이 더 눈에 띕니다.
- 원인은 `getAiTaskAssignments` 점수 매칭이고, 이번 diff 밖의 기존 동작입니다 [추론]. 다음 probe 후보로 둡니다.

**server.py d56d47f의 화면 영향**
- 응답 모양은 바뀌지 않았습니다 [diff 관측].
- 429가 나면 「분석 중」이나 「답변을 찾는 중」 상태가 최대 3초 더 길어질 뿐이고, 화면 회귀는 없습니다.

## 회귀 확인 [관측, `r2/out.json`]
| 항목 | 1280px | 390px |
|---|---|---|
| 가로 스크롤(docW/vw, 펼친 상태 포함) | 1280/1280 | 390/390 |
| 넘침(scrollWidth > clientWidth, 접은 상태와 펼친 상태) | 0건 | 0건 |
| 할 일 제목과 배지 겹침 | 0/5 | 0/5 |
| 탭 바 넘침(sw/cw) | 1150/1150 | 328/328 (2줄로 줄바꿈) |
| 콘솔 에러 (보드, 규칙 모드, 미분석, 실패) | 0건 | 0건 |
| Enter 1회당 /api/ask 요청 | 1 | 1 |
| 페이지 높이 (접은 상태) | 1594px | 2486px (r1 2446 대비 +40, 탭 2줄 몫) |

- 경계 폭 확인 [관측 `tabs-r2.js`]
  - 900px: 탭 1줄, 838/838
  - 901px: 탭 1줄, 811/811
  - 390px: 탭 2줄(행 오프셋 0과 40), 7개 모두 보임
  - 미디어쿼리 경계 양쪽에서 숨는 탭이 없습니다.
- 금지 표현: 이번 diff의 추가 문구는 「먼저 할 일」, 「AI 코치가 이 공고에 맞춰 정리한 문장입니다…」, 새 placeholder입니다.
  - 금지 표현 13종 중 어느 것에도 해당하지 않습니다 [육안 대조 · r2에서 grep은 다시 돌리지 않았습니다].

## r1 지적별 닫힘 여부
| r1 지적 | 상태 | 근거 |
|---|---|---|
| P1-1 askAgency 소실 | 닫힘 | DOM에 3/3, 데스크톱과 모바일 모두. 탭에서 맨 위 3행으로 보임(`r2/mob-question-tab.png`) |
| P1-2 모바일 탭 3개 숨음 | 닫힘 | 390px에서 7/7 보임, 2줄 |
| P2-1 action 소실 | 닫힘 | action 3/3, reason 3/3, 「먼저 할 일」 줄로 표시 |
| P2-4 placeholder 잘림 | 닫힘 | 문구 폭 176px, 입력칸 내부 폭 217px (canvas measureText) |
| P2-2 화살표 키 | 남김. 판정 영향 없음 | Enter와 Space로 조작할 수 있습니다 |
| P2-3 배지-내용 어긋남 | 남김. 판정 영향 없음 | 서버 판정 소관이고 화면 분기는 정상입니다 |
| P2-5 미분석 빈 탭 | 남김. 판정 영향 없음 | 에러 0, 가로 넘침 0 |
| P2-6 관심 초점 라벨 | 남김. 판정 영향 없음 | 분석 화면에는 남아 있습니다 |
| P2-7 완료 배지 대비 | 남김. 판정 영향 없음 | 기능 문제가 아닙니다 |

- r1 종료 조건(askAgency 3/3 표시)도 제가 다시 돌린 `r2/out.json` 기준으로 충족했습니다.

## 확인하지 못한 것
- **e2e 17/17과 단위 275/275**: 팀장 실측 [인용]입니다. 8976용 설정 사본을 만들면 5분 안에 돌릴 수 있습니다.
- **429 재시도 경로의 실제 화면**: 429를 일부러 낼 수 없어 관측하지 못했습니다. 서버 stub이 필요해 20분 정도 걸립니다.
- **한글 IME 조합 중 Enter**: r1과 같이 확인하지 못했습니다. 실기기에서 1분이면 됩니다.
- **391~899px 중간 폭**: 390px, 900px, 901px 세 점만 측정했습니다.

## 최종 커밋에서 확인할 종료 조건
```
S=/private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/f8aeebcf-ab9b-40d5-ae4d-3a1efe657c86/scratchpad/visual-reviewer; node $S/review-r2.js >/dev/null && node -e 'const o=require(process.argv[1]);const m=o.mob;process.exit(m.tablist.sw<=m.tablist.cw&&m.coachData.ask.length>0&&m.coachData.ask.every(a=>a[1])&&m.coachData.checks.every(c=>c[2])&&!m.errs.length?0:1)' $S/r2/out.json
```
- 93bf642에서는 이 조건이 실패합니다. r1 실측값이 tablist 541>328, ask 0/3, action 0/3이었습니다.
- e08a1f9에서는 위 r2 실측 값 기준으로 통과입니다(328/328, ask 3/3, action 3/3, 에러 0). 이 한 줄 자체를 따로 돌린 종료 코드는 아직 기록하지 않았습니다.
