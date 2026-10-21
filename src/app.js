const sampleNotice = {
  sourceUrl:
    "https://www.onbid.co.kr/op/cltrpbancinf/pbanc/pbancdtlinf/PbancDtlInqController/mvmnPbancDtl.do?cltrPrptDivCd=10&cltrScrnGrpCd=0&onbidCltrno=1413572&onbidPbancNo=887390&pbctCdtnNo=5988631&pbctNo=10032196",
  mode: "기본 샘플 공고",
  noticeId: "202605-13728-00",
  title: "2026년도010회 국유재산 대부입찰 공고",
  agency: "한국자산관리공사",
  assetType: "국유재산",
  disposition: "임대",
  dispositionLabel: "임대/대부입찰",
  bidMethod: "일반경쟁(최고가방식) / 총액",
  bidType: "전자입찰",
  noticeDate: "2026-05-18",
  round: "2026년도 010회차",
  contact: "국유재산지원처 / 물건정보참조",
  relatedDocs: ["국유재산 대부입찰공고문.pdf", "[참고] 쉽게 풀어쓴 국유재산 대부 입찰.jpg"],
  fields: [
    {
      key: "notice_id",
      value: "202605-13728-00",
      source: "온비드 공고 상세",
      report: "공고 식별 및 원문 링크",
    },
    {
      key: "asset_type",
      value: "국유재산 / 임대",
      source: "재산유형, 처분방식",
      report: "공고 한 줄 요약",
    },
    {
      key: "agency",
      value: "한국자산관리공사",
      source: "공고기관",
      report: "담당기관 및 확인 질문",
    },
    {
      key: "bid_method",
      value: "일반경쟁(최고가방식) / 총액",
      source: "입찰방식",
      report: "핵심 조건",
    },
    {
      key: "bid_type",
      value: "전자입찰",
      source: "입찰구분",
      report: "진행 방식",
    },
    {
      key: "bid_deposit",
      value: "입찰금액 X 5%",
      source: "입찰정보 > 입찰보증금",
      report: "비용 후보",
    },
    {
      key: "required_documents",
      value: "공동입찰/대리입찰 서류, 인감증명서 또는 본인서명사실확인서",
      source: "공고문 > 공동입찰/대리입찰 제출서류 문단, 제출서류 테이블",
      report: "제출서류 체크리스트",
    },
    {
      key: "post_award_duties",
      value: "잔대금 납부기한은 원문 기준 확인 필요, 대부료 납부 방식 확인",
      source: "입찰정보 > 잔대금 납부기한, 공고문 > 국유재산 연간대부료 납부 방법",
      report: "낙찰 후 확인사항",
    },
  ],
  schedule: [
    {
      title: "공고일",
      value: "2026-05-18",
      note: "공개 온비드 공고 상세 표시값",
      status: "source",
    },
    {
      title: "제출서류 마감",
      value: "입찰 기간 마감일 17:00까지",
      note: "공동/대리입찰 서류는 원본 제출 조건 확인 필요",
      status: "check",
    },
    {
      title: "전자보증서 신청",
      value: "입찰마감일 전 영업일 18:00 전",
      note: "SGI서울보증 전자보증서 발급 조건 확인",
      status: "check",
    },
    {
      title: "낙찰 후 잔대금",
      value: "원문 기준 기한 확인 필요",
      note: "온비드 표기값의 단위와 실제 기한은 공고 원문 및 담당기관 확인",
      status: "warn",
    },
  ],
  documents: {
    person: [
      "본인서명사실확인서 또는 인감증명서",
      "온비드 회원 및 인증서 등록",
      "전자보증서 또는 입찰보증금 준비",
    ],
    sole: [
      "사업자등록증명 또는 사업자등록증",
      "인감증명서 또는 본인서명사실확인서",
      "국세/지방세 완납 여부 확인",
      "공동/대리입찰 시 참가신청서 원본 제출",
    ],
    corp: [
      "법인등기사항전부증명서",
      "법인인감증명서",
      "사업자등록증명",
      "공동/대리입찰 위임·신청 서류",
    ],
    founder: [
      "개인 신분 확인 서류",
      "사업자등록 전 입찰 가능 여부 담당기관 확인",
      "창업 목적의 공간/자산 활용 가능 조건 확인",
    ],
  },
  costs: [
    {
      title: "입찰보증금",
      value: "입찰금액 X 5%",
      note: "전자보증서 가능. 실제 납부 방식은 공고 원문 우선",
    },
    {
      title: "국유재산 대부료",
      value: "연간대부료 기준",
      note: "50만원 초과 시 연 12회 이내 분납 가능 조건 표시",
    },
    {
      title: "서류 제출 비용",
      value: "등기/원본 발급 비용 후보",
      note: "공동/대리입찰 시 원본 제출 조건 때문에 발생 가능",
    },
  ],
  risks: [
    {
      title: "서류 제출 방식 착오",
      reason: "공동입찰/대리입찰은 전자서명 또는 서류 제출 방식이 나뉜다.",
      question: "이번 물건에서 공동/대리입찰 서류 제출 방식과 마감 시간을 담당부서에 확인했는가?",
      source: "공고문 > 공동입찰/대리입찰 제출서류 문단",
    },
    {
      title: "원본 서류 불일치",
      reason: "인감증명서와 신청서상 날인 도장의 일치 여부를 확인한다.",
      question: "인감 또는 서명 방식이 신청서와 증명서에서 일치하는가?",
      source: "공고문 > 인감증명서/본인서명사실확인서 일치 여부 유의문구",
    },
    {
      title: "보증서 발급 시점",
      reason: "전자보증서 발급 신청은 입찰마감일 전 영업일 18시 전으로 제한된다.",
      question: "전자보증서가 필요한 경우 발급 신청 가능 시간을 역산했는가?",
      source: "입찰정보 > 전자보증서 설명 문단",
    },
    {
      title: "대부료 납부 방식",
      reason: "연간대부료 금액 구간에 따라 분납 또는 일시 납부 조건이 달라진다.",
      question: "연간대부료 금액 기준으로 분납 가능 여부와 납부 일정을 확인했는가?",
      source: "공고문 > 국유재산 연간대부료 납부 방법",
    },
  ],
  todayActions: [
    {
      title: "공고 유형 확인",
      value: "국유재산 임대/대부입찰",
      note: "매각 검토 목적이면 다른 유형의 공고를 선택해야 합니다.",
      status: "safe",
    },
    {
      title: "입찰보증금 방식 확인",
      value: "입찰금액 X 5%",
      note: "전자보증서 사용 가능 여부와 신청 마감 시간을 확인합니다.",
      status: "check",
    },
    {
      title: "공동/대리입찰 여부 결정",
      value: "선택에 따라 원본 서류 제출 방식 달라짐",
      note: "공동입찰 또는 대리입찰이면 서류 원본 제출 조건을 먼저 확인합니다.",
      status: "check",
    },
  ],
  alerts: [
    {
      title: "전자보증서 신청",
      value: "입찰마감일 전 영업일 18:00 전",
      note: "SGI서울보증 등 전자보증서 발급 가능 시간을 역산합니다.",
      status: "warn",
    },
    {
      title: "공동/대리입찰 서류",
      value: "입찰 기간 마감일 17:00까지",
      note: "원본 제출 조건이 있으면 우편/방문 소요 시간을 반영합니다.",
      status: "warn",
    },
    {
      title: "낙찰 후 계약",
      value: "공고 원문 기준 확인",
      note: "잔대금, 주민등록등본 등 후속 제출물을 담당기관에 확인합니다.",
      status: "check",
    },
  ],
  boardTasks: [
    {
      id: "guarantee",
      title: "입찰보증금 방식 확인",
      action: "전자보증서 사용 가능 여부와 신청 마감 시간을 확인",
      due: "입찰마감일 전 영업일 18:00 전",
      detail: "공고상 입찰보증금은 입찰금액의 5%입니다. 실제 납부 방식과 전자보증서 가능 여부는 공고 원문과 보증기관 안내를 확인합니다.",
      question: "전자보증서 발급 가능 여부와 신청 마감 시간이 이번 물건에 그대로 적용되는가?",
      source: "입찰정보 > 입찰보증금, 전자보증서 설명 문단",
      cta: "SGI서울보증",
      url: "https://www.sgic.co.kr/",
      defaultDone: false,
    },
    {
      id: "business-cert",
      title: "사업자등록증명 준비처 열기",
      action: "홈택스에서 발급 가능 경로 확인",
      due: "입찰 전",
      detail: "개인사업자 자격 확인에 필요한 서류입니다. 공고별 제출 방식과 원본/사본 여부는 담당기관 확인이 필요합니다.",
      question: "개인사업자 참여 시 사업자등록증명 원본 또는 발급일 조건이 있는가?",
      source: "공고문 > 제출서류 테이블",
      cta: "홈택스 열기",
      url: "https://www.hometax.go.kr/",
      defaultDone: false,
      userTypes: ["sole"],
    },
    {
      id: "identity-cert",
      title: "신분 확인 서류 준비처 확인",
      action: "개인 기준 제출서류가 필요한지 확인",
      due: "입찰 전",
      detail: "개인 또는 예비창업자는 본인 확인 서류와 인증서 등록 조건을 먼저 확인합니다. 실제 제출서류는 공고 원문과 담당기관 기준을 우선합니다.",
      question: "개인 또는 예비창업자 명의로 입찰 가능한지, 낙찰 후 계약 주체 제한이 있는가?",
      source: "공고문 > 입찰참가자격, 제출서류 테이블",
      cta: "정부24 열기",
      url: "https://www.gov.kr/",
      defaultDone: false,
      userTypes: ["person", "founder"],
    },
    {
      id: "corp-cert",
      title: "법인 증빙서류 준비처 확인",
      action: "법인등기사항증명서와 법인인감증명서 경로 확인",
      due: "입찰 전",
      detail: "법인 참여자는 대표권, 법인인감, 사업자 정보 확인 서류가 필요할 수 있습니다. 원본/사본 및 발급일 조건은 담당기관에 확인합니다.",
      question: "법인등기사항증명서와 법인인감증명서의 발급일, 원본 제출 조건이 있는가?",
      source: "공고문 > 제출서류 테이블",
      cta: "인터넷등기소",
      url: "https://www.iros.go.kr/",
      defaultDone: false,
      userTypes: ["corp"],
    },
    {
      id: "joint-bid",
      title: "공동/대리입찰 여부 결정",
      action: "해당 여부를 정하고 원본 서류 제출 조건을 확인",
      due: "입찰 기간 마감일 17:00 전",
      detail: "공동입찰 또는 대리입찰이면 참가신청서, 위임장, 인감/서명 관련 서류 제출 방식이 달라질 수 있습니다.",
      question: "이번 물건에서 공동/대리입찰 서류 제출 방식과 마감 시간은 무엇인가?",
      source: "공고문 > 공동입찰/대리입찰 제출서류 문단",
      cta: "온비드 원문",
      url: "https://www.onbid.co.kr/op/cltrpbancinf/pbanc/pbancdtlinf/PbancDtlInqController/mvmnPbancDtl.do?cltrPrptDivCd=10&cltrScrnGrpCd=0&onbidCltrno=1413572&onbidPbancNo=887390&pbctCdtnNo=5988631&pbctNo=10032196",
      defaultDone: false,
    },
    {
      id: "agency-question",
      title: "담당기관 확인 질문 정리",
      action: "대부료 분납, 잔대금, 후속 제출물을 문의할 질문으로 정리",
      due: "입찰 전",
      detail: "AI가 결론을 내리는 대신 담당기관에 확인해야 할 질문을 원문 근거와 함께 분리합니다.",
      question: "대부료 분납, 잔대금 기한, 낙찰 후 제출물은 공고 원문 기준으로 어떻게 확정되는가?",
      source: "입찰정보 > 잔대금 납부기한, 공고문 > 국유재산 연간대부료 납부 방법",
      cta: "공고 원문",
      url: "https://www.onbid.co.kr/op/cltrpbancinf/pbanc/pbancdtlinf/PbancDtlInqController/mvmnPbancDtl.do?cltrPrptDivCd=10&cltrScrnGrpCd=0&onbidCltrno=1413572&onbidPbancNo=887390&pbctCdtnNo=5988631&pbctNo=10032196",
      defaultDone: false,
    },
  ],
  prepItems: {
    person: [
      {
        title: "온비드 회원가입 및 인증서 등록",
        reason: "전자입찰 참여 전 기본 준비",
        where: "온비드",
        url: "https://www.onbid.co.kr/",
        status: "미확인",
      },
      {
        title: "본인서명사실확인서 또는 인감증명서",
        reason: "공동/대리입찰 또는 원본 서류 제출 시 확인",
        where: "정부24 안내 또는 읍면동 주민센터",
        url: "https://www.gov.kr/mw/AA020InfoCappView.do?CappBizCD=13110000047",
        status: "확인 필요",
      },
      {
        title: "전자보증서 또는 입찰보증금",
        reason: "입찰보증금 조건 충족",
        where: "SGI서울보증/온비드 공고 안내",
        url: "https://www.sgic.co.kr/",
        status: "미준비",
      },
    ],
    sole: [
      {
        title: "사업자등록증명",
        reason: "개인사업자 자격 확인",
        where: "국세청 홈택스",
        url: "https://www.hometax.go.kr/",
        status: "미준비",
      },
      {
        title: "본인서명사실확인서 또는 인감증명서",
        reason: "신청서 날인/서명 일치 여부 확인",
        where: "정부24 안내 또는 읍면동 주민센터",
        url: "https://www.gov.kr/mw/AA020InfoCappView.do?CappBizCD=13110000047",
        status: "확인 필요",
      },
      {
        title: "국세/지방세 증명 후보",
        reason: "기관 또는 공고별 추가 요구 가능성 확인",
        where: "홈택스/정부24",
        url: "https://www.gov.kr/",
        status: "공고 확인",
      },
      {
        title: "전자보증서 또는 입찰보증금",
        reason: "입찰금액의 5% 조건 충족",
        where: "SGI서울보증/온비드 공고 안내",
        url: "https://www.sgic.co.kr/",
        status: "미준비",
      },
    ],
    corp: [
      {
        title: "법인등기사항전부증명서",
        reason: "법인 자격 및 대표권 확인",
        where: "인터넷등기소",
        url: "https://www.iros.go.kr/",
        status: "미준비",
      },
      {
        title: "법인인감증명서",
        reason: "신청서 날인 및 위임서류 확인",
        where: "인터넷등기소/등기소 무인발급기",
        url: "https://data.iros.go.kr/rp/ro/openRgsKioskInfrm.do",
        status: "확인 필요",
      },
      {
        title: "사업자등록증명",
        reason: "사업자 정보 확인",
        where: "국세청 홈택스",
        url: "https://www.hometax.go.kr/",
        status: "미준비",
      },
    ],
    founder: [
      {
        title: "개인 신분 확인 서류",
        reason: "개인 자격 입찰 가능 여부 확인",
        where: "정부24/주민센터",
        url: "https://www.gov.kr/",
        status: "확인 필요",
      },
      {
        title: "사업자등록 전 입찰 가능 여부",
        reason: "창업 목적 사용 가능성과 계약 주체 확인",
        where: "공고 담당기관 문의",
        url: "https://www.onbid.co.kr/",
        status: "문의 필요",
      },
      {
        title: "전자보증서 또는 입찰보증금",
        reason: "입찰보증금 조건 충족",
        where: "SGI서울보증/온비드 공고 안내",
        url: "https://www.sgic.co.kr/",
        status: "미준비",
      },
    ],
  },
  watchlist: [
    {
      notice: "202605-13728-00 국유재산 대부입찰",
      type: "국유재산 / 임대·대부",
      next: "보증서 신청 시간 확인",
      status: "준비중",
    },
    {
      notice: "매각 공고 후보",
      type: "국유재산 / 매각",
      next: "사용자 관심지역 입력 후 후보 선택",
      status: "미선택",
    },
    {
      notice: "창업 공간 후보",
      type: "공공시설 / 임대",
      next: "용도 제한 및 시설 상태 확인",
      status: "담당기관 확인 필요",
    },
  ],
};

const pipelineSteps = [
  "URL/조건 입력",
  "공고번호·물건번호 자동 추출",
  "공고 유형과 목적 비교",
  "일정·비용·서류 추출",
  "준비처 링크와 확인 질문 연결",
  "준비 보드 생성",
];

const initialSampleNotice = JSON.parse(JSON.stringify(sampleNotice));
// 「샘플 불러오기」가 입력칸에 넣는 주소다(2026-10-19 동원님 지정 · 공유재산 임대 · 경기도 성남시
// 분당구 삼평동 696-1). 위 sampleNotice 와는 다른 공고다. 버튼은 주소만 채우고, 화면 내용은
// 「다음」으로 분석해야 이 공고로 바뀐다. 단축 주소는 서버가 302 를 따라가 물건상세로 읽는다.
const SAMPLE_INPUT_URL = "https://www.onbid.co.kr/shortcut.do?code=C8Femdw4sdo4";

const userTypeLabels = {
  person: "개인",
  sole: "개인사업자",
  corp: "법인",
  founder: "예비창업자",
};

const focusLabels = {
  lease: "임대/대부 공고 검토",
  sale: "매각/공매 공고 검토",
  startup: "창업 공간 탐색",
};

let currentView = "input";
let currentStage = 0;
let analysisRequestId = 0;
let analysisError = null;
let analyzedInputValue = "";
let boardGenerated = false;
// AI 코치 질문의 진행 상태다. renderReport 는 체크박스 하나에도 코치 영역 innerHTML 을 통째로 바꾸므로,
// 받은 답과 잠금 상태를 DOM 이 아니라 여기 두고 다시 그릴 때 이 값에서 되살린다(3팀 진단 I1·I3).
// DOM 에 두면 답을 기다리는 사이 다시 그려진 새 요소에 「찾는 중」만 남고 답은 떨어진 옛 요소에 써진다.
let coachAnswerHtml = "";
let askInFlight = false;
let askRequestId = 0;
// 서버는 IP 당 1분 5회로 막는다. 429 를 받은 뒤 바로 다시 누르면 또 막히므로 그동안 버튼을 잠근다.
// 공고와 무관한 제한이라 새 공고로 넘어가도 풀지 않는다.
let askCooldownUntil = 0;
let askCooldownTimer = null;
// 입력~분석 마법사(1p 유형/목적 → 2p URL → 3p 결과 → 전환화면)의 현재 화면.
// currentView("input")는 그대로 바뀌지 않고, 그 안에서 보여줄 하위 화면만 이 값으로 고른다.
let inputStep = "profile";
let transitionTimer = null;
const wizardSteps = ["profile", "url", "result", "transition"];
// 서류 체크박스를 누를 때마다 전체 화면을 다시 그리는데, <details> 는 재생성될 때
// 기본값(닫힘)으로 돌아간다. 사용자가 연속으로 여러 서류를 체크할 수 있도록 이 상태를
// 따로 기억해뒀다가 다시 그릴 때 반영한다.
let docChecklistOpen = false;
// 할 일 카드의 「자세히」를 모두 펼쳐 둘지다. 기본은 접힘이다 — 펼쳐 두면 카드마다 문의 문장·
// 상세 설명·근거가 쏟아져 화면이 정신없다(2026-10-19 동원님 지시). 「안내 수준」 버튼이 이 값만
// 뒤집는다. 저장하지 않으므로 새로 열면 다시 접힌 상태다.
let guideDetailed = false;
// 준비 보드에서 지금 보여 줄 단계(1~4). null 이면 진행 상태에서 고른다(getBoardStage). 사용자가
// 단계 표시나 이전·다음 버튼을 누르면 그 값으로 고정되고, 새 공고를 분석하면 다시 null 이 된다.
let boardStageNum = null;
// 아래 고정 AI 코치를 접어 두었는지다. 보는 사람 브라우저에만 남기는 편의 설정이라 localStorage 에 둔다.
const coachCollapsedStorageKey = "onbid-public-asset-doc-agent-coach-collapsed-v1";
// 사용자가 접기/펴기를 고른 적이 없으면, 좁거나 낮은 화면에서는 접힌 상태로 시작한다(R2). 펼친 고정 영역이
// 390px 에서 화면의 29%, 가로 모드에서 59% 를 덮어 첫 화면에 보드 본문이 거의 없었다. 고른 값이 있으면 그것을 따른다.
const COACH_COMPACT_QUERY = "(max-width: 600px), (max-height: 500px)";
function getInitialCoachCollapsed() {
  const saved = readJsonStorage(coachCollapsedStorageKey, null);
  if (saved === true || saved === false) return saved;
  return Boolean(window.matchMedia?.(COACH_COMPACT_QUERY).matches);
}
let coachCollapsed = getInitialCoachCollapsed();
const taskStorageKey = "onbid-public-asset-doc-agent-tasks-v1";
const recentNoticeStorageKey = "onbid-public-asset-doc-agent-recent-v1";
const favoriteNoticeStorageKey = "onbid-public-asset-doc-agent-favorites-v1";

// 준비 단계(공고 확인 → 입찰 전 준비 → 입찰 참여 → 낙찰 후 준비). currentStage/pipelineSteps(Step1 분석
// 파이프라인, 1895·1903행 근처)와 겹치지 않게 prepStage 계열로 둔다(3팀 ux-audit §⑸ 제약).
// 서버(server.py build_tasks())가 이미 4개 id를 고정 순서로 만들므로, 서버 응답 구조를
// 바꾸지 않고 화면 쪽에 이 매핑 상수 하나만 둔다 — 서버 필드 추가보다 변경 범위가 작다.
// sequential 은 「순차 잠금 사슬에 들어가는 단계인가」다. 1~3단계는 사용자가 지금 해야 하는
// 일이라 앞 단계를 마쳐야 열린다. 4단계는 성질이 다르다 — 낙찰은 체크박스로 만들 수 있는
// 상태가 아니라 개찰 결과이고, 3단계 price 는 「최저입찰가격을 확인했다」는 뜻이지
// 「낙찰됐다」는 뜻이 아니다. 그래서 4단계는 잠그지 않고 sequential: false 로 둔다
// (2026-10-18 ux-design-review 질문 2).
const PREP_STAGES = [
  // bid-qualification 은 서버가 아니라 화면이 만든다(getBidQualificationTask · 자격 제한이 있는 공고에만).
  { num: 1, title: "공고 확인", taskIds: ["bid-qualification", "notice-type", "bid-period"], sequential: true },
  { num: 2, title: "입찰 전 준비", taskIds: ["documents"], sequential: true },
  { num: 3, title: "입찰 참여", taskIds: ["price"], sequential: true },
  { num: 4, title: "낙찰 후 준비", taskIds: [], sequential: false },
];

// 4단계가 담는 서류의 stage 값. server.py 의 resolve_doc_stage() 가 판정해 넣는 값과 같아야
// 한다(src/server.py). 한쪽만 고치면 4단계가 조용히 빈다.
const POST_AWARD_DOC_STAGE = "낙찰 후·계약 시";

function getTaskStageNum(taskId) {
  const stage = PREP_STAGES.find((candidate) => candidate.taskIds.includes(taskId));
  return stage ? stage.num : null;
}

// 경험 수준 질문(질문 A) 응답. 공고와 무관한 전역 키 — taskStorageKeyFor(notice)와 분리된다.
const experienceLevelStorageKey = "opada-experience-level";

function getExperienceLevel() {
  try {
    const saved = window.localStorage.getItem(experienceLevelStorageKey);
    return saved === "beginner" || saved === "experienced" ? saved : null;
  } catch {
    return null;
  }
}


// "처음이에요"(또는 아직 응답하지 않음)일 때 더 자세히 보여준다 — 과설명 비용보다
// 초보자가 덜 설명받아 놓치는 비용이 크다는 ux-audit §⑵ 판단을 그대로 따른다.
function isExperienceBeginner() {
  return getExperienceLevel() !== "experienced";
}

const aiTaskSignals = [
  {
    taskIds: ["price", "guarantee"],
    taskKeywords: ["가격", "보증금", "대부료", "비용", "납부", "잔금"],
    checkKeywords: ["대부료", "비용", "고정비", "공과금", "보험", "보증금", "납부", "잔금"],
  },
  {
    taskIds: ["documents", "joint-bid", "business-cert", "identity-cert", "corp-cert"],
    taskKeywords: ["서류", "원본", "대리", "공동", "위임", "증명", "제출"],
    checkKeywords: ["서류", "제출", "원본", "대리", "공동", "직접제출", "접수"],
  },
  {
    taskIds: ["notice-type"],
    taskKeywords: ["유형", "목적", "사용", "용도", "재산유형", "공유"],
    checkKeywords: ["업종", "사용", "용도", "목적", "승인", "제한"],
  },
  {
    taskIds: [],
    taskKeywords: ["담당기관", "질문", "문의", "현장", "인수"],
    checkKeywords: ["현장", "인수", "원상복구", "담당기관", "문의"],
  },
  {
    taskIds: ["bid-period"],
    taskKeywords: ["기간", "마감", "개찰", "일정"],
    checkKeywords: ["마감", "일정", "시각", "시간"],
  },
];

const byId = (id) => document.getElementById(id);

function setView(view) {
  if (view === "report" && isAnalysisReady()) {
    boardGenerated = true;
    currentStage = pipelineSteps.length;
  }
  currentView = view;
  document.querySelectorAll(".view").forEach((node) => node.classList.remove("is-visible"));
  document.querySelectorAll(".tab").forEach((node) => {
    node.classList.remove("is-active");
    node.removeAttribute("aria-current");
  });
  byId(`view-${view}`).classList.add("is-visible");
  const activeTab = document.querySelector(`[data-view="${view}"]`);
  activeTab.classList.add("is-active");
  activeTab.setAttribute("aria-current", "page");
  if (location.hash.replace("#", "") !== view) {
    history.replaceState(null, "", `#${view}`);
  }
  updateDockHeightVar();
}

function renderWizardStep() {
  const activeIndex = wizardSteps.indexOf(inputStep);
  wizardSteps.forEach((step, index) => {
    byId(`wizard-step-${step}`).classList.toggle("is-active", index === activeIndex);
  });
  // 단계 표시는 버튼이다. 누르면 그 하위 페이지로 간다(2026-10-19 동원님 지시). 1-3 은 분석이 끝난 뒤에만 열린다.
  document.querySelectorAll("[data-wizard-dot]").forEach((dot) => {
    const dotIndex = wizardSteps.indexOf(dot.dataset.wizardDot);
    const active = dotIndex === activeIndex;
    const reachable = isWizardStepReachable(dot.dataset.wizardDot);
    dot.classList.toggle("is-active", active);
    dot.classList.toggle("is-done", dotIndex < activeIndex);
    dot.disabled = !reachable;
    dot.title = reachable ? "" : "1-2 에서 「분석하기」를 누르면 열립니다";
    if (active) dot.setAttribute("aria-current", "step");
    else dot.removeAttribute("aria-current");
  });
}

