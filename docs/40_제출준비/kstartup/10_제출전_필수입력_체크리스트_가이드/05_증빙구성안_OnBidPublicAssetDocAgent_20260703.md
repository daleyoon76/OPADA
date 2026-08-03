# 선택 증빙 구성안 - OnBid Public Asset Doc Agent

작성시각: 2026-07-04 00:15 KST

## 구성 원칙

KAMCO 제출 패키지는 공식 신청서와 기획서가 중심이다. 선택 증빙은 과하게 붙이지 않고, 평가자가 `공공데이터 활용 제품/서비스`를 이해하는 데 필요한 전용 자료만 앞에 둔다.

기존 제품 증빙은 `보유 기술 근거`로만 사용하고, 기존 사업명·다른 공고명·다른 수요기업명이 보이는 자료는 제외한다.

## 권장 증빙 순서

| 쪽 | 내용 | 파일 후보 | 판정 |
| --- | --- | --- | --- |
| 1 | OnBid Public Asset Doc Agent 1페이지 브리프 | `20_제출초안/01_1페이지_브리프_OnBidPublicAssetDocAgent_20260703.md` | 포함 |
| 2 | 평가항목 매핑표 요약 | `20_제출초안/02_평가항목_매핑표_OnBidPublicAssetDocAgent_20260703.md` | 포함 |
| 3 | 서비스 화면형 증빙 | `20_제출초안/05_서비스화면_와이어프레임_OnBidPublicAssetDocAgent_20260704.md` | 포함 |
| 4 | 샘플 입력: 온비드 국유재산 임대 공고 구조화 | `20_제출초안/sample_inputs/onbid_sample_public_asset_notice_20260703.md` | 포함 |
| 5~6 | 샘플 출력: 공고 분석 리포트 | `20_제출초안/sample_outputs/onbid_public_asset_analysis_report_v01_20260703.md` | 포함 |
| 7 | 공공데이터 활용 구조도 | `20_제출초안/03_공공데이터_활용구조도_OnBidPublicAssetDocAgent_20260704.md` | 포함 |
| 8 | API 필드 매핑 샘플 | `20_제출초안/sample_inputs/onbid_api_field_mapping_sample_20260704.md` | 포함 |
| 9 | 기존 문서 Agent 워크플로우 | `docs/reusable-application-documents-20260703/files/C_reusable_product_evidence/` | 선택 |
| 10 | HWPX/PDF 산출 경험 | `bizketch_04_hwpx_sample.pdf` 또는 요약 1쪽 | 선택 |

## 포함하지 않을 자료

| 자료 | 제외 이유 |
| --- | --- |
| 모두의 챌린지 AX 제출본 | 불합격 이력과 타 공고명 노출 위험 |
| Top-Down 다날 전용 정산문서 자료 | 수요기업과 도메인이 달라 재사용 자료처럼 보일 위험 |
| AI+ OpenData 정책자금 제출본 전체 | 다른 과제명과 계약연계형 문맥 노출 위험 |
| 개인정보가 보이는 화면 | 제출·커밋 위험 |

## 보조 증빙 설명 문장

사용 가능:

> 아래 자료는 온비드 공공자산 서비스 구현물이 아니라, 데일컴퍼니가 보유한 문서 기반 AI Agent, HWPX/PDF 산출, 룰 기반 검증 경험을 보여주는 보조 증빙입니다. 본 아이템에서는 해당 경험을 KAMCO·온비드 공공데이터 기반 공고 해석 리포트로 전환합니다.

사용 금지:

> 온비드 입찰 자동화 완료, 공매 낙찰 예측, 권리분석 자동화, 투자수익률 예측, 법률 검토 자동화
