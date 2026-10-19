# reviewer r3: 코치 질문창 r2 반영 커밋 2f0d0b4 재판정 결과

<sub>팀장 기록: reviewer 반환물을 반환 직후 원문 그대로 옮겼다(2026-10-19 · 읽기 전용 역할이라 팀장이 파일화). 엔터티로 바뀐 `<`·`>`·`&` 만 원래 글자로 되돌렸다.</sub>

## 1. 머리
- 판정 범위는 `1f011dd..2f0d0b4`(커밋 2f0d0b4 하나)이고, 판정한 최종 커밋은 `2f0d0b4` 입니다.
- `git diff 1f011dd..2f0d0b4 | shasum -a 256` 앞 16자는 `0b78f98567dced81` 입니다. packet 값과 일치합니다 [관측].
- 착수는 `2026년 10월 19일 월요일 16시 54분 02초 KST`, 마지막 `date` 는 `16시 55분 47초 KST` 입니다. 도구 호출은 4회입니다.
- 워크트리는 건드리지 않았습니다. `git status --short` 는 `?? node_modules` 하나뿐입니다 [관측].
- 사본은 `/private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/cec4c90c-5d4e-4a9c-9bd2-043030beb5a0/scratchpad/role-reviewer-terms/` 아래 `r3base`·`r3m1`·`r3m2`·`r3m3` 에 두었습니다. `__pycache__` 는 0개입니다.

## 2. 판정: GO
- r2 지적 네 건이 모두 닫혔습니다.
- 앞 라운드에 살아남았던 변이도 이제 잡힙니다.
- 열린 P0·P1·P2 는 없습니다.

## 3. 지적 표

| 등급 | 위치 | 내용 | 근거 | 처방 | 처방이 기대는 것 |
|---|---|---|---|---|---|
| 🔵 | `styles.css` `.coach-ask-answer > p:not(.coach-ask-note) + .coach-ask-reference` | 선택자를 옛 형태로 되돌려도 시험이 통과합니다. 화면 모양만 바뀌는 변이입니다. | [추론] E2E 는 이 경계선을 단정하지 않습니다(미실행). | 고칠 필요는 없고 기록만 합니다. [미실행] | 없음 |
| 🔵 | 거절 안내 글씨 크기 | 팀장이 선택 사항으로 남겼습니다. | [인용 2f0d0b4 본문] | 그대로 둡니다. | 없음 |

## 4. 고정 질문 답

**1. r2 지적이 닫혔는가**
- P2-a: 닫혔습니다.
  - [관측] `server.py` 판정식은 `start not in word_starts or any(start < b < end for b in word_bounds)` 입니다. r2fix 와 같은 조건입니다.
  - [관측] r2fix 와 2f0d0b4 를 무작위 질문 2만 건으로 대조했습니다. 차이는 0건입니다. 이 대조 도구는 r2 에서 변이를 9443건·408건 찾아낸 도구입니다.
  - [관측] `endcond2.py` 는 `bad []`, exit 0 입니다.
- P2-b: 닫혔습니다. 아래 변이를 사본에서 돌렸습니다 [관측].
  - r2 생존 변이 m1(offset 삭제): 397/399, 실패로 끝남
  - r2 생존 변이 m2(continue→break): 398/399, 실패로 끝남
  - 새로 넣은 변이 r3m3(`bounds.add(offset)` 삭제): 397/399, 실패로 끝남
  - 기준 판은 399/399 입니다. 팀장이 적은 값과 같습니다.
- P2-c: 닫혔습니다.
  - [관측] 미연결 갈래는 `ONBID_REFERENCE_OFFLINE_NOTE` 를 씁니다.
  - [관측] none 갈래는 `declinedHtml` 을 그대로 둡니다.
  - [관측] E2E 는 미연결 갈래에 `toBeVisible(offlineNote)` 와 `not.toContainText(declinedNote)` 를 둡니다.
  - E2E 실행 결과(34 passed)는 팀장 기록입니다 [인용 e2e-r2fix.txt].
- 🔵 국유·수탁 꼬리표: 닫혔습니다.
  - [관측] general 갈래 픽스처에 국유재산·수탁재산 refs 를 넣고 두 꼬리표가 보이는지 단정합니다.

**2. 새 상태가 제품으로서 맞는가**
- 미연결 문장 「AI 코치에 연결되지 않아 질문에 나온 용어의 온비드 설명만 보여 드립니다.」는 사실만 말합니다.
  - 용어 질문이면 아래 설명이 곧 답이 됩니다. 판단 질문이면 설명만 보인다는 사실이 드러납니다.
  - r2 에서 교정 사전과 대조해 0건이었고, 화면 문자열 검사는 20/20 이라고 합니다 [관측 r2 · 인용 strings-r2fix.txt].
- 의도대로 버린 것은 하나입니다. 띄어 쓴 오타 「유 찰되면」은 이제 잡히지 않습니다 [관측 r2fix]. 커밋 본문에도 적혀 있고, 받아들일 만합니다 [추론].

**3. 살아남는 변이**
- 앞 지적 표의 CSS 선택자 되돌리기가 있습니다 [추론]. 화면 모양만 바뀝니다.
- 동치라서 제외한 변이도 하나 있습니다.
  - `bounds.add(offset)` 을 `offset += len(token)` 뒤로 옮기는 변이입니다.
  - 그러면 경계 집합이 0이 빠지고 끝 위치가 들어갑니다. 두 값 모두 `start < b < end` 를 만족할 수 없으므로 결과가 같습니다 [추론].

**4. 처방이 기대는 것**
- 이번 라운드에는 처방이 없습니다.

**5. 최종 판정**
- GO 입니다.

## 5. 최종 커밋에서 확인할 종료 조건
- 명령(워크트리 루트에서):
  - `python3 -B tests/test_docs_extraction.py && python3 -I -B /private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/cec4c90c-5d4e-4a9c-9bd2-043030beb5a0/scratchpad/role-reviewer-terms/endcond2.py; echo $?`
- 기대 결과: 요약 줄 `399/399 통과` 와 `bad []`, 그리고 `0`
- 두 판에서 확인했습니다 [관측].
  - ⑴ 수정 전 `1f011dd`: `endcond2.py` 가 exit 1 이었습니다(r2).
  - ⑵ 지금 `2f0d0b4` 사본: 399/399, exit 0 입니다.
- push 하는 커밋이 `2f0d0b4` 와 다르면 그 차이 범위를 다시 판정해야 합니다.