function isWizardStepReachable(step) {
  if (inputStep === "transition") return false;
  if (step === "result") return isAnalysisReady();
  return step === "profile" || step === "url";
}

function setInputStep(step) {
  inputStep = step;
  renderWizardStep();
  byId(`wizard-step-${step}`).scrollIntoView({ block: "start", behavior: "smooth" });
}

function badge(text, type = "safe") {
  return `<span class="badge ${type}">${text}</span>`;
}

// 화면 템플릿은 네 가지로 한정한다(2026-10-19 동원님 지시 · 탭마다 UI 가 달랐다).
// ⑴ 블록(.block · 제목 + 내용) ⑵ 정보 행(infoRow · 머리표 · 제목 · 설명 · 근거 · 링크)
// ⑶ 값 칸(factCell · 라벨 + 값) ⑷ 할 일 카드(renderTaskItem). 새 화면 요소는 이 넷 안에서 만든다.
function infoRow({ tag = "", tone = "neutral", title = "", text = "", meta = "", action = null, cls = "" } = {}) {
  const actionHtml = action
    ? `<a class="info-row-action text-action" href="${action.href}" target="_blank" rel="noreferrer">${action.label}</a>`
    : "";
  return `<div class="info-row ${cls}">
    <div class="info-row-head">${tag ? badge(tag, tone) : ""}${title ? `<strong class="info-row-title">${title}</strong>` : ""}${actionHtml}</div>
    ${text ? `<p class="info-row-text">${text}</p>` : ""}
    ${meta ? `<p class="info-row-meta">${meta}</p>` : ""}
  </div>`;
}

function factCell(label, valueHtml, cls = "") {
  return `<div class="fact-row ${cls}"><span class="field-label">${label}</span>${valueHtml}</div>`;
}

// server.py의 NOTICE_VALUE_FALLBACK 과 같은 문구다 — 입찰기간·최저입찰가격을 추출하지
// 못했을 때 화면 여러 곳에 흩어져 있던 실패 문구를 이 값 하나로 맞춘다(2026-09-22 UI 정리).
const NOTICE_VALUE_FALLBACK = "원문 확인 필요";

function fieldValue(value) {
  const isFallback = value === NOTICE_VALUE_FALLBACK;
  return `<strong class="field-value${isFallback ? " is-fallback" : ""}">${value}</strong>`;
}

function normalizedText(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/\s+/g, "");
}

function coachChecks() {
  return Array.isArray(sampleNotice.aiCoach?.unresolvedChecks) ? sampleNotice.aiCoach.unresolvedChecks : [];
}

function hasKeyword(text, keywords) {
  return keywords.some((keyword) => text.includes(normalizedText(keyword)));
}

function scoreTaskAiMatch(task, check) {
  const taskText = normalizedText(`${task.title} ${task.action} ${task.detail} ${task.question} ${task.source}`);
  const checkText = normalizedText(`${check.title} ${check.reason} ${check.action} ${check.source}`);
  let score = 0;

  aiTaskSignals.forEach((signal) => {
    const taskHit = signal.taskIds.includes(task.id) || hasKeyword(taskText, signal.taskKeywords);
    const checkHit = hasKeyword(checkText, signal.checkKeywords);
    if (taskHit && checkHit) {
      score += signal.taskIds.includes(task.id) ? 6 : 4;
    }
  });

  return score;
}

function getTaskAiMatch(task) {
  const checks = coachChecks();
  if (!checks.length) {
    return null;
  }

  let best = null;
  checks.forEach((check, index) => {
    const score = scoreTaskAiMatch(task, check);
    if (score >= 4 && (!best || score > best.score)) {
      best = { check, score, index };
    }
  });

  return best;
}

function getAiTaskAssignments(tasks) {
  const checks = coachChecks();
  const candidates = [];
  tasks.forEach((task) => {
    checks.forEach((check, checkIndex) => {
      const score = scoreTaskAiMatch(task, check);
      if (score >= 4) {
        candidates.push({ task, check, checkIndex, score });
      }
    });
  });

  candidates.sort((a, b) => b.score - a.score);
  const assignedTasks = new Map();
  const assignedChecks = new Set();
  const maxAssignments = Math.min(3, checks.length);

  candidates.forEach((candidate) => {
    if (assignedTasks.size >= maxAssignments) {
      return;
    }
    if (assignedTasks.has(candidate.task.id) || assignedChecks.has(candidate.checkIndex)) {
      return;
    }
    assignedTasks.set(candidate.task.id, {
      check: candidate.check,
      score: candidate.score,
      index: candidate.checkIndex,
    });
    assignedChecks.add(candidate.checkIndex);
  });

  return assignedTasks;
}

function renderPipeline() {
  const html = pipelineSteps
    .map((step, index) => {
      const isLastStep = index === pipelineSteps.length - 1;
      const waitingForPrepare = isLastStep && isAnalysisReady() && !boardGenerated;
      const done = index < currentStage && !waitingForPrepare;
      const active = !waitingForPrepare && index === currentStage && currentStage < pipelineSteps.length;
      const cls = done ? "done" : active ? "active" : "";
      const state = done ? "완료" : active ? "진행" : "대기";
      return `<li class="${cls}"><span class="state">${state}</span><strong>${step}</strong></li>`;
    })
    .join("");
  byId("pipeline").innerHTML = html;
}

function getSelectedFocus() {
  return byId("asset-focus").value;
}

function getNoticeInput() {
  const raw = byId("notice-url").value.trim();
  const urlMatch = raw.match(/https?:\/\/\S+/i);
  return urlMatch ? urlMatch[0] : raw;
}

function noticeKey(notice) {
  return [
    notice.onbidPbancNo || notice.noticeId || "notice",
    notice.onbidCltrno || notice.cltrMngNo || notice.title || "item",
  ]
    .join("::")
    .replace(/\s+/g, "-");
}

function taskStorageKeyFor(notice) {
  return `${taskStorageKey}::${noticeKey(notice)}`;
}

const docStorageKey = "onbid-public-asset-doc-agent-docs-v1";

function docStorageKeyFor(notice) {
  return `${docStorageKey}::${noticeKey(notice)}`;
}

// 공동입찰·대리입찰 질문(2단계 서류준비)의 답은 공고마다 다시 물어야 하므로 공고별로 저장한다.
const docConditionStorageKey = "onbid-public-asset-doc-agent-doc-conditions-v1";

function docConditionStorageKeyFor(notice) {
  return `${docConditionStorageKey}::${noticeKey(notice)}`;
}

function getDocConditionAnswers() {
  const saved = readJsonStorage(docConditionStorageKeyFor(sampleNotice), {});
  return {
    joint: saved.joint === "yes" ? "yes" : "no",
    proxy: saved.proxy === "yes" ? "yes" : "no",
  };
}

function setDocConditionAnswer(key, value) {
  const current = getDocConditionAnswers();
  current[key] = value === "yes" ? "yes" : "no";
  writeJsonStorage(docConditionStorageKeyFor(sampleNotice), current);
}

// 공동입찰·대리입찰에서 "예"로 답했을 때 추가로 안내하는 서류다. 이 공고 원문에서 추출한
// 것이 아니라, server.py DOC_HOWTO가 이미 쓰는 공식 서식명을 그대로 재사용한 일반 안내다.
const DOC_CONDITION_SUPPLEMENT = {
  joint: [
    {
      name: "공동입찰참가신청서",
      howto: "공고 첨부 서식 또는 온비드 자료실 서식",
      howtoUrl: "https://www.onbid.co.kr/",
      // 압류재산 공매공고문 「16. 주의사항」 자항 ③호는 단서로 끝난다 — 「다만, 인터넷 공매의
      // 경우에는 공동입찰신청을 온비드 등록으로 대신할 수 있습니다」. 같은 공고문 「1. 입찰방법
      // 가」항이 압류재산 공매를 인터넷 공매로 명시하므로, 이 단서를 빼면 하지 않아도 되는 직접
      // 제출을 하라고 안내하게 된다(2026-10-18 researcher-fact-check 사실 1).
      // 🔴 이 단서는 압류재산 전용이다 — 국유재산 대부입찰 공고문(researcher-fact-check 사실 3)
      // 은 이 단서가 없고 "전자서명 방식 또는 서류제출 방식 중 선택"을 제시한다. 재산유형을
      // 가르지 않으면 압류재산 전용 문구가 국유재산 화면에도 새어 나간다(2026-10-19 E2E S3).
      note: "압류재산 공매는 인터넷 공매이므로, 공동입찰신청을 온비드 등록으로 대신할 수 있습니다(압류재산 공매공고문 「16. 주의사항」 자항 ③호 단서). 서류를 직접 제출하기 전에 공고 원문의 해당 조항을 먼저 확인하십시오.",
      noteAssetTypes: ["압류재산"],
    },
    {
      name: "공동매수신청인 전원의 인감증명서 또는 본인서명사실확인서",
      howto: "정부24 또는 주민센터",
      howtoUrl: "https://www.gov.kr/",
      note: "인감증명서가 없으면 본인서명사실확인서로 대신할 수 있습니다. 공고문이 두 서류를 선택지로 함께 적습니다.",
    },
  ],
  proxy: [
    {
      name: "대리입찰신청서",
      howto: "공고 첨부 서식 또는 온비드 자료실 서식",
      howtoUrl: "https://www.onbid.co.kr/",
      note: "여러 사람의 공동입찰을 대리하는 경우에는 대리입찰신청서와 공동입찰신청서를 모두 제출해야 유효한 입찰로 처리됩니다(캠코 온비드 이용 매뉴얼 「입찰하기」).",
    },
    { name: "위임장", howto: "공고 첨부 서식 또는 온비드 자료실 서식", howtoUrl: "https://www.onbid.co.kr/" },
    {
      name: "입찰자의 인감증명서 또는 본인서명사실확인서",
      howto: "정부24 또는 주민센터",
      howtoUrl: "https://www.gov.kr/",
      note: "인감증명서가 없으면 본인서명사실확인서로 대신할 수 있습니다. 공고문이 두 서류를 선택지로 함께 적습니다.",
    },
    { name: "대리인 신분증 등 본인 확인 서류 (확인 필요)", howto: "", howtoUrl: "" },
  ],
};

const DOC_SUPPLEMENT_EVIDENCE =
  "이 공고 원문에서 추출한 문장이 아니라, 공동입찰·대리입찰 시 온비드 공매에서 통상 요구하는 서류에 대한 일반 안내입니다. 실제 필요 여부와 서식은 공고 원문과 담당기관 기준으로 다시 확인하십시오.";

function buildDocConditionSupplementItem(base, conditionLabel, assetType) {
  // noteAssetTypes 가 있으면 그 재산유형에서만 note 를 붙인다 — 특정 재산유형의 공고문
  // 조항을 근거로 한 note 는 다른 재산유형에 그대로 옮기면 틀린 안내가 된다(위 joint[0] 참조).
  const noteApplies =
    !base.noteAssetTypes || base.noteAssetTypes.some((type) => String(assetType || "").includes(type));
  const note = noteApplies ? base.note : "";
  return {
    name: base.name,
    conditions: [conditionLabel],
    conditionKeys: [],
    copy: "",
    validity: "",
    method: "",
    due: "",
    count: "",
    stage: "입찰 전",
    howto: base.howto,
    howtoUrl: base.howtoUrl,
    sourceSection: "",
    evidence: note ? `${note} ${DOC_SUPPLEMENT_EVIDENCE}` : DOC_SUPPLEMENT_EVIDENCE,
  };
}

// 4단계(낙찰 후 준비)의 일반 안내 서류다. DOC_CONDITION_SUPPLEMENT 와 같은 방식으로, 이 공고
// 원문에서 추출한 것이 아니라는 사실을 항목마다 evidence 에 명시한다. 공고에서 뽑은 「낙찰
// 후·계약 시」 서류는 표본 23건 중 6건에만 있어서, 이 안내가 없으면 4단계가 대부분의 공고에서
// 빈 껍데기가 된다(2026-10-18 ux-design-review P1-2). 재산유형과 무관하게 넣는다.
//
// 첫 묶음을 맨 위에 둔다 — 매각결정기일까지 내지 않으면 매각불허결정이 될 수 있어, 기한을
// 놓치면 낙찰 자체가 취소된다. 두 번째 묶음보다 되돌리기가 비싸다.
const POST_AWARD_DOC_GROUPS = [
  {
    condition: "낙찰 직후 · 매각결정기일 전까지 (압류재산)",
    // 이 묶음의 근거는 압류재산 공매공고문이다. 다른 재산유형에는 매각결정기일이라는 절차
    // 자체가 없을 수 있다. 🔴 그래도 숨기지 않고 접어 둔다 — 숨기면 재산유형 추출이 틀렸을
    // 때(「재산유형 확인」으로 떨어지는 경로가 실제로 있다) 사용자가 이 묶음의 존재조차 모르고
    // 지나간다. 접어 두면 제목은 보이므로 눌러서 확인할 수 있다.
    assetTypes: ["압류재산"],
    items: [
      {
        name: "농지 매수자격 증명 서류 (농지취득자격증명 또는 반려 공문 또는 토지이용계획 확인원)",
        due: "매각결정기일 전까지",
        howto: "정부24 (농지 소재지 읍·면·동)",
        howtoUrl: "https://www.gov.kr/",
        note: "공매재산이 농지(전·답·과수원 등)인 경우에만 해당합니다. 매각결정기일 전까지 제출하지 않으면 매각불허결정이 될 수 있습니다. 당초 매각결정기일로부터 10일 이내 범위에서 1회 연기를 신청할 수 있습니다. 근거는 「압류재산 공매공고문 16. 주의사항 다항」입니다.",
      },
      {
        name: "농지대장 (농민인 경우 추가 제출)",
        due: "매각결정기일 전까지",
        howto: "정부24",
        howtoUrl: "https://www.gov.kr/",
        note: "농민인 경우 위 매수자격 증명 서류에 더해 추가로 제출합니다. 근거는 「압류재산 공매공고문 16. 주의사항 다항」입니다.",
      },
    ],
  },
  {
    condition: "소유권이전 단계",
    // 소유권을 넘겨받는 매각 절차의 서류다. 임대·대부 공고에는 소유권이전이 없으므로 접는다
    // (2026-10-19 정합성 대조 · 임대 공고에도 펼쳐져 나가던 문제).
    dispositions: ["매각"],
    // 제출처는 재산유형마다 다르다. 압류재산은 매수인이 서류를 준비해 캠코에 내고 캠코가 등기를
    // 촉탁한다. 국유재산 매각은 매수자가 직접 이전등기를 한다. 이용기관 물건은 공고문이 정한다
    // (온비드 이용안내 「낙찰절차 안내」 압류재산 STEP04·국유재산 STEP03 · FAQ 「압류재산
    // 소유권이전절차 및 유의사항」 · team-reports/2026-10-19-onbid-journey-conformance/researcher-onbid-journey.md C6·C8·C10).
    items: [
      { name: "등기사항전부증명서", howto: "인터넷등기소", howtoUrl: "https://www.iros.go.kr/" },
      { name: "토지·건축물대장", howto: "정부24", howtoUrl: "https://www.gov.kr/" },
      { name: "매수자 주민등록등본", howto: "정부24 또는 주민센터", howtoUrl: "https://www.gov.kr/" },
      { name: "취득세·등록면허세 영수증", howto: "위택스 또는 시·군·구청 세무과", howtoUrl: "https://www.wetax.go.kr/" },
      { name: "국민주택채권 매입필영수증", howto: "", howtoUrl: "" },
      { name: "등기신청수수료 납부영수증", howto: "인터넷등기소 또는 등기소", howtoUrl: "https://www.iros.go.kr/" },
    ],
    note: "제출처는 재산유형마다 다릅니다. 압류재산은 매수인이 서류를 준비해 캠코 관할 부점에 우편이나 방문으로 내고, 등기촉탁은 캠코가 합니다. 매수인이 등기소에 직접 낼 수는 없습니다. 국유재산 매각은 매수자가 직접 이전등기를 합니다. 그 밖의 재산은 공고문이 정한 절차를 따르십시오. 근거는 온비드 이용안내 「낙찰절차 안내」입니다.",
  },
];

const POST_AWARD_SUPPLEMENT_EVIDENCE =
  "이 공고 원문에서 추출한 문장이 아니라, 낙찰 후 절차에서 통상 요구하는 서류에 대한 일반 안내입니다. 실제 필요 여부와 기한, 제출처는 공고 원문과 담당기관 기준으로 다시 확인하십시오.";

function buildPostAwardDocItem(base, group) {
  const note = [base.note, group.note].filter(Boolean).join(" ");
  return {
    name: base.name,
    conditions: [group.condition],
    conditionKeys: [],
    copy: "",
    validity: "",
    method: "",
    due: base.due || "",
    count: "",
    stage: POST_AWARD_DOC_STAGE,
    howto: base.howto,
    howtoUrl: base.howtoUrl,
    sourceSection: "",
    evidence: note ? `${note} ${POST_AWARD_SUPPLEMENT_EVIDENCE}` : POST_AWARD_SUPPLEMENT_EVIDENCE,
  };
}

// 서류의 단계 판정은 server.py 의 resolve_doc_stage() 다(조항 표제 사전 → 문장 결정적
// 문구 → 미분류, team-reports/2026-10-18-bid-doc-timeline/stage-classification-design.md).
// 그 판정이 틀렸을 때 두 방향의 비용이 «같지 않다».
//   - 「낙찰 후」로 잘못 보내면: 사용자가 4단계를 지금 할 일로 보지 않아 그 서류를 아예 놓치고,
//     입찰 마감 전 제출물이었다면 입찰 자체가 무효가 된다.
//   - 「입찰 전」으로 잘못 보내면: 서류 하나를 더 확인하는 비용에서 멈춘다.
// 그래서 값이 정확히 POST_AWARD_DOC_STAGE 일 때만 4단계로 보내고, 그 밖의 모든 값(빈 값·미지의
// 값·"미분류"·"별도 문의 필요"·판정 실패)은 2단계로 보낸다. 🔴 이 비대칭을 뒤집지 않는다 —
// 「낙찰 후가 아닌 것만 2단계」로 바꾸면 미지의 값이 4단계로 흘러 위 첫째 비용을 물게 된다
// (ux-design-review P0-2). "미분류"·"별도 문의 필요"는 2단계 «안에서» 확정 항목과 구분되는
// 별도 구획으로 보인다(isUnclassifiedDoc·isNeedsInquiryDoc, renderDocChecklist).
function isPostAwardDoc(item) {
  return item?.stage === POST_AWARD_DOC_STAGE;
}

// 조항 표제·문장 어디서도 단계를 확정하지 못한 서류. "우리가 확정했다"(아래 isConfirmedPreBidDoc)
// 와 구분해 사용자에게 「확인이 더 필요하다」를 숨기지 않는다(stage-classification-design.md §3).
const UNCLASSIFIED_DOC_STAGE = "미분류";
function isUnclassifiedDoc(item) {
  return item?.stage === UNCLASSIFIED_DOC_STAGE;
}

// 컨소시엄 협정서처럼 온비드 공통 규정에 일반 근거가 없는 서류. "미분류"와 달리 사전을
// 넓혀도 못 찾는다는 뜻이라 화면 문구와 처리(공고기관 문의 안내)가 다르다.
const NEEDS_INQUIRY_DOC_STAGE = "별도 문의 필요";
function isNeedsInquiryDoc(item) {
  return item?.stage === NEEDS_INQUIRY_DOC_STAGE;
}

// 입찰 전(2단계) 안에서 "우리가 확정한" 항목만 — 미분류·별도 문의는 각자 구획으로 뺀다.
function isConfirmedPreBidDoc(item) {
  return !isPostAwardDoc(item) && !isUnclassifiedDoc(item) && !isNeedsInquiryDoc(item);
}

// 낙찰 후 안내 묶음이 이 공고의 재산유형에 해당하는지 본다. assetTypes 선언이 없는 묶음은
// 모든 재산유형에 해당한다(소유권이전 단계가 그렇다).
//
// 🔴 재산유형을 «읽지 못했을 때»는 해당하는 것으로 본다. server.py 는 추출 실패 시
// 「재산유형 확인」을 넣는데, 그 값을 「해당하지 않음」으로 읽으면 압류재산 공고인데도
// 매각결정기일 묶음이 접혀서 기한을 놓칠 수 있다. 접는 쪽이 비싼 오류다.
const POST_AWARD_ASSET_TYPE_UNKNOWN = "재산유형 확인";

function isPostAwardGroupApplicable(group) {
  return !postAwardNotApplicableReason(group);
}

// 처분방식도 같은 비대칭 기본값을 쓴다 — 매각인지 임대인지 읽지 못했으면 해당하는 것으로 본다.
// 「임대·대부」로 «읽혔고» 「매각·공매」 낱말이 없을 때만 매각 묶음을 접는다.
function isLeaseOnlyDisposition() {
  const disposition = String(sampleNotice.dispositionLabel || "");
  return /임대|대부/.test(disposition) && !/매각|공매/.test(disposition);
}

// 해당하지 않으면 그 이유(화면 문구 종류)를, 해당하면 빈 문자열을 돌려준다.
function postAwardNotApplicableReason(group) {
  const assetTypes = Array.isArray(group?.assetTypes) ? group.assetTypes : [];
  if (assetTypes.length) {
    const assetType = String(sampleNotice.assetType || "").trim();
    const known = assetType && assetType !== POST_AWARD_ASSET_TYPE_UNKNOWN;
    if (known && !assetTypes.some((candidate) => assetType.includes(candidate))) return "assetType";
  }
  const dispositions = Array.isArray(group?.dispositions) ? group.dispositions : [];
  if (dispositions.includes("매각") && isLeaseOnlyDisposition()) return "disposition";
  return "";
}

function splitDocGroupsByStage(groups) {
  const preBid = [];
  const postAward = [];
  groups.forEach((group) => {
    const items = Array.isArray(group.items) ? group.items : [];
    const preItems = items.filter((item) => !isPostAwardDoc(item));
    const postItems = items.filter((item) => isPostAwardDoc(item));
    if (preItems.length) preBid.push({ ...group, items: preItems });
    if (postItems.length) postAward.push({ ...group, items: postItems });
  });
  return { preBid, postAward };
}

// 공동입찰·대리입찰 질문 답에 맞춰 조건별 그룹을 걸러내고, "예"일 때는 일반 안내 서류를
// 더해 "최종 준비서류 리스트"를 만든다. 체크 상태·진행률(getUniqueDocNames 등)과
// 화면 렌더링(renderDocChecklist)이 같은 이 목록을 기준으로 삼는다.
function getVisibleDocGroups() {
  const groups = Array.isArray(sampleNotice.docChecklist?.groups) ? sampleNotice.docChecklist.groups : [];
  const answers = getDocConditionAnswers();
  const visibleGroups = groups.filter((group) => {
    const label = group.condition || "";
    if (label.includes("공동입찰") && answers.joint !== "yes") return false;
    if (label.includes("대리입찰") && answers.proxy !== "yes") return false;
    return true;
  });
  const existingNames = new Set();
  visibleGroups.forEach((group) => (group.items || []).forEach((item) => existingNames.add(item.name)));
  const supplementGroups = [];
  if (answers.joint === "yes") {
    const items = DOC_CONDITION_SUPPLEMENT.joint
      .filter((base) => !existingNames.has(base.name))
      .map((base) => buildDocConditionSupplementItem(base, "공동입찰", sampleNotice.assetType));
    if (items.length) supplementGroups.push({ condition: "공동입찰 추가 안내", items });
  }
  if (answers.proxy === "yes") {
    const items = DOC_CONDITION_SUPPLEMENT.proxy
      .filter((base) => !existingNames.has(base.name))
      .map((base) => buildDocConditionSupplementItem(base, "대리입찰", sampleNotice.assetType));
    if (items.length) supplementGroups.push({ condition: "대리입찰 추가 안내", items });
  }
  // 낙찰 후 일반 안내는 조건(공동·대리) 답과 무관하게 항상 붙인다 — 재산유형·입찰 방식과
  // 관계없이 낙찰되면 거치는 절차다. 공고 원문에서 같은 이름을 이미 뽑았으면 중복으로 넣지 않는다.
  const postAwardGroups = POST_AWARD_DOC_GROUPS.map((group) => ({
    condition: group.condition,
    notApplicable: !isPostAwardGroupApplicable(group),
    notApplicableReason: postAwardNotApplicableReason(group),
    items: group.items
      .filter((base) => !existingNames.has(base.name))
      .map((base) => buildPostAwardDocItem(base, group)),
  })).filter((group) => group.items.length);
  return [...visibleGroups, ...supplementGroups, ...postAwardGroups];
}

// 2단계(입찰 전 준비) 블록이 그리는 서류 그룹.
function getPreBidDocGroups() {
  return splitDocGroupsByStage(getVisibleDocGroups()).preBid;
}

// 4단계(낙찰 후 준비) 블록이 그리는 서류 그룹.
function getPostAwardDocGroups() {
  return splitDocGroupsByStage(getVisibleDocGroups()).postAward;
}

// 2단계 안에서 "우리가 확정한" 항목만 남긴 그룹 — 미분류·별도 문의 필요 항목은
// 각자 구획(getUnclassifiedPreBidDocItems·getNeedsInquiryPreBidDocItems)으로 뺀다.
// 체크 상태·진행률(getUniqueDocNames 등)은 getPreBidDocGroups(미분류·별도 문의 포함)를
// 그대로 쓴다 — 사용자가 그 서류들도 끝내 준비해야 하므로 진행률 분모에서 빼지 않는다.
function getConfirmedPreBidDocGroups() {
  return getPreBidDocGroups()
    .map((group) => ({ ...group, items: (group.items || []).filter(isConfirmedPreBidDoc) }))
    .filter((group) => group.items.length);
}

// 조건별 그룹에 같은 서류명이 여러 번 걸릴 수 있어(§4-2), 평면 구획은 이름으로 중복을 지운다.
function flattenUniqueDocItems(groups, predicate) {
  const seen = new Set();
  const items = [];
  groups.forEach((group) => {
    (group.items || []).forEach((item) => {
      if (!predicate(item) || seen.has(item.name)) return;
      seen.add(item.name);
      items.push(item);
    });
  });
  return items;
}

function getUnclassifiedPreBidDocItems() {
  return flattenUniqueDocItems(getPreBidDocGroups(), isUnclassifiedDoc);
}

