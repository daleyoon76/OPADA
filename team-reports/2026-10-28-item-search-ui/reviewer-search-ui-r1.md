# reviewer r1: 조건으로 물건 찾기 (/api/search 화면 노출 · 마감 물건 제외 · usbdNft 덮어쓰기 중단)

> 읽기 전용 역할의 반환물을 팀장이 옮겨 적었다(2026-10-28 · agent-team 규칙 7). 본문은 반환 원문 그대로다.
> 판정 대상 diff sha256 `09280830c3a748487f8a55bf045d1f6ff5d9607c983bdba8848e3ae32ffcfbe8` · 기준 커밋 `e76a508`.
> 처분은 맨 아래 「팀장 처분」 절에 있다.

- 판정 대상: diff 사본 `scratchpad/review-search/target.diff`
  - sha256 `09280830c3a748487f8a55bf045d1f6ff5d9607c983bdba8848e3ae32ffcfbe8`, 기준 커밋 e76a508 [관측]
  - 작업 트리의 `git diff e76a508 -- src tests` 해시도 이 값과 같다. 판정 도중 트리가 바뀌지 않았다 [관측].
- 내가 돌린 것: `python3 tests/test_search_filter.py` 1회 → 49/49, exit 0 [관측] · scratch 단위 재현 2개(`repro.py` · `cache_stats.py`).
- 판정: **조건부 GO**. P0 0건, P1 1건.

## 1. 결함

### P1-1. 목록 갱신 실패 문장의 urlopen 원문이 그대로 화면에 나간다 (I5 관례 위반 · 이번 diff 가 새로 노출)
- `src/server.py:4601` `cache["refreshError"] = f"목록 갱신 중 오류가 발생해 기존 캐시를 그대로 씁니다: {exc}"` → `server.py:5057` 이 `cacheRefreshError` 로 내보냄 → 새 `src/app.js:3750` 이 escape 만 하고 그림.
- [관측] 재현: 캐시 경로를 없는 파일로, `fetch_all_cltr_items` 가 URLError 를 던지게 바꾸자 `목록 갱신 중 오류가 발생해 기존 캐시를 그대로 씁니다: <urlopen error [Errno 8] nodename nor servname provided, or not known>`.
- 재현 경로: 캐시가 24시간 넘었고 네트워크가 끊기거나 API 타임아웃인 상태에서 검색. 응답 200 이고 메타 줄에 원문이 보인다.
- [추론] 캐시가 빈 상태(첫 가동)에서 갱신이 실패하면 items 가 `[]` 라 「조건에 맞는 입찰 가능한 물건이 없습니다. 조건을 넓혀…」가 뜬다. 원인은 목록 미수신인데 조건을 넓히라고 안내한다.
- 처방 [미실행]: ⑴ `{exc}` 를 빼고 원문은 stderr 로. 문장 후보 「목록을 새로 받지 못해 이전에 받은 목록으로 찾았습니다.」 ⑵ `cacheFetchedAt` 가 비고 items 0건이면 「지금 물건 목록을 받지 못했습니다. 잠시 뒤 다시 시도하십시오」.
- 기대는 것: `refresh_cltr_cache()` 반환 dict 와 `fetchedAt` 빈 값(`server.py:4519`). `refreshError` 를 단정하는 기존 테스트 0건 [관측 · grep].

### P2-1. 검색 요청 중에도 Enter 로 같은 검색을 다시 보낼 수 있다
- 버튼은 disabled 지만 `app.js:3983` keydown 이 `runItemSearch()` 를 다시 부른다. 화면 상태는 requestId 로 꼬이지 않는다 [관측].
- [추론] 서버에서는 LLM 해석 · 상위 5건 재조회가 다시 돌고, 첫 검색이면 전체 수집(실측 69.9초)이 잠금 없이 겹칠 수 있다.
- 처방: `runItemSearch` 머리에서 `if (byId("item-search-run").disabled) return;`.

### P2-2. 분석 중에 검색 결과가 도착하면 새로 그린 「이 물건 분석하기」 버튼이 활성으로 보인다
- `setAnalysisInputsBusy(true)` 는 그 시점의 버튼만 잠근다(`app.js:3863`). 클릭은 `startAnalysisFromSearch` 의 `input.disabled` 가드가 조용히 무시한다 [관측].
- 처방: `renderItemSearchResult` 끝에서 `notice-url.disabled` 를 보고 같은 상태로 그린다.

### P2-3. 실시간 재확인 값이 「지금 회차」인지 확인되지 않았다 (추론 · 확인 필요)
- `refresh_top_items_live` 는 `live_items[0]` 의 마감일시를 덮어쓴다. usbdNft=0 실측은 `items[0]` 이 첫 회차일 가능성과 맞는다 [추론].
- 그렇다면 과다 제외 또는 다른 회차 날짜 노출. 불변식은 2차 split 이 지킨다. 닫는 비용: 라이브 1회.

### P2-4. 400 경로의 `str(exc)` 원문 노출 가능성 (기존 동작 · 이번 화면이 통로)
- `/api/search` 의 `except (ValueError, URLError, TimeoutError)` 가 400 으로 `str(exc)` 를 주고 화면은 500 미만이면 그대로 보인다. 화면에서 닿는 입력은 찾지 못했다 [추론].

XSS/주입 [관측]: 칩 · 물건명 · 장소 · facts · `cacheFetchedAt` · `data-search-analyze` · `href` 모두 `escapeHtml` 을 거친다. `detailUrl` 은 고정 접두 + `urlencode` 라 `javascript:` 가 들어올 수 없다.

