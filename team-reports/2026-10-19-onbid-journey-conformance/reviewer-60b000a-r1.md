## reviewer r1 판정: 커밋 `60b000a`

**머리**
- 판정 대상: `60b000a` (`60b000affdec4638594f4fae568387ffe46c7f79`), 기준 `4b292c9`. 사본 HEAD 는 `60b000a` 이고, `git status` 는 착수 때와 종료 때 모두 `?? node_modules` 한 줄입니다 [관측].
- diff sha256 재측정값은 `83a9121a386009a909390a37a033f53086ae6f003dd21cda27bf7bb510ad1ba4` 입니다. 앞 16자가 packet 과 같고, 12:09:36 과 12:23:18 두 번 쟀습니다 [관측].
- 작성 시각: 2026-10-19 (월) 12:23:18 KST (`date`). 착수는 12:09:36 이고 예산 안에서 끝냈습니다. 도구 호출은 약 56회이고, 그중 6회는 제 셸·구문 오류입니다.

## 판정: 조건부 GO

[관측] 층별 표제는 정답표 기준으로 오분류를 늘리지 않고 미분류를 16건에서 5건으로 줄였습니다(분모 149).
[관측] 다만 국유재산 07·08 의 농지취득자격증명이 4단계로만 옮겨졌습니다. 같은 조항 원문은 「사전확인 후 응찰하시기 바랍니다」입니다. 이 방향은 프로젝트가 가장 비싸다고 정한 오배치입니다(app.js:868-871).
F1 을 처방으로 닫거나 팀장이 근거를 적고 수용하면 GO 입니다.

## 지적 표

| ID | 등급 | 파일:줄 | 지적 | 재현 입력 또는 근거 | 처방 | 처방이 기대는 것 |
|---|---|---|---|---|---|---|
| F1 | P1 | src/server.py:485-490, 556-560 | 07·08 농지취득자격증명이 바깥 층 표제 「9. 계약체결 및 대금납부방법」을 물려받아 「낙찰 후·계약 시」로 확정됨. 커밋 전에는 2단계 미분류 구획에 있었음 | stages-before/after.tsv 114·133행 [관측] · untrusted-sample23/text/07_0.txt:64, 79-80 [관측] | optB(권고): ⑴ SENTENCE_STAGE_RULES 입찰 전 대안에 `사전\s*확인\s*후\s*(?:응찰\|입찰)` 추가 ⑵ 표제를 가장 안쪽이 아닌 층에서 물려받았고, 그 표제가 낙찰 후를 가리키고, 같은 조항 창에 입찰 전 결정 문구가 있으면 미분류로 반환. [실행] | `doc_stage_at` 이 표제를 문장보다 먼저 반환하는 줄(server.py:556-560). `governing_heading` 이 내장 표제를 못 찾으면 carried_heading 을 그대로 돌려주는 줄(server.py:532). 호출부(server.py:812-814)가 물려받음 여부를 넘겨야 함 |
| F2 | P2 | src/server.py:475-482 | 처음 보는 번호 체계는 무조건 안쪽 층에 쌓임. 번호 없는 문단(※·▶)은 층을 닫지 않음. 그래서 형제·무관 조항이 바깥 사전 표제를 물려받음. 표본 23건에서 F1 밖의 실례는 관측하지 못함 | 아래 Q1 의 T1·T2·T5 [관측] | optB 를 넣으면 T1·T3 이 미분류로 돌아감 [실행]. T2·T5 는 남음. 후보 (가) A16 축 행 음성 칸에 「다른 체계 형제 · 번호 없는 문단 뒤 목록: 미커버」 기록 (나) 기호(■·◆) 층은 쌓지 않고 스택을 비움 [미실행] | A16 AXES 행(tests/test_docs_extraction.py:110-116) |
| F3 | P2 | src/server.py:1097 | `입찰\s*금액` 이 「최저입찰금액」에도 걸려 반대 안내가 나감 | `deposit_basis_note("최저입찰금액 X 10%", …)` 결과는 「최저입찰가격이 아니라 … 입찰금액을 기준」 [관측]. 표본 HTML 표시값은 3종뿐(입찰금액 X 5% 24회 · 입찰금액 X 10% 20회 · 최저입찰가격 X 10% 6회, 고정 파일, 중복 포함)이라 실노출은 관측하지 못함 [관측] | `r"(?<!최저)(?<!최저 )입찰\s*금액"`. [실행] 사본 optD 에서 단위 337/337. 「최저입찰금액」은 「원문에서 확인」으로 가고, 「입찰금액 X 10% (최저입찰가 이상)」은 입찰금액 기준을 유지함. 분기 순서만 바꾸는 안은 뒤 입력을 반대로 보낼 것으로 봄 [추론] | Python `re` 고정폭 lookbehind(2자·3자). optD 에서 동작 확인 |
| F4 | P2 | src/app.js:1696 · tests/screen.spec.js:1174 | 셋째 규칙의 「나의온비드에서」가 정본 A10 인용(researcher-onbid-journey.md:86)에 없음. 정본에서 나의온비드는 B2(:94)와 D6(:126)에만 나옴 | 정본 grep [관측] | 「입찰서 제출과 보증금 납부가 끝났는지는 온비드에서 직접 확인하십시오. 확인하지 않아 생긴 불이익은 입찰자 책임입니다.」로 바꾸고, S13 단정 `toContain("나의온비드")` 를 `toContain("직접 확인")` 으로 함께 바꿈. 또는 FAQ #4421 본문 인용을 정본에 더하고 문구를 유지함. [실행] 정본 grep 1회, 대체 문장을 교정 사전 25항 detect 에 대조해 0건 | S13 단정(screen.spec.js:1174) |
| F5 | P2 | 커밋 60b000a 본문 1번 항목 | 「번호 체계(1.·가.·1)·Ⅰ.·■)별 층」이라 적었지만 로마 숫자 규칙은 ASCII `[IVX]+` 뿐임. `heading_kind("Ⅰ. 입찰 개요")` 는 빈 값이고 HEADING_LINE_RE 도 맞지 않음. 표본 21_1.txt:13 에 「Ⅰ.」가 실제로 있음 | [관측] | 히스토리는 그대로 두고, 다음 커밋 본문이나 handoff 에 「유니코드 Ⅰ. 은 층에 들지 않는다」 정정 한 줄. [실행] grep 1회 | roman 규칙(server.py:463) |