function getNeedsInquiryPreBidDocItems() {
  return flattenUniqueDocItems(getPreBidDocGroups(), isNeedsInquiryDoc);
}

// 조건별 그룹(공동입찰·대리입찰·공통 등)에 같은 서류명이 중복으로 나열되므로,
// 체크 상태와 진행률은 「행」이 아니라 「고유 서류명」 기준으로 센다.
function getUniqueDocNames() {
  const groups = getVisibleDocGroups();
  const names = new Set();
  groups.forEach((group) => {
    (group.items || []).forEach((item) => {
      if (item.name) names.add(item.name);
    });
  });
  return [...names];
}

function getDocState() {
  const names = getUniqueDocNames();
  const saved = readJsonStorage(docStorageKeyFor(sampleNotice), {});
  return names.reduce((acc, name) => {
    acc[name] = Boolean(saved[name]);
    return acc;
  }, {});
}

function saveDocState(state) {
  const key = docStorageKeyFor(sampleNotice);
  const saved = readJsonStorage(key, {});
  writeJsonStorage(key, { ...saved, ...state });
}

function countDocNames(groups, state) {
  const names = [];
  groups.forEach((group) => {
    (group.items || []).forEach((item) => {
      if (item.name && !names.includes(item.name)) names.push(item.name);
    });
  });
  const doneCount = names.filter((name) => state[name]).length;
  const totalCount = names.length;
  return { state, names, doneCount, totalCount, percent: totalCount ? Math.round((doneCount / totalCount) * 100) : 0 };
}

// 2단계(입찰 전 준비)의 서류 진행률이다. 4단계(낙찰 후) 서류는 분모에서 뺀다. 넣으면 두 가지가
// 깨진다. ⑴ 낙찰도 되지 않았는데 분모가 커져 진행률이 실제보다 낮게 보인다. ⑵ 「서류를 전부
// 체크하면 documents 를 켜 준다」는 보조 동작이 낙찰 후 서류까지 요구하게 되어, 2단계 완료가
// 3단계 개방 조건이므로 입찰 단계가 영원히 열리지 않는 교착이 된다(ux-design-review §4-⑺).
function getDocSummary() {
  return countDocNames(getPreBidDocGroups(), getDocState());
}

// 해당하지 않을 수 있다고 접어 둔 묶음(notApplicable)은 분모에서 뺀다(2026-10-19 동원님 결정 U1).
// 화면이 스스로 「해당하지 않을 수 있습니다」라고 접은 서류를 진행률이 다시 요구하면 두 정보가 어긋난다.
function getPostAwardDocSummary() {
  return countDocNames(getPostAwardDocGroups().filter((group) => !group.notApplicable), getDocState());
}

function currentNoticeCard() {
  const summary = getTaskSummary();
  return {
    id: noticeKey(sampleNotice),
    notice: sampleNotice.noticeId || sampleNotice.title || "온비드 공고",
    title: sampleNotice.title || "온비드 공고",
    type: `${sampleNotice.assetType || "재산유형 확인"} / ${sampleNotice.dispositionLabel || "처분방식 확인"}`,
    next: summary.nextTask?.action || "공고 원문 확인",
    status: formatProgress(summary),
    sourceUrl: sampleNotice.sourceUrl,
    // 관심 공고 카드에 마감 상태 배지를 보이려면 저장 시점의 countdown 값이 필요하다.
    // 분석을 다시 하지 않는 한 갱신되지 않으므로, 저장 시점 기준이라는 한계가 있다.
    countdown: sampleNotice.countdown || null,
    viewedAt: new Date().toISOString(),
  };
}

function readJsonStorage(key, fallback) {
  try {
    const saved = JSON.parse(window.localStorage.getItem(key) || "null");
    return saved ?? fallback;
  } catch {
    return fallback;
  }
}

function writeJsonStorage(key, value) {
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // 저장하지 못해도 화면은 그대로 동작한다.
  }
}

function getRecentNotices() {
  return readJsonStorage(recentNoticeStorageKey, []);
}

function saveRecentNotice() {
  if (!isAnalysisReady()) return;
  const card = currentNoticeCard();
  const recent = getRecentNotices().filter((item) => item.id !== card.id);
  writeJsonStorage(recentNoticeStorageKey, [card, ...recent].slice(0, 8));
}

function getFavoriteNoticeIds() {
  const saved = readJsonStorage(favoriteNoticeStorageKey, []);
  return new Set(Array.isArray(saved) ? saved : []);
}

function setFavoriteNoticeIds(ids) {
  writeJsonStorage(favoriteNoticeStorageKey, Array.from(ids));
}

function isFavoriteNotice(id) {
  return getFavoriteNoticeIds().has(id);
}

function toggleFavoriteNotice(id) {
  const ids = getFavoriteNoticeIds();
  if (ids.has(id)) {
    ids.delete(id);
  } else {
    ids.add(id);
  }
  setFavoriteNoticeIds(ids);
  renderWatchlist();
}

// 2단계(서류준비)의 "내 보관함으로 보내기"가 쓰는 저장소다. 핵심 정보 + 공동입찰/대리입찰
// 답 + 확정된 서류 리스트를 한데 묶어 보관하고, 화면 노출은 기존 "관심 공고"(즐겨찾기)
// 구조를 그대로 재사용한다(별개의 저장 체계를 새로 만들지 않는다).
const docLockerStorageKey = "onbid-public-asset-doc-agent-locker-v1";

function getLockerRecords() {
  const saved = readJsonStorage(docLockerStorageKey, []);
  return Array.isArray(saved) ? saved : [];
}

function buildLockerRecord() {
  const answers = getDocConditionAnswers();
  const docList = [];
  getVisibleDocGroups().forEach((group) =>
    (group.items || []).forEach((item) => {
      if (item.name && !docList.includes(item.name)) docList.push(item.name);
    }),
  );
  return {
    id: noticeKey(sampleNotice),
    notice: sampleNotice.noticeId || sampleNotice.title || "온비드 공고",
    title: sampleNotice.title || "온비드 공고",
    sourceUrl: sampleNotice.sourceUrl || "",
    bidPeriod: sampleNotice.bidPeriod || "",
    minimumBidPrice: sampleNotice.minimumBidPrice || "",
    jointBid: answers.joint,
    proxyBid: answers.proxy,
    docList,
    savedAt: new Date().toISOString(),
  };
}

function saveNoticeToLocker() {
  if (!isAnalysisReady()) return null;
  const record = buildLockerRecord();
  const records = getLockerRecords().filter((item) => item.id !== record.id);
  writeJsonStorage(docLockerStorageKey, [record, ...records].slice(0, 20));
  // 관심 공고 화면에서도 바로 보이도록 "최근 살펴본 공고"에 먼저 남기고 즐겨찾기한다.
  saveRecentNotice();
  const favoriteIds = getFavoriteNoticeIds();
  favoriteIds.add(record.id);
  setFavoriteNoticeIds(favoriteIds);
  renderWatchlist();
  return record;
}

function isAnalyzedInputCurrent() {
  return getNoticeInput() === analyzedInputValue;
}

function isAnalysisReady() {
  return Boolean(getNoticeInput() && isAnalyzedInputCurrent() && !analysisError && sampleNotice.mode !== "기본 샘플 공고");
}

function getInputWarning() {
  const input = getNoticeInput();
  if (!input) {
    return {
      title: "온비드 공고/물건 URL을 입력해야 합니다",
      body: "온비드 공고 또는 물건 URL을 붙여 넣으면 공개 페이지를 읽어 준비 보드로 변환합니다.",
    };
  }

  if (!/^https?:\/\/([^/]+\.)?onbid\.co\.kr\//i.test(input)) {
    return {
      title: "온비드 URL만 분석할 수 있습니다",
      body: "현재 MVP는 onbid.co.kr의 공고 상세, 물건 상세, short URL을 대상으로 합니다.",
    };
  }

  return null;
}

// 공공데이터 입찰정보에 제한 조건이 하나라도 있으면 2-1 맨 앞에 「입찰 자격 확인」 할 일을 둔다(2026-10-19 동원님 결정 U10 ⑷).
// 자격 조건은 체크 대상이 아니라 그냥 지나가기 쉬웠다. 제한이 없으면 만들지 않아 진행률 분모가 그대로다.
// 서버(build_tasks)는 고치지 않는다 — 다른 세션이 server.py 를 맡고 있어 화면 쪽에서만 만든다.
function getBidQualificationTask() {
  const limits = Array.isArray(sampleNotice.bidLimits) ? sampleNotice.bidLimits : [];
  const restricted = limits.filter((limit) => limit.restricted);
  if (!restricted.length) return null;
  // 값 칸은 항목 이름이 아니라 실제 제한 내용이다. 이름만 두면 바로 위 「입찰 자격 조건」 블록을 되풀이할 뿐 카드에 정보가 없다(r1 P2-1).
  const first = restricted[0];
  const firstValue = String(first.value || "").length > 40 ? `${String(first.value).slice(0, 40)}…` : first.value;
  return {
    id: "bid-qualification",
    title: "입찰 자격 확인",
    action: `${first.label}: ${firstValue}${restricted.length > 1 ? ` 외 ${restricted.length - 1}건` : ""}`,
    // 출처가 공고 원문이 아니라 공공데이터다. 다른 카드와 같은 라벨을 쓰면 출처를 잘못 말한다(r1 P2-1).
    valueLabel: "공공데이터에서 확인된 값",
    // AI 매칭과 무관하게, 끝내기 전까지 늘 「확인 필요」다. 놓치면 입찰이 무효가 될 수 있는 조건이다.
    needsCheck: true,
    due: "분석 직후",
    detail: `공공데이터에 입찰 자격 제한이 있습니다(${restricted.map((limit) => `${limit.label}: ${limit.value}`).join(" / ")}). 조건에 맞지 않으면 입찰이 무효가 될 수 있으니 공고문 원문의 참가자격 조항을 먼저 확인합니다.`,
    question: "이 물건의 입찰 참가자격 제한에 내가 해당하는지 담당기관이나 공고 원문에서 확인합니다.",
    source: "공공데이터 온비드 물건 입찰정보(getCltrBidInf2)",
    cta: "온비드 원문",
    url: sampleNotice.sourceUrl,
    defaultDone: false,
  };
}

function getApplicableTasks() {
  const userType = getSelectedUserType();
  const boardTasks = Array.isArray(sampleNotice.boardTasks) ? sampleNotice.boardTasks : [];
  const qualificationTask = getBidQualificationTask();
  // 정렬 뒤 맨 앞에 붙인다. 정렬에 넣으면 AI 매칭 점수가 높은 할 일이 그 앞으로 올라간다.
  const sortedTasks = boardTasks
    .filter((task) => !task.userTypes || task.userTypes.includes(userType))
    .map((task, index) => ({ task, index, stage: getTaskStageNum(task.id) ?? PREP_STAGES.length + 1, aiMatch: getTaskAiMatch(task) }))
    .sort((a, b) => {
      // 단계가 1차 정렬 키다 — AI 매칭 점수 정렬은 같은 단계 안으로만 한정한다
      // (ux-audit §⑴ "구현 시 반드시 지킬 것"). 단계가 없는(알 수 없는) id는 맨 뒤로 보낸다.
      const stageDiff = a.stage - b.stage;
      if (stageDiff) return stageDiff;
      const scoreDiff = (b.aiMatch?.score || 0) - (a.aiMatch?.score || 0);
      return scoreDiff || a.index - b.index;
    })
    .map(({ task }) => task);
  return qualificationTask ? [qualificationTask, ...sortedTasks] : sortedTasks;
}

function getTaskState() {
  const tasks = getApplicableTasks();
  try {
    const saved = JSON.parse(window.localStorage.getItem(taskStorageKeyFor(sampleNotice)) || "{}");
    return tasks.reduce((acc, task) => {
      acc[task.id] = typeof saved[task.id] === "boolean" ? saved[task.id] : task.defaultDone;
      return acc;
    }, {});
  } catch {
    return tasks.reduce((acc, task) => {
      acc[task.id] = task.defaultDone;
      return acc;
    }, {});
  }
}

function saveTaskState(state) {
  try {
    const key = taskStorageKeyFor(sampleNotice);
    const saved = JSON.parse(window.localStorage.getItem(key) || "{}");
    window.localStorage.setItem(key, JSON.stringify({ ...saved, ...state }));
  } catch {
    // Local storage is a convenience for the prototype; the checklist still works in-session.
  }
}

function resetTaskState() {
  // 버튼은 각 단계 페이지에 있지만 이 공고의 모든 단계 체크와 서류 체크를 지운다. 범위를 확인창에 적는다(U11).
  if (!window.confirm("2-1~2-4 할 일 체크와 서류 체크를 모두 지웁니다. 되돌릴 수 없습니다. 계속할까요?")) {
    return;
  }
  window.localStorage.removeItem(taskStorageKeyFor(sampleNotice));
  window.localStorage.removeItem(docStorageKeyFor(sampleNotice));
  saveRecentNotice();
  renderReport();
  renderWatchlist();
}

function getTaskSummary() {
  const state = getTaskState();
  const tasks = getApplicableTasks();
  const doneCount = tasks.filter((task) => state[task.id]).length;
  const totalCount = tasks.length;
  // tasks는 getApplicableTasks()가 이미 단계 순으로 정렬해 두므로, 맨 앞의 미완료 항목이
  // 바로 "가장 앞선 미완료 단계의 첫 미완료 task"다(ux-audit §⑴ nextTask 재정의).
  // currentNoticeCard().next(관심 공고 탭)도 이 값을 그대로 쓴다.
  const nextTask = tasks.find((task) => !state[task.id]) || tasks[tasks.length - 1] || null;
  return { state, tasks, doneCount, totalCount, nextTask, percent: totalCount ? Math.round((doneCount / totalCount) * 100) : 0 };
}

// 단계 완료·잠김은 체크 상태에서 매 렌더마다 파생 계산한다 — 별도의 "unlock" 플래그를
// localStorage에 저장하지 않는다(ux-audit §⑴). 그 단계에 속한 task id가 이 공고에 하나도
// 없으면(예: 테스트 픽스처가 documents 하나만 주는 경우) 그 단계는 공집합 완료로 보고
// 다음 단계를 막지 않는다 — `[].every()`가 true인 표준 의미를 그대로 쓴다.
// 네 번째 상태 notYet(「아직 할 일이 아님」)은 done 보다 «먼저» 판정한다. 그러지 않으면
// taskIds 가 빈 4단계가 위의 `[].every()` 로 done:true 가 되어, 사용자가 낙찰도 되지 않았고
// 서류도 한 장 내지 않았는데 「4단계 · 낙찰 후 준비 ✅ 완료」를 읽는다(P0-1). 그래서 판정 순서를
// locked → notYet → done → active 로 고정하고, notYet 인 단계의 done 은 아예 false 로 눌러
// 파생값 자체가 「완료」를 주장하지 못하게 한다.
//
// notYet 은 sequential: false 인 단계에만 붙는다. 4단계는 항목이 있어도, 또 사용자가 미리
// 체크해 두어도 낙찰 전에는 notYet 이다 — 이 서비스는 낙찰 여부를 알 수 없고, 알 수 없는 것을
// 「도달했다」로 추정하지 않는다. sequential 인 단계가 공집합일 때의 기존 동작(공집합 완료로
// 보고 다음 단계를 막지 않는다)은 그대로 둔다.
function getPrepStageStatus() {
  const state = getTaskState();
  const tasks = getApplicableTasks();
  let unlocked = true;
  return PREP_STAGES.map((stageDef) => {
    const taskIds = stageDef.taskIds.filter((id) => tasks.some((task) => task.id === id));
    const done = taskIds.every((id) => state[id]);
    const notYet = !stageDef.sequential;
    const locked = stageDef.sequential ? !unlocked : false;
    if (stageDef.sequential) unlocked = unlocked && done;
    return { num: stageDef.num, title: stageDef.title, taskIds, notYet, done: notYet ? false : done, locked };
  });
}

function formatProgress(summary) {
  return summary.totalCount ? `${summary.doneCount}/${summary.totalCount} 완료` : "체크리스트 대기";
}

function getFitMessage() {
  const inputWarning = getInputWarning();
  if (inputWarning) {
    // 목적 불일치와 같은 「불일치」 머리표를 쓰지 않는다. 입력이 비었거나 형식이 틀린 것이다(I5).
    // 1-2 에 처음 들어와 칸이 빈 것은 잘못이 아니다. 「분석하기」를 빈 칸으로 누른 뒤에만(aria-invalid) 경고 톤이다(r1 P2-3).
    const notTriedYet = !getNoticeInput() && byId("notice-url")?.getAttribute("aria-invalid") !== "true";
    return {
      type: "mismatch",
      neutral: notTriedYet,
      badgeLabel: notTriedYet ? "안내" : "입력 필요",
      title: inputWarning.title,
      body: inputWarning.body,
      action: getNoticeInput() ? "온비드 URL을 붙여 넣은 뒤 「분석하기」를 누르십시오." : "URL을 붙여 넣거나 「샘플 불러오기」를 누르십시오.",
      inputBlocked: true,
    };
  }

  if (analysisError) {
    return {
      type: "mismatch",
      badgeLabel: "오류",
      title: "공고 분석에 실패했습니다",
      body: analysisError,
      // 서버·연결 오류는 URL 문제가 아니다. URL 을 확인하라고 하면 고칠 방법을 잘못 알려 준다(I5).
      action:
        analysisError === ANALYSIS_SERVER_ERROR_MESSAGE
          ? "「분석하기」를 다시 누르면 같은 URL을 다시 읽습니다."
          : "URL이 온비드 공고/물건 상세 페이지인지 확인한 뒤 「분석하기」를 다시 누르십시오.",
      inputBlocked: true,
    };
  }

  if (!isAnalyzedInputCurrent()) {
    return {
      type: "check",
      title: "아직 이 URL을 분석하지 않았습니다",
      // 「바뀌었습니다」는 한 번 분석한 뒤 URL 이 달라졌을 때만 쓴다. 처음 붙여 넣은 사람은 바꾼 것이 없다(U4).
      body: analyzedInputValue
        ? "입력 URL이 바뀌었습니다. 공고 분석을 실행해야 이 URL 기준의 준비 보드가 생성됩니다."
        : "공고 분석을 실행해야 이 URL 기준의 준비 보드가 생성됩니다.",
      action: "「분석하기」를 누르면 유효성 결과와 공고·물건 연결 정보를 먼저 보여 줍니다.",
      inputBlocked: true,
    };
  }

  const focus = getSelectedFocus();
  const isSaleNotice = /매각|공매|압류/.test(`${sampleNotice.assetType} ${sampleNotice.dispositionLabel}`);
  const isLeaseNotice = /임대|대부/.test(`${sampleNotice.assetType} ${sampleNotice.dispositionLabel} ${sampleNotice.title}`);

  if (focus === "sale" && !isSaleNotice) {
    return {
      type: "mismatch",
      title: "목적과 입력 공고 유형이 다릅니다",
      body:
        "현재 분석된 공고는 매각/공매 유형으로 확인되지 않았습니다. 매각 검토를 하려면 온비드 매각/공매 공고 URL인지 확인해야 합니다.",
      action: "이 공고로 계속 볼 수는 있지만, 먼저 내 검토 목적을 공고 유형에 맞게 바꾸는 것이 안전합니다.",
    };
  }

  if (focus === "lease" && isSaleNotice && !isLeaseNotice) {
    return {
      type: "mismatch",
      title: "목적과 입력 공고 유형이 다릅니다",
      body: "현재 분석된 공고는 임대/대부가 아니라 매각/공매 계열로 보입니다.",
      action: "이 공고로 계속 볼 수는 있지만, 임대/대부 검토라면 해당 유형의 온비드 공고 URL을 입력하세요.",
    };
  }

  if (focus === "startup") {
    return {
      type: "check",
      title: "창업 공간 후보로는 볼 수 있지만 용도 확인이 필요합니다",
      body:
        "창업 공간으로 활용 가능한지는 용도, 사용 제한, 시설 상태, 담당기관 확인이 필요합니다.",
      action: "준비 보드에서 창업 목적 사용 가능 여부를 확인 항목으로 안내합니다.",
    };
  }

  return {
    type: "match",
    title: "목적과 입력 공고 유형이 맞습니다",
    body: "분석된 온비드 공고를 기준으로 일정, 제출서류, 가격/보증금을 준비 보드로 정리합니다.",
    action: "결과를 확인한 뒤 다음을 누르면 체크리스트와 준비처 링크로 넘어갑니다.",
  };
}

// 준비 보드 1단계(공고 확인) 전용 판정 — 입찰기간 만료 또는 목적/형태 불일치가 있으면
// "처음으로 돌아가시겠어요?" 배너를 보여준다. 새 판정 로직을 만들지 않고 이미 있는
// bid_countdown()의 결과(countdown.state === "closed")와 getFitMessage()의 "mismatch"
// 분기를 그대로 재사용한다 — 날짜·선택값 비교일 뿐 낙찰 가능성·유불리는 판단하지 않는다.
// renderReport()가 blockingMessage(입력 없음·분석 실패·URL 변경 후 미분석)를 먼저 걸러낸
// 뒤에만 호출되므로, 여기서는 그 세 가지를 다시 보지 않는다.
function getStage1RestartWarning(fit) {
  const expired = sampleNotice.countdown?.state === "closed";
  const mismatched = fit.type === "mismatch";
  if (!expired && !mismatched) return null;
  const reasons = [];
  if (expired) {
    reasons.push(`입찰기간이 이미 지났습니다(${sampleNotice.countdown.deadline} 마감).`);
  }
  if (mismatched) {
    reasons.push(fit.body);
  }
  return { expired, mismatched, reasons };
}

// 위 판정이 있을 때만 1단계 카드 그룹 위에 보이는 배너. 둘 다 아니면 호출부가 빈 문자열을
// 받도록 getStage1RestartWarning()에서 이미 null을 돌려준다(불필요한 경고 노출 금지).
function renderStage1RestartWarning(warning) {
  if (!warning) return "";
  return `<div class="fit-panel mismatch stage1-restart-warning">
    <div class="fit-top">
      ${badge("확인 필요", "warn")}
      <strong>이 공고로 계속 진행하기 전에 확인이 필요합니다</strong>
    </div>
    ${warning.reasons.map((reason) => `<p>${escapeHtml(reason)}</p>`).join("")}
    <p class="small-text">처음으로 돌아가면 지금 분석 중인 공고 데이터를 버리고 유형·목적 선택부터 다시 시작합니다.</p>
    <div class="actions">
      <button type="button" class="primary small-button" data-restart-wizard>처음으로 돌아가시겠어요?</button>
    </div>
  </div>`;
}

// "공고 유형 확인"·"입찰기간 확인"·"최저입찰가격 확인" 할 일 카드에, AI가 이미 비교·추출해 둔
// 결과를 자세히 블록 문장으로 보여준다. getFitMessage()의 판정 로직 자체는 바꾸지 않고
// 그 결과를 "보여주는" 자리만 넓힌다 — 단정하지 않고 헤지한다.
function getAiPrecheckForTask(task, fit) {
  if (task.id === "notice-type") {
    if (fit.type === "match") {
      return {
        precheck: "선택한 검토 목적과 공고 유형을 비교했을 때 맞는 것으로 보입니다. 원문·담당기관 확인을 우선합니다.",
      };
    }
    if (fit.type === "check") {
      return {
        precheck: `${fit.body} 원문·담당기관 확인을 우선합니다.`,
      };
    }
    return {
      precheck: `선택한 검토 목적과 공고 유형이 다른 것으로 보입니다. ${fit.body} 원문·담당기관 확인을 우선합니다.`,
    };
  }

  if (task.id === "bid-period" || task.id === "price") {
    const extracted = task.action !== NOTICE_VALUE_FALLBACK;
    if (extracted) {
      // 가격이 "비공개"인 것도 추출 실패가 아니라 이용기관이 그렇게 정한 정상 값이다
      // (known-pitfalls.md 「가격 표시」 — minimum_bid_value()가 명시적으로 돌리는 값).
      const precheck =
        task.id === "price" && task.action === "비공개"
          ? "공고 원문에서 가격이 비공개로 설정된 것으로 보입니다. 원문·담당기관 확인을 우선합니다."
          : // 값은 바로 위 「공고 원문에서 확인된 값」 칸에 있다. 같은 값을 문장으로 되풀이하지 않는다(U10 ⑶).
            "공고 원문에서 확인된 것으로 보입니다. 원문·담당기관 확인을 우선합니다.";
      return { precheck };
    }
    return {
      precheck: "원문에서 값을 찾지 못했습니다. 직접 확인해 주세요.",
    };
  }

  return null;
}

// 2p(URL 입력)의 안내/오류 자리 — 입력이 비었거나 형식이 틀렸거나 분석에 실패했을 때만 쓴다.
function renderUrlStepFeedback(fit) {
  const feedback = byId("url-step-feedback");
  if (!fit.inputBlocked) {
    feedback.className = "url-step-feedback";
    feedback.innerHTML = "";
    return;
  }
  const typeBadge = fit.neutral ? "neutral" : fit.type === "match" ? "safe" : "warn";
  feedback.className = `url-step-feedback fit-panel ${fit.neutral ? "is-neutral" : fit.type}`;
  feedback.innerHTML = `
    <div class="fit-top">
      ${badge(fit.badgeLabel || (fit.type === "mismatch" ? "불일치" : "확인 필요"), typeBadge)}
      <strong>${fit.title}</strong>
    </div>
    <p>${escapeHtml(fit.body)}</p>
    <p class="small-text">${fit.action}</p>
  `;
}

