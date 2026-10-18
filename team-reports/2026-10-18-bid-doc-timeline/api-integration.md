# 공공데이터 API 제출서류 필드 연동

- 작성 시각: 2026-10-18 19:44 KST (`date` 출력)
- 코드 레포: `/Users/user/Documents/Dev/Hometest_op-agentic` · 브랜치 `agentic-journey`
- 착수 기준 커밋: `d3b3cca`
- 인증키: `ONBID_API_SERVICE_KEY` 가 `.env.local` 에 실제로 존재합니다(길이 64). 직전 작업자가 적은 「이 기기에 키가 없다」는 전제는 사실이 아닙니다. 키 값은 이 문서와 어떤 로그에도 남기지 않았습니다.

---

## 0. 한 줄 결론

API 호출이 막힌 원인은 인증키가 아니라 **서버가 이미 받아 쓰는 `cltrInfVO` 객체에서 `pbctCdtnNo` 를 꺼내지 않고 버리는 것**이었고, 그 값을 채워 넣으니 `getCltrBidInf2` 가 재산유형 6종에서 모두 응답했습니다. 다만 **제출서류의 「내용」 필드는 거의 전부 비어 있고 「제출기한·제출방식」에만 쓸 만한 값이 옵니다.**

---

## 1. API 실제 응답

### 1-1. 호출이 왜 한 번도 되지 않았는가

`getCltrBidInf2`(`item_bid_detail`)는 `cltrMngNo` 와 `pbctCdtnNo` 를 **둘 다** 요구합니다. 하나만 보내면 `resultCode=11 NO_MANDATORY_REQUEST_PARAMETERS_ERROR` 가 돌아옵니다. [관측]

`src/server.py:1198` 의 조건이 `if cltr_mng_no and pbct_cdtn_no:` 이므로, `pbct_cdtn_no` 가 비면 이 API는 호출 대상 목록에 들어가지도 않습니다.

그 `pbct_cdtn_no` 는 `build_notice()`(2246행)에서 온비드 화면의 hidden input 과 URL 쿼리에서만 읽습니다. 그런데 표본 공고 URL로 실제로 돌려 보면 그 값이 **빈 문자열**입니다. [관측]

```
publicData.identifiers = {"pbancMngNo": "202605-13303-00", "cltrMngNo": "2026-04177-001", "pbctCdtnNo": ""}
호출된 서비스 3개 = real_estate_detail · notice_detail · notice_bid_detail
item_bid_detail 은 목록에 없음
```

🔴 **그런데 그 값은 이미 서버 손에 있습니다.** `fetch_onbid_cltr_detail()`(916행)이 온비드 AJAX `inqPbancDtlCltrInf.do` 에서 받아 오는 `cltrInfVO` 객체에 `pbctCdtnNo` 가 들어 있습니다. 필드 119개 가운데 하나입니다. [관측]

| 표본 | `cltrInfVO.cltrMngNo` | `cltrInfVO.pbctCdtnNo` |
| --- | --- | --- |
| 01 압류재산/매각 | `2026-04177-001` | `5978916` |
| 04 국유재산/임대 | `2026-062564-645` | `6060942` |
| 09 공유재산/매각 | `2026-0300-002152` | `5962095` |

`build_notice()` 는 이 객체에서 `cltrMngNo` 만 꺼내 쓰고(2258행) `pbctCdtnNo` 는 보지 않습니다. 이것이 41일 동안 이 API가 한 번도 호출되지 않은 실제 원인입니다.

### 1-2. 재산유형 6종의 실제 응답값

진행 중인 물건은 온비드 메인의 신규·마감임박 물건 조회 AJAX(`inqMainNewCltr.do` · `inqMainddlnImminentCltr.do`)로 12건을 받아, 재산유형 코드가 서로 다른 것만 골랐습니다. 2026-10-18 기준 진행 중 공고입니다(`onbidPbancNo` 908061~909660).

고정 샘플은 `tests/fixtures/cltr_bid_inf_samples.json` 에 6건을 저장했습니다. 응답 필드 수는 6건 모두 65개입니다.

**지시받은 15개 제출서류 필드 + 관련 플래그의 실측값**

