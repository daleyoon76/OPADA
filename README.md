# Hometest_op — OnBid Public Asset Doc Agent

KAMCO Startup TechBlaze 제출용으로 만든 온비드 공공자산 공고 해석 리포트 Agent(OnBid Public Asset Doc Agent) MVP입니다. 서류 합격 이후 `supporting-programs` 레포에서 분리해 독립 레포로 관리합니다.

## 구조

| 폴더 | 내용 |
| --- | --- |
| `src/` | MVP 소스 코드 (`server.py`, `app.js`, `index.html`, `styles.css`) |
| `tests/` | 테스트 스펙 (`public-data-status.spec.js`) |
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

- `#input`: 공고 가져오기. 온비드 공고/물건 URL을 분석하고 `준비 보드 만들기`로 넘어갑니다.
- `#report`: 준비 보드. AI가 찾은 준비 빈칸을 체크리스트 우선순위로 연결합니다.
- `#watchlist`: 관심 공고. 분석한 공고를 자동 저장하고 관심 공고를 표시합니다.

## 주의

법률 판단, 투자 판단, 자동 입찰, PDF 리포트 생성 기능은 포함하지 않으며, 추출값은 원문과 담당기관 확인을 우선합니다.

## 배경 문서

제출 배경, 평가항목 매핑, 검증 기록 등은 `docs/` 아래를 참고하세요. 특히 `docs/90_MVP개발/`에 MVP 개발/개선 루프 기록이 있습니다.