// 3p(분석 결과) 화면. 사용자 피드백("분석결과 박스 안의 객체 배치나 구조가 너무 정신없다")에 따라
// 서로 다른 배경·테두리를 가진 상자 여러 개를 쌓는 대신, "핵심 정보"·"확인 사항"·"온비드 연결"
// 세 묶음으로만 나눈다. 묶음 안의 항목은 데이터·판정 로직을 그대로 쓰고 배치만 바꾼다.
function renderAnalysisResult() {
  const panel = byId("analysis-result");
  const fit = getFitMessage();
  renderUrlStepFeedback(fit);

  if (fit.inputBlocked) {
    panel.className = "result-page";
    panel.innerHTML = "";
    return;
  }

  const typeBadge = fit.type === "match" ? "safe" : "warn";
  const publicData = sampleNotice.analysisMeta?.publicData;
  const coach = sampleNotice.aiCoach;
  const links = sampleNotice.relatedUrls || {};

  panel.className = "result-page";
  // 모든 절을 같은 블록 템플릿(.block · 제목 + 내용)으로 그린다. 판정·확인 사항은 정보 행,
  // 핵심 정보는 값 칸이다(2026-10-19 동원님 지시: 이 페이지의 UI가 통일되지 않았다).
  panel.innerHTML = `
    <section class="block result-status ${fit.type}">
      <h3 class="block-title">판정</h3>
      ${infoRow({
        tag: fit.type === "mismatch" ? "불일치" : fit.type === "check" ? "확인 필요" : "일치",
        tone: typeBadge,
        title: fit.title,
        text: escapeHtml(fit.body),
      })}
    </section>

    <section class="block">
      <h3 class="block-title">핵심 정보 <span class="block-meta">${sampleNotice.pageType || "온비드 페이지"}${publicData ? ` · ${publicDataLabel(publicData)}` : ""}</span></h3>
      <div class="fact-grid preview-grid">
        ${factCell("공고/물건명", fieldValue(sampleNotice.title))}
        ${factCell("유형", fieldValue(`${sampleNotice.assetType} · ${sampleNotice.dispositionLabel}`))}
        ${factCell("입찰기간", fieldValue(sampleNotice.bidPeriod || sampleNotice.bidDeadline || NOTICE_VALUE_FALLBACK))}
        ${factCell("최저입찰가격", fieldValue(sampleNotice.minimumBidPrice || NOTICE_VALUE_FALLBACK))}
      </div>
      <p class="deadline-line">${countdownBadge()}</p>
    </section>

    <section class="block">
      <h3 class="block-title">확인 사항</h3>
      <div class="info-list result-check-list">
        ${renderDocSourceNotice()}
        ${renderAiReadySummary(coach)}
      </div>
      <p class="block-note">온비드 원문 기준이며, 최대 30분 지연될 수 있습니다. 마감이 가까우면 원문에서 다시 확인하십시오.</p>
    </section>

    <section class="block">
      <h3 class="block-title">온비드 연결</h3>
      <div class="link-chips linked-pages">
        <a class="link-chip" href="${sampleNotice.sourceUrl}" target="_blank" rel="noreferrer">현재 분석 페이지 ↗</a>
        ${links.noticeDetail ? `<a class="link-chip" href="${links.noticeDetail}" target="_blank" rel="noreferrer">공고보기 ↗</a>` : ""}
        ${
          links.itemDetail
            ? links.itemDetailUncertain
              ? `<a href="${links.itemDetail}" target="_blank" rel="noreferrer" class="link-chip link-uncertain">물건상세 (열리지 않을 수 있음) ↗</a>`
              : `<a class="link-chip" href="${links.itemDetail}" target="_blank" rel="noreferrer">물건상세 ↗</a>`
            : ""
        }
      </div>
      <p class="block-note result-action">${fit.action}</p>
    </section>
  `;
}

// 준비 보드 아래에 붙어 따라다니는 코치 질문 줄이다(2026-10-19 동원님 지시). 접기 버튼으로 머리 한 줄만 남길 수 있고,
// 머리 줄에 「이 물건 정보를 알고 답한다」는 사실과 실제로 보내는 항목을 적는다(askNoticeQuestion 의 notice·docs·board).
// 아래 예시 질문은 지금 보는 단계에서 초보자가 자주 묻는 것이다(커뮤니티 조사 1절 · 서버 COMMON_QUESTION_GUIDES).
const COACH_SUGGESTIONS = {
  1: ["개인도 입찰할 수 있나요?", "최저입찰가격과 감정평가금액은 뭐가 달라요?", "이제 뭘 해야 하나요?"],
  2: ["서류는 언제까지 내야 하나요?", "입찰에 쓰는 인증서는 뭔가요?", "이제 뭘 해야 하나요?"],
  3: ["입찰금액은 어떻게 정하면 좋을까요?", "제출한 입찰서를 취소할 수 있나요?", "입찰보증금은 얼마를 언제 내나요?", "낙찰됐는지 어디서 확인하나요?"],
  4: ["낙찰되면 다음 절차는 뭐예요?", "낙찰을 포기하면 보증금은 어떻게 되나요?", "잔금은 언제까지 내야 하나요?"],
};

function shortNoticeTitle(title, max = 22) {
  const text = String(title || "").trim();
  return text.length > max ? `${text.slice(0, max)}…` : text;
}

// 코치가 무엇을 보고 답하는지 적은 문장이다. 고정 영역에서 한 줄을 늘 차지해 머리 줄 툴팁과 입력칸 설명으로 옮겼다(R2 · V9).
const COACH_CONTEXT_DETAIL = "공고 유형 · 입찰기간 · 최저입찰가격 · 입찰보증금 · 담당기관 · 제출서류와 지금 준비 보드의 진행 상황을 함께 보고 답합니다.";

function renderBoardCoach(coach, stageNum) {
  // 모델에 붙지 않았으면 「AI 가 했다」고 말하지 않는다. 색만 바꾸면 색을 못 보는 사람에게는
  // 같은 화면이고, 색을 보는 사람에게도 문구가 사실과 어긋난 채 남는다.
  const llmConnected = coach?.llmStatus === "connected";
  const title = shortNoticeTitle(sampleNotice.title);
  const suggestions = COACH_SUGGESTIONS[stageNum] || [];
  return `<section class="coach-ask-card coach-dock${coachCollapsed ? " is-collapsed" : ""}${coachAnswerHtml ? " has-answer" : ""}">
    <div class="coach-dock-head">
      <span class="coach-dock-label">${badge(llmConnected ? "AI 누락 점검" : "규칙 기반 누락 점검", llmConnected ? "neutral" : "warn")}<strong>AI 코치에게 물어보기</strong></span>
      <span class="coach-context" title="${sampleNotice.title ? `${sampleNotice.title} · ` : ""}${COACH_CONTEXT_DETAIL}"><span class="coach-context-long">${title ? `「${title}」 정보를 알고 답합니다` : "이 공고 정보를 알고 답합니다"}</span><span class="coach-context-short">이 물건 정보를 알고 답합니다</span></span>
      <button type="button" class="coach-toggle" data-coach-toggle aria-expanded="${!coachCollapsed}" aria-controls="coach-dock-body">${coachCollapsed ? "펴기 ▴" : "접기 ▾"}</button>
    </div>
    <div id="coach-dock-body" class="coach-dock-body"${coachCollapsed ? " hidden" : ""}>
      <p id="coach-context-help" class="sr-only">${COACH_CONTEXT_DETAIL}</p>
      <div class="coach-ask-row">
        <input type="text" id="coach-question-input" placeholder="이 물건에 대해 물어보세요. 예: ${suggestions[0] || "잔금은 언제까지 내야 하나요?"}" maxlength="200" aria-label="AI 코치에게 물어볼 질문" aria-describedby="coach-context-help">
        <button type="button" class="primary small-button" data-ask-question>질문하기</button>
      </div>
      ${
        suggestions.length
          ? `<div class="coach-suggest" role="group" aria-label="자주 묻는 질문">
        <span class="coach-suggest-label">자주 묻는 질문</span>
        ${suggestions.map((q) => `<button type="button" class="link-chip" data-coach-suggest="${q}">${q}</button>`).join("")}
      </div>`
          : ""
      }
      <div class="coach-answer-tools"${coachAnswerHtml ? "" : " hidden"}><button type="button" class="text-action coach-clear-answer" data-coach-clear>답 지우기</button></div>
      <div id="coach-question-result" class="coach-ask-result" aria-live="polite"></div>
    </div>
  </section>`;
}

// 보드를 다시 그려도 입력 중인 질문과 받은 답은 남긴다. 체크박스 하나만 눌러도 renderReport 가 돈다.
// 입력 중인 질문은 아직 상태 변수가 없어 DOM 에서 옮기고, 답·잠금은 상태 변수에서 되살린다.
function renderBoardCoachKeepingState(coach, stageNum) {
  const host = byId("board-coach");
  if (!host) return;
  const prevInput = byId("coach-question-input")?.value || "";
  host.innerHTML = coach ? renderBoardCoach(coach, stageNum) : "";
  const input = byId("coach-question-input");
  if (input) input.value = prevInput;
  const result = byId("coach-question-result");
  if (result) result.innerHTML = coachAnswerHtml;
  applyCoachAskControls();
}

// 서버 오류 문구처럼 밖에서 온 글을 innerHTML 에 넣을 때 태그가 아니라 글자로 보이게 한다.
function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

// 답 HTML 을 보관하고, 쓰는 그 시점에 결과 요소를 다시 찾아 쓴다. 요소 참조를 들고 기다리면
// 그사이 renderReport 가 새 요소로 바꿔 답이 화면에 나오지 않는다(I1).
function setCoachAnswer(html) {
  coachAnswerHtml = html;
  const result = byId("coach-question-result");
  if (result) result.innerHTML = html;
  // 답이 있으면 좁은 화면에서 「자주 묻는 질문」 줄을 숨기고(CSS · has-answer), 답만 지우는 버튼을 보인다(R1).
  document.querySelector(".coach-dock")?.classList.toggle("has-answer", Boolean(html));
  const tools = document.querySelector(".coach-answer-tools");
  if (tools) tools.hidden = !html;
}

function isCoachAskLocked() {
  return askInFlight || Date.now() < askCooldownUntil;
}

// 질문하기 · 자주 묻는 질문 칩의 잠금과 버튼 글자를 상태 변수대로 맞춘다. 코치 영역을 새로 그린 뒤에도 부른다.
function applyCoachAskControls() {
  const coolingDown = Date.now() < askCooldownUntil;
  const locked = isCoachAskLocked();
  const askButton = document.querySelector("#board-coach [data-ask-question]");
  if (askButton) {
    askButton.disabled = locked;
    askButton.textContent = coolingDown ? "1분 뒤 다시" : "질문하기";
  }
  document.querySelectorAll("#board-coach [data-coach-suggest]").forEach((chip) => {
    chip.disabled = locked;
  });
  const result = byId("coach-question-result");
  if (result) {
    if (askInFlight) result.setAttribute("aria-busy", "true");
    else result.removeAttribute("aria-busy");
  }
}

// 새 공고로 넘어가면 이전 공고에 대한 답을 지우고, 기다리던 답은 번호를 올려 버린다.
// 번호를 올리지 않으면 늦게 온 옛 공고의 답이 새 공고의 코치 영역에 써진다.
function clearCoachAnswer() {
  askRequestId += 1;
  askInFlight = false;
  setCoachAnswer("");
  applyCoachAskControls();
}

function startAskCooldown() {
  askCooldownUntil = Date.now() + 60000;
  clearTimeout(askCooldownTimer);
  askCooldownTimer = setTimeout(() => {
    askCooldownUntil = 0;
    applyCoachAskControls();
  }, 60000);
  applyCoachAskControls();
}

// 고정 영역 높이를 --dock-h 에 넣어 html 의 scroll-padding-bottom 으로 쓴다. Tab 으로 옮긴 포커스가 고정 영역 뒤에
// 가려졌다(I6 · 1280 16건 · 390 18건). 준비 보드가 아닐 때는 고정 영역이 없으므로 0 이다.
// 여백 16px 은 여기서 더해 둔다. 그래야 다른 화면에서 값이 정확히 0 이 된다.
function updateDockHeightVar() {
  const dock = document.querySelector(".board-dock");
  const onBoard = currentView === "report" && dock && dock.getClientRects().length > 0;
  document.documentElement.style.setProperty("--dock-h", onBoard ? `${Math.ceil(dock.getBoundingClientRect().height) + 16}px` : "0px");
}

function setCoachCollapsed(collapsed) {
  coachCollapsed = collapsed;
  writeJsonStorage(coachCollapsedStorageKey, collapsed);
  const card = document.querySelector(".coach-dock");
  const body = byId("coach-dock-body");
  const toggle = document.querySelector("[data-coach-toggle]");
  if (!card || !body || !toggle) return;
  card.classList.toggle("is-collapsed", collapsed);
  body.hidden = collapsed;
  toggle.setAttribute("aria-expanded", String(!collapsed));
  toggle.textContent = collapsed ? "펴기 ▴" : "접기 ▾";
}

// 할 일 카드의 「자세히」를 모두 펼칠지 정하는 두 칸 버튼이다. 지금 상태가 눌린 모양(aria-pressed)으로
// 보이고, 그 아래 한 줄이 각 상태에서 무엇이 보이는지 적는다(2026-10-19 동원님 지시: 「자세히 ⇄ 간단히」는
// 현재 상태도, 얼마나 자세한지도 알 수 없었다).
function renderGuideLevel() {
  const host = byId("guide-level");
  const hint = byId("guide-level-hint");
  if (!host || !hint) return;
  host.innerHTML = [
    ["brief", "간단히", !guideDetailed],
    ["detail", "자세히", guideDetailed],
  ]
    .map(
      ([key, label, on]) =>
        `<button type="button" class="seg-option${on ? " is-on" : ""}" data-guide-level="${key}" aria-pressed="${on}">${label}</button>`,
    )
    .join("");
  hint.textContent = guideDetailed
    ? "지금은 「자세히」입니다. 할 일 카드마다 문의 문장·상세 설명·근거를 펼쳐 보여 줍니다."
    : "지금은 「간단히」입니다. 할 일 카드에는 확인할 값만 보입니다. 문의 문장·상세 설명·근거는 카드의 「자세히」를 누르면 보입니다.";
}

// 서버(find_onbid_references)가 질문에서 찾은 온비드 용어 설명이다. 모델 답과 따로 온다 — 모델이
// 답하지 못했거나 연결되지 않았어도 이 설명은 보여 준다(2026-10-19 동원님 지시: 온비드 사이트·가이드에
// 있는 용어 설명은 반드시 한다). 문장은 서버 상수에서 오고 모델이 만든 것이 아니다.
// 모델이 답했으면 그 답이 이 설명을 풀어 쓴 것이라 같은 글이 두 번 보인다. 그때는 접어 둔다(collapsed).
// 재산유형 전용 설명은 용어 옆에 그 사실을 붙인다. 압류재산 전용 15건 가운데 6건은 문장에 「압류」가 없다
// (2026-10-19 리뷰 r1 P2-1). common·sale·lease 와 사전 용어(scope 빈 값)에는 붙이지 않는다.
const ONBID_REFERENCE_SCOPE_TAGS = { 압류재산: "압류재산 기준", 국유재산: "국유재산 기준", 수탁재산: "수탁재산 기준" };
// 모델이 답하지 않았는데 용어 설명만 보이면 질문에 답한 것처럼 읽힌다(리뷰 r1 P1-2).
const ONBID_REFERENCE_DECLINED_NOTE = "이 질문에는 답하지 않았습니다. 질문에 나온 용어의 온비드 설명만 보여 드립니다.";
// 연결이 안 된 것은 답을 거절한 것과 다르다. 용어 질문이면 아래 설명이 곧 답이다(리뷰 r2 P2-c).
const ONBID_REFERENCE_OFFLINE_NOTE = "AI 코치에 연결되지 않아 질문에 나온 용어의 온비드 설명만 보여 드립니다.";
// 설명이 질문의 일부만 덮을 수 있다(「유찰되면 보증금은?」에는 유찰 뜻만 붙는다 · 리뷰 r1 P1-1).
const ONBID_REFERENCE_PARTIAL_NOTE = "질문하신 내용 가운데 위 설명에 없는 것은 공고 원문이나 담당기관에서 확인하세요.";

function renderOnbidReferences(references, collapsed = false) {
  if (!Array.isArray(references) || !references.length) return "";
  const items = references
    .map((ref) => {
      const tag = ONBID_REFERENCE_SCOPE_TAGS[ref.scope];
      return `<p><strong>${ref.term}</strong>${tag ? ` <span class="small-text">(${tag})</span>` : ""} ${ref.text}</p>
      <p class="small-text">출처: ${ref.source}</p>`;
    })
    .join("");
  if (collapsed) {
    return `<details class="coach-ask-reference">
      <summary>온비드 안내 기준 용어 설명 (${references.length})</summary>
      ${items}
    </details>`;
  }
  return `<div class="coach-ask-reference">
      ${badge("온비드 안내 기준 용어 설명", "neutral")}
      ${items}
    </div>`;
}

// 초보자가 자주 묻는 질문에 서버가 붙인 고정 안내(server.py COMMON_QUESTION_GUIDES)다. 모델이 쓴 글이 아니므로
// 「AI」라고 말하지 않는다. 낙찰 뒤 절차는 재산유형별 문장이 화면 쪽(postAwardProcessNote)에 있어 여기서 붙인다.
function renderCommonGuide(guide, references) {
  const lines = [...(guide.lines || [])];
  let source = guide.source || "";
  if (guide.id === "after-award") {
    const process = postAwardProcessNote();
    lines.push(`이 공고(${process.label}) 기준 순서: ${process.order}`, process.deposit);
    source = process.source;
  }
  const contact = [sampleNotice.agency, sampleNotice.contact].filter((value) => value && value !== NOTICE_VALUE_FALLBACK).join(" ");
  return `<div class="coach-ask-answer coach-guide">
    <p class="coach-guide-head">${badge("온비드 규칙 기반 안내", "neutral")}<strong>${guide.title}</strong></p>
    <ul class="coach-guide-lines">${lines.map((line) => `<li>${line}</li>`).join("")}</ul>
    <p class="small-text">근거: ${source}. 공고마다 예외가 있을 수 있으니 공고 원문과 담당기관 확인이 우선입니다.${contact ? ` 담당기관: ${contact}` : ""}</p>
    ${
      guide.jump && guide.jump !== getBoardStage(getPrepStageStatus()).num
        ? `<button type="button" class="secondary small-button" data-board-stage="${guide.jump}">${guide.jumpLabel}</button>`
        : ""
    }
    ${renderOnbidReferences(references, true)}
  </div>`;
}

function renderQuestionAnswer(answer) {
  if (answer?.guide) return renderCommonGuide(answer.guide, answer.references);
  const referencesHtml = renderOnbidReferences(answer?.references);
  const referencesWithNote = (note) =>
    referencesHtml ? `<div class="coach-ask-answer"><p class="small-text coach-ask-note">${note}</p>${referencesHtml}</div>` : "";
  const declinedHtml = referencesWithNote(ONBID_REFERENCE_DECLINED_NOTE);
  if (!answer?.connected) {
    const offlineHtml = referencesWithNote(ONBID_REFERENCE_OFFLINE_NOTE);
    if (offlineHtml) return offlineHtml;
    return `<div class="coach-ask-answer">
      ${badge("AI 연결 안 됨", "warn")}
      <p>이 질문에는 지금 자동으로 답할 수 없습니다. 담당기관에 문의하세요.</p>
    </div>`;
  }
  if (answer.answerable && answer.answer) {
    // 제도·용어 질문(general)에 온비드 설명이 있으면 모델이 풀어 쓴 답 대신 온비드 문장을 그대로 보인다.
    // 모델은 「text 에 없는 사실은 덧붙이지 않는다」는 지시를 받고도 덧붙였다(2026-10-19 「유찰」 실측).
    if (answer.answerType === "general" && referencesHtml) {
      return `<div class="coach-ask-answer">${referencesHtml}<p class="small-text">${ONBID_REFERENCE_PARTIAL_NOTE}</p></div>`;
    }
    const badgeLabel =
      answer.answerType === "board"
        ? "준비 보드 기반 안내"
        : answer.answerType === "general"
          ? "공매 절차 일반 안내"
          : "공고 원문 기반 답변";
    return `<div class="coach-ask-answer">
      ${badge(badgeLabel, "neutral")}
      <p>${answer.answer}</p>
      ${renderOnbidReferences(answer.references, true)}
    </div>`;
  }
  if (declinedHtml) return declinedHtml;
  return `<div class="coach-ask-answer">
    ${badge("담당기관 문의 필요", "warn")}
    <p>이 질문은 공고 원문만으로 답하기 어렵습니다. 담당기관에 문의하세요.</p>
  </div>`;
}

// 질문할 «그 시점»의 준비 보드 상태. 「이제 뭘 해야 하나요?」 같은 질문은 이것 없이는 답할 근거가 없다.
function getBoardSnapshot() {
  const summary = getTaskSummary();
  const assignments = getAiTaskAssignments(summary.tasks);
  const docSummary = getDocSummary();
  return {
    tasks: summary.tasks.map((task) => ({
      id: task.id,
      title: task.title,
      status: task.action,
      due: task.due,
      done: Boolean(summary.state[task.id]),
      needsCheck: assignments.get(task.id)?.check?.title || "",
    })),
    docs: {
      done: docSummary.doneCount,
      total: docSummary.totalCount,
      pending: docSummary.names.filter((name) => !docSummary.state[name]),
    },
    userType: userTypeLabels[getSelectedUserType()],
  };
}

// 502 · 네트워크 오류처럼 시스템이 답을 못 준 경우다. 「담당기관에 문의」는 답할 수 없는 질문에만 쓴다(I5).
const ASK_SYSTEM_FAILURE_MESSAGE = "답을 받지 못했습니다. 잠시 뒤 다시 질문하십시오.";

async function askNoticeQuestion() {
  // 결과 요소는 여기서 잡아 두지 않는다. 답을 기다리는 사이 코치 영역이 새로 그려질 수 있다(I1).
  const input = byId("coach-question-input");
  if (!input || !byId("coach-question-result")) return;
  // 버튼 · 칩 · Enter 세 경로가 모두 여기로 온다. 진행 중이거나 429 직후면 보내지 않는다(I3 · 연타 3번에 3건이 나갔다).
  if (isCoachAskLocked()) return;
  const conditionAnswers = getDocConditionAnswers();
  const question = input.value.trim();
  if (!question) {
    setCoachAnswer(`<p class="small-text">질문을 입력하세요.</p>`);
    return;
  }
  const requestId = ++askRequestId;
  askInFlight = true;
  setCoachAnswer(`<p class="small-text">답변을 찾는 중입니다...</p>`);
  applyCoachAskControls();
  try {
    const response = await window.fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        notice: {
          title: sampleNotice.title,
          assetType: sampleNotice.assetType,
          dispositionLabel: sampleNotice.dispositionLabel,
          bidMethod: sampleNotice.bidMethod,
          bidPeriod: sampleNotice.bidPeriod,
          bidDeadline: sampleNotice.bidDeadline,
          minimumBidPrice: sampleNotice.minimumBidPrice,
          appraisalPrice: sampleNotice.appraisalPrice,
          agency: sampleNotice.agency,
          contact: sampleNotice.contact,
          bidDeposit: (sampleNotice.costs || []).find((item) => item.title === "입찰보증금")?.value || "",
          evictionResponsibility: sampleNotice.evictionResponsibility || "",
          jointBidAnswer: conditionAnswers.joint === "yes" ? "공동입찰 예정" : "공동입찰 아님",
          proxyBidAnswer: conditionAnswers.proxy === "yes" ? "대리입찰 예정" : "대리입찰 아님",
        },
        docs: (sampleNotice.requiredDocs || []).slice(0, 10),
        board: getBoardSnapshot(),
      }),
    });
    const payload = await response.json();
    // 새 공고로 넘어가며 번호가 올라갔으면 이 답은 지금 화면의 공고에 대한 것이 아니다.
    if (requestId !== askRequestId) return;
    if (response.status === 429) startAskCooldown();
    if (!payload.ok) {
      // 서버 내부 오류(5xx)는 원본 문구 대신 다시 물으라고 안내한다. 담당기관은 시스템 장애를 알 수 없다(I5).
      // 429 · 400(질문을 입력하세요)처럼 사용자가 할 일이 담긴 문구는 그대로 보인다.
      const systemFailure = response.status >= 500 || !payload.error;
      if (systemFailure) console.warn("AI 코치 질문 실패", response.status, payload.error);
      setCoachAnswer(`<p class="small-text">${escapeHtml(systemFailure ? ASK_SYSTEM_FAILURE_MESSAGE : payload.error)}</p>`);
      return;
    }
    setCoachAnswer(renderQuestionAnswer(payload.result));
  } catch (error) {
    if (requestId !== askRequestId) return;
    console.warn("AI 코치 질문 실패", error);
    setCoachAnswer(`<p class="small-text">${ASK_SYSTEM_FAILURE_MESSAGE}</p>`);
  } finally {
    // 낡은 요청이면 잠금은 이미 clearCoachAnswer 가 풀었다. 여기서 풀면 새 요청의 잠금까지 풀린다.
    if (requestId === askRequestId) {
      askInFlight = false;
      applyCoachAskControls();
    }
  }
}

// 온비드가 입찰자에게 공통으로 거는 규칙이다. 공고마다 달라지는 값이 아니라 고정 문구로 둔다.
// 근거: 온비드 이용안내 「입찰참가 안내」 STEP04-4·STEP04-5, 입찰참가자 준수규칙(압류 제8조②·
// 제9조③④, 국유 제9조④⑤ 등) · team-reports/2026-10-19-onbid-journey-conformance/
// researcher-onbid-journey.md A8~A10. 이용기관이 따로 정하면 예외가 있어 「원칙」으로 쓴다.
const ONBID_BID_RULES = [
  "입찰서는 제출한 뒤에 수정하거나 취소할 수 없는 것이 원칙입니다.",
  "입찰보증금 납부 계좌는 입찰서를 제출한 뒤에 발급됩니다. 입찰 마감 시각까지 보증금을 내지 않으면 입찰이 무효가 됩니다.",
  "입찰서 제출과 보증금 납부가 끝났는지는 온비드에서 직접 확인하십시오. 확인하지 않아 생긴 불이익은 입찰자 책임입니다.",
  // 아래 두 줄의 근거: 온비드 FAQ #67972(2회 이상 제출 가능 물건이면 같은 회차에 재입찰 가능) ·
  // 국유재산 입찰참가자 준수규칙 제12조③(낙찰자 신원 비공개). 2026-10-19 커뮤니티 조사 1-1·1-3 에서
  // 초보자가 「입찰을 취소할 수 없나」「입찰자 수를 볼 수 있나」를 물었다.
  "온비드에서 2회 이상 입찰서 제출이 가능하다고 안내된 물건이면 같은 회차에 다시 입찰할 수 있습니다. 그 안내가 없으면 첫 줄의 원칙대로 제출한 입찰서를 수정하거나 취소할 수 없습니다.",
  "개찰 뒤 낙찰자가 누구인지는 공개되지 않습니다. 내 입찰 결과는 온비드 「나의온비드 > 입찰결과」에서 직접 확인합니다.",
];