| 필드 | 공유재산/매각(분양) | 불용품/매각 | 공유재산/임대 | 국유재산/매각 | 기타일반재산/매각 | 파산자산/매각 |
| --- | --- | --- | --- | --- | --- | --- |
| `bidPtctAplyYn` | `N` | `N` | `N` | `N` | `N` | `N` |
| `bidRltnDcmtCont` | 빈값 | 빈값 | 빈값 | 빈값 | 빈값 | 빈값 |
| `bidRltnDcmtSbmsnTermNm` | 빈값 | 빈값 | 빈값 | 빈값 | 빈값 | 빈값 |
| `bidRltnDcmtSbmsnMthodNm` | 빈값 | 빈값 | 빈값 | 빈값 | 빈값 | 빈값 |
| `collbMthodDcmtCont` | 빈값 | 빈값 | 빈값 | 빈값 | 빈값 | 빈값 |
| `collbDcmtSbmsnTermNm` | `입찰마감일시 전까지` | 빈값 | 빈값 | 빈값 | 빈값 | 빈값 |
| `collbDcmtSbmsnMthodNm` | `직접제출` | 빈값 | 빈값 | 빈값 | 빈값 | 빈값 |
| `subtBidDcmtCont` | 빈값 | `대리입찰서류` | 빈값 | 빈값 | 빈값 | `대리입찰서류` |
| `subtBidDcmtSbmsnTermNm` | 빈값 | `입찰마감일시 전까지` | 빈값 | 빈값 | 빈값 | `입찰마감일시 전까지` |
| `subtBidDcmtSbmsnMthodNm` | `직접제출` | `직접제출` | 빈값 | 빈값 | 빈값 | `온라인/직접제출` |
| `bidPtctAplyDcmtCont` | 빈값 | 빈값 | 빈값 | 빈값 | 빈값 | 빈값 |
| `bidPtctAplyTermNm` | `~` | `~` | `~` | `~` | `~` | `~` |
| `bidPtctDcmtSbmsnMthodNm` | 빈값 | 빈값 | 빈값 | 빈값 | 빈값 | 빈값 |
| `tdpsSbtnDcmtYn` | `N` | `N` | `N` | `N` | `N` | `N` |
| `tdpsSbtnDcmtCont` | 빈값 | 빈값 | 빈값 | 빈값 | 빈값 | 빈값 |
| `tdpsSbtnDcmtSbmsnTermNm` | 빈값 | 빈값 | 빈값 | 빈값 | 빈값 | 빈값 |
| `tdpsSbtnDcmtSbmsnMthodNm` | 빈값 | 빈값 | 빈값 | 빈값 | 빈값 | 빈값 |
| `qlfcLmtCdtnCont` | `없음(모든 회원 입찰가능)` | 〃 | 〃 | 〃 | 〃 | 〃 |
| `rgnLmtCdtnCont` | 빈값 | 빈값 | `부산광역시` | 빈값 | 빈값 | 빈값 |
| `etcLmtCdtnCont` | 빈값 | 빈값 | 빈값 | 빈값 | 빈값 | 빈값 |

### 1-3. 이 표에서 읽히는 것

**⑴ 서류 「내용」 필드는 쓸 수 없습니다.** 다섯 개(`bidRltnDcmtCont`·`collbMthodDcmtCont`·`bidPtctAplyDcmtCont`·`tdpsSbtnDcmtCont`) 가운데 값이 온 것은 하나도 없습니다. `subtBidDcmtCont` 만 2건에서 값이 왔는데 그 값이 `대리입찰서류` 라는 **구분명 그대로**입니다. [관측]

사실관계 검증 §1 사실 9가 「화면 표의 서류명 칸이 구분명 그대로였으니 API에도 같은 구분명이 들어 있을 가능성이 높다」고 추론했는데, 그 추론이 맞았습니다. API는 화면보다 더 나은 서류명을 주지 않습니다.

**⑵ 제출기한과 제출방식에는 쓸 만한 값이 옵니다.** 이것이 화면 파싱으로는 얻기 어려웠던 것입니다. 값의 종류는 세 가지였습니다: `입찰마감일시 전까지` · `직접제출` · `온라인/직접제출`.

**⑶ 🔴 플래그가 `N` 인데도 기한·방식 값이 남아 있는 사례가 있습니다.** 공유재산 분양 건은 `collbBidPsblYn='N'`(공동입찰 불가)인데 `collbDcmtSbmsnTermNm` 과 `collbDcmtSbmsnMthodNm` 에 값이 있고, `subtBidPsblYn='N'`(대리입찰 불가)인데 `subtBidDcmtSbmsnMthodNm='직접제출'` 이 있습니다. [관측]

