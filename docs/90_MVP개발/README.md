# OnBid Public Asset Doc Agent MVP

## 목적

KAMCO Startup TechBlaze 신청서에 넣을 서비스 형상 증빙을 만들기 위한 로컬 정적 MVP입니다.

## 실행

```powershell
cd C:\Users\WIN_AD02366572\Documents\Dev\supporting-programs\07_KAMCO_Startup_TechBlaze\90_MVP개발\app
python server.py
```

브라우저에서 `http://127.0.0.1:8975/`를 엽니다.

공공데이터포털 인증키가 있으면 실행 전에 아래 환경변수 중 하나로 넣습니다.

```powershell
$env:ONBID_API_SERVICE_KEY="공공데이터포털_일반_인증키"
python server.py
```

키가 없으면 서비스는 온비드 공개 원문 분석만 수행합니다. 사용자 화면에는 기술 상태 대신 `원문 분석`으로 표시합니다.

인증키는 README나 코드에 저장하지 않습니다. 공공데이터포털 승인 직후 일부 API가 403을 반환하거나 `NODATA_ERROR`를 반환해도 온비드 공개 원문 분석 결과는 계속 표시됩니다.

AI 인증이 가능한 로컬 환경에서는 온비드 원문 추출값을 기반으로 초보자가 놓치기 쉬운 준비 빈칸을 찾습니다. 화면에는 공급자명이 아니라 `AI 누락 점검`, `AI 우선 액션`, `AI 우선 확인`으로 표시합니다. 입찰 여부, 가격 결정, 법률/권리관계, 수익성 판단은 제공하지 않도록 프롬프트와 후처리를 둡니다.

## 화면

- `#input`: 공고 가져오기. 온비드 공고/물건 URL을 분석하고, 유효성·공고/물건 연결·AI 분석 완료 상태를 먼저 확인한 뒤 `준비 보드 만들기`로 넘어갑니다.
- `#report`: 준비 보드. AI가 찾은 준비 빈칸을 체크리스트 우선순위로 연결하고, 담당기관에 물어볼 문장과 원문 근거를 함께 확인합니다.
- `#watchlist`: 관심 공고. 분석한 공고를 `최근 살펴본 공고`로 자동 저장하고, 별표를 누른 항목을 관심 공고에 함께 표시합니다.

## 최신 제출용 캡처 후보

- `screenshots/validation/33_input-clean-user-language.png`: URL 분석, 공고/물건 연결, `원문 분석`, AI 분석 완료 상태.
- `screenshots/validation/36_board-ai-value-final-check.png`: AI 우선 액션, AI 우선 체크리스트, 담당기관 문의 문장, 원문 근거.
- `screenshots/validation/17_watchlist-recent-favorite.png`: 최근 살펴본 공고와 관심 공고 저장 흐름.

## 주의

이 MVP는 온비드 공고/물건 URL을 서버에서 가져와 주요 필드를 추출하는 프로토타입입니다. short URL은 최종 온비드 URL로 따라간 뒤 분석합니다. 인증키가 있으면 공공데이터포털 온비드 상세 API로 물건/입찰 정보를 보강합니다. 법률 판단, 투자 판단, 자동 입찰, PDF 리포트 생성 기능은 포함하지 않으며, 추출값은 원문과 담당기관 확인을 우선합니다.