- 처방 실행 여부: F1 [실행](optA·optB 두 안), F2 일부 [실행](T1·T3), 나머지 [미실행], F3 [실행], F4 [실행], F5 [실행].
- 1라운드이므로 「내 rN 처방 원인」과 「앞 라운드 누락」은 해당이 없습니다.
- 상충 자체 검사 [관측]: optB 는 이 커밋의 목표(909445형 미분류 해소)를 되돌리지 않습니다.
  - T6(909445형) 결과는 그대로입니다.
  - 표본 21 의 16건도 그대로입니다.

## 질문 1: 의도대로 동작하는가

답: 옛 동작보다 나빠지는 입력이 있습니다 [관측].
- 재현 스크립트: `/private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/44440f55-a894-47c1-ab59-bf748ae182d1/scratchpad/role-reviewer/repro_q1.py`
- 경로: `extract_doc_items({}, [("첨부:공고문.pdf", text)])`. 줄바꿈은 `/` 로 적었습니다.

| 입력 | 4b292c9 | 60b000a | 판정 |
|---|---|---|---|
| T1 `8. 낙찰자 제출서류 / 가. 주민등록등본 1부 / ■ 공동입찰 시 유의사항 / 공동입찰자는 입찰 마감일까지 인감증명서를 제출하여야 합니다.` | 인감증명서 입찰 전 | 낙찰 후 | 나빠짐(■ 형제가 8. 을 물려받음) |
| T2 `10. 최종낙찰자 제출서류 / 가. 개인 / 1) 주민등록등본 1부 / ※ 입찰 참가 시에는 아래 서류를 입찰 마감일까지 제출 / 1) 사업자등록증 1부` | 사업자등록증 미분류 | 낙찰 후 | 나빠짐 |
| T3 `가. 낙찰자는 낙찰일로부터 5일 이내에 계약을 체결하여야 합니다. / 1) 입찰 참가 시 사업자등록증을 입찰 마감일까지 제출` | 입찰 전 | 낙찰 후 | 나빠짐(07·08 과 같은 부류) |
| T4 같은 「1.」이 두 층: `1. 낙찰자 제출서류 / 가. 개인 / 1. 주민등록등본 1부 / 2. 인감증명서 1부` | 미분류 | 미분류 | 같음(나빠지지도 고쳐지지도 않음) |
| T5 첨부의 쪽 단위 긴 줄 2개: `9. 계약체결 및 대금납부방법 …` / `가. 입찰 시 유의사항 … 사업자등록증 사본 1부` | 미분류 | 낙찰 후 | 나빠짐(쪽 전체가 바깥 표제로 남음) |
| T6 909445형 + 같은 층 형제 | 미분류·미분류 | 낙찰 후·입찰 전 | 의도대로 |
| 한 줄 첨부 2건(repro_oneline.py) | | | 옛 동작과 같음 |