// 3단계(입찰 참여)에서 "담당기관에 물어볼 질문 정리"를 뺀 자리에 두는 정보 리스트다.
// 새 추출 로직을 만들지 않고 1·3단계 task의 action(이미 서버가 계산한 값)을 그대로 보여준다.
// 개찰일시는 notice에 그 값을 담는 필드가 없어 추출 로직이 생기기 전까지는 행 자체를 만들지 않는다.
function renderBidParticipationInfo(taskSummary) {
  const bidPeriodTask = taskSummary.tasks.find((task) => task.id === "bid-period");
  const priceTask = taskSummary.tasks.find((task) => task.id === "price");
  const bidPlace = sampleNotice.bidType === "전자입찰" ? "온비드 전자입찰" : NOTICE_VALUE_FALLBACK;
  const rows = [
    ["입찰기간", bidPeriodTask?.action || NOTICE_VALUE_FALLBACK],
    ["입찰 장소", bidPlace],
    // 2-1 공고 요약에서 이 칸을 뺐으므로(U10 ⑴) 준비 보드에서 최저입찰가격을 보는 곳은 여기다. price 할 일이
    // 없는 공고도 옛 요약 칸처럼 공고 값을 보인다.
    ["최저입찰가격", priceTask?.action || sampleNotice.minimumBidPrice || NOTICE_VALUE_FALLBACK],
  ];
  return `<div class="bid-participation-info">
    <section class="block">
      <h3 class="block-title">입찰 참여 정보</h3>
      <div class="fact-grid">${rows.map(([label, value]) => factCell(label, fieldValue(value))).join("")}</div>
      ${
        // 입찰서는 온비드에서 직접 낸다. 이 단계의 실제 다음 행동이 그곳이라 바로 여는 길을 둔다(U12).
        sampleNotice.sourceUrl
          ? `<div class="link-chips"><a class="link-chip" href="${sampleNotice.sourceUrl}" target="_blank" rel="noreferrer">온비드에서 이 물건 열기 ↗</a></div>`
          : ""
      }
    </section>
    <section class="block bid-rules">
      <h3 class="block-title">온비드 입찰 규칙</h3>
      <ul class="info-list">${ONBID_BID_RULES.map((rule) => `<li class="info-row"><p class="info-row-text">${rule}</p></li>`).join("")}</ul>
      <p class="block-note">근거는 온비드 이용안내 「입찰참가 안내」와 입찰참가자 준수규칙입니다. 공고마다 예외가 있을 수 있으니 공고 원문도 확인하십시오.</p>
    </section>
  </div>`;
}

function renderAiReadySummary(coach) {
  const checks = coach?.unresolvedChecks || [];
  return infoRow({
    tag: coach?.llmStatus === "connected" ? "AI 분석 완료" : "규칙 기반 점검 완료",
    tone: coach?.llmStatus === "connected" ? "safe" : "warn",
    title: "준비 보드에서 우선순위 체크리스트로 보여드립니다.",
    text: checks.length
      ? // 담당기관 질문 개수는 화면 어디에도 그리지 않는다. 없는 것을 약속하지 않는다(U8).
        "확인할 항목을 준비 보드 단계별 할 일로 정리했습니다."
      : "공고별 준비 보드에서 다음 확인 항목을 정리합니다.",
  });
}

const docSourceBadge = {
  A: "본문에서 찾을 수 있음",
  B: "첨부를 봐야 함",
  C: "원문에 없을 수 있음",
  unknown: "위치 미상",
};

const docChecklistStatusBadge = {
  // 초록(safe)을 쓰지 않는다 — 검증이 아니라 참고용 목록이라 "자격 충족"으로 읽히면 안 된다
  // (캠코 정인기 차장 조건, 2026-09-07 · P0, 2026-09-12 상호작용 감사).
  extracted: ["추출됨", "neutral"],
  attachment_only: ["본문 미기재", "warn"],
  not_in_notice: ["원문에 없음", "warn"],
  not_found: ["추출 실패", "warn"],
};

// preview-grid·coach-facts와 같은 field-label/field-value 클래스를 재사용한다 — 칩 폭에
// 맞춰 CSS(.doc-chip .field-label/.field-value)가 크기만 눌러 준다(2026-09-22 UI 정리).
function docLabeledChip(label, value) {
  return value ? `<span class="field-label">${label}</span> <span class="field-value">${value}</span>` : "";
}

function docExtraChips(item) {
  return [
    item.stage,
    item.copy,
    item.count,
    item.validity && docLabeledChip("유효기간", item.validity),
    item.method && docLabeledChip("제출", item.method),
    item.due && docLabeledChip("기한", item.due),
  ]
    .filter(Boolean)
    .map((chip) => `<span class="doc-chip">${chip}</span>`)
    .join("");
}

// 서류 조건 축 10개(server.py CONDITION_AXES) 중 신청인 유형과 직접 연결되는 것은
// corp(법인)·person(개인) 두 축뿐이다. 나머지(대리입찰·공동입찰·지역제한 등)는 사용자
// 유형과 무관해 판단 대상에서 뺀다 — 축이 없는 그룹은 항상 펼침으로 둔다.
const DOC_GROUP_CONDITION_USER_TYPES = {
  corp: ["corp"],
  person: ["person", "sole", "founder"],
};

function getDocGroupUserTypes(group) {
  const conditionKeys = new Set();
  (group.items || []).forEach((item) => {
    (item.conditionKeys || []).forEach((key) => conditionKeys.add(key));
  });
  const userTypes = new Set();
  conditionKeys.forEach((key) => {
    (DOC_GROUP_CONDITION_USER_TYPES[key] || []).forEach((type) => userTypes.add(type));
  });
  return [...userTypes];
}

function renderDocSourceNotice() {
  const checklist = sampleNotice.docChecklist;
  const profile = checklist?.profile;
  if (!profile) return "";
  // doc-source-notice 클래스는 e2e(tests/screen.spec.js S1 배지 색 단언)가 셀렉터로 쓴다 — 유지한다.
  return infoRow({
    cls: "doc-source-notice",
    tag: docSourceBadge[profile.code] || docSourceBadge.unknown,
    tone: profile.code === "A" ? "safe" : "warn",
    title: profile.label,
    text: profile.detail,
    // detail 은 서버 문구(DOC_SOURCE_PROFILES)라 「아래 첨부파일」을 고치지 못한다. 1-3 에는 첨부 영역이 없으므로
    // 실제 위치를 덧붙인다(U7).
    meta: profile.code === "B" ? "첨부파일은 준비 보드 2-1 에서 함께 확인하십시오." : "",
  });
}

// 「원문 근거」의 출처. 서버 sourceSection(「공고문」·「제출서류」·「첨부:파일명」)에 가장 바깥 조항 표제(sourceOutline)를
// 이어 「공고문 > 10. 낙찰(예정)자 제출서류」로 만든다. 화면이 만든 보충 항목은 sourceSection 이 비어 출처가 없다.
function docSourceLocation(item) {
  const section = String(item.sourceSection || "");
  if (!section) return "";
  const doc = section.startsWith("첨부:") ? `첨부 「${section.slice(3)}」` : section;
  const outline = String(item.sourceOutline || "");
  return outline ? `${doc} > ${outline}` : doc;
}

// 서류 체크박스 한 행. renderDocGroup(조건별 묶음)과 renderDocFlatSection(미분류·별도 문의
// 구획)이 같은 마크업을 쓰도록 빼냈다 — 복사해 두면 한쪽만 고쳐질 때 체크박스 배선이 갈린다.
function renderDocCheckRow(item, docState, locked, lockMsgId) {
  return `<li class="${docState[item.name] ? "is-checked" : ""}${locked ? " is-locked" : ""}">
    <label class="doc-check">
      <input type="checkbox" data-doc-name="${item.name}" ${docState[item.name] ? "checked" : ""}${
        locked ? ` disabled aria-disabled="true" aria-describedby="${lockMsgId}"` : ""
      }>
      <strong>${item.name}</strong>
    </label>
    <span class="doc-chips">${docExtraChips(item)}</span>
    ${
      item.howto
        ? `<span class="doc-howto">발급처: <a href="${item.howtoUrl}" target="_blank" rel="noreferrer">${item.howto}</a></span>`
        : `<span class="doc-howto">발급처: 공고 원문·첨부 서식 또는 담당기관 확인</span>`
    }
    ${isUnclassifiedDoc(item) && UPON_REQUEST_DOC_RE.test(String(item.evidence || "")) ? `<span class="doc-howto">${UPON_REQUEST_DOC_NOTE}</span>` : ""}
    <details><summary>원문 근거</summary>${
      docSourceLocation(item) ? `<p class="small-text doc-evidence-source">출처: ${escapeHtml(docSourceLocation(item))}</p>` : ""
    }<p class="small-text">${item.evidence}</p>${
      item.sourceHeading ? `<p class="small-text">시점 근거: ${escapeHtml(item.sourceHeading)}</p>` : ""
    }</details>
  </li>`;
}

// D7(2026-10-19) · 「예술의전당의 요청이 있을 경우 … 제출」처럼 기관이 요청할 때만 내는 서류는 시점이 없어 미분류로
// 남는다. 「입찰 전에 필요할 수 있다」는 구획 안내와 다르다는 것을 그 행에 따로 적는다.
// 「보완 요청 시 7일 이내 제출」 같은 입찰 서류 문장에도 걸리는 「요청 시」는 뺐다(리뷰 d8378b6 r2 P2-A).
const UPON_REQUEST_DOC_RE = /요청이\s*있을\s*경우|요청하는\s*경우/;
const UPON_REQUEST_DOC_NOTE = "기관이 요청할 때만 내는 서류일 수 있습니다.";

// D2(2026-10-19) · 서버는 첨부를 4개까지 · 8MB 까지만 읽는다. 읽지 못한 첨부가 있으면 그 수와 이유를 말한다 —
// 말하지 않으면 목록이 첨부까지 다 읽은 결과처럼 보인다(원문 36건 중 18건이 일부를 못 읽음).
const ATTACHMENT_READ_REASON = {
  not_tried: "한 번에 읽는 개수를 넘음",
  too_large: "파일이 너무 큼",
  failed: "내용을 읽지 못함",
};
function renderAttachmentReadNotice(checklist) {
  const unread = (Array.isArray(checklist?.attachmentReads) ? checklist.attachmentReads : []).filter(
    (read) => read && read.status !== "read",
  );
  if (!unread.length) return "";
  const names = unread
    .map((read) => `${escapeHtml(String(read.name || ""))}(${ATTACHMENT_READ_REASON[read.status] || "읽지 못함"})`)
    .join(", ");
  return `<p class="small-text attachment-unread">첨부 ${unread.length}개를 읽지 못했습니다: ${names}. 그 첨부에 서류가 더 있을 수 있으니 직접 확인하십시오.</p>`;
}

// 조건별 서류 그룹 1개. 2단계(renderDocChecklist)와 4단계(renderPostAwardPanel)가 같은 마크업을
// 쓰도록 빼냈다 — 두 곳에 같은 <li> 를 복사해 두면 한쪽만 고쳐질 때 체크박스 배선이 갈린다.
function renderDocGroup(group, docState, locked, open, lockMsgId) {
  const items = Array.isArray(group.items) ? group.items : [];
  return `<details class="doc-group"${open ? " open" : ""}>
    <summary><h4>${group.condition}</h4>${badge(`${items.length}개 서류`, "neutral")}</summary>
    <ul>
      ${items.map((item) => renderDocCheckRow(item, docState, locked, lockMsgId)).join("")}
    </ul>
  </details>`;
}

// 2단계 안에서 미분류·별도 문의 필요 서류를 확정 항목과 분리해 보여주는 구획
// (stage-classification-design.md §3 "미분류를 1급 상태로 두는 설계"). 확정 항목이
// 우선이므로 open 은 호출부가 결정하지 않고 항상 펼쳐 둔다 — 접혀 있으면 "우리도 모른다"는
// 사실을 사용자가 못 보고 지나칠 수 있다.
function renderDocFlatSection(cls, title, noticeHtml, items, docState, locked, lockMsgId) {
  if (!items.length) return "";
  return `<details class="doc-group ${cls}" open>
    <summary><h4>${title}</h4>${badge(`${items.length}개 서류`, "warn")}</summary>
    ${noticeHtml}
    <ul>
      ${items.map((item) => renderDocCheckRow(item, docState, locked, lockMsgId)).join("")}
    </ul>
  </details>`;
}

function renderUnclassifiedDocSection(docState, locked, lockMsgId) {
  const items = getUnclassifiedPreBidDocItems();
  return renderDocFlatSection(
    "doc-group-unclassified",
    "단계를 확정하지 못한 서류",
    // 2026-10-19 · 판정이 실패했다는 사실만 말하면 초보자는 서비스가 고장 난 것으로 읽는다. 왜 여기 있는지를 말한다
    // (team-reports/2026-10-19-bid-stage-sot/implementation-plan.md 4단계 · D1: 시점을 못 찾은 서류는 2단계에 남긴다).
    `<p class="small-text">공고문에서 이 서류의 제출 시점을 찾지 못했습니다. 입찰 전에 필요할 수 있어 여기에 함께 두었습니다. 「원문 근거」를 열어 확인하고, 그래도 모르면 담당기관에 확인하십시오.</p>`,
    items,
    docState,
    locked,
    lockMsgId,
  );
}

function renderNeedsInquiryDocSection(docState, locked, lockMsgId) {
  const items = getNeedsInquiryPreBidDocItems();
  const contact = String(sampleNotice.docChecklist?.contact || "").trim();
  return renderDocFlatSection(
    "doc-group-needs-inquiry",
    "공고기관에 직접 문의해야 하는 서류",
    `<p class="small-text">이 서류는 공고기관에 직접 문의해야 합니다.${
      contact ? ` 담당부점/공고기관: ${contact}` : " 담당부점/공고기관 연락처가 확인되지 않았으니 공고 원문에서 확인하십시오."
    }</p>`,
    items,
    docState,
    locked,
    lockMsgId,
  );
}

function renderDocConditionQuestions(answers) {
  const options = [
    { key: "joint", question: "공동입찰인가요?" },
    { key: "proxy", question: "대리입찰인가요?" },
  ];
  return `<div class="doc-condition-question">
    ${options
      .map(
        (option) => `<div class="doc-condition-row">
          <p>${option.question}</p>
          <div class="doc-condition-options" role="radiogroup" aria-label="${option.question}">
            ${["yes", "no"]
              .map(
                (value) => `<button type="button" class="secondary small-button${answers[option.key] === value ? " is-active" : ""}" aria-pressed="${answers[option.key] === value}" data-doc-condition="${option.key}" data-doc-condition-value="${value}">${value === "yes" ? "예" : "아니오"}</button>`,
              )
              .join("")}
          </div>
        </div>`,
      )
      .join("")}
  </div>`;
}

// 제출기한은 온비드 화면 표와 공고문 본문이 어긋난다. 같은 국유재산 공고에서 화면 표는
// 「입찰마감일시 전까지 / 직접제출」인데 공고문 본문은 「입찰 기간 마감일 17:00까지 우편으로」였다
// (2026-10-18 researcher-fact-check 사실 4-③). 입찰 마감일시가 17:00보다 늦으면 실제 마감은
// 표보다 이르다. 그래서 기한을 보여주는 자리마다 이 문구를 함께 둔다.
//
// 표 원본 블록 안에서는 이 문구를 p 가 아니라 div 로 감싼다 — 그 블록의 p 는 「표의 한 행」이고,
// e2e 의 tableRowCounts(셀렉터 ".doc-table p")가 그것을 행 수로 센다. p 로 넣으면 표가 한 행
// 늘어난 것으로 세어져 N3 거짓 안내 게이트의 도달 단정이 어긋난다(2026-10-18 실측 2건 실패).
const DOC_DUE_CAUTION =
  "제출기한은 공고문 원문의 기한이 더 이를 수 있으니 반드시 원문을 확인하십시오. 온비드 화면 표와 공고문 본문의 기한·제출방법이 어긋나는 공고가 있습니다.";

// 공공데이터 getCltrBidInf2 가 준 제출기한·제출방식을 보여준다. 서버가 입찰 방식 가능 여부
// 플래그로 이미 걸러 보낸 것만 들어온다(src/server.py 의 build_bid_doc_terms 주석 ⑶ — 플래그가
// N 인데 기한 값이 남아 있는 공고가 실제로 있어, 거르지 않으면 거짓 안내가 된다).
//
// 🔴 화면 표 기한과 API 기한이 어긋날 때의 우선순위를 여기서 정한다. 두 값을 모두 보여주고,
// 더 이른 기한을 기준으로 준비하라고 안내한 뒤 공고문 원문 확인으로 넘긴다. 한쪽만 보여주고
// 그것이 늦은 쪽이면 사용자가 마감을 놓치는데, 이 서비스에서 그 오류가 가장 비싸다.
// 어느 쪽이 이른지는 기계로 판정하지 않는다 — 「입찰마감일시 전까지」와 「우편으로 17:00까지」는
// 서로 비교할 수 있는 형식이 아니고, 억지로 비교하면 틀린 쪽을 이르다고 단정하게 된다.
// 근거: 2026-10-18 researcher-fact-check 사실 4-③(같은 공고에서 화면 표와 본문이 어긋난 사례).
const API_DOC_TERM_SOURCE_NOTE =
  "아래 기한과 방식은 공공데이터 온비드 물건 입찰상세에서 받은 값입니다. 온비드 화면 표와 공고문 본문이 이 값과 다를 수 있습니다.";
const API_DOC_TERM_CONFLICT_NOTE =
  "두 값 가운데 더 이른 기한을 기준으로 준비하시고, 공고문 원문의 해당 조항을 반드시 확인하십시오.";

// 🔴 공동입찰·대리입찰 질문 답에 맞춰 한 번 더 거른다. 서버는 「이 공고에서 그 방식이
// 가능한가」만 보고 보내는데, 화면에는 「내가 그 방식으로 입찰하는가」라는 사용자 답이 따로
// 있다. 거르지 않으면 사용자가 「공동입찰 아니오」라고 답했는데도 공동입찰 제출기한이 화면에
// 남아, 같은 화면의 서류 체크리스트(그 답으로 그룹을 걸러낸다)와 어긋난다.
// 2026-10-18 브라우저 측정에서 실제로 그 상태를 관측해 고쳤다.
const API_DOC_TERM_CONDITION_KEYS = { 공동입찰: "joint", 대리입찰: "proxy" };

function getApiDocTerms() {
  const terms = sampleNotice.apiDocTerms;
  if (!Array.isArray(terms)) return [];
  const answers = getDocConditionAnswers();
  return terms.filter((term) => {
    if (!term || !(term.due || term.method)) return false;
    const answerKey = API_DOC_TERM_CONDITION_KEYS[term.kind];
    // 질문이 걸린 구분은 「예」일 때만 보여준다. 질문이 없는 구분(입찰참가신청 ·
    // 입찰보증금 대체서류)은 사용자 답과 무관하므로 그대로 둔다.
    return !answerKey || answers[answerKey] === "yes";
  });
}

// 같은 구분(공동입찰·대리입찰)의 화면 추출 서류에 적힌 기한을 모은다. 중복은 지운다.
function getScreenDuesForKind(kind) {
  const dues = new Set();
  getPreBidDocGroups().forEach((group) => {
    if (!String(group.condition || "").includes(kind)) return;
    (Array.isArray(group.items) ? group.items : []).forEach((item) => {
      const due = String(item.due || "").trim();
      if (due) dues.add(due);
    });
  });
  return [...dues];
}

function renderApiDocTermsPanel() {
  const terms = getApiDocTerms();
  if (!terms.length) return "";
  const rowsHtml = terms
    .map((term) => {
      const screenDues = getScreenDuesForKind(term.kind).filter((due) => due !== term.due);
      const hasConflict = Boolean(term.due) && screenDues.length > 0;
      return `<li${hasConflict ? ' class="has-term-conflict"' : ""}>
        <strong>${term.kind}</strong>
        <span class="doc-chips">
          ${term.due ? badge(`기한 ${term.due}`, "warn") : ""}
          ${term.method ? badge(`방식 ${term.method}`, "neutral") : ""}
        </span>
        ${
          hasConflict
            ? `<p class="api-term-conflict">온비드 화면 표에는 기한이 "${screenDues.join(" · ")}"로 적혀 있어 두 값이 다릅니다. ${API_DOC_TERM_CONFLICT_NOTE}</p>`
            : ""
        }
      </li>`;
    })
    .join("");
  return `<div class="api-doc-terms">
    <h4>제출기한·제출방식 (공공데이터 기준)</h4>
    <p class="small-text">${API_DOC_TERM_SOURCE_NOTE}</p>
    <ul>${rowsHtml}</ul>
  </div>`;
}

// 입찰참가신청 필요 여부. 이 값이 「필요」면 공고기관 승인을 먼저 받아야 입찰할 수 있어서 서류
// 준비 순서가 통째로 바뀌므로 2단계 맨 위에 강조해 둔다. 「불필요」면 그 사실만 조용히 적는다.
// 서버가 값을 주지 못하면 이 블록을 아예 그리지 않는다 — 가장 눈에 띄는 자리에 「우리가 모른다」를
// 두지 않는다(2026-10-18 ux-design-review P1-1 의 판단을 그대로 따른다).
function renderBidParticipationApplyPanel() {
  const info = sampleNotice.bidParticipationApply;
  if (!info || typeof info.required !== "boolean") return "";
  if (!info.required) {
    return `<section class="block bid-apply-panel is-not-required">
      <h3 class="block-title">입찰참가신청</h3>
      ${infoRow({
        tag: "불필요",
        tone: "safe",
        // 블록 제목 · 머리표가 이미 「입찰참가신청 · 불필요」라 행 제목은 뜻만 말한다(V11).
        title: "사전 승인 없이 바로 입찰할 수 있습니다",
        meta: `근거: ${info.source}`,
      })}
    </section>`;
  }
  const detailHtml = [
    info.docs ? `<li>신청 서류: ${info.docs}</li>` : "",
    info.due ? `<li>신청 기한: ${info.due}</li>` : "",
    info.method ? `<li>제출 방식: ${info.method}</li>` : "",
  ]
    .filter(Boolean)
    .join("");
  return `<section class="block bid-apply-panel is-required">
    <h3 class="block-title">입찰참가신청</h3>
    <div class="info-row">
      <div class="info-row-head">${badge("먼저 할 일", "warn")}<strong class="info-row-title">이 물건은 공고기관 승인을 받아야 입찰할 수 있습니다.</strong></div>
      <p class="info-row-text">서류를 먼저 내고 승인을 기다려야 합니다. 승인 전에는 입찰 자체가 되지 않으므로, 아래 서류 준비보다 이것이 먼저입니다.</p>
      ${detailHtml ? `<ul class="info-row-list">${detailHtml}</ul>` : ""}
    </div>
    <p class="block-note">신청 절차와 마감 시각은 공고문 원문에서 반드시 확인하십시오. 근거는 ${info.source} 입니다.</p>
  </section>`;
}

// 자격제한·지역제한·기타제한. 「이 물건에 응찰할 자격이 되는가」는 사용자가 가장 먼저 알아야
// 하는 것이라 1단계(공고 확인)에 둔다. 제한이 없다는 값도 알 가치가 있어 함께 보여주되,
// 제한이 실제로 있는 항목만 강조한다.
function renderBidLimitsPanel() {
  const limits = sampleNotice.bidLimits;
  if (!Array.isArray(limits) || !limits.length) return "";
  const rowsHtml = limits
    .map(
      (limit) => `<li class="info-row${limit.restricted ? " is-restricted" : ""}">
        <div class="info-row-head">${badge(limit.restricted ? "제한 있음" : "제한 없음", limit.restricted ? "warn" : "safe")}<strong class="info-row-title">${limit.label}</strong></div>
        <p class="info-row-text">${limit.value}</p>
      </li>`,
    )
    .join("");
  const hasRestriction = limits.some((limit) => limit.restricted);
  return `<section class="block bid-limits-panel${hasRestriction ? " has-restriction" : ""}">
    <h3 class="block-title">입찰 자격 조건 <span class="block-meta">공공데이터 기준</span></h3>
    ${
      hasRestriction
        ? `<p class="block-lead">제한 조건이 있습니다. 조건에 맞지 않으면 입찰이 무효가 될 수 있으니 공고문 원문에서 먼저 확인하십시오.</p>`
        : `<p class="block-lead">제한 조건이 확인되지 않았습니다. 그래도 공고문 원문의 참가자격 조항을 한 번 확인하십시오. 조항에 괄호 안 표기(사업자 등)가 있으면 그 뜻은 원문과 담당기관에서 확인하십시오.</p>`
    }
    <ul class="info-list">${rowsHtml}</ul>
  </section>`;
}

// 첨부파일 탭은 2-1 에만 있다. 2-2 의 「첨부파일을 확인하십시오」가 가리킬 곳과 그곳으로 가는 버튼이다(U7).
function renderAttachmentPointer() {
  return `<p class="small-text attachment-pointer">첨부파일은 2-1 공고 확인의 「공고 자료 › 첨부파일」에서 확인하십시오.
    <button type="button" class="secondary small-button" data-goto-attachments>2-1 첨부파일 보기</button></p>`;
}