## 2. 불변식(과거 마감일 비노출)을 깨는 경로

| 경로 | 결과 | 근거 |
|---|---|---|
| limit(5) 밖 물건 | 지켜짐. 1차 · 2차 split 이 전체에 적용 | [관측] `server.py:5047` · `5050` |
| 마감일시 14자리 · 하이픈 형식 | 지난 날짜는 빠짐 | [관측] repro B |
| 마감일시 8자리 · 2자리 연도 | 빠지지 않고 남음 | [관측] repro B |
| 위 형식이 화면에 날짜로 나가는가 | 안 나감. 12자리 미만이면 빈 문자열 | [관측 · 코드] |
| 실제 캐시에 그런 형식 | 없음. 6,321건 전부 12자리 · 열린 상태인데 지난 물건 0건 | [관측] fetchedAt 15:40:01 · 15:55 기준 |
| 캐시 시각과 현재 시각 차이 | 지켜짐. 요청마다 `time.strftime` | [관측] |
| 서버 TZ 가 KST 가 아닐 때 | 깨짐. TZ=UTC 면 지난 9시간 안에 마감된 물건이 남음 | [추론] · P2 |
| 화면을 열어 둔 채 마감 시각이 지날 때 | 그린 결과에 남음. 다시 검색하면 빠짐 | [추론] 설계 한계 · 기록만 |

- 8자리 형식은 fail open. 처방 후보 fail closed 는 S31 과 충돌하므로 팀장 결정.

## 3. 새 상태가 제품으로서 맞는가

- 프로필 목적(매입)과 결과 처분방식(임대)이 달라도 걸러지지 않는다. 열린 2,691건 중 임대 635건 [관측]. facts 에 처분방식이 보인다. 칩에 「매각 · 임대 모두」 안내를 두면 오해가 준다(제품 판단).
- 10건 제한은 맞다. 6~10번째는 「목록 기준 시각의 값입니다」로 표지가 섞인다.
- 첫 검색 대기 문구 「1분 정도」 ↔ 실측 69.9초, 대체로 맞다.
- 안내 문구 「입찰 기간 안에 있는 물건만」은 「입찰준비중」(시작 전)도 남기므로 「입찰 기간이 끝나지 않은 물건만」이 정확하다.
- 「URL이 없으면」 패널이 처리 단계 패널 아래에 있고 Step 1-2 라벨이 두 번 나온다. 배치는 제품 판단.

## 4. 단순화 여지
- `describeSearchFilters` 의 `const won = (value) => formatSearchWon(value);` 는 별칭일 뿐이다. 그 밖에 과한 코드는 없다.

## 5. 처방별 기대는 것

| 처방 | 기대는 것 | 실행 |
|---|---|---|
| P1-1 ⑴ | `server.py:4601` | 미실행 · 테스트 의존 0건 grep 실행 |
| P1-1 ⑵ | `fetchedAt` 빈 값 · `cacheFetchedAt` | 미실행 |
| P2-1 | `item-search-run.disabled` | 미실행 |
| P2-2 | `notice-url.disabled`(`app.js:3861`) | 미실행 |
| P2-3 | 응답 행 순서(미관측) | 미실행 |
| fail closed | `server.py:4894` `len(end) >= 12` · S31 충돌 | 미실행 |

## 검증 누락
- 2차 split 배선: 단위 테스트 없음 · 라이브만 [인용]. 라우트를 함수로 뽑아야 시험 가능.
- JS 세 함수 · 결과 0건 · 오류 화면: 라이브 1회 필요.
- 팀장이 인용한 변이 12종과 라이브 결과는 [인용] · 재실행 안 함.

## 6. 판정
- **조건부 GO**. 조건은 P1-1 반영.
- 최종 커밋 종료 조건: `grep -c 'refreshError"\] = f".*{exc}' src/server.py` 가 0. 수정 전 1. 대리 지표이므로 URLError 주입 뒤 `refreshError` 에 `urlopen` 이 없는지 보는 단위 테스트를 권한다.

---

## 팀장 처분 (2026-10-28)

| 지적 | 처분 | 근거 |
|---|---|---|
| P1-1 ⑴ 원문 노출 | 채택 · 반영 | `{exc}` 제거 · stderr 로그 · 단위 테스트 S39~ |
| P1-1 ⑵ 빈 캐시 안내 | 채택 · 반영 | 화면에서 `cacheFetchedAt` 빈 값 + 0건 분기 |
| P2-1 Enter 중복 | 채택 · 반영 | 가드 1줄 |
| P2-2 버튼 상태 | 채택 · 반영 | 렌더 때 `notice-url.disabled` 반영 |
| P2-3 회차 행 | 기각(결함 아님) | [관측] 라이브 1회(실행 시각 미기록 · 다음 명령의 `date` 16:00:33 보다 앞): 19회 물건 응답 1행 · `pbctCdtnNo` 6212867 · 입찰기간 202611271000~1700 이 캐시 지금 회차와 같음. 다른 것은 usbdNft 뿐 |
| P2-4 400 원문 | 이월 | 화면에서 닿는 입력 미발견 · 기존 동작 |
| 서버 TZ | 채택 · 반영 | 현재 시각을 KST(UTC+9)로 고정 계산 |
| 8자리 fail open | 이월(현행 유지) | 캐시 0건 · S31 결정 유지 |
| 안내 문구 | 채택 · 반영 | 「입찰 기간이 끝나지 않은 물건만」 |
| 처분방식 안내 · 패널 위치 | 이월(동원님 판단) | 제품 판단 |
| `won` 별칭 | 채택 · 반영 | 별칭 제거 |