- 나빠진 네 건은 모두 낙찰 후 쪽으로 움직였습니다.
- 원인 [관측, 코드 읽음]:
  - `push_heading`(server.py:475-482)은 처음 보는 체계를 무조건 안쪽에 쌓습니다.
  - 표제가 아닌 줄은 스택을 건드리지 않습니다.
  - `stage_heading_from_stack`(:485-490)은 바깥 사전 표제까지 올라갑니다.
  - 표제가 문장 규칙보다 먼저라서(:556-560) 같은 줄의 입찰 전 문구를 이깁니다.
- 별건(이번 diff 밖, 두 판 모두 같음) [관측]:
  - 입력: `10. 최종낙찰자 제출서류 가. 사업자등록증 1부 나. 법인인감증명서 1부 11. 입찰 시 유의사항 가. 주민등록등본 1부`(한 줄 첨부).
  - 결과: `governing_heading` 이 형제 「11.」을 건너뛰어, 주민등록등본이 두 판 모두 낙찰 후로 갑니다.

## 질문 2: 새 상태가 제품으로서 맞는가

**(a) 4단계에만 두면 해가 된다고 판단합니다.**
- 원문 07_0.txt:79-80 은 「매수자가 갖추어야 할 요건이므로 사전확인 후 응찰하시기 바랍니다」입니다 [관측].
- 위치 변화 [관측]:
  - 커밋 전에는 미분류였고, 2단계 「단계를 확정하지 못한 서류」 구획에 보였습니다(app.js:873-876).
  - 커밋 후에는 4단계에만 있습니다.
- app.js:868-871 은 낙찰 후 오배치를 「4단계를 지금 할 일로 보지 않아 그 서류를 아예 놓친다」는 비싼 방향으로 정했습니다 [관측].
- 입찰 전 확정(optA)도 정확하지 않다고 봅니다. 농지취득자격증명은 보통 낙찰 뒤 발급받는 서류입니다 [추론]. 그래서 미분류로 되돌리는 optB 를 권합니다.
- optB 실행 결과 [실행]:
  - 사본: `/private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/44440f55-a894-47c1-ab59-bf748ae182d1/scratchpad/role-reviewer/optB`
  - 단위 337/337.
  - 표본 23건 측정 요약은 measure-after2.txt 와 diff 0줄입니다(오분류 2/149 · 미분류 5/149).
  - 항목별 단계 diff 는 07·08 농지취득자격증명 2줄(낙찰 후에서 미분류)뿐입니다.
  - optA 는 같은 2줄이 입찰 전으로 가고 나머지는 같습니다.
- 노출 범위: 07·08 은 같은 국유재산 공고 양식입니다. 다른 국유재산 매각 공고도 같은 양식이면 넓게 나갑니다 [추론, 미측정].

**(b) 임대 공고에서 소유권이전 묶음을 접는 판정은 맞습니다.**
- 근거 [인용]:
  - researcher-onbid-journey.md:110-114 의 C6·C8·C10 매각/임대 칸은 모두 「매각」입니다.
  - :117-126 의 임대·대부 D1~D6 에는 소유권이전 단계가 없습니다.