function renderDocChecklist(locked) {
  const checklist = sampleNotice.docChecklist;
  if (!checklist) return "";
  const profile = checklist.profile || {};
  let [statusLabel, statusType] = docChecklistStatusBadge[checklist.status] || ["확인 필요", "warn"];
  // 첨부를 열지 않았으면 「원문에 없음」이라고 말할 수 없다. 우리가 확인한 것은 본문뿐이고,
  // 첨부는 눈앞에 렌더된다. 배지가 「원문」이라고 말하면 그 첨부와 정면으로 어긋난다.
  if (checklist.status === "not_in_notice" && (sampleNotice.relatedDocs?.length || 0) > 0) {
    statusLabel = "본문에 없음";
  }
  const rawGroups = Array.isArray(checklist.groups) ? checklist.groups : [];
  const answers = getDocConditionAnswers();
  // 2단계는 「입찰 전」 서류만 그린다. 「낙찰 후·계약 시」 서류는 4단계 블록이 맡는다.
  // 확정 항목(groups)을 위에, 미분류·별도 문의 필요는 각자 구획으로 아래에 둔다 — 셋을
  // 똑같이 섞어 보여주면 "우리가 확정했다"와 "우리도 모른다"를 사용자가 구별할 수 없다
  // (stage-classification-design.md §3).
  const groups = getConfirmedPreBidDocGroups();
  const userType = getSelectedUserType();
  const docState = getDocState();

  const groupsHtml = groups
    .map((group) => {
      const groupUserTypes = getDocGroupUserTypes(group);
      const isRelevant = !groupUserTypes.length || groupUserTypes.includes(userType);
      return renderDocGroup(group, docState, locked, isRelevant, "stage-lock-msg-2");
    })
    .join("");
  const unclassifiedHtml = renderUnclassifiedDocSection(docState, locked, "stage-lock-msg-2");
  const needsInquiryHtml = renderNeedsInquiryDocSection(docState, locked, "stage-lock-msg-2");
  const hasAnyPreBidItems = getPreBidDocGroups().some((group) => (group.items || []).length);

  const docSummary = getDocSummary();

  return `<section class="doc-panel">
    <div class="doc-head">
      ${badge(docSourceBadge[profile.code] || docSourceBadge.unknown, profile.code === "A" ? "safe" : "warn")}
      ${badge(statusLabel, statusType)}
      <strong>${checklist.headline}</strong>
    </div>
    <p>제출서류 리스트입니다.</p>
    <p class="small-text">${DOC_DUE_CAUTION}</p>
    ${renderApiDocTermsPanel()}
    ${renderDocConditionQuestions(answers)}
    ${
      docSummary.totalCount
        ? `<div class="doc-progress">
          <strong>${docSummary.doneCount}/${docSummary.totalCount}개 서류 준비 완료</strong>
          <span class="progress" role="progressbar" aria-label="서류 준비 진행률" aria-valuemin="0" aria-valuemax="${docSummary.totalCount}" aria-valuenow="${docSummary.doneCount}"><i style="width:${docSummary.percent}%"></i></span>
          <p class="small-text">같은 이름의 서류는 어느 그룹에서 체크해도 함께 반영됩니다. 실제로는 "공통" + 내 입찰 방식(단독/공동/대리) 서류만 준비하면 됩니다.</p>
        </div>`
        : ""
    }
    <p class="doc-reference">${checklist.reference || ""}</p>
    <p>${profile.label || ""}</p>
    <p class="small-text">${profile.detail || ""}</p>
    ${profile.code === "B" ? renderAttachmentPointer() : ""}
    ${renderAttachmentReadNotice(checklist)}
    ${
      hasAnyPreBidItems
        ? groupsHtml + unclassifiedHtml + needsInquiryHtml
        : rawGroups.length
          ? `<p class="small-text">공동입찰·대리입찰에 해당하지 않아 추가로 준비할 서류가 없습니다. 질문에 "예"로 답하면 관련 서류가 다시 나타납니다.</p>`
          : `<p class="small-text">조건별 서류 목록을 만들지 못했습니다. 첨부파일과 온비드 원문을 확인하십시오.</p>${renderAttachmentPointer()}`
    }
    ${
      checklist.tableRows?.length
        ? `<details class="doc-table">
            <summary>온비드 제출서류 표 원본 (${checklist.tableRows.length}행)</summary>
            <div class="small-text">${DOC_DUE_CAUTION}</div>
            ${checklist.tableRows
              .map(
                (row) => `<p class="small-text">${row.category} / ${row.name}${row.generic ? " (구분명 그대로)" : ""} / ${row.due} / ${row.method}</p>`,
              )
              .join("")}
          </details>`
        : ""
    }
    <ul class="doc-notes">${(checklist.notes || []).map((note) => `<li>${note}</li>`).join("")}</ul>
    <div class="doc-locker-action">
      <button type="button" class="primary small-button" data-store-to-locker>관심 공고에 저장</button>
      <span id="doc-locker-feedback" class="doc-locker-feedback" role="status" aria-live="polite"></span>
    </div>
  </section>`;
}

function renderAttachments() {
  const host = byId("attachment-list");
  if (!host) return;
  const docs = Array.isArray(sampleNotice.relatedDocs) ? sampleNotice.relatedDocs : [];
  host.innerHTML = docs.length
    ? docs
      .map(
        (doc) =>
          infoRow({
            cls: "attachment-row",
            title: typeof doc === "string" ? doc : doc.name,
            action: typeof doc === "string" || !doc.downloadUrl ? null : { href: doc.downloadUrl, label: "내려받기" },
          }),
      )
      .join("")
    : `<p class="block-note">이 공고에는 첨부파일이 없습니다.</p>`;
  host.innerHTML += attachmentInventoryNote(docs);
}

// 압류재산 공고의 첨부 목록에 「명세서」가 든 파일이 없으면 그 사실만 적는다. 「없으니 위험하다」는
// 판단은 쓰지 않는다(2026-10-19 커뮤니티 조사 1-2 · 지식iN 「공매재산 명세서가 없어요」). 파일명 검사라
// 본문 안에 명세서가 들어 있는 첨부는 못 알아본다 — 그래서 「찾지 못했습니다」까지만 말한다.
function attachmentInventoryNote(docs) {
  if (!String(sampleNotice.assetType || "").includes("압류재산")) return "";
  // 첨부가 0건이면 바로 위 「첨부파일이 없습니다」가 이미 그 사실을 말한다(리뷰 r1 #6).
  if (!docs.length) return "";
  const names = docs.map((doc) => (typeof doc === "string" ? doc : String(doc?.name || "")));
  if (names.some((name) => name.includes("명세서"))) return "";
  return `<p class="block-note attachment-inventory-note">첨부 파일명에서 「명세서」를 찾지 못했습니다. 압류재산 공매의 공매재산명세서가 따로 있는지는 온비드 물건 상세와 담당 부점에서 확인하십시오.</p>`;
}


// 온비드 자료실 이용설명서(입찰자용 매뉴얼)와 유튜브 안내 영상 링크다(2026-09-14 확인).
// 온비드 화면·유튜브 어디에도 공공누리 표시가 없어 원문을 옮기지 않고 링크로만 연결한다.
const REFERENCE_LINKS = [
  {
    title: "차세대 온비드 이용 매뉴얼(입찰자용)",
    note: "PDF 11개 · 화면별 분책(회원가입·물건·공고·입찰하기 등)",
    url: "https://www.onbid.co.kr/op/btbdguid/utlzdescdata/utlzdescdata/UtlzDescDataInqController/mvmnUtlzDescDataDtl.do?gnrBtbdLstNo=102905",
  },
  {
    title: "차세대 온비드 이용 매뉴얼(입찰자용)_모바일",
    note: "PDF 11개 · 모바일 화면 기준",
    url: "https://www.onbid.co.kr/op/btbdguid/utlzdescdata/utlzdescdata/UtlzDescDataInqController/mvmnUtlzDescDataDtl.do?gnrBtbdLstNo=102893",
  },
  {
    title: "차세대 온비드 퀵가이드(입찰자용)",
    note: "PDF 1개",
    url: "https://www.onbid.co.kr/op/btbdguid/utlzdescdata/utlzdescdata/UtlzDescDataInqController/mvmnUtlzDescDataDtl.do?gnrBtbdLstNo=102829",
  },
  {
    title: "빠른입찰 이용가이드",
    note: "PDF 1개",
    url: "https://www.onbid.co.kr/op/btbdguid/utlzdescdata/utlzdescdata/UtlzDescDataInqController/mvmnUtlzDescDataDtl.do?gnrBtbdLstNo=110214",
  },
  {
    title: "[일반회원] 간편인증 매뉴얼",
    note: "PDF 1개",
    url: "https://www.onbid.co.kr/op/btbdguid/utlzdescdata/utlzdescdata/UtlzDescDataInqController/mvmnUtlzDescDataDtl.do?gnrBtbdLstNo=102819",
  },
  {
    title: "온비드 공식 유튜브 채널",
    note: "이용 안내 영상 모음",
    url: "https://www.youtube.com/channel/UCkzxJZSiJThYL34ajiCyVJQ/featured",
  },
  {
    title: "온비드 이용 안내 재생목록 (1)",
    note: "유튜브 재생목록",
    url: "https://www.youtube.com/watch?v=ZNlKLr9ViAE&list=PLIFzprTkgcSpFf-QpLb-CQIQ26ywfvN5h",
  },
  {
    title: "온비드 이용 안내 재생목록 (2)",
    note: "유튜브 재생목록",
    url: "https://www.youtube.com/watch?v=oC6xBZMImuA&list=PLIFzprTkgcSpcXUE-4OBqQE0Tr69n6JgW",
  },
];

function renderReferenceLinks() {
  const host = byId("reference-list");
  if (!host) return;
  host.innerHTML = `${REFERENCE_LINKS.map((item) =>
    infoRow({ title: item.title, text: item.note, action: { href: item.url, label: "열기 ↗" } }),
  ).join("")}<p class="block-note">온비드가 제공하는 원문 자료입니다. 내용은 온비드 화면에서 직접 확인하십시오.</p>`;
}

function renderGlossary() {
  const host = byId("glossary-list");
  if (!host) return;
  const entries = Array.isArray(sampleNotice.glossary) ? sampleNotice.glossary : [];
  // 경험 수준 질문 A에서 "처음이에요"면 용어 사전 안내를 조금 더 적극적으로 보여준다
  // (ux-audit §⑵). 목록을 바꾸지 않고 안내문 한 줄만 추가하는 표시 전환이다.
  const beginnerNote = isExperienceBeginner()
    ? `<p class="block-note">처음이시면 모르는 용어가 나올 때 이 탭에서 먼저 찾아보세요.</p>`
    : "";
  // 서버는 두 묶음을 준다 — basic(이 공고 유형이면 보여 주는 절차 용어 · server.py GLOSSARY_TAB_TERMS ∩ ONBID_GUIDE_TERMS)과
  // match(공고 표기에 든 낱말을 사전에서 찾은 것). group 이 없는 옛 응답과 E2E 픽스처는 match 로 본다.
  // 2026-10-19 커뮤니티 조사: 초보자 질문의 첫째 갈래가 「용어 뜻을 모른다」였는데 이 탭은 공고명에 든
  // 낱말만 보여 줘서 거의 비어 있었다.
  const basic = entries.filter((entry) => entry.group === "basic");
  const matched = entries.filter((entry) => entry.group !== "basic");
  const rowsHtml = (list) => list.map((entry) => infoRow({ title: entry.term, text: entry.meaning })).join("");
  // 「재산유형 확인」·「처분방식 확인」은 값이 아니라 지시어라 괄호 안에 넣지 않는다(리뷰 r1 #5 · r2 R2-2).
  // 읽힌 쪽만 괄호에 넣고, 둘 다 못 읽었으면 공통 용어라는 사실만 적는다.
  const knownParts = [sampleNotice.assetType, sampleNotice.dispositionLabel]
    .map((value) => String(value || ""))
    .filter((value) => value && !value.endsWith(" 확인"));
  const basicTitle = knownParts.length ? `이 공고 유형(${knownParts.join(" · ")})의 기본 용어` : "모든 공고에 공통인 기본 용어";
  // 기본 용어는 출처를 함께 보여 준다. 질문창과 같은 사전(server.py ONBID_GUIDE_TERMS)에서 왔다.
  const basicRowsHtml = basic
    .map((entry) =>
      infoRow({ cls: entry.source ? "has-source" : "", title: entry.term, text: entry.meaning, meta: entry.source ? `근거: ${entry.source}` : "" }),
    )
    .join("");
  const basicHtml = basic.length ? `<h4 class="info-group-title glossary-group-title">${basicTitle}</h4>${basicRowsHtml}` : "";
  const matchedHtml = matched.length
    ? `<h4 class="info-group-title glossary-group-title">공고 표기에 나온 용어</h4>${rowsHtml(matched)}`
    : "";
  host.innerHTML = entries.length
    ? `${beginnerNote}${basicHtml}${matchedHtml}<p class="block-note">화면의 재산유형·처분방식은 온비드 표기를 그대로 쓰고, 뜻만 여기에서 안내합니다. 뜻풀이의 근거는 온비드 이용안내·입찰참가자 준수규칙·FAQ 이고, 공고마다 예외가 있을 수 있으니 공고 원문이 우선입니다.</p>`
    : `<p class="block-note">이 공고의 표기에 해당하는 용어 안내가 없습니다. 온비드 원문 표기를 그대로 확인하십시오.</p>`;
}

function countdownBadge() {
  const countdown = sampleNotice.countdown;
  if (!countdown?.label) return "";
  // 머리표 뜻은 셋이다 — 주의(warn) · 정보(neutral) · 충족(safe). 긴급이 아닌 마감 D-n 은 정보다(V2).
  const type = countdown.state === "urgent" ? "urgent" : countdown.state === "closed" ? "warn" : "neutral";
  return `${badge(countdown.label, type)} <span class="small-text">${countdown.deadline} 마감 · 알림 발송은 하지 않습니다</span>`;
}

function publicDataLabel(publicData) {
  const labels = {
    connected: "공공데이터 보조",
    partial: "원문+데이터 보조",
    no_data: "원문 분석",
    pending: "원문 분석",
    failed: "원문 분석",
    missing_key: "원문 분석",
    skipped: "원문 분석",
  };
  return labels[publicData?.status] || "원문 분석";
}

function publicDataSourceNote(publicData) {
  if (!publicData) {
    return "";
  }
  if (publicData.status === "connected" || publicData.status === "partial") {
    return `보조 데이터: ${publicDataLabel(publicData)} - ${publicData.message}`;
  }
  return "보조 데이터: 현재 화면은 온비드 공개 원문에서 추출한 값으로 정리했습니다.";
}

function renderActionState() {
  const ready = isAnalysisReady();
  const isCaution = ready && getFitMessage().type === "mismatch";
  const prepareButton = byId("prepare");
  if (prepareButton) {
    prepareButton.disabled = !ready;
    prepareButton.className = !ready ? "secondary" : isCaution ? "primary is-caution" : "primary";
    prepareButton.textContent = "다음";
  }
  const analyzeButton = byId("analyze");
  if (analyzeButton && !analyzeButton.disabled) {
    analyzeButton.textContent = ready ? "다시 분석하기" : "분석하기";
    analyzeButton.className = "primary";
  }
}

function getSelectedUserType() {
  return byId("user-type").value;
}

// 전체 진행률 스테퍼(visual-audit §⑴). 기존 .pipeline li.done/.active 배색을 재사용하고,
// 색만으로 상태를 구분하지 않도록 아이콘(aria-hidden)과 텍스트 라벨을 함께 둔다(§⑷ 접근성).
function renderPrepStageStepper(stageStatus, activeNum = null) {
  const items = stageStatus
    .map((stage) => {
      // locked를 done보다 먼저 본다 — "되돌리기" 후 이전 단계를 다시 막으면, 이 단계의
      // task 체크값은 보존돼도(done=true) 접근은 다시 잠긴다(ux-audit §⑴ "되돌리기 처리").
      // 그 상태를 "완료"로 보여주면 잠금을 숨기는 것이 된다.
      // notYet 은 done 보다 먼저 본다 — 항목이 0개인 4단계는 파생값에서 done 을 눌러 두지만,
      // 표시 쪽에서도 순서를 지켜 「완료」가 뜰 경로를 남기지 않는다(P0-1).
      const icon = getStageIcon(stage);
      const label = stage.locked
        ? `잠김, 2-${stage.num - 1} 단계를 마치면 열립니다`
        : stage.notYet
          ? "아직 할 일이 아닙니다"
          : stage.done
            ? "완료"
            : "진행중";
      const cls = stage.locked ? "is-locked" : stage.notYet ? "is-not-yet" : stage.done ? "is-done" : "is-active";
      // 화면 아래에 붙는 작은 단계 표시다. 단계마다 눌러서 그 페이지로 간다. 보이는 글은 번호·아이콘·제목뿐이고,
      // 상태 문장(잠김 이유 등)은 화면 읽기 프로그램과 툴팁으로만 준다(2026-10-19 · 더 작고 간략하게).
      const viewing = stage.num === activeNum;
      return `<li class="${cls}${viewing ? " is-viewing" : ""}" role="listitem">
        <button type="button" class="mini-step" data-board-stage="${stage.num}" title="${label}"${viewing ? ` aria-current="step"` : ""}>
          <span class="mini-step-num">2-${stage.num}</span>
          ${icon ? `<span class="prep-stage-icon" aria-hidden="true">${icon}</span>` : ""}
          <span class="mini-step-label">${stage.title}</span>
          <span class="sr-only">${label}</span>
        </button>
      </li>`;
    })
    .join("");
  return `<ol class="prep-stage-stepper mini-stepper" role="list" aria-label="준비 단계">${items}</ol>`;
}

// 위·아래 단계 표시가 같은 아이콘을 쓴다. 진행 중은 아이콘이 없다(▶ 는 「접힘」 표시와 같은 모양이라 쓰지 않는다).
// 아이콘은 aria-hidden 이고 상태 문구는 sr-only · title 에 따로 있다. 색으로만 상태를 구분하지 않게 한다(V5 · I8).
function getStageIcon(stage) {
  return stage.locked ? "🔒" : stage.notYet ? "⏳" : stage.done ? "✓" : "";
}

// 준비 보드 위쪽 단계 표시. 공고 가져오기(1-1~1-3)와 같은 버튼 모양이고, 누르면 그 단계 페이지로 간다.
// 잠긴 단계도 눌러서 미리 볼 수 있다(아래 고정 단계 표시와 같은 동작). 상태는 버튼 툴팁과 화면 읽기용 글로 준다.
function renderBoardTopStepper(stageStatus, activeNum) {
  return `<ol class="mini-stepper wizard-progress" aria-label="준비 보드 단계">${stageStatus
    .map((stage) => {
      const viewing = stage.num === activeNum;
      const state = stage.locked ? "잠김 · 앞 단계를 마치면 열립니다" : stage.notYet ? "낙찰 뒤에 할 일" : stage.done ? "완료" : "진행 중";
      const cls = [viewing ? "is-active" : "", !viewing && stage.done ? "is-done" : "", stage.locked ? "is-locked" : ""]
        .filter(Boolean)
        .join(" ");
      return `<li><button type="button" class="mini-step ${cls}" data-board-stage="${stage.num}" title="${state}"${viewing ? ` aria-current="step"` : ""}>
        <span class="mini-step-num">2-${stage.num}</span>${getStageIcon(stage) ? `<span class="prep-stage-icon" aria-hidden="true">${getStageIcon(stage)}</span>` : ""}<span class="mini-step-label">${stage.title}</span><span class="sr-only"> · ${state}</span>
      </button></li>`;
    })
    .join("")}</ol>`;
}

// 처음 보여 줄 단계는 아직 끝나지 않았고 열려 있는 첫 단계다. 그런 단계가 없으면 열려 있는 마지막 단계다.
function getBoardStage(stageStatus) {
  const chosen = stageStatus.find((stage) => stage.num === boardStageNum);
  if (chosen) return chosen;
  return (
    stageStatus.find((stage) => !stage.done && !stage.locked && !stage.notYet) ||
    [...stageStatus].reverse().find((stage) => !stage.locked) ||
    stageStatus[0]
  );
}

function renderBoardPageNav(stageStatus, active) {
  const prev = stageStatus.find((stage) => stage.num === active.num - 1);
  const next = stageStatus.find((stage) => stage.num === active.num + 1);
  // 이 단계를 마쳤으면 다음 단계 버튼을 주 버튼으로 바꿔 다음 할 일을 알려 준다.
  return `${
    prev ? `<button type="button" class="secondary" data-board-stage="${prev.num}">← 2-${prev.num} ${prev.title}</button>` : "<span></span>"
  }${
    next
      ? `<button type="button" class="${active.done ? "primary" : "secondary"}" data-board-stage="${next.num}">2-${next.num} ${next.title} →</button>`
      : // 마지막 단계(2-4)에서 흐름을 닫는 행동이다. 「새 물건 분석으로」와 같은 동작을 쓴다(U12).
        `<button type="button" class="secondary" data-new-analysis>새 물건 분석</button>`
  }`;
}

// task-list 안의 단계 그룹 헤딩(visual-audit §⑵). 잠긴 단계는 체크 행만 잠그고
// 헤딩 자체는 항상 보인다 — "1단계를 마치면 열립니다" 문구가 1차 전달 수단이고 자물쇠는 보조.
function renderStageHeading(stage) {
  const lockMsgId = `stage-lock-msg-${stage.num}`;
  // locked를 done보다 먼저 본다 — renderPrepStageStepper()와 같은 이유(되돌리기 후
  // 재잠김된 단계를 "완료"로 잘못 보여주지 않는다).
  if (stage.locked) {
    return `<h4 class="stage-group-heading is-locked">
      <span aria-hidden="true">🔒</span>
      <span>2-${stage.num} ${stage.title}</span>
      <span id="${lockMsgId}" class="small-text">2-${stage.num - 1} 단계를 마치면 열립니다</span>
    </h4>`;
  }
  // notYet 을 done 보다 먼저 본다 — 4단계는 taskIds 가 비어 있어 예전 판정이라면 공집합 완료로
  // 「✅ 완료」가 떴다. 낙찰도 되지 않은 단계를 완료로 적는 것은 허위 완료 표시다(P0-1).
  // 「3단계를 마치면 열립니다」 문구도 쓰지 않는다 — 3단계를 마쳐도 낙찰되지 않으면 할 일이 아니다.
  if (stage.notYet) {
    return `<h4 class="stage-group-heading is-not-yet">
      <span aria-hidden="true">⏳</span>
      <span>2-${stage.num} ${stage.title}</span>
      ${badge("아직 할 일이 아닙니다", "neutral")}
    </h4>`;
  }
  if (stage.done) {
    return `<h4 class="stage-group-heading is-done">
      <span aria-hidden="true">✓</span>
      <span>2-${stage.num} ${stage.title}</span>
      ${badge("완료", "safe")}
    </h4>`;
  }
  // 진행 중인 단계는 머리를 그리지 않는다. 페이지 제목이 이미 단계 이름이고, ▶ 가 바로 아래 「▶ 자세히」(닫힌 접기)와
  // 같은 모양이라 「접혀 있다」로 읽혔다(V4 · V5). 잠김 · 낙찰 후 · 완료처럼 할 말이 있을 때만 머리를 둔다.
  return "";
}

// 4단계(낙찰 후 준비) 블록. 머리 안내는 과설명이 아니라 단계 판정 오분류의 안전망이다 —
// 서류의 단계 판정은 server.py 의 resolve_doc_stage() 다(조항 표제 사전 → 문장 결정적
// 문구 → 미분류). 입찰 전 서류가 이 블록으로 잘못 분류되면 사용자가 그 서류를 아예 보지
// 못해 입찰이 무효가 된다. 그래서 2단계 목록도 함께 확인하라고 적는다(ux-design-review P0-2 대책 ⑵).
//
// 체크박스는 잠그지 않는다 — 미리 준비하는 사용자를 막을 이유가 없다. 다만 이 서류는
// getDocSummary() 분모에 들어가지 않으므로 2단계 진행률과 단계 잠금에는 영향이 없다.
// 낙찰 뒤 절차 순서와 보증금 귀속을 재산유형·처분방식별로 한 줄씩 적는다. 온비드 공통 규칙이 정하는
// 것은 압류·국유·수탁 셋뿐이고, 공유·기타일반 같은 이용기관 물건은 공고문이 정한다(온비드 이용안내
// 「낙찰절차 안내」 기타 탭 · 이용기관 입찰참가자 준수규칙 제13조). 일괄 문구는 틀리므로 유형마다 갈랐고,
// 읽지 못한 유형은 공통 안내만 둔다. 근거 정리본: team-reports/2026-10-19-onbid-journey-conformance/
// researcher-onbid-journey.md 2-C·2-D 절. 커뮤니티 조사 1-4(「그 이후의 절차가 어떻게 되는지」 · 「낙찰을
// 포기하려 합니다. 보증금을 돌려받을 수 있는지요」)가 이 자리의 이유다.
function postAwardProcessNote() {
  const assetType = String(sampleNotice.assetType || "");
  const disposition = String(sampleNotice.dispositionLabel || "");
  const label = `${assetType || "재산유형 확인"} · ${disposition || "처분방식 확인"}`;
  const isLease = isLeaseOnlyDisposition();
  const isSale = /매각|공매/.test(disposition);
  if (assetType.includes("압류재산")) {
    return {
      label,
      order:
        "개찰 → 매각결정(개찰일로부터 7일 이내) → 잔대금 납부(매각결정기일로부터 낙찰가 3,000만 원 이상 30일 · 미만 7일) → 소유권이전 서류를 캠코 관할 부점에 제출(등기촉탁은 캠코가 합니다). 별도 매매계약 단계는 없습니다.",
      deposit: "잔대금을 기한 안에 내지 않으면 매각결정이 취소되고 입찰보증금은 돌려받지 못합니다.",
      source: "압류재산 공매공고문 · 압류재산 입찰참가자 준수규칙 · 온비드 FAQ(매각결정기일 · 소유권이전절차)",
    };
  }
  if (assetType.includes("국유재산") && isLease) {
    return {
      label,
      order: "낙찰 → 대부료 잔금 납부(낙찰일로부터 5영업일 이내) → 대부계약 체결(점유자가 있으면 명도집행 완료 뒤).",
      deposit: "기간 안에 계약을 맺지 않으면 낙찰이 무효가 되고 입찰보증금은 국고에 귀속됩니다.",
      source: "온비드 이용안내 「낙찰절차 안내」 국유재산 대부 · 국유재산 입찰참가자 준수규칙 제15조",
    };
  }
  if (assetType.includes("국유재산") && isSale) {
    return {
      label,
      order: "낙찰 → 매매계약 체결(낙찰일로부터 5영업일) → 잔대금 납부(계약일로부터 60일) → 매수자가 직접 소유권이전등기.",
      deposit: "계약을 맺지 않거나 잔대금을 내지 않으면 매매계약이 해제되고 입찰보증금은 국고에 귀속됩니다.",
      source: "온비드 이용안내 「낙찰절차 안내」 국유재산 매각 · 국유재산 입찰참가자 준수규칙 제15조·제16조",
    };
  }
  if (assetType.includes("수탁재산") && !isLease) {
    return {
      label,
      order: "낙찰 → 매매계약 체결 → 중도금·잔대금 납부 → 위임기관에서 이전서류를 받아 매수자가 등기 신청. 계약 기한은 안내문·규칙·공고문의 표기가 서로 달라(5일 · 5영업일) 어느 쪽이 적용되는지는 공고 원문과 담당기관에서 확인합니다.",
      deposit: "계약을 맺지 않으면 입찰보증금은 매도자에게 귀속됩니다.",
      source: "온비드 이용안내 「낙찰절차 안내」 수탁재산 · 수탁재산 입찰참가자 준수규칙 제11조",
    };
  }
  if (assetType.includes("공유재산") || assetType.includes("기타일반재산")) {
    return {
      label,
      order: "낙찰 → 계약 체결 → 대금(또는 사용료) 납부 → 소유권이전(매각) 또는 사용 개시(임대). 계약 기한·대금 기한·서류는 모두 공고문이 정합니다.",
      deposit: "계약을 맺지 않을 때 입찰보증금을 어떻게 처리하는지도 공고문이 정합니다. 공고기관 귀속으로 적은 공고가 있습니다.",
      source: "온비드 이용안내 「낙찰절차 안내」 기타 탭 · 이용기관 입찰참가자 준수규칙 제13조",
    };
  }
  return {
    label,
    // 재산유형을 못 읽은 공고뿐 아니라 파산자산·수탁 임대처럼 온비드 공통 규칙이 절차를 정하지 않는
    // 조합도 이 분기로 온다. 그래서 「읽지 못해」라고 쓰지 않는다(리뷰 r1 #2).
    order: "이 재산유형·처분방식 조합의 낙찰 뒤 절차는 공고 원문이 정하므로 공통 안내만 둡니다. 계약·대금·이전 절차와 기한은 재산유형마다 다릅니다.",
    deposit: "기한을 지키지 못하면 입찰보증금을 돌려받지 못할 수 있습니다. 귀속처는 재산유형과 공고마다 다릅니다.",
    source: "온비드 이용안내 「낙찰절차 안내」",
  };
}

