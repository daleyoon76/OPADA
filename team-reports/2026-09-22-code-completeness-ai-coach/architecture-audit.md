# architecture-auditor 반환물 — AI 코치 로직 구조 감사 (2026-09-22)

조사 대상 커밋: `9a1e0819babdcd98a2f285ac7409d3d31046419c` (Hometest_op, `main`)

본 감사는 읽기 전용입니다. 코드는 수정하지 않았습니다.

---

## 구조 요약

`build_ai_coach()`(server.py:1692)가 `vertex_ai_coach → gemini_ai_coach → local_ai_coach` 순으로 시도하지만, 실제 데이터 생성 로직은 **`local_ai_coach()`(server.py:1308) 단 하나**입니다.

- `gemini_ai_coach`(1537)·`vertex_ai_coach`(1609)는 LLM 응답을 JSON 파싱만 하고(`parsed` 변수), 그 파싱된 내용을 **버립니다**. 실제로 반환하는 것은 `local = local_ai_coach(notice, docs)` 결과에 `sanitize_ai_text`만 적용한 것입니다(1601·1684행). `llmStatus`와 `model` 필드만 LLM 성공 여부를 반영합니다.
- 따라서 `confirmedFacts`·`unresolvedChecks`는 LLM 연결 여부와 무관하게 **항상 local_ai_coach가 만든 값**입니다. 이는 문제 1·2의 수정 지점이 한 곳으로 좁혀진다는 뜻이라 구조적으로는 유리합니다.
- 다만 화면 배지("AI 분석 완료" vs "규칙 기반 누락 점검", app.js:962·1074)는 `llmStatus === "connected"`만 보고 갈립니다. 사용자에게는 "AI가 판단했다"는 인상을 주지만 실제 판단 로직(콘텐츠)은 규칙 기반과 동일합니다. 이 자체가 문제 3과 같은 종류의 "표시와 실제 근거의 불일치" 구조이며, 참고 사례로만 남깁니다.

`user-type`·`asset-focus`는 서버로 전혀 전달되지 않습니다(아래 1번 참조). 클라이언트에는 이미 이와 유사한 축(사용자 유형 기반 필터링)을 서버 데이터에 매칭시키는 **동작 중인 선례**가 하나 있습니다(`DOC_GROUP_CONDITION_USER_TYPES`, app.js:1128) — 다만 그 선례가 다루는 축(법인/개인 서류 조건)과 문제 1이 원하는 축(임대 후 업종·용도 적합성)은 데이터 종류가 다릅니다.

---

## 1. user-type / asset-focus가 서버에 전달되는가

**전달되지 않습니다.** "안 쓰는 것"이 아니라 "애초에 요청에 실리지 않습니다."

- 분석 요청은 app.js:1766 한 곳입니다: `fetch(/api/analyze?url=${encodeURIComponent(getNoticeInput())})`. 쿼리 파라미터는 `url` 뿐입니다.
- 서버 라우팅도 이를 뒷받침합니다: server.py:2335~2337의 `do_GET`은 `parsed.query`에서 `url`만 꺼내 `build_notice(raw_url)`을 호출합니다. `user-type`·`asset-focus`를 읽는 코드가 없습니다.
- `getSelectedUserType()`(app.js:1381)·`getSelectedFocus()`(app.js:589)는 순수 클라이언트 상태 조회 함수이고, 호출부는 전부 클라이언트 렌더링입니다:
  - `getApplicableTasks()`(747) — 보드 작업 목록 필터
  - `renderDocChecklist()`의 `getDocGroupUserTypes` 매칭(1167~1173) — 서류 그룹 표시/접힘
  - `getFitMessage()`(841) — 상단 "목적과 공고 유형이 맞는지" 안내 문구
  - 샘플 미리보기 라벨(1458)
- 즉 `local_ai_coach`가 이 값을 "받고도 무시"하는 게 아니라, **함수 시그니처(`notice, docs`) 자체에 이 값이 들어올 경로가 없습니다.** 이건 파라미터 누락이 아니라 API 계약 자체에 축이 하나 빠진 것입니다.

---

## 2. unresolved_checks를 사용자 입력 기반으로 매칭시키려면

**결론부터: 지금 있는 데이터로는 부분 개선만 가능하고, "내 업종으로 실제 사용 가능한지" 같은 핵심 판단은 불가능합니다.**

지금 있는 데이터로 가능한 것:
- `asset-focus`가 서버로 전달된다면, `is_sale` 분기와 `asset-focus`(lease/sale/startup)를 대조해 **명백한 불일치**(예: focus=sale인데 서버가 판단한 유형은 임대)일 때 안내 문구를 조정하는 정도는 가능합니다. 다만 이 판단은 이미 클라이언트 `getFitMessage()`(841~872)가 별도로 하고 있습니다(아래 리스크 참조).
- `user-type`(개인/법인/개인사업자/예비창업자)은 서버의 `docChecklist.items[].conditionKeys`(corp/person 등, server.py:1316)와 같은 축을 공유합니다. 이 축은 app.js가 이미 클라이언트에서 매칭 중입니다(`DOC_GROUP_CONDITION_USER_TYPES`, 1128). 즉 **서류 조건 축은 재사용 가능**하지만, 이는 문제 1이 지적한 "업종으로 실제 사용 가능한지"·"현장 상태"·"반복 비용" 세 항목과는 다른 축입니다.

지금 있는 데이터로 불가능한 것 (더 필요한 데이터):
- "내 업종으로 실제 사용 가능한지"를 판정하려면 공고별 **용도 제한/사용 승인 조건** 구조화 필드가 필요합니다. `notice` 딕셔너리에는 `assetType`·`title`·`dispositionLabel`·`noticeOutline`(비구조화 텍스트) 정도만 있고, "이 시설이 카페/사무실/창고 등 특정 업종에 쓰일 수 있는가"를 나타내는 필드가 없습니다.
- "현장 상태와 인수 범위", "대부료 외 반복 비용"도 마찬가지로 구조화된 필드가 없고, `noticeOutline`/`sections`(원문 텍스트 조각)에서 정규식으로 추출을 새로 만들어야 하는데, 이는 이번 조사 범위를 넘는 별도 파싱 작업입니다(참고 문서에 나온 회차 파싱 이슈와 같은 부류의 작업량).
- 결론: **user-type/asset-focus를 서버로 보내는 배선을 고쳐도, 그 자체만으로는 문제 1의 세 항목을 "매칭"시킬 수 없습니다.** 배선을 고치면 할 수 있는 것은 "명백히 무관한 축(공고 유형 vs 검토 목적) 불일치 감지"뿐이고, "업종 적합성 실제 판정"은 새 데이터 추출이 선행돼야 합니다.

---

## 3. confirmedFacts에 상태 플래그를 추가하는 방식이 맞는가

**`docChecklist.status` 패턴 재사용이 구조적으로 맞습니다.** 이미 같은 문제(추출됨 vs 실패)를 겪은 자리가 있고, 그 자리의 상태 값 체계(`extracted`/`attachment_only`/`not_in_notice`/`not_found`, app.js:1102 `docChecklistStatusBadge`)가 이미 동작 중입니다.

- 서버 쪽 근거: `confirmed_facts`는 리스트 형태(`[{"label":..., "value":...}]`, server.py:1344~1349)입니다. 각 항목에 `status` 키 하나를 추가하는 구조 변경은 리스트 형태를 유지하면서 낮은 리스크로 가능합니다. `docChecklist`가 이미 `status: str` 필드를 아이템 단위가 아니라 체크리스트 단위로 갖는 것처럼, `confirmedFacts`도 항목 단위 `status: "extracted" | "fallback"` 필드를 추가하는 편이 리스트 구조와 자연스럽게 맞습니다.
- 다른 방법(예: fallback 문자열 자체에 마커를 심고 클라이언트가 문자열 패턴 매칭)은 권장하지 않습니다 — `sanitize_ai_text`(1505)가 문자열 치환을 수행하는 경로가 있어("보장"→"확인" 등), fallback 문자열이 우연히 치환 대상과 겹치면 상태 판별이 깨질 수 있습니다. 상태는 별도 필드로 명시하는 편이 안전합니다.
- 화면 쪽: `renderCoachPanel`의 `factsHtml`(app.js:946~948)이 `fact.label`/`fact.value`만 읽습니다. `docChecklistStatusBadge`와 동일한 패턴으로 `fact.status`를 보고 배지를 붙이는 헬퍼를 하나 추가하면 기존 `docSourceBadge`/`docChecklistStatusBadge` 두 상수와 나란히 세 번째 상수(`confirmedFactStatusBadge` 류)가 생기는 모양이 됩니다. 이는 "같은 개념의 상태 상수가 세 벌 존재"하는 구조가 되므로, 작은 보강 제안에서 공통화 여지를 남겨둡니다.

---

## 4. 영향받는 다른 호출부 전체 목록

**server.py 쪽 (confirmedFacts/unresolvedChecks를 만드는 함수)**
- `local_ai_coach()` (1308) — 유일한 실제 생성 로직. 여기만 고치면 아래 두 함수는 자동으로 따라옵니다.
- `gemini_ai_coach()` (1537), `vertex_ai_coach()` (1609) — 자체 스키마(`unresolvedChecks` 프롬프트 스키마, 1572·1652)를 LLM에 요청하지만 파싱 결과를 쓰지 않고 `local_ai_coach`를 그대로 씁니다. 이 프롬프트의 `schema` 정의는 **죽은 코드에 가깝습니다** (LLM이 그 형식으로 답해도 버려짐). 문제 1·2를 고칠 때 이 프롬프트 스키마 설명 문구(예: "이미 값이 있는 내용을 다시 묻지 않는")도 사람이 읽었을 때 실제 동작과 다르다고 오인할 수 있어, 함께 손볼지 팀장 판단이 필요합니다(직접 수정 대상은 아니므로 여기서는 발견만 보고합니다).
- `build_ai_coach()` (1692) — 위 세 함수를 오케스트레이션. 구조 변경 없이 그대로 통과.

**app.js 쪽 (confirmedFacts/unresolvedChecks를 소비하는 자리)**
- `renderCoachPanel()` (937) — `coach.confirmedFacts`(943)·`coach.unresolvedChecks`(944)를 직접 읽어 HTML 생성. 문제 1·3 수정의 주 렌더 지점.
- `renderAiReadySummary()` (1069) — `coach.unresolvedChecks.length`만 카운트해서 문구 생성. 개수만 쓰므로 구조 변경 영향은 작음.
- `getBoardChecks()` (약 499행) — `sampleNotice.aiCoach?.unresolvedChecks` 배열 반환. 이 결과가 다시 `getTaskAiMatch()`류 함수(정확한 라인은 미확인)로 넘어가 `renderTaskAiNudge()`(1081)의 `aiMatch.check`에 연결되는 것으로 보입니다 — **이 연결 체인은 이번 조사에서 시간상 끝까지 추적하지 못했습니다. 미확인으로 남깁니다.**
- 상단 분석 결과 패널의 `renderAnalysisResult()` → `renderAiReadySummary(coach)` 호출(932행 부근) — coach 객체를 그대로 전달하므로 구조 변경 시 별도 수정 불필요.

---

## P0/P1/P2 구조 리스크

**P0**
- `is_sale` 판정 로직의 SSOT 분열. 서버는 `disposition`/`asset_type` 문자열 부분일치(server.py:1318)로, 클라이언트 `getFitMessage()`는 `assetType+dispositionLabel+title` 정규식(app.js:842~843)으로 **각자 독립적으로** 매각/임대를 재판정합니다. 두 판정이 어긋나면(예: 서버는 임대로 봤는데 클라이언트 정규식은 매각으로 봄) 상단 "목적과 공고 유형이 맞습니다" 배지와 하단 `unresolvedChecks` 내용이 서로 모순되는 화면이 나올 수 있습니다. 문제 1을 고치면서 판정 축을 늘릴수록(asset-focus까지 추가) 이 분열이 함께 늘어납니다.
  - 근거: server.py:1318, app.js:842~843.

**P1**
- LLM 경로(`gemini_ai_coach`/`vertex_ai_coach`)가 자신이 요청한 LLM 응답의 `unresolvedChecks`/`confirmedFacts` 내용을 버리고 `local_ai_coach` 결과로 대체합니다(server.py:1601, 1684). `llmStatus: "connected"` 배지는 "AI가 실제로 이 콘텐츠를 만들었다"는 인상을 주지만 사실이 아닙니다. 문제 3에서 `confirmedFacts`에 `extracted` 상태를 붙일 때, 이 `llmStatus`와 새 `status` 필드가 서로 다른 걸 가리키는 것으로 오인되지 않게 설계가 필요합니다.
  - 근거: server.py:1596~1606, 1679~1689.