| 샘플 | `collbBidPsblYn` | 공동 기한·방식 | `subtBidPsblYn` | 대리 기한·방식 |
| --- | --- | --- | --- | --- |
| 공유재산/매각(분양) | `N` | **값 있음** | `N` | **방식만 값 있음** |
| 불용품/매각 | `N` | 빈값 | `Y` | 값 있음 |
| 공유재산/임대 | `N` | 빈값 | `N` | 빈값 |
| 국유재산/매각 | `N` | 빈값 | `N` | 빈값 |
| 기타일반재산/매각 | `N` | 빈값 | `N` | 빈값 |
| 파산자산/매각 | `N` | 빈값 | `Y` | 값 있음 |

그러므로 기한·방식을 화면에 붙일 때는 **그 입찰 방식이 실제로 가능한지를 플래그로 먼저 걸러야 합니다.** 걸러지 않으면 「공동입찰이 안 되는 물건에 공동입찰 서류 제출기한을 안내하는」 거짓 안내가 됩니다.

**⑷ `bidPtctAplyTermNm` 은 6건 전부 `~` 입니다.** 시작과 끝을 잇는 구분자만 남은 값이고 날짜가 없습니다. 쓸 수 없습니다.

**⑸ `qlfcLmtCdtnCont` 는 6건 전부 같은 값입니다.** 균일한 결과는 측정 실패의 신호일 수 있어 따로 확인했는데, 같은 호출에서 `rgnLmtCdtnCont` 는 1건만 값이 있고 `subtBidDcmtCont` 는 2건만 값이 있어 값이 갈립니다. 그러므로 측정 실패가 아니라 실제로 이 6건이 모두 자격제한 없는 공매인 것으로 봅니다. 다만 **제한이 있는 물건의 값이 무슨 형태인지는 확인하지 못했습니다.** [미확인]

### 1-4. 확인하지 못한 것

- 🔴 **압류재산(`cltrPrptDivCd=0007`)의 물건 단위 응답을 확인하지 못했습니다.** 2026-09-07 표본 23건은 차수가 끝나 `resultCode=03 NODATA_ERROR` 를 돌려주고, 온비드 메인의 진행 중 물건 12건에 압류재산이 없었습니다. 압류재산 공고 검색 AJAX(`inqSzrPrptPbancClg.do`)는 응답했지만 검색 조건 파라미터를 알지 못해 `totalCount=0` 이었습니다. [관측]
- 압류재산의 **공고 단위** 값은 확인했습니다. `getPbancBidInf2`(이미 연동돼 있는 API)가 표본 01 압류재산에서 `bidPtctAplyYn='N'` · `tdpsSbtnDcmtYn='N'` · `nrnkAplyPsblYn='Y'` · `pcmtPayMtdCont='일시불'` · `pcmtPayTermCont='30일'` · `pbctTdpsCont='입찰가격*10%'` 를 돌려줍니다. [관측] 다만 이 API에는 서류 「내용·기한·방식」 필드 자체가 없습니다(응답 필드 17개).
- `bidPtctAplyYn='Y'`(입찰참가신청이 필요한) 물건을 한 건도 보지 못했습니다. 그 경우 `bidPtctAplyDcmtCont`·`bidPtctAplyTermNm`·`bidPtctDcmtSbmsnMthodNm` 에 값이 채워지는지는 **미확인**입니다. 명세 설명문이 「[입찰참가신청필요여부 : Y인 경우]」라고 적고 있어 그때 채워질 것으로 보이지만 관측은 아닙니다. [추론]
- 공공데이터 목록 API(`getPbancList2` · `getRlstCltrList2`)의 필수 파라미터를 알아내지 못했습니다. 다섯 가지 조합을 시도해 모두 `resultCode=11` 이었습니다. [관측] 이 게이트웨이는 웹 검색이 꺼져 있어 포털 명세를 조회하지 못했습니다.

---

## 2. 연동한 것과 연동하지 않은 것

(2단계 구현 뒤 작성)

## 3. 기한이 어긋나는 사례

(2단계 구현 뒤 작성)

## 4. `CONTRACT_STAGE_RE` 정확도 측정

(3단계 작업 뒤 작성)

## 5. 검증 결과

(구현 뒤 작성)

## 6. 구현됨 / 로컬 검증됨 / 미검증

(구현 뒤 작성)

## 7. 남은 작업

(구현 뒤 작성)