function renderPostAwardPanel() {
  const groups = getPostAwardDocGroups();
  const docState = getDocState();
  const summary = getPostAwardDocSummary();
  // 재산유형에 해당하지 않는 묶음은 접어 두고(open=false) 그 사실을 적는다. 숨기지 않는다 —
  // 재산유형 추출이 틀렸을 때 사용자가 그 묶음의 존재조차 모르고 지나가면, 매각결정기일처럼
  // 놓치면 낙찰이 취소되는 기한을 통째로 잃는다.
  const groupsHtml = groups
    .map((group) => {
      const applicable = !group.notApplicable;
      const reasonText =
        group.notApplicableReason === "disposition"
          ? `이 묶음은 소유권을 넘겨받는 매각 절차의 서류여서, 지금 공고의 처분방식(${sampleNotice.dispositionLabel})에는 해당하지 않을 수 있습니다.`
          : `이 묶음은 압류재산 공매공고문에 근거한 것이어서, 지금 공고의 재산유형(${sampleNotice.assetType})에는 해당하지 않을 수 있습니다.`;
      const noteHtml = applicable
        ? ""
        : `<p class="post-award-not-applicable">${reasonText} 접어 두었지만 지웠다는 뜻은 아닙니다. 해당 여부는 공고 원문과 담당기관에서 확인하십시오.</p>`;
      // 안내는 자기 묶음 «뒤»에 둔다. 앞에 두면 바로 위 묶음의 설명처럼 읽힌다(2026-10-19 여정 점검).
      return renderDocGroup(group, docState, false, applicable, "") + noteHtml;
    })
    .join("");
  const process = postAwardProcessNote();
  return `<section class="block post-award-panel">
    <h3 class="block-title">낙찰 뒤 절차 <span class="block-meta">${process.label}</span></h3>
    <p class="block-lead">낙찰된 뒤에 할 일입니다. 지금 당장 준비할 필요는 없지만, 기한을 놓치면 낙찰이 취소될 수 있는 항목이 있어 미리 열어 둡니다.</p>
    <div class="info-list">
      <div class="info-row post-award-caution">
        <div class="info-row-head">${badge("함께 확인", "warn")}<strong class="info-row-title">입찰 전에 내야 하는 서류가 여기 섞여 있을 수 있습니다. 2-2 입찰 전 준비 목록도 함께 확인하십시오.</strong></div>
      </div>
      <div class="info-row post-award-process">
        <div class="info-row-head">${badge("순서", "neutral")}<strong class="info-row-title">낙찰 뒤 절차 순서</strong></div>
        <p class="info-row-text">${process.order}</p>
        <p class="info-row-text">${process.deposit}</p>
        <p class="info-row-meta">근거: ${process.source}. 기한과 서류는 공고 원문과 담당기관 확인이 우선입니다.</p>
      </div>
    </div>
    <p class="block-note">${DOC_DUE_CAUTION}</p>
    ${
      summary.totalCount
        ? `<div class="doc-progress">
          <strong>${summary.doneCount}/${summary.totalCount}개 서류 확인</strong>
          <span class="progress" role="progressbar" aria-label="낙찰 후 서류 확인 진행률" aria-valuemin="0" aria-valuemax="${summary.totalCount}" aria-valuenow="${summary.doneCount}"><i style="width:${summary.percent}%"></i></span>
          <p class="small-text">이 진행률은 2-2 입찰 전 준비의 서류 진행률과 따로 계산합니다. 여기를 체크해도 입찰 단계 잠금은 열리지 않습니다.</p>
        </div>`
        : groups.length
          ? `<p class="small-text post-award-none-applicable">이 공고 유형에 해당하는 낙찰 후 서류를 찾지 못했습니다. 아래 접힌 묶음은 다른 재산유형·처분방식 기준입니다.</p>`
          : `<p class="small-text">이 공고에서 낙찰 후 서류를 찾지 못했습니다. 공고 원문과 첨부파일을 확인하십시오.</p>`
    }
    ${groupsHtml}
  </section>`;
}

// 할 일 카드 1개. locked이면 체크 행(.task-row)에만 흐림 처리를 걸고, <details>(자세히)·
// 원문 링크·문의 문구는 잠금과 무관하게 항상 정상 표시한다(ux-audit §⑴ "잠긴 단계의 표시").
function renderTaskItem(task, taskSummary, aiAssignments, fit, docChecklistHtml, locked) {
  const aiMatch = aiAssignments.get(task.id);
  const aiPrecheck = getAiPrecheckForTask(task, fit);
  const isFoundValue = task.action && task.action !== NOTICE_VALUE_FALLBACK;
  const done = taskSummary.state[task.id];
  const dueTone = done ? "safe" : task.due === NOTICE_VALUE_FALLBACK ? "neutral" : "warn";
  // 자세히 블록은 기본 닫힘이다. 「안내 수준」 버튼으로 펼쳐도 완료된 카드는 닫아 둔다(visual-audit §⑵).
  // 경험 수준 질문 A의 응답과는 묶지 않는다 — 「처음이에요」여도 기본은 접힘이다(2026-10-19).
  const detailsOpen = !done && guideDetailed;
  const stageNum = getTaskStageNum(task.id);
  const lockMsgId = stageNum !== null ? `stage-lock-msg-${stageNum}` : "";
  return `<article class="task-item ${done ? "is-done" : ""} ${aiMatch ? "has-ai-nudge" : ""}">
        <div class="task-row ${locked ? "is-locked-row" : ""}">
          <label class="task-check">
            <input type="checkbox" data-task-id="${task.id}" ${done ? "checked" : ""}${
              locked ? ` disabled aria-disabled="true"${lockMsgId ? ` aria-describedby="${lockMsgId}"` : ""}` : ""
            }>
            <span>
              <strong>${task.title}</strong>
            </span>
          </label>
          <span class="task-badges">
            ${(aiMatch || task.needsCheck) && !done ? badge("확인 필요", "warn") : ""}
            ${badge(done ? "완료" : task.due, dueTone)}
          </span>
        </div>
        ${
          task.action
            ? `<div class="task-action-value ${isFoundValue ? "is-extracted" : "is-fallback"}">
          <span class="task-action-value-label">${task.valueLabel || "공고 원문에서 확인된 값"}</span>
          <strong>${task.action}</strong>
        </div>`
            : ""
        }
        ${
          aiPrecheck
            ? `<div class="task-precheck">
          <span class="task-precheck-label">규칙 기반 사전 확인</span>
          <p>${aiPrecheck.precheck}</p>
        </div>`
            : ""
        }
        ${
          task.id === "documents" && docChecklistHtml
            ? `<details id="doc-checklist-details" ${docChecklistOpen ? "open" : ""}>
          <summary>서류 준비 체크리스트 (${getDocSummary().doneCount}/${getDocSummary().totalCount})</summary>
          <div id="doc-checklist" class="doc-checklist">${docChecklistHtml}</div>
        </details>`
            : ""
        }
        <details class="task-detail" ${detailsOpen ? "open" : ""}>
          <summary>자세히</summary>
          <dl class="detail-grid">
            ${aiMatch?.check?.reason ? `<dt>${aiMatch.check.title}</dt><dd>${aiMatch.check.reason}</dd>` : ""}
            ${aiMatch?.check?.action ? `<dt>먼저 할 일</dt><dd>${aiMatch.check.action}</dd>` : ""}
            <dt>문의 문장</dt><dd>${task.question}</dd>
            <dt>상세 설명</dt><dd>${task.detail}</dd>
            <dt>근거</dt><dd>${task.source} · <a class="text-action" href="${task.url}" target="_blank" rel="noreferrer">${task.cta}</a></dd>
          </dl>
        </details>
      </article>`;
}

// 분석 전 빈 보드에서는 쓸 수 없는 조작(간단히·자세히 · 초기화 · 새 물건 분석 · 공고 요약·자료 · 단계 표시)을 숨긴다(U3).
function setBoardChromeHidden(hidden) {
  document.querySelector("#view-report .section-title [data-new-analysis]")?.toggleAttribute("hidden", hidden);
  document.querySelector("#view-report .board-page-toolbar")?.toggleAttribute("hidden", hidden);
  byId("guide-level-hint")?.toggleAttribute("hidden", hidden);
  byId("board-top-stepper")?.toggleAttribute("hidden", hidden);
  byId("board-status")?.toggleAttribute("hidden", hidden);
  if (hidden) byId("board-stage1-extra").hidden = true;
}

function focusReportTitle() {
  const title = byId("report-title");
  title.setAttribute("tabindex", "-1");
  title.focus({ preventScroll: true });
}

function renderReport() {
  const userType = getSelectedUserType();
  const fit = getFitMessage();
  const publicData = sampleNotice.analysisMeta?.publicData;
  const inputWarning = getInputWarning();
  const staleInputWarning = !inputWarning && !analysisError && !isAnalyzedInputCurrent()
    ? { title: "아직 이 URL을 분석하지 않았습니다", body: "입력 URL이 바뀌었지만 아직 공고 분석을 실행하지 않았습니다." }
    : null;
  const blockingMessage = inputWarning || (analysisError ? { title: "공고 분석에 실패했습니다", body: analysisError } : null) || staleInputWarning;
  const taskSummary = getTaskSummary();
  const aiAssignments = getAiTaskAssignments(taskSummary.tasks);
  // 한 번도 분석하지 않은 상태(처음 들어옴 · 샘플만 불러옴 · 「새 물건 분석으로」 뒤)는 실패도 URL 변경도 아니다.
  // 「분석 실패」·「입력 URL이 바뀌었지만」을 쓰면 아무것도 안 한 사람이 「뭔가 실패했다」로 읽는다(U3 · I4).
  const neverAnalyzed = analyzedInputValue === "" && !analysisError;
  setBoardChromeHidden(neverAnalyzed);

  if (neverAnalyzed) {
    byId("board-top-stepper").innerHTML = "";
    byId("report-hero").innerHTML = "";
    byId("board-status").innerHTML = "";
    byId("board-coach").innerHTML = "";
    byId("board-page-nav").innerHTML = "";
    byId("board-step-label").textContent = "Step 2";
    byId("report-title").textContent = "내 준비 보드";
    byId("task-list").innerHTML = `
      <section class="block board-empty">
        <h3 class="block-title">아직 가져온 공고가 없습니다</h3>
        <p class="block-lead">공고 가져오기에서 온비드 URL을 분석하면 이 자리에 공고별 준비 단계와 할 일이 생깁니다.</p>
        <div class="actions"><button type="button" class="primary" data-goto-input>공고 가져오기로</button></div>
      </section>
    `;
    return;
  }

  if (blockingMessage) {
    const sourceLink = byId("source-url-link");
    if (sourceLink) {
      sourceLink.href = sampleNotice.sourceUrl;
    }
    byId("board-top-stepper").innerHTML = "";
    byId("report-hero").innerHTML = `
      <h3>${blockingMessage.title}</h3>
      <p>${badge("분석 필요", "warn")} <span class="small-text">원문 우선</span></p>
      <p>${escapeHtml(blockingMessage.body)}</p>
      <p class="small-text">온비드 공고/물건 URL을 입력하고 공고 분석을 다시 실행하세요.</p>
    `;

    byId("board-status").innerHTML = [
      ["다음 액션", "온비드 URL 입력 후 공고 분석"],
      ["진행률", "분석 대기"],
    ]
      .map(
        ([label, value]) => `<div class="status-card">
          <b>${label}</b>
          <strong>${value}</strong>
        </div>`,
      )
      .join("");

    byId("task-list").innerHTML = `
      <article class="task-item">
        <strong>아직 분석된 온비드 공고가 없습니다.</strong>
        <p class="small-text">분석이 성공하면 이 영역이 공고별 준비 체크리스트로 바뀝니다.</p>
      </article>
    `;
    byId("quick-facts").innerHTML = [
      // 「분석 실패」는 실제로 실패했을 때만 쓴다. URL 만 바뀐 경우는 실패가 아니다(U3).
      ["입력 상태", inputWarning ? "URL 확인 필요" : analysisError ? "분석 실패" : "URL 변경 뒤 분석 전"],
      ["실제 분석", "미수행"],
      ["다음 단계", "온비드 URL 재입력"],
      ["안전 경계", "샘플 결과로 대체 표시하지 않음"],
    ]
      .map(
        ([label, value]) => `<div class="fact-row">
          <span>${label}</span>
          <strong>${value}</strong>
        </div>`,
      )
      .join("");
    byId("deadline-cost-list").innerHTML = "";
    byId("source-notes").innerHTML = "";
    byId("board-coach").innerHTML = "";
    byId("attachment-list").innerHTML = "";
    byId("glossary-list").innerHTML = "";
    byId("board-step-label").textContent = "Step 2";
    byId("report-title").textContent = "내 준비 보드";
    byId("board-stage1-extra").hidden = false;
    byId("board-page-nav").innerHTML = "";
    renderGuideLevel();
    return;
  }

  const sourceLink = byId("source-url-link");
  if (sourceLink) {
    sourceLink.href = sampleNotice.sourceUrl;
  }

  byId("report-hero").innerHTML = `
    <h3>${sampleNotice.title}</h3>
    <p class="hero-meta">${badge(fit.type === "mismatch" ? "목적 불일치" : "목적 확인", fit.type === "match" ? "safe" : "warn")} ${countdownBadge()}
      <span class="small-text">${sampleNotice.assetType} ${sampleNotice.dispositionLabel} · ${userTypeLabels[userType]}${
        publicData ? ` · ${publicDataLabel(publicData)}` : ""
      }</span></p>
    ${fit.type === "match" ? "" : `<p>${escapeHtml(fit.body)}</p>`}
  `;

  const stageStatus = getPrepStageStatus();
  const documentsStageNum = getTaskStageNum("documents");
  const documentsStageLocked = stageStatus.find((stage) => stage.num === documentsStageNum)?.locked || false;
  const docChecklistHtml = renderDocChecklist(documentsStageLocked);
  renderAttachments();
  renderGlossary();
  renderGuideLevel();
  const activeStage = getBoardStage(stageStatus);
  renderBoardCoachKeepingState(sampleNotice.aiCoach, activeStage.num);
  // 준비 보드 하위 페이지는 공고 가져오기와 같은 「Step 2-N」 표기를 쓰고, 한 번에 한 단계만 보인다.
  byId("board-step-label").textContent = `Step 2-${activeStage.num}`;
  byId("report-title").textContent = activeStage.title;
  // 공고 요약과 공고 자료 탭은 2-1(공고 확인) 페이지에만 둔다.
  byId("board-stage1-extra").hidden = activeStage.num !== 1;
  byId("board-page-nav").innerHTML = renderBoardPageNav(stageStatus, activeStage);
  byId("board-top-stepper").innerHTML = renderBoardTopStepper(stageStatus, activeStage.num);
  byId("board-status").innerHTML = `
    ${renderPrepStageStepper(stageStatus, activeStage.num)}
    <div class="board-progress">
      <b>진행률</b>
      <strong>${formatProgress(taskSummary)}</strong>
      <span class="progress" role="progressbar" aria-label="준비 진행률" aria-valuemin="0" aria-valuemax="${taskSummary.totalCount}" aria-valuenow="${taskSummary.doneCount}"><i style="width:${taskSummary.percent}%"></i></span>
    </div>
  `;

  // 단계 그룹 헤딩 → 그 단계 소속 task들 순서로 그린다. taskSummary.tasks는 이미
  // getApplicableTasks()가 단계순으로 정렬해 뒀다(§⑴). 알 수 없는 id(테스트 픽스처 외
  // 레거시 데이터)는 헤딩 없이 뒤에 붙인다 — 기존 "단계 밖" 동작을 보존한다.
  const tasksByStage = new Map();
  const leftoverTasks = [];
  taskSummary.tasks.forEach((task) => {
    const stageNum = getTaskStageNum(task.id);
    if (stageNum === null) {
      leftoverTasks.push(task);
      return;
    }
    if (!tasksByStage.has(stageNum)) tasksByStage.set(stageNum, []);
    tasksByStage.get(stageNum).push(task);
  });

  // 1단계(공고 확인)에서만 보는 만료·불일치 경고 — 둘 다 아니면 null이라 배너를 만들지
  // 않는다. phase2 범위: 공고 확인 단계 내부 로직만, 다른 단계에는 영향이 없다.
  const stage1Warning = getStage1RestartWarning(fit);

  const groupedTaskHtml = stageStatus
    .map((stage) => {
      const stageTasks = tasksByStage.get(stage.num) || [];
      // 4단계는 build_tasks() 가 만드는 task 가 없고 서류 블록만 담는다. 그래서 「항목 0개면
      // 그리지 않는다」는 조기 반환을 그대로 두면 4단계가 통째로 사라지고, 상단 스테퍼에만
      // 남아 「목록에는 없는 단계」가 된다(P0-1의 다른 절반).
      const postAwardHtml = stage.num === 4 ? renderPostAwardPanel() : "";
      // 단계마다 페이지가 하나라, 할 일이 없는 단계도 빈 페이지 대신 그 사실을 적는다.
      // 단계 밖 task(알 수 없는 id)는 2-1 페이지 끝에 붙인다.
      const leftoverHtml =
        stage.num === 1
          ? leftoverTasks.map((task) => renderTaskItem(task, taskSummary, aiAssignments, fit, docChecklistHtml, false)).join("")
          : "";
      const cardsHtml =
        stageTasks
          .map((task) => renderTaskItem(task, taskSummary, aiAssignments, fit, docChecklistHtml, stage.locked))
          .join("") + leftoverHtml;
      // 이 단계를 마쳤고 다음 단계가 있으면, 마지막 할 일 카드 바로 아래에 다음 단계로 가는 주 버튼을 둔다(U2).
      // 다음 버튼이 문서 끝(공고 요약·공고 자료 아래)에만 있어 「다 했는데 어디로?」에서 멈췄다.
      const nextStage = stageStatus.find((candidate) => candidate.num === stage.num + 1);
      const stageDoneHtml =
        stage.done && !stage.locked && nextStage && stageTasks.length
          ? `<div class="info-list stage-done-next">
          <div class="info-row">
            <div class="info-row-head">${badge("완료", "safe")}<strong class="info-row-title">2-${stage.num}을 마쳤습니다</strong></div>
            <div class="actions"><button type="button" class="primary small-button" data-board-stage="${nextStage.num}">2-${nextStage.num} ${nextStage.title}로 →</button></div>
          </div>
        </div>`
          : "";
      const emptyHtml =
        !cardsHtml && !postAwardHtml
          ? `<p class="block-note">이 단계에 자동으로 만든 할 일이 없습니다. 공고 원문을 확인하십시오.</p>`
          : "";
      const restartWarningHtml = stage.num === 1 ? renderStage1RestartWarning(stage1Warning) : "";
      // 1단계에는 입찰 자격 조건을, 2단계 맨 위에는 입찰참가신청 필요 여부를 둔다. 둘 다
      // 공공데이터 getCltrBidInf2 응답에서만 오고, 값이 없으면 빈 문자열이라 그려지지 않는다.
      // 입찰참가신청은 cardsHtml 앞에 둬야 2단계 「맨 위」가 된다 — 서류 체크리스트보다
      // 먼저 보여야 하는 것은 「승인을 먼저 받아야 하는가」다.
      const bidLimitsHtml = stage.num === 1 ? renderBidLimitsPanel() : "";
      const bidApplyHtml = stage.num === 2 ? renderBidParticipationApplyPanel() : "";
      // 3단계(입찰 참여)의 정보 블록. 잠겨 있어도 보여준다(ux-audit §⑴ "잠긴 상태에서도 자세히·원문 링크는
      // 항상 보인다" 원칙과 동일). 이 단계 전용 질문창은 지웠다 — 아래 고정 AI 코치와 겹쳤다(2026-10-19 동원님 지시).
      // 대신 아래 코치가 이 단계의 자주 묻는 질문(입찰금액·취소·보증금·결과 확인)을 예시로 보인다.
      const bidParticipationHtml = stage.num === 3 ? renderBidParticipationInfo(taskSummary) : "";
      // 잠긴 단계는 기본으로 접는다 — 체크박스만 비활성화하고 카드 내용을 전부 펼쳐 두면
      // 아직 손댈 수 없는 두세 단계 분량이 한 화면에 그대로 쏟아져 "한 번에 너무 많다"는
      // 체감으로 이어진다(2026-10-11 사용자 지적). 눌러서 미리 볼 수 있는 길은 남긴다.
      const stageCls = stage.locked
        ? "is-locked"
        : stage.notYet
          ? "is-not-yet"
          : stage.done
            ? "is-done"
            : "is-active";
      // 지금 보는 단계만 보이고 나머지는 hidden 이다. 다른 단계의 체크 상태·잠금은 그대로 DOM 에 남는다.
      return `<section class="stage-group ${stageCls}" data-stage-num="${stage.num}"${stage.num === activeStage.num ? "" : " hidden"}>
        ${renderStageHeading(stage)}
        ${restartWarningHtml}
        ${bidLimitsHtml}
        ${bidApplyHtml}
        ${cardsHtml}
        ${stageDoneHtml}
        ${emptyHtml}
        ${bidParticipationHtml}
        ${postAwardHtml}
      </section>`;
    })
    .join("");

  byId("task-list").innerHTML = taskSummary.tasks.length
    ? groupedTaskHtml
    : `<article class="task-item">
        <strong>체크리스트를 자동 생성하지 못했습니다.</strong>
        <p class="small-text">온비드 원문을 열어 입찰기간, 제출서류, 가격/보증금, 담당기관을 먼저 확인하세요.</p>
        <div class="task-meta">
          <span class="small-text">원문 우선</span>
          <a class="text-action" href="${sampleNotice.sourceUrl}" target="_blank" rel="noreferrer">온비드 원문</a>
        </div>
      </article>`;

  // 공고 유형 · 입찰기간 · 최저입찰가격은 같은 2-1 화면의 할 일 카드 값과 1-3 핵심 정보에 이미 있다.
  // 한 화면에 입찰기간이 네 번 나와 진짜 확인할 것이 묻혔다(U10 ⑴). 다른 곳에 없는 칸만 남긴다.
  byId("quick-facts").innerHTML = [
    ["공고번호", sampleNotice.noticeId],
    ["공고기관", sampleNotice.agency],
    ["입찰방식", sampleNotice.bidMethod],
    // 공동입찰은 못 읽었으면 「원문 확인」이다. 「불가능」·「해당없음」으로 접거나 행을 숨기지 않는다 —
    // 숨기면 사용자가 「해당 없다」로 읽는다.
    ["공동입찰", sampleNotice.jointBidAllowed || "원문 확인"],
    // 명도책임은 압류재산 공고문에만 나온다(표본 3/23). 값이 없으면 행을 만들지 않는다 —
    // 「원문 확인」으로 두면 모든 공고에 없는 항목을 있다고 알린다.
    ...(sampleNotice.evictionResponsibility
      ? [["명도책임", `${sampleNotice.evictionResponsibility} 부담`]]
      : []),
  ]
    .map(([label, value, valueClass = ""]) => factCell(label, `<strong class="field-value ${valueClass}">${value}</strong>`))
    .join("");

  byId("deadline-cost-list").innerHTML = [
    // 입찰기간 알림 행은 뺀다. 마감 D-n 행과 할 일 카드가 같은 값을 말한다(U10 ⑵).
    ...sampleNotice.alerts.filter((item) => item.title !== "입찰기간").map((item) => ({ ...item, type: "알림" })),
    ...sampleNotice.costs.map((item) => ({ ...item, type: "비용" })),
  ]
    .map((item) => {
      // 「입찰기간」 알림만 원문 확인 필요/실제 값 구분을 표시한다 — 다른 알림·비용 항목의
      // value 는 이 대체 문구로 채워지지 않는다.
      const valueClass =
        item.title === "입찰기간" ? (item.value === NOTICE_VALUE_FALLBACK ? "is-fallback" : "is-extracted") : "";
      return infoRow({
        tag: item.type,
        title: `${item.title}: <span class="${valueClass}">${item.value}</span>`,
        text: item.note,
      });
    })
    .join("");

  // 「물어볼 문장」·「공고문 항목」 탭은 지웠다(2026-10-19 동원님 지시 · 특별히 정확한 정보를 주지 못했다).
  const sourceNotes = [
    `출처 URL: <a href="${sampleNotice.sourceUrl}" target="_blank" rel="noreferrer">온비드 공고 상세</a>`,
  ];
  if (publicData) {
    sourceNotes.push(publicDataSourceNote(publicData));
    if (publicData.services?.length) {
      const serviceSummary = publicData.services
        .map((service) => `${service.name} ${service.ok ? "OK" : "확인 필요"}`)
        .join(", ");
      sourceNotes.push(`보조 데이터 조회: ${serviceSummary}`);
    }
  }
  sourceNotes.push(
    "보조 데이터 값과 공고 원문이 다를 경우 공고 원문 및 담당기관 확인을 우선합니다.",
    "입찰 여부, 법률 판단, 권리관계 판단, 수익성 판단은 제공하지 않습니다.",
  );
  byId("source-notes").innerHTML = sourceNotes.map((note) => infoRow({ tag: "확인", tone: "neutral", text: note })).join("");
}

