# 샘플 API 필드 매핑 - OnBid Public Asset Doc Agent

## 목적

공공데이터 활용성이 선언에 머물지 않도록, 온비드 API/파일데이터의 필드를 어떤 출력 리포트 항목으로 연결할지 미리 정의한다. 실제 API 인증키 적용 전에는 공공데이터포털 명세와 샘플 응답, 온비드 공개 공고 원문을 기반으로 오프라인 샘플을 만든다.

## 표준 입력 스키마 v0

| 표준 필드 | 출처 후보 | 설명 |
| --- | --- | --- |
| `notice_id` | 공고목록/공고상세 | 공고 식별자 |
| `asset_id` | 물건목록/물건상세 | 물건 식별자 |
| `notice_title` | 공고목록/공고상세 | 공고명 |
| `agency` | 공고목록/공고상세 | 공고기관 |
| `asset_type` | 물건목록/상세 | 부동산, 차량, 동산, 국유재산 등 |
| `location` | 물건상세 | 소재지 |
| `area_sqm` | 물건상세 | 면적 |
| `base_price_krw` | 물건상세/입찰정보 | 예정가격 또는 최저입찰가 |
| `bid_method` | 공고상세 입찰정보 | 최고가, 총액, 제한경쟁 등 |
| `bid_period` | 공고상세 입찰정보 | 입찰서 제출기간 |
| `bid_deposit` | 공고상세 입찰정보 | 입찰보증금 |
| `open_date` | 공고상세 입찰정보 | 개찰일시 |
| `required_documents` | 공고문/첨부 | 제출서류 목록 |
| `post_award_duties` | 공고문/첨부 | 낙찰 후 신청, 납부, 보증보험 등 |
| `risk_clauses` | 공고문/첨부 | 현장확인, 수익 미보장, 인허가 책임 등 |
| `glossary_terms` | 온비드 용어사전 | 어려운 용어 |

## 공식 서비스명·원문 필드 근거

공공데이터포털 상세 페이지에서 확인한 설명을 기준으로, 공식 서비스의 필드 표현을 아래처럼 표준 필드로 매핑한다.

| 공식 데이터/서비스 | 공식 설명에 나타난 필드·조건 | 표준 필드 | 리포트 연결 |
| --- | --- | --- | --- |
| 차세대 온비드 공고목록 조회서비스 | 필수 입력 조건: `cltrTypeCd`, `prptDivCd`, `opbdDtStart`, `opbdDtEnd`; 조회 정보: 공고명, 공고기관, 공고일, 회차 | `asset_type`, `notice_title`, `agency`, `bid_period` | 관심 공고 목록, 마감 임박 표시 |
| 차세대 온비드 공고상세 조회서비스 | 필수 입력 조건: `pbancMngNo`; 공고유형, 재산유형, 처분방식, 입찰방식, 입찰구분, 입찰금액 공개여부, 공고기관, 공고일 | `notice_id`, `asset_type`, `bid_method`, `agency` | 공고 핵심 조건, 원문 근거 |
| 차세대 온비드 공고상세 입찰정보 조회서비스 | 필수 입력 조건: `pbancMngNo`; 공동입찰가능여부, 대리입찰가능여부, 전자보증서 가능여부, 입찰보증금, 잔대금 납부방법, 잔대금 납부기한, 입찰참가신청필요여부, 입찰일정 및 장소 | `bid_method`, `bid_deposit`, `post_award_duties`, `bid_period` | 일정표, 비용 후보, 낙찰 후 의무 |
| 차세대 온비드 공고상세 물건정보 조회서비스 | 필수 입력 조건: `pbancMngNo`; 재산유형, 처분방식, 용도, 물건명, 유찰횟수, 일괄입찰여부, 물건주소, 회차, 공매차수, 입찰시작일시, 입찰종료일시 | `asset_type`, `location`, `bid_period`, `notice_title` | 물건 요약, 비교표, 리스크 카드 |
| 온비드 용어사전 | 컬럼: `Terminology`, `Glossary`; 온비드 공매 절차, 부동산·동산, 산업, 법률 관련 용어 846개 | `glossary_terms` | 쉬운 용어 설명, Q&A 보조 |
| 온비드 월별 입찰참가자 현황 | 컬럼: `Year/Month`, `Number of bidders for KAMCO auction`, `Number of bidders for auction by user institutions`, `Total`; 2013년~2025년 월별 유효 입찰참가자 수 | `market_signal` | 반복 수요 설명, 시장성 보조 |

## 출력 매핑

| 출력 리포트 항목 | 필요한 표준 필드 | 생성 방식 |
| --- | --- | --- |
| 한 줄 요약 | `notice_title`, `agency`, `asset_type`, `location`, `bid_method` | 템플릿 + AI 요약 |
| 핵심 조건표 | `asset_type`, `location`, `area_sqm`, `base_price_krw`, `bid_method` | 표준 필드 직접 표시 |
| 일정표 | `bid_period`, `bid_deposit`, `open_date`, `post_award_duties` | 날짜 파서 + 마감 리스크 분류 |
| 제출서류 체크리스트 | `required_documents`, 사용자 유형 | 사용자 유형별 분기 |
| 비용 후보 | `base_price_krw`, `bid_deposit`, 공고문 비용 조항 | 원문 수치 + 확인 필요 표시 |
| 리스크 카드 | `risk_clauses` | 위험 유형 라벨링 |
| 용어 설명 | `glossary_terms` | 온비드 용어사전 정의 연결 |
| Q&A | 전체 필드 + 원문 근거 | 근거 기반 답변 |

## 샘플 입력 JSON v0

```json
{
  "notice_id": "860826",
  "asset_id": "1968104",
  "notice_title": "국유재산(국립군산대학교 제2학생회관 복사 및 인쇄점) 유상사용 수익허가자 선정",
  "agency": "군산대학교",
  "asset_type": "국유재산 임대",
  "location": "군산시 대학로 558 제2학생회관",
  "area_sqm": 110.81,
  "base_price_krw": 4773850,
  "bid_method": "제한경쟁(최고가방식)/총액",
  "bid_period": "2026-01-30 15:00 ~ 2026-02-09 17:00",
  "required_documents": [
    "사업자등록증 사본 또는 사업자등록증명원",
    "주민등록등본 또는 법인등기부등본",
    "인감증명서",
    "국세 및 지방세 완납증명서"
  ],
  "post_award_duties": [
    "낙찰 후 7일 이내 사용수익허가 신청",
    "낙찰금액 선납",
    "계약이행보증보험증권 제출"
  ],
  "risk_clauses": [
    "현장설명 생략",
    "영업수익 보장 없음",
    "유관기관 허가사항은 입찰자 책임"
  ]
}
```

## 조회시각 표시 계획

| 메타데이터 | 예시 |
| --- | --- |
| 데이터 출처 | 한국자산관리공사 차세대 온비드 공고목록/공고상세/물건상세/입찰정보 조회서비스 |
| 조회시각 | 리포트 생성 시점 표시 |
| 원문 URL | 온비드 공고 상세 URL |
| 원문 우선 원칙 | API 값과 공고문이 다를 경우 공고문 및 담당기관 확인을 우선 |
