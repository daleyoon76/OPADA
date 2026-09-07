# Hometest_op — OnBid Public Asset Doc Agent

KAMCO Startup TechBlaze 제출용으로 만든 온비드 공공자산 공고 해석 리포트 Agent(OnBid Public Asset Doc Agent) MVP입니다. 서류 합격 이후 `supporting-programs` 레포에서 분리해 독립 레포로 관리합니다.

## 구조

| 폴더 | 내용 |
| --- | --- |
| `src/` | MVP 소스 코드 (`server.py`, `app.js`, `index.html`, `styles.css`) |
| `tests/` | 테스트 스펙. `test_docs_extraction.py`(순수 함수 게이트) · `screen.spec.js`(화면 노출) · `public-data-status.spec.js`(실 URL e2e) · `measure_sample_23.py`(표본 계측) |
| `docs/` | KAMCO Startup TechBlaze 제출 전 과정 문서 (원문 공고, 검토, 제출초안, 증빙, 제출준비, 본선준비, MVP 개발 기록 등). 원래 `07_KAMCO_Startup_TechBlaze` 폴더를 그대로 옮긴 것입니다. |

## 실행

```powershell
cd src
python server.py
```

브라우저에서 `http://127.0.0.1:8975/`를 엽니다.

공공데이터포털 인증키가 있으면 실행 전에 환경변수로 넣습니다.

```powershell
$env:ONBID_API_SERVICE_KEY="공공데이터포털_일반_인증키"
python server.py
```

키가 없으면 온비드 공개 원문 분석만 수행합니다. 인증키는 README나 코드에 저장하지 않습니다.

## 화면

- `#input`: 공고 가져오기. 온비드 공고/물건 URL을 분석합니다.
  - 분석 직후 「서류 목록을 본문에서 찾을 수 있는지 / 첨부를 봐야 하는지 / 원문에 없는지」를 재산유형 기준으로 먼저 알립니다.
  - 마감 D-day를 표시합니다. 알림 발송 기능은 없습니다.
- `#report`: 준비 보드.
  - 조건별(대리·공동·법인/개인·미성년자·업종자격·지역제한 등) 제출서류 체크리스트를 보여줍니다.
  - 서류마다 단계·원본/사본·부수·유효기간·제출방법·제출기한·발급처·원문 근거를 붙입니다.
  - 첨부파일 내려받기 링크, 공고문 항목 목차, 재산유형·처분방식 용어 안내를 함께 둡니다.
- `#watchlist`: 관심 공고. 분석한 공고를 자동 저장하고 관심 공고를 표시합니다.

## 주의

- 법률 판단, 투자 판단, 자동 입찰, PDF 리포트 생성 기능은 포함하지 않으며, 추출값은 원문과 담당기관 확인을 우선합니다.
- **서류 체크리스트는 참고용입니다.** 적격 여부를 판정하지 않고, 항목이 비어 있어도 다음 단계를 막지 않습니다.
- 서류명을 뽑지 못하면 뽑지 못했다고 화면에 그대로 표시합니다. 추출 성공으로 위장하지 않습니다.
- 첨부 공고문(PDF·HWP) 내부 텍스트는 아직 읽지 않습니다. 파일 목록과 내려받기 링크까지만 제공합니다.

## 배경 문서

제출 배경, 평가항목 매핑, 검증 기록 등은 `docs/` 아래를 참고하세요. 특히 `docs/90_MVP개발/`에 MVP 개발/개선 루프 기록이 있습니다.