function renderWatchlist() {
  const hasBlockingMessage = Boolean(getInputWarning() || analysisError || !isAnalyzedInputCurrent());
  const summary = getTaskSummary();
  const recent = getRecentNotices();
  const favoriteIds = getFavoriteNoticeIds();
  const favoriteRecent = recent.filter((item) => favoriteIds.has(item.id));
  const favoriteKeys = new Set(favoriteRecent.map((item) => `${item.title || item.notice}|${item.type}`));

  const savedItems = [
    ...favoriteRecent.map((item) => ({ ...item, favorite: true, dynamic: true })),
    ...sampleNotice.watchlist.map((item, index) => ({
      id: `sample-${index}`,
      notice: item.notice,
      title: item.notice,
      type: item.type,
      next: item.next,
      status: item.status,
      sourceUrl: item.sourceUrl || "https://www.onbid.co.kr/",
      favorite: true,
      dynamic: false,
      sample: true,
    })).filter((item) => !favoriteKeys.has(`${item.title || item.notice}|${item.type}`)),
  ];

  // 서버가 항상 실어 보내는 placeholder(sample) 는 사용자가 «저장한» 것이 아니다.
  // 합쳐 세면 하나도 저장하지 않은 사용자에게 「관심 공고 2건」이 뜬다.
  const savedByUser = savedItems.filter((item) => !item.sample);

  // 지표 카드 3개 대신 1-3 과 같은 값 칸 한 블록이다(V6).
  byId("watch-summary").innerHTML = `<div class="fact-grid">${[
    ["관심 공고", `${savedByUser.length}건`],
    ["최근 살펴본 공고", `${recent.length}건`],
    ["현재 공고 진행률", hasBlockingMessage ? "입력 공고 미분석" : formatProgress(summary)],
  ]
    .map(([label, value]) => factCell(label, `<strong class="field-value">${value}</strong>`))
    .join("")}</div>`;

  const savedHtml = savedItems.length
    ? savedItems.map((item) => watchItemHtml(item, { showFavorite: item.dynamic })).join("")
    : `<div class="empty-state">최근 살펴본 공고에서 별표를 누르면 이곳에 관심 공고로 저장됩니다.</div>`;

  const recentHtml = recent.length
    ? recent.map((item) => watchItemHtml({ ...item, favorite: favoriteIds.has(item.id) }, { showFavorite: true })).join("")
    : `<div class="empty-state">공고를 분석하면 최근 살펴본 공고가 여기에 쌓입니다.</div>`;

  byId("watchlist-table").innerHTML = `
    <section class="watch-section">
      <div class="watch-section-title">
        <h3>관심 공고</h3>
        <p>별표한 최근 공고와 샘플 관심 공고를 모아 보는 영역입니다.</p>
      </div>
      <div class="watch-list">${savedHtml}</div>
    </section>
    <section class="watch-section">
      <div class="watch-section-title">
        <h3>최근 살펴본 공고</h3>
        <p>분석한 공고가 자동으로 남고, 별표를 누르면 관심 공고에도 함께 표시됩니다.</p>
      </div>
      <div class="watch-list">${recentHtml}</div>
    </section>
  `;
}

function watchItemHtml(item, options = {}) {
  const favoriteLabel = item.favorite ? "관심 공고에서 해제" : "관심 공고에 추가";
  const favoriteButton = options.showFavorite
    ? `<button class="star-button ${item.favorite ? "is-on" : ""}" type="button" data-favorite-id="${item.id}" aria-pressed="${item.favorite ? "true" : "false"}" title="${favoriteLabel}" aria-label="${favoriteLabel}">${item.favorite ? "★" : "☆"}</button>`
    : `<span class="star-placeholder" aria-hidden="true">★</span>`;
  // countdown은 카드가 저장된 시점(공고를 분석했을 때)의 마감 상태다. 다시 분석하지
  // 않으면 갱신되지 않으므로 "지금 이 순간"의 마감 여부와 다를 수 있다.
  const countdown = item.countdown;
  const countdownType = countdown?.state === "urgent" ? "urgent" : countdown?.state === "closed" ? "warn" : "neutral";
  // 정보 행 모양이다(V6) — 머리 줄(별표 · 머리표 · 물건명 · 원문) / 공고번호 · 유형 / 다음 할 일 · 진행.
  // 같은 말을 두 번 쓰지 않는다. 예시 항목은 공고번호 자리에 제목이 그대로 들어 있고, 최근 공고는 다음 할 일이
  // 공고 유형 값일 때가 있다.
  const title = item.title || item.notice;
  const headBadge = item.sample ? badge("예시", "warn") : countdown?.label ? badge(countdown.label, countdownType) : "";
  const textParts = [item.notice !== title ? item.notice : "", item.type].filter(Boolean);
  const metaParts = [item.next !== item.type ? item.next : "", item.status ? `${item.status}` : ""].filter(Boolean);
  const action = item.sample
    ? `<span class="info-row-action text-action is-disabled" aria-disabled="true">예시 항목(원문 없음)</span>`
    : `<a class="info-row-action link-chip" href="${item.sourceUrl || "https://www.onbid.co.kr/"}" target="_blank" rel="noreferrer">원문 ↗</a>`;
  return `<article class="info-row watch-row">
    <div class="info-row-head">${favoriteButton}${headBadge}<strong class="info-row-title">${title}</strong>${action}</div>
    ${textParts.length ? `<p class="info-row-text">${textParts.join(" · ")}</p>` : ""}
    ${metaParts.length ? `<p class="info-row-meta">${metaParts.join(" · ")}</p>` : ""}
  </article>`;
}

function renderAll() {
  renderWizardStep();
  renderPipeline();
  renderAnalysisResult();
  renderReport();
  renderWatchlist();
  renderActionState();
}


function replaceNotice(nextNotice) {
  Object.keys(sampleNotice).forEach((key) => {
    delete sampleNotice[key];
  });
  Object.assign(sampleNotice, nextNotice);
}

async function runAnalysis() {
  const inputWarning = getInputWarning();
  if (inputWarning) {
    analysisError = null;
    currentStage = 0;
    // aria-invalid 를 먼저 붙여야 다시 그린 안내가 경고 톤(입력 필요)이 된다.
    focusNoticeUrlAsInvalid();
    renderAll();
    byId("url-step-feedback").scrollIntoView({ block: "center", behavior: "smooth" });
    return;
  }
  const requestId = ++analysisRequestId;
  // 응답이 왔을 때의 입력값이 아니라 요청에 실은 값을 「분석한 URL」로 기록한다(I2). 응답 시점 값을 쓰면
  // 분석 중 URL 을 고친 경우 옛 공고 결과가 새 URL 의 것으로 기록되어 「아직 분석하지 않았습니다」 경고가 꺼진다.
  const requestedInput = getNoticeInput();
  const analyzeButton = byId("analyze");
  setAnalysisInputsBusy(true);
  analyzeButton.textContent = "분석 중";
  analysisError = null;
  boardGenerated = false;
  currentStage = 0;
  renderAll();

  try {
    currentStage = 1;
    renderPipeline();
    // ngrok 무료 계정은 브라우저 UA로 오는 요청에 경고 인터스티셜(HTML)을 끼워 넣는다.
    // 같은 origin의 이 fetch도 그 대상이라, 헤더 없이는 JSON 대신 HTML을 받아 파싱이 깨진다
    // (2026-09-12 실측 — curl로 재현). 이 헤더는 ngrok 문서가 정한 공식 우회 방법이고,
    // ngrok을 안 거칠 때는 우리 서버가 그냥 무시하는 헤더라 부작용이 없다.
    const response = await fetch(`/api/analyze?url=${encodeURIComponent(requestedInput)}`, {
      headers: { "ngrok-skip-browser-warning": "true" },
    });
    const payload = await response.json();
    if (requestId !== analysisRequestId) return;
    if (!response.ok || !payload.ok) {
      const error = new Error(payload.error || "온비드 페이지 분석에 실패했습니다.");
      error.status = response.status;
      throw error;
    }
    currentStage = pipelineSteps.length - 1;
    replaceNotice(payload.notice);
    boardStageNum = null;
    analyzedInputValue = requestedInput;
    clearCoachAnswer();
    saveRecentNotice();
    renderAll();
    setInputStep("result");
    // 분석 성공 뒤 포커스가 사라진 「분석하기」 자리(BODY)에 남지 않게 1-3 제목으로 옮긴다(I7).
    const resultTitle = document.querySelector("#wizard-step-result h2");
    resultTitle.setAttribute("tabindex", "-1");
    resultTitle.focus({ preventScroll: true });
  } catch (error) {
    if (requestId !== analysisRequestId) return;
    analysisError = toAnalysisErrorMessage(error);
    boardGenerated = false;
    currentStage = 0;
    renderAll();
    setInputStep("url");
    byId("url-step-feedback").scrollIntoView({ block: "center", behavior: "smooth" });
  } finally {
    // 낡은 응답이면 번호를 올린 쪽(restartWizardToProfile · 샘플 불러오기)이 이미 잠금을 풀었다.
    if (requestId === analysisRequestId) {
      setAnalysisInputsBusy(false);
      renderActionState();
      // 실패면 고칠 자리(URL 칸)로 포커스를 보낸다. 칸은 위에서 잠금이 풀린 뒤라야 포커스를 받는다(I7).
      if (analysisError) focusNoticeUrlAsInvalid();
    }
  }
}

function focusNoticeUrlAsInvalid() {
  const input = byId("notice-url");
  input.setAttribute("aria-invalid", "true");
  input.focus({ preventScroll: true });
}

// 「HTTP Error 500」·「<urlopen error …>」 같은 원본 문구는 사용자가 고칠 수 있는 것이 아니다. 화면에는
// 다시 시도하라는 문장만 보이고 원본은 콘솔에 남긴다(I5). URL 형식 문제처럼 서버가 이유를 적어 준 400 은 그대로 보인다.
const ANALYSIS_SERVER_ERROR_MESSAGE = "온비드 페이지를 지금 읽지 못했습니다. 잠시 뒤 다시 분석하십시오.";
const ANALYSIS_SERVER_ERROR_PATTERN = /HTTP Error|urlopen|Errno|timed out|timeout|Connection|SSL|JSON|Unexpected token|Failed to fetch|NetworkError|Load failed/i;

function toAnalysisErrorMessage(error) {
  const message = error?.message || "";
  const serverSide = !error?.status || error.status >= 500 || ANALYSIS_SERVER_ERROR_PATTERN.test(message);
  if (!serverSide) return message || "온비드 페이지 분석에 실패했습니다.";
  console.warn("공고 분석 실패", error?.status, message);
  return ANALYSIS_SERVER_ERROR_MESSAGE;
}

// 분석 중에는 URL 입력과 샘플 불러오기를 막는다. 막지 않으면 결과와 입력칸의 URL 이 서로 다른 공고가 된다(I2).
function setAnalysisInputsBusy(busy) {
  byId("notice-url").disabled = busy;
  byId("load-sample").disabled = busy;
  const analyzeButton = byId("analyze");
  analyzeButton.disabled = busy;
  if (busy) analyzeButton.setAttribute("aria-busy", "true");
  else analyzeButton.removeAttribute("aria-busy");
}

// ARIA tabs 패턴의 roving tabindex — 선택된 탭만 tabindex=0, 나머지는 -1
// (2026-10-04 visual-reviewer r1 P2-2).
function selectSupportTab(tab) {
  document.querySelectorAll("[data-support-tab]").forEach((candidate) => {
    const selected = candidate === tab;
    candidate.setAttribute("aria-selected", String(selected));
    candidate.setAttribute("tabindex", selected ? "0" : "-1");
    byId(`panel-${candidate.dataset.supportTab}`).hidden = !selected;
  });
}

// 1단계 경고의 "처음으로" 버튼 — 지금 분석 중인 공고 데이터를 버리고 마법사 1p(유형·목적
// 선택)로 완전히 되돌린다. load-sample 버튼이 쓰는 초기화 방식(초기 샘플 공고로 되돌리기)과
// 같은 패턴이되, URL 입력칸은 비워서 다른 공고 URL을 새로 입력하게 한다.
function restartWizardToProfile() {
  analysisRequestId += 1;
  // 분석 중에 돌아오면 그 응답은 버려지고 finally 가 잠금을 풀지 않으므로 여기서 푼다.
  setAnalysisInputsBusy(false);
  clearCoachAnswer();
  boardStageNum = null;
  clearTimeout(transitionTimer);
  replaceNotice(JSON.parse(JSON.stringify(initialSampleNotice)));
  byId("notice-url").value = "";
  analyzedInputValue = "";
  analysisError = null;
  boardGenerated = false;
  currentStage = 0;
  renderAll();
  setView("input");
  setInputStep("profile");
}

// "새 물건 분석으로" 버튼 — 지금 보던 공고의 분석 결과·체크리스트 진행 상태·공동입찰/
// 대리입찰 답을 내 보관함(관심 공고와 같은 저장소)에 저장한 뒤, 마법사 1p(유형·목적
// 선택)로 완전히 되돌린다. 저장은 "내 보관함으로 보내기"가 쓰는 saveNoticeToLocker()를
// 그대로 재사용하고(analysisReady 가 아니면 조용히 건너뜀), 되돌리기는 restartWizardToProfile()을
// 그대로 재사용한다 — 보관함에서 다시 불러오는 기능은 이번 범위 밖이다.
function startNewAnalysis() {
  if (!window.confirm("지금 공고를 관심 공고에 저장하고 새 물건 분석을 시작할까요?")) {
    return;
  }
  saveNoticeToLocker();
  restartWizardToProfile();
}

// 화면 머리의 코드 판. 서버가 기동한 판(server)과 지금 디스크의 판(current)을 견준다.
// 다르면 서버가 옛 코드로 돌고 있다는 뜻이라 재시작을 알린다(2026-10-19 동원님 요청).
//
// 다만 커밋 해시만 견주면 발표자료·team-reports·추적 문서를 커밋해도 경고가 떴다
// (2026-10-21 동원님 지적). 재시작이 실제로 필요한 것은 src/ 가 바뀐 경우뿐이므로,
// 서버가 srcChanged: false 로 「src/ 는 그대로」라고 알려 줄 때만 경고를 가린다.
// 그 필드가 없는 옛 서버가 돌고 있으면 가리지 않는다 — 모르는 쪽에서는 알린다.
function formatCodeRevision(payload) {
  const server = payload?.server || {};
  if (!server.commit) return "코드 판: git 정보를 읽지 못했습니다";
  const parts = [`코드 판 r${server.number} · ${server.commit} · ${server.branch} · 서버 기동 ${payload.startedAt}`];
  const current = payload.current || {};
  if (current.commit && current.commit !== server.commit && payload.srcChanged !== false) {
    parts.push(`<strong class="code-revision-warn">서버 기동 뒤 코드가 ${current.commit} 로 바뀌었습니다. 서버를 다시 시작해야 합니다</strong>`);
  }
  if (server.dirty || current.dirty) {
    parts.push(`<strong class="code-revision-warn">커밋하지 않은 변경이 있습니다</strong>`);
  }
  return parts.join(" · ");
}

async function renderCodeRevision() {
  const host = byId("code-revision");
  if (!host) return;
  try {
    const response = await window.fetch("/api/version");
    host.innerHTML = formatCodeRevision(await response.json());
  } catch {
    host.textContent = "코드 판: 서버에서 확인하지 못했습니다";
  }
}

function init() {
  renderCodeRevision();
  // 처음 1-2 에 들어온 사람에게 무엇인지 모를 URL 을 미리 채워 두지 않는다. 샘플은 「샘플 불러오기」가 채운다(U4).
  byId("notice-url").value = "";
  analyzedInputValue = "";
  renderAll();
  renderReferenceLinks();

  document.querySelectorAll(".tab").forEach((button) => {
    button.addEventListener("click", () => setView(button.dataset.view));
  });

  byId("load-sample").addEventListener("click", () => {
    analysisRequestId += 1;
    setAnalysisInputsBusy(false);
    clearCoachAnswer();
    byId("analyze").textContent = "분석하기";
    replaceNotice(JSON.parse(JSON.stringify(initialSampleNotice)));
    boardStageNum = null;
    byId("notice-url").value = SAMPLE_INPUT_URL;
    analyzedInputValue = "";
    boardGenerated = false;
    analysisError = null;
    // 1-1 에서 고른 검토 목적은 덮어쓰지 않는다. 샘플이 목적과 다르면 1-3 이 그대로 불일치를 보인다(U5).
    currentStage = 0;
    renderAll();
  });

  byId("profile-next").addEventListener("click", () => setInputStep("url"));
  byId("wizard-back-url").addEventListener("click", () => setInputStep("profile"));
  byId("wizard-back-result").addEventListener("click", () => setInputStep("url"));

  byId("analyze").addEventListener("click", runAnalysis);
  byId("prepare").addEventListener("click", () => {
    if (!isAnalysisReady()) return;
    boardGenerated = true;
    // 1-3 에서 넘어오면 항상 2-1 부터 보인다. 비워 두면 getBoardStage 가 「아직 끝나지 않은 첫 단계」를 고르므로,
    // 같은 공고의 2-1 체크가 저장돼 있으면 2-2 로 건너뛰었다(2026-10-19 동원님 제보).
    boardStageNum = 1;
    currentStage = pipelineSteps.length;
    renderPipeline();
    setInputStep("transition");
    // 전환 화면은 "준비보드를 만들어드려요" 메시지를 짧게 보여준 뒤 자동으로 준비 보드로
    // 넘어간다 — 사용자가 또 한 번 버튼을 눌러야 하는 멈춤 지점이 아니다.
    clearTimeout(transitionTimer);
    transitionTimer = window.setTimeout(() => {
      inputStep = "result";
      renderWizardStep();
      // setView 는 다시 그리지 않는다. 위에서 고른 2-1 이 화면에 반영되도록 여기서 보드를 다시 그린다.
      renderReport();
      setView("report");
      byId("report-title").setAttribute("tabindex", "-1");
      byId("report-title").focus();
    }, 900);
  });
  byId("user-type").addEventListener("change", renderAll);
  byId("asset-focus").addEventListener("change", renderAll);
  byId("notice-url").addEventListener("input", () => {
    // 다시 입력하기 시작하면 「잘못된 입력」 표시를 푼다.
    byId("notice-url").removeAttribute("aria-invalid");
    analysisError = null;
    boardGenerated = false;
    currentStage = 0;
    renderAll();
  });
  byId("reset-tasks").addEventListener("click", resetTaskState);

  document.addEventListener("change", (event) => {
    const taskId = event.target?.dataset?.taskId;
    if (taskId) {
      // 잠긴 단계의 task는 체크박스가 disabled라 보통 change 이벤트가 안 나지만,
      // 이중 방어로 한 번 더 막는다(ux-audit §⑴ "구현 시 반드시 지킬 것").
      const stageNum = getTaskStageNum(taskId);
      const lockedStage = stageNum !== null && getPrepStageStatus().find((stage) => stage.num === stageNum)?.locked;
      if (lockedStage) {
        event.target.checked = !event.target.checked;
        return;
      }
      const state = getTaskState();
      state[taskId] = event.target.checked;
      saveTaskState(state);
      saveRecentNotice();
      renderReport();
      renderWatchlist();
      document.querySelector(`[data-task-id="${CSS.escape(taskId)}"]`)?.focus();
      return;
    }
    const docName = event.target?.dataset?.docName;
    if (!docName) return;
    const docState = getDocState();
    docState[docName] = event.target.checked;
    saveDocState(docState);
    // 서류를 전부 체크하면 "제출서류 확인" 항목을 도와서 체크해준다. 다만 이후 사용자가
    // 그 항목을 직접 풀거나 켜는 것은 그대로 존중한다 — 서류가 미완이라고 강제로
    // 되돌리지 않는다(한 방향 보조 동작).
    const docSummary = getDocSummary();
    if (docSummary.totalCount > 0 && docSummary.doneCount === docSummary.totalCount) {
      const taskState = getTaskState();
      taskState.documents = true;
      saveTaskState(taskState);
    }
    saveRecentNotice();
    renderReport();
    renderWatchlist();
    document.querySelector(`[data-doc-name="${CSS.escape(docName)}"]`)?.focus();
  });

  document.addEventListener(
    "toggle",
    (event) => {
      if (event.target?.id === "doc-checklist-details") {
        docChecklistOpen = event.target.open;
      }
    },
    true,
  );

  document.addEventListener("keydown", (event) => {
    // 한글 조합 중 Enter 는 조합 확정용이라 건너뛴다(안 그러면 같은 질문이 두 번 나간다).
    if (event.key !== "Enter" || event.isComposing || event.keyCode === 229) return;
    if (event.target?.id === "coach-question-input") {
      event.preventDefault();
      askNoticeQuestion();
    }
  });

  // ARIA tabs 패턴 — 좌우 화살표로 탭 이동, Home/End로 처음·끝 탭 선택
  // (2026-10-04 visual-reviewer r1 P2-2).
  document.addEventListener("keydown", (event) => {
    const tab = event.target.closest?.("[data-support-tab]");
    if (!tab) return;
    const tabs = Array.from(document.querySelectorAll("[data-support-tab]"));
    const index = tabs.indexOf(tab);
    let nextIndex = null;
    if (event.key === "ArrowRight") nextIndex = (index + 1) % tabs.length;
    else if (event.key === "ArrowLeft") nextIndex = (index - 1 + tabs.length) % tabs.length;
    else if (event.key === "Home") nextIndex = 0;
    else if (event.key === "End") nextIndex = tabs.length - 1;
    if (nextIndex === null) return;
    event.preventDefault();
    const nextTab = tabs[nextIndex];
    selectSupportTab(nextTab);
    nextTab.focus();
  });

  document.addEventListener("click", (event) => {
    const guideButton = event.target.closest("[data-guide-level]");
    if (guideButton) {
      const level = guideButton.dataset.guideLevel;
      guideDetailed = level === "detail";
      renderReport();
      // 두 칸 버튼도 다시 그려진다. 같은 칸으로 포커스를 되돌린다(I7).
      document.querySelector(`[data-guide-level="${level}"]`)?.focus();
      return;
    }
    const wizardDot = event.target.closest("[data-wizard-dot]");
    if (wizardDot) {
      if (!wizardDot.disabled && isWizardStepReachable(wizardDot.dataset.wizardDot)) setInputStep(wizardDot.dataset.wizardDot);
      return;
    }
    const stageButton = event.target.closest("[data-board-stage]");
    if (stageButton) {
      boardStageNum = Number(stageButton.dataset.boardStage);
      renderReport();
      byId("view-report").scrollIntoView({ block: "start" });
      // 누른 버튼이 다시 그려져 사라지므로 포커스가 BODY 로 빠졌다(I7). 새 페이지 제목으로 옮긴다.
      focusReportTitle();
      return;
    }
    if (event.target.closest("[data-goto-input]")) {
      // 1-1 을 지나지 않았으면 1-1, 지났으면 1-2 로 간다. 결과 화면(1-3)은 분석 전이라 열 수 없다.
      setView("input");
      setInputStep(inputStep === "profile" ? "profile" : "url");
      return;
    }
    if (event.target.closest("[data-goto-attachments]")) {
      boardStageNum = 1;
      renderReport();
      const attachmentTab = byId("tab-attachment-list");
      selectSupportTab(attachmentTab);
      attachmentTab.scrollIntoView({ block: "center" });
      attachmentTab.focus();
      return;
    }
    if (event.target.closest("[data-restart-wizard]")) {
      restartWizardToProfile();
      return;
    }
    if (event.target.closest("[data-new-analysis]")) {
      startNewAnalysis();
      return;
    }
    const docConditionButton = event.target.closest("[data-doc-condition]");
    if (docConditionButton) {
      setDocConditionAnswer(docConditionButton.dataset.docCondition, docConditionButton.dataset.docConditionValue);
      renderReport();
      return;
    }
    if (event.target.closest("[data-store-to-locker]")) {
      const record = saveNoticeToLocker();
      const feedback = byId("doc-locker-feedback");
      if (feedback) {
        feedback.textContent = record ? "관심 공고에 저장되었습니다." : "먼저 공고를 분석해야 저장할 수 있습니다.";
      }
      return;
    }
    const supportTab = event.target.closest("[data-support-tab]");
    if (supportTab) {
      selectSupportTab(supportTab);
      return;
    }

    if (event.target.closest("[data-ask-question]")) {
      askNoticeQuestion();
      return;
    }
    const suggestButton = event.target.closest("[data-coach-suggest]");
    if (suggestButton) {
      const input = byId("coach-question-input");
      if (input) input.value = suggestButton.dataset.coachSuggest;
      askNoticeQuestion();
      return;
    }
    if (event.target.closest("[data-coach-clear]")) {
      clearCoachAnswer();
      // 누른 버튼이 사라지므로 포커스를 질문 입력칸으로 옮긴다.
      byId("coach-question-input")?.focus();
      return;
    }
    if (event.target.closest("[data-coach-toggle]")) {
      setCoachCollapsed(!coachCollapsed);
      return;
    }
    const target = event.target.closest("[data-jump]");
    if (!target) {
      const favoriteTarget = event.target.closest("[data-favorite-id]");
      if (favoriteTarget) {
        const favoriteId = favoriteTarget.dataset.favoriteId;
        // 즐겨찾기한 항목은 "관심 공고"·"최근 살펴본 공고" 두 섹션에 같은 id의 버튼이
        // 동시에 존재할 수 있다. querySelector 하나만 쓰면 항상 문서상 첫 번째(관심 공고
        // 섹션)로 포커스가 튀어, 사용자가 실제로 클릭한 섹션과 달라진다. 클릭한 섹션의
        // 위치(인덱스)를 기억해 재렌더 후 같은 자리부터 우선 찾는다.
        const sections = Array.from(document.querySelectorAll("#watchlist-table .watch-section"));
        const clickedSectionIndex = sections.indexOf(favoriteTarget.closest(".watch-section"));
        toggleFavoriteNotice(favoriteId);
        const newSections = document.querySelectorAll("#watchlist-table .watch-section");
        const sameSection = newSections[clickedSectionIndex];
        const nextFocus =
          sameSection?.querySelector(`[data-favorite-id="${CSS.escape(favoriteId)}"]`) ||
          document.querySelector(`[data-favorite-id="${CSS.escape(favoriteId)}"]`);
        nextFocus?.focus();
      }
      return;
    }
    setView(target.dataset.jump);
  });

  const dockForHeight = document.querySelector(".board-dock");
  if (dockForHeight && window.ResizeObserver) new ResizeObserver(updateDockHeightVar).observe(dockForHeight);

  const initial = location.hash.replace("#", "");
  if (["input", "report", "watchlist"].includes(initial)) {
    setView(initial);
  } else {
    setView("input");
  }

  window.addEventListener("hashchange", () => {
    const next = location.hash.replace("#", "");
    if (["input", "report", "watchlist"].includes(next) && next !== currentView) {
      setView(next);
    }
  });
}

document.addEventListener("DOMContentLoaded", init);