- 판정식 app.js:914-917 은 「임대·대부」가 있고 「매각·공매」가 없을 때만 접습니다. 처분방식을 읽지 못하면 펼칩니다 [관측, 읽음].
- 옛 코드(4b292c9 app.js:905-907)는 assetTypes 가 없는 묶음을 무조건 해당으로 봤습니다 [관측]. 그래서 커밋 본문의 「임대 공고에도 펼쳐졌다」는 코드 수준에서는 맞고, 브라우저로 관측한 것은 아닙니다.
- 기본 sampleNotice 가 국유재산 · 「임대/대부입찰」(app.js:8-10)이라 첫 화면에서 이 묶음이 접힙니다 [관측]. 정본과 맞는 변화입니다.
- 접힘 사유는 `splitDocGroupsByStage` 의 `{ ...group }` 복사(app.js:939-940)로 4단계까지 전달됩니다 [관측].

**(c) 입찰 규칙 세 줄과 정본 A8~A10 대조**

| 화면 문장 | 정본 | 판정 |
|---|---|---|
| 「입찰서는 제출한 뒤에 수정하거나 취소할 수 없는 것이 원칙입니다.」 | A8 「제출한 입찰서는 수정, 변경 및 취소가 불가능합니다.」(:83). 예외는 :138-141 | 맞음. 「변경」은 「수정」에 포함됨. 예외는 「원칙」과 꼬리 문단이 덮음 |
| 「입찰보증금 납부 계좌는 입찰서를 제출한 뒤에 발급됩니다. 입찰 마감 시각까지 보증금을 내지 않으면 입찰이 무효가 됩니다.」 | A9 의 G4 · R1 제8조② 인용(:84) | 맞음 |
| 「…나의온비드에서 직접 확인하십시오. 확인하지 않아 생긴 불이익은 입찰자 책임입니다.」 | A10 「…매수신청인 본인이 책임을 부담합니다.」(:86) | 책임 문장은 맞음. 「나의온비드」라는 위치는 인용에 없음(F4) |

**(d) 보증금 note 세 갈래는 3절 1번(:132-135)과 맞습니다** [인용 · 관측, 함수 직접 호출].
- 「입찰금액」이면 입찰금액 기준 문장이 나갑니다.
- 「최저입찰가·예정가」이면 최저입찰가격 값을 안내합니다. 압류의 「공매예정가격 X 10%」도 이 갈래로 갑니다.
- 그 밖이면 「원문에서 확인」입니다.
- 남은 결함은 F3 하나입니다.

## 질문 3: 금지표현

- 0건입니다 [관측].
- 대상은 diff 의 추가 줄 318줄이고, 패턴은 16개입니다(띄어쓰기 변형 포함, 「대행」 포함). `grep -f` 종료코드는 1(일치 없음)이었습니다.
- 이 패턴은 대리 지표입니다. 같은 뜻의 다른 표현(예: 「대신 입찰」)은 통과시킵니다.
- `tests/test_screen_strings.py` 를 60b000a 사본에서 직접 돌려 20/20 이었습니다 [관측].

## 질문 4: 처방이 기대는 것

지적 표의 마지막 열에 적었습니다.

## 검증 누락 (닫는 비용)

1. E2E 33 passed 와 게이트 「실행 상태: passed」는 [인용]입니다. 다시 돌리지 않았습니다. 닫는 비용은 E2E 1회입니다.
2. optB 에는 변이 3종을 넣지 않았습니다. 처방을 넣는 쪽 몫이고, 닫는 비용은 명령 3줄입니다.
   - 새 판정 줄 삭제.
   - `inherited and` 앞에 `True or` 를 끼우는 머리 단락.
   - `heading is carried_heading` 무력화.
   - optB 는 `is` 비교를 씁니다. `==` 로 바꾸면 뜻이 달라질 수 있습니다 [추론].
3. T2·T5 부류가 실공고에 얼마나 있는지는 표본 23건 밖에서 재지 않았습니다. 닫는 비용은 라이브 수집 1회입니다.
4. 07·08 양식이 다른 국유재산 공고에 얼마나 있는지도 재지 않았습니다. 닫는 비용은 라이브 1회입니다.
5. 단위 337/337 과 화면 문자열 20/20 은 60b000a 사본(`git archive`)에서 직접 돌려 닫았습니다 [관측]. 변이 17종은 [인용]입니다.

