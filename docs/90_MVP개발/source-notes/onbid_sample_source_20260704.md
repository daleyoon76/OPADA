# 온비드 샘플 공고 출처 메모

확인일: 2026-07-04 KST  
용도: OnBid Public Asset Doc Agent MVP 샘플 데이터 출처

## 사용 공고

- 공고명: `2026년도010회 국유재산 대부입찰 공고`
- 공고번호: `202605-13728-00`
- 재산유형: 국유재산
- 공고기관: 한국자산관리공사
- 입찰방식: 일반경쟁(최고가방식) / 총액
- 입찰구분: 전자입찰
- 공고일: 2026-05-18
- 출처 URL: `https://www.onbid.co.kr/op/cltrpbancinf/pbanc/pbancdtlinf/PbancDtlInqController/mvmnPbancDtl.do?cltrPrptDivCd=10&cltrScrnGrpCd=0&onbidCltrno=1413572&onbidPbancNo=887390&pbctCdtnNo=5988631&pbctNo=10032196`

## MVP 반영 방식

- 온비드 공개 페이지에서 확인되는 공고명, 기관, 재산유형, 입찰방식, 입찰구분, 공고일, 관련문서, 제출서류, 입찰보증금, 잔대금 기한, 대부료 납부 방식, 리스크 문구를 표준 JSON 형태로 수작업 구조화했다.
- 기본 샘플은 제출 증빙용으로 보관하되, 현재 로컬 MVP는 온비드 공개 페이지와 short URL을 서버에서 읽어 같은 스키마로 변환한다.
- 화면에는 `실제 온비드 페이지 분석`, `원문 확인 필요`, `법률/투자 판단 아님`을 표시한다.