- `asset-focus`의 "창업 공간 탐색" 옵션에 대해 클라이언트 카피(app.js:864~871 `getFitMessage`)는 "준비 보드에서는 창업 목적 사용 가능 여부를 내가 담당기관에 물어볼 질문으로 분리합니다"라고 **약속**하지만, `local_ai_coach`에는 `startup`에 대응하는 분기가 없습니다(오직 `is_sale` 2분기). 카피가 실제로 없는 기능을 있다고 말하는 상태입니다.
  - 근거: app.js:864~871 vs server.py:1354~1429(`if is_sale / else` 2분기뿐).

**P2**
- 상태 배지 상수가 이미 두 벌 존재합니다(`docSourceBadge` app.js:1095, `docChecklistStatusBadge` app.js:1102). 문제 3 해법으로 세 번째 상수를 추가하면 "동일 개념(추출 상태)을 표현하는 상수가 세 곳에 분산"되는 구조가 됩니다. 당장 기능엔 문제없으나 이후 상태값 이름을 바꿀 때 세 곳을 동시에 고쳐야 하는 결합이 생깁니다.
  - 근거: app.js:1095~1109.

---

## 작은 보강 제안 (재설계 아님)

- `/api/analyze` 쿼리에 `userType`·`assetFocus` 파라미터를 추가하고, `build_notice` 또는 `local_ai_coach` 호출부에서 `notice`와 별개 인자로 넘기는 것을 검토 대상으로 남깁니다(단, 2번 답변대로 이것만으로 문제 1이 완전히 풀리지 않는다는 점을 함께 전달해야 합니다).
- `confirmedFacts` 각 항목에 `status: "extracted" | "fallback"` 필드를 추가하고, `docChecklistStatusBadge`와 이름·색상 팔레트를 맞춘 새 상수 하나만 추가합니다(재설계 없이 패턴 복제).
- `is_sale` 판정을 서버 응답 필드(`notice.aiCoach.isSale` 또는 `notice.dispositionCategory`)로 한 번만 계산해 서버가 내려주고, 클라이언트 `getFitMessage()`가 자체 정규식 대신 그 값을 읽게 하면 P0 리스크(SSOT 분열)가 줄어듭니다. 이는 이번 문제 1·3 수정과 자연스럽게 묶일 수 있는 범위입니다.
- `getFitMessage()`의 `startup` 분기 카피(864~871)를 실제 동작에 맞게 수정하거나, `local_ai_coach`에 `asset-focus == startup`용 분기를 추가하는 것 중 하나를 택해야 한다는 점을 to-do 후보로 남깁니다.

---

## 제품 판단이 필요한 지점 (사용자 확인 필요)

- **user-type/asset-focus를 서버로 보낼지 여부.** 지금은 순수 클라이언트 상태입니다. 서버로 보내면 API 계약이 늘어나고(캐시 키·URL 파라미터 증가), 같은 URL이라도 사용자 입력에 따라 다른 분석 결과가 나오는 구조로 바뀝니다. 이 설계 변경 자체를 할지 먼저 정해야 합니다.
- **"업종으로 실제 사용 가능한지" 판정을 어디까지 자동화할지.** 지금 데이터로는 명백한 불일치 감지 정도만 가능하고, 실제 업종-용도 매칭은 새 추출 로직(원문 텍스트에서 용도 제한 문구를 뽑는 작업)이 필요합니다. 이 추출 작업을 이번 개선 범위에 포함할지, 아니면 우선 "지금은 자동 판정할 수 없다"고 솔직히 밝히는 문구로 대체할지 결정이 필요합니다.
- **`llmStatus`와 `confirmedFacts.status`를 사용자에게 어떻게 동시에 보여줄지.** "AI 분석 완료" 배지 아래에 "이 값은 fallback입니다" 배지가 같이 뜨는 화면이 자연스러운지, 아니면 `llmStatus` 배지 자체의 의미를 재정의(예: "규칙 기반"으로 통일)할지는 UX/카피 판단입니다.
- **`getFitMessage()`의 startup 카피를 고칠지, `local_ai_coach`에 startup 분기를 새로 만들지.** 이번 조사에서 발견한 기존 결함이며, 사용자가 원 지적(문제 1)과 함께 처리할지 별도 이슈로 뺄지 정해야 합니다.