재발 방지 한 줄(제 측정 오류): f-string 따옴표 중첩과, `bash -c` 안의 정규식·awk `$` 때문에 6회 막혔습니다. 정규식·awk·Python 이 섞인 명령은 처음부터 스크래치 파일로 쓰고 `bash 파일`, `awk -f`, `grep -f` 로 돌립니다.

## 권고를 반영한 뒤 최종 커밋에서 확인할 종료 조건 1개

```
ONBID_SAMPLE_HTML_DIR=/private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/44440f55-a894-47c1-ab59-bf748ae182d1/scratchpad/untrusted-sample23/html ONBID_SAMPLE_TEXT_DIR=/private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/44440f55-a894-47c1-ab59-bf748ae182d1/scratchpad/untrusted-sample23/text PYTHONPYCACHEPREFIX=/private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/44440f55-a894-47c1-ab59-bf748ae182d1/scratchpad/role-reviewer/pyc python3 /private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/44440f55-a894-47c1-ab59-bf748ae182d1/scratchpad/scripts/dump_stages.py /private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/44440f55-a894-47c1-ab59-bf748ae182d1/scratchpad/opada-dev | awk -f /private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/44440f55-a894-47c1-ab59-bf748ae182d1/scratchpad/role-reviewer/term.awk; echo $?
```

- 통과 기준은 출력 `0` 과 종료코드 `0` 입니다.
- `term.awk` 전문은 다음 세 줄입니다.
  ```
  BEGIN { FS = "\t" }
  ($1 == "07" || $1 == "08") && $2 == "농지취득자격증명" && $4 == "낙찰 후·계약 시" { n++ }
  END { print n + 0; exit (n > 0) }
  ```
- ⑴ 수정 전 상태에서 실패하는가: 60b000a 사본에서 `2`, 종료코드 1 이었습니다 [실행]. 이때 제 dump 는 stages-after.tsv 와 바이트까지 같았습니다(`cmp` 0).
- ⑵ 처방을 넣은 사본에서 통과하는가: optB 와 optA 모두 `0`, 종료코드 0 이었습니다 [실행]. 4b292c9 결과(stages-before.tsv)도 `0` 입니다.
- 이 조건은 대리 지표입니다. 07·08 두 줄만 보고, 같은 부류의 다른 공고와 T2·T5 는 잡지 않습니다.
- 짝으로 `measure_stage_classification.py` 요약이 measure-after2.txt 와 diff 0줄인지도 함께 보십시오.

## 산출물 경로

모두 `/private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/44440f55-a894-47c1-ab59-bf748ae182d1/scratchpad/role-reviewer/` 아래에 있습니다.
- 재현 스크립트: `/private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/44440f55-a894-47c1-ab59-bf748ae182d1/scratchpad/role-reviewer/repro_q1.py`, `/private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/44440f55-a894-47c1-ab59-bf748ae182d1/scratchpad/role-reviewer/repro_oneline.py`
- 처방 사본: `/private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/44440f55-a894-47c1-ab59-bf748ae182d1/scratchpad/role-reviewer/optA`, `/private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/44440f55-a894-47c1-ab59-bf748ae182d1/scratchpad/role-reviewer/optB`, `/private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/44440f55-a894-47c1-ab59-bf748ae182d1/scratchpad/role-reviewer/optD`
- 단계 덤프: `/private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/44440f55-a894-47c1-ab59-bf748ae182d1/scratchpad/role-reviewer/stages-optA.tsv`, `/private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/44440f55-a894-47c1-ab59-bf748ae182d1/scratchpad/role-reviewer/stages-optB.tsv`, `/private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/44440f55-a894-47c1-ab59-bf748ae182d1/scratchpad/role-reviewer/stages-base-mine.tsv`
- 측정 요약: `/private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/44440f55-a894-47c1-ab59-bf748ae182d1/scratchpad/role-reviewer/optB-measure.txt`
- 종료 조건: `/private/tmp/claude-501/-Users-user-Documents-Dev-Hometest-op/44440f55-a894-47c1-ab59-bf748ae182d1/scratchpad/role-reviewer/term.awk`

사본 `opada-dev` 와 레포는 수정하지 않았습니다.