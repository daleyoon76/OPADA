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
const taskStorageKey = "onbid-public-asset-doc-agent-tasks-v1";
const recentNoticeStorageKey = "onbid-public-asset-doc-agent-recent-v1";
const favoriteNoticeStorageKey = "onbid-public-asset-doc-agent-favorites-v1";

const aiTaskSignals = [
  {
    taskIds: ["price", "guarantee", "agency-question"],
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
    taskIds: ["agency", "agency-question"],
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
}

function badge(text, type = "safe") {
  return `<span class="badge ${type}">${text}</span>`;
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
  window.localStorage.setItem(key, JSON.stringify(value));
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

function getApplicableTasks() {
  const userType = getSelectedUserType();
  const boardTasks = Array.isArray(sampleNotice.boardTasks) ? sampleNotice.boardTasks : [];
  return boardTasks
    .filter((task) => !task.userTypes || task.userTypes.includes(userType))
    .map((task, index) => ({ task, index, aiMatch: getTaskAiMatch(task) }))
    .sort((a, b) => {
      const scoreDiff = (b.aiMatch?.score || 0) - (a.aiMatch?.score || 0);
      return scoreDiff || a.index - b.index;
    })
    .map(({ task }) => task);
}

function getTaskState() {
  const tasks = getApplicableTasks();
  try {
    const saved = JSON.parse(window.localStorage.getItem(taskStorageKey) || "{}");
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
    const saved = JSON.parse(window.localStorage.getItem(taskStorageKey) || "{}");
    window.localStorage.setItem(taskStorageKey, JSON.stringify({ ...saved, ...state }));
  } catch {
    // Local storage is a convenience for the prototype; the checklist still works in-session.
  }
}

function resetTaskState() {
  if (!window.confirm("진행 상황을 초기화할까요?")) {
    return;
  }
  window.localStorage.removeItem(taskStorageKey);
  renderReport();
  renderWatchlist();
}

function getTaskSummary() {
  const state = getTaskState();
  const tasks = getApplicableTasks();
  const doneCount = tasks.filter((task) => state[task.id]).length;
  const totalCount = tasks.length;
  const nextTask = tasks.find((task) => !state[task.id]) || tasks[tasks.length - 1] || null;
  return { state, tasks, doneCount, totalCount, nextTask, percent: totalCount ? Math.round((doneCount / totalCount) * 100) : 0 };
}

function formatProgress(summary) {
  return summary.totalCount ? `${summary.doneCount}/${summary.totalCount} 완료` : "체크리스트 대기";
}

function getFitMessage() {
  const inputWarning = getInputWarning();
  if (inputWarning) {
    return {
      type: "mismatch",
      title: inputWarning.title,
      body: inputWarning.body,
      action: "온비드 URL을 입력한 뒤 공고 분석을 실행하세요.",
      inputBlocked: true,
    };
  }

  if (analysisError) {
    return {
      type: "mismatch",
      title: "공고 분석에 실패했습니다",
      body: analysisError,
      action: "URL이 온비드 공고/물건 상세 페이지인지 확인한 뒤 다시 실행하세요.",
      inputBlocked: true,
    };
  }

  if (!isAnalyzedInputCurrent()) {
    return {
      type: "check",
      title: "아직 이 URL을 분석하지 않았습니다",
      body: "입력 URL이 바뀌었습니다. 공고 분석을 실행해야 이 URL 기준의 준비 보드가 생성됩니다.",
      action: "공고 분석 버튼을 누르면 유효성 결과와 공고/물건 연결 정보를 먼저 보여줍니다.",
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
      action: "준비 보드에서는 창업 목적 사용 가능 여부를 내가 담당기관에 물어볼 질문으로 분리합니다.",
    };
  }

  return {
    type: "match",
    title: "목적과 입력 공고 유형이 맞습니다",
    body: "분석된 온비드 공고를 기준으로 일정, 제출서류, 가격/보증금, 내가 담당기관에 물어볼 질문을 준비 보드로 정리합니다.",
    action: "결과를 확인한 뒤 준비 보드 만들기를 누르면 체크리스트와 준비처 링크로 넘어갑니다.",
  };
}

function renderAnalysisResult() {
  const panel = byId("analysis-result");
  const fit = getFitMessage();
  const typeBadge = fit.type === "match" ? "safe" : "warn";
  panel.className = `fit-panel ${fit.type}`;

  if (fit.inputBlocked) {
    panel.innerHTML = `
      <div class="fit-top">
        ${badge(fit.type === "mismatch" ? "불일치" : "확인 필요", typeBadge)}
        <strong>${fit.title}</strong>
      </div>
      <p>${fit.body}</p>
      <p class="small-text">${fit.action}</p>
    `;
    return;
  }

  const publicData = sampleNotice.analysisMeta?.publicData;
  const coach = sampleNotice.aiCoach;
  const links = sampleNotice.relatedUrls || {};

  panel.innerHTML = `
    <div class="fit-top">
      ${badge(fit.type === "mismatch" ? "불일치" : fit.type === "check" ? "확인 필요" : "일치", typeBadge)}
      <strong>${fit.title}</strong>
    </div>
    <p class="small-text">${sampleNotice.pageType || "온비드 페이지"}${publicData ? ` · ${publicDataLabel(publicData)}` : ""}</p>
    <p>${fit.body}</p>
    <div class="preview-grid">
      <div><b>공고/물건명</b><strong>${sampleNotice.title}</strong></div>
      <div><b>유형</b><strong>${sampleNotice.assetType} / ${sampleNotice.dispositionLabel}</strong></div>
      <div><b>입찰기간</b><strong>${sampleNotice.bidPeriod || sampleNotice.bidDeadline || "원문 확인"}</strong></div>
      <div><b>가격/보증금</b><strong>${sampleNotice.minimumBidPrice || sampleNotice.bidDeposit || "원문 확인"}</strong></div>
    </div>
    <div class="linked-pages">
      <b>온비드 연결</b>
      <a href="${sampleNotice.sourceUrl}" target="_blank" rel="noreferrer">현재 분석 페이지</a>
      ${links.noticeDetail ? `<a href="${links.noticeDetail}" target="_blank" rel="noreferrer">공고보기</a>` : ""}
      ${links.itemDetail ? `<a href="${links.itemDetail}" target="_blank" rel="noreferrer">물건상세</a>` : ""}
    </div>
    ${renderAiReadySummary(coach)}
    <p class="small-text">${fit.action}</p>
  `;
}

function renderCoachPanel(coach, options = {}) {
  const panelClass = options.board ? "coach-panel board" : "coach-panel";
  const coachMode = "AI 누락 점검";
  const facts = (coach?.confirmedFacts || []).slice(0, options.board ? 2 : 4);
  const checks = (coach?.unresolvedChecks || []).slice(0, 3);
  const questions = (coach?.askAgency || []).slice(0, 2);
  const factsHtml = !options.board && facts
    .map((fact) => `<div><b>${fact.label}</b><strong>${fact.value}</strong></div>`)
    .join("");
  const checksHtml = checks
    .map(
      (item) => `<article class="coach-check">
        <strong>${item.title}</strong>
        <p>${options.board ? item.action : item.reason}</p>
        ${options.board ? "" : `<em>${item.action}</em>`}
      </article>`,
    )
    .join("");
  const questionsHtml = questions.map((question) => `<li>${question}</li>`).join("");

  return `<section class="${panelClass}">
    <div class="coach-head">
      ${badge(coachMode, coach?.llmStatus === "connected" ? "safe" : "warn")}
      <strong>${options.board ? "AI가 먼저 볼 빈칸을 체크리스트에 연결했습니다." : coach?.headline || "AI가 미해결 항목만 골랐습니다."}</strong>
    </div>
    <p>${options.board ? "아래 체크리스트에서 AI 우선 확인 표시가 붙은 항목부터 처리하세요." : coach?.plainSummary || "이미 보이는 값은 반복하지 않고, 실제 준비 전에 남는 빈칸만 분리합니다."}</p>
    ${factsHtml ? `<div class="coach-facts">${factsHtml}</div>` : ""}
    ${checksHtml ? `<div class="coach-checks">${checksHtml}</div>` : ""}
    ${
      questionsHtml && !options.board
        ? `<div class="coach-questions">
          <b>내가 담당기관에 물어볼 문장</b>
          <ul>${questionsHtml}</ul>
        </div>`
        : ""
    }
    <p class="small-text">${coach?.safeBoundary || "입찰 여부, 법률 판단, 수익성 판단은 제공하지 않습니다."}</p>
  </section>`;
}

function renderAiReadySummary(coach) {
  const checks = coach?.unresolvedChecks || [];
  const questionCount = (coach?.askAgency || []).length;
  return `<section class="ai-ready-summary">
    <div>
      ${badge("AI 분석 완료", coach?.llmStatus === "connected" ? "safe" : "warn")}
      <strong>준비 보드에서 우선순위 체크리스트로 보여드립니다.</strong>
    </div>
    <p>${checks.length ? `${checks.length}개 미해결 항목과 ${questionCount}개 담당기관 확인 질문을 준비했습니다.` : "공고별 준비 보드에서 다음 확인 항목을 정리합니다."}</p>
  </section>`;
}

function renderTaskAiNudge(aiMatch) {
  if (!aiMatch?.check) {
    return "";
  }
  const check = aiMatch.check;
  return `<div class="task-ai-nudge">
    <div>
      ${badge("AI 우선 확인", "safe")}
      <strong>${check.title}</strong>
    </div>
    <p>${check.action || check.reason || "이 항목을 먼저 확인하세요."}</p>
  </div>`;
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
    prepareButton.textContent = ready ? "준비 보드 만들기" : "분석 후 만들기";
  }
  const analyzeButton = byId("analyze");
  if (analyzeButton && !analyzeButton.disabled) {
    analyzeButton.textContent = ready ? "다시 분석" : "공고 분석";
    analyzeButton.className = ready ? "secondary" : "primary";
  }
}

function getSelectedUserType() {
  return byId("user-type").value;
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
  const firstAiTask = taskSummary.tasks.find((task) => aiAssignments.has(task.id));
  const firstAiMatch = firstAiTask ? aiAssignments.get(firstAiTask.id) : null;

  if (blockingMessage) {
    const sourceLink = byId("source-url-link");
    if (sourceLink) {
      sourceLink.href = sampleNotice.sourceUrl;
    }
    byId("report-hero").innerHTML = `
      <h3>${blockingMessage.title}</h3>
      <p>${badge("분석 필요", "warn")} <span class="small-text">원문 우선</span></p>
      <p>${blockingMessage.body}</p>
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
      ["입력 상태", inputWarning ? "URL 확인 필요" : "분석 실패"],
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
    byId("question-list").innerHTML = "";
    byId("source-notes").innerHTML = "";
    byId("board-coach").innerHTML = "";
    return;
  }

  const sourceLink = byId("source-url-link");
  if (sourceLink) {
    sourceLink.href = sampleNotice.sourceUrl;
  }

  byId("report-hero").innerHTML = `
    <h3>${sampleNotice.title}</h3>
    <p>${sampleNotice.assetType} ${sampleNotice.dispositionLabel} / ${userTypeLabels[userType]} / ${focusLabels[getSelectedFocus()]}</p>
    <p class="small-text">${sampleNotice.mode || "온비드 분석"}${
      publicData ? ` · ${publicDataLabel(publicData)}` : ""
    } · 원문 우선</p>
    <p>${badge(fit.type === "mismatch" ? "목적 불일치" : "목적 확인", fit.type === "match" ? "safe" : "warn")}</p>
    <p>${fit.body}</p>
  `;

  const coach = sampleNotice.aiCoach;
  byId("board-coach").innerHTML = coach
    ? renderCoachPanel(coach, { board: true })
    : "";

  byId("board-status").innerHTML = [
    [aiAssignments.size ? "AI 우선 액션" : "다음 액션", firstAiMatch?.check?.title || firstAiTask?.title || taskSummary.nextTask?.title || "원문 확인"],
    ["진행률", formatProgress(taskSummary)],
  ]
    .map(
      ([label, value]) => `<div class="status-card">
        <b>${label}</b>
        <strong>${value}</strong>
        ${
          label === "진행률"
            ? `<span class="progress" role="progressbar" aria-label="준비 진행률" aria-valuemin="0" aria-valuemax="${taskSummary.totalCount}" aria-valuenow="${taskSummary.doneCount}"><i style="width:${taskSummary.percent}%"></i></span>`
            : ""
        }
      </div>`,
    )
    .join("");

  byId("task-list").innerHTML = taskSummary.tasks.length
    ? taskSummary.tasks
      .map(
        (task) => {
        const aiMatch = aiAssignments.get(task.id);
        const shouldOpenDetails = aiMatch && firstAiTask?.id === task.id;
        return `<article class="task-item ${taskSummary.state[task.id] ? "is-done" : ""} ${aiMatch ? "has-ai-nudge" : ""}">
        <label class="task-check">
          <input type="checkbox" data-task-id="${task.id}" ${taskSummary.state[task.id] ? "checked" : ""}>
          <span>
            <strong>${task.title}</strong>
            <em>${task.action}</em>
          </span>
        </label>
        ${renderTaskAiNudge(aiMatch)}
        <div class="task-meta">
          ${badge(taskSummary.state[task.id] ? "완료" : task.due, taskSummary.state[task.id] ? "safe" : "warn")}
          <a class="text-action" href="${task.url}" target="_blank" rel="noreferrer">${task.cta}</a>
        </div>
        <details ${shouldOpenDetails ? "open" : ""}>
          <summary>담당기관에 물어볼 문장</summary>
          ${aiMatch?.check?.reason ? `<p><b>AI가 짚은 빈칸</b>: ${aiMatch.check.reason}</p>` : ""}
          <p><b>문의 문장</b>: ${task.question}</p>
          <p>${task.detail}</p>
          <p class="small-text">근거: ${task.source}</p>
        </details>
      </article>`;
        },
      )
      .join("")
    : `<article class="task-item">
        <strong>체크리스트를 자동 생성하지 못했습니다.</strong>
        <p class="small-text">온비드 원문을 열어 입찰기간, 제출서류, 가격/보증금, 담당기관을 먼저 확인하세요.</p>
        <div class="task-meta">
          <span class="small-text">원문 우선</span>
          <a class="text-action" href="${sampleNotice.sourceUrl}" target="_blank" rel="noreferrer">온비드 원문</a>
        </div>
      </article>`;

  byId("quick-facts").innerHTML = [
    ["공고번호", sampleNotice.noticeId],
    ["공고기관", sampleNotice.agency],
    ["입찰방식", sampleNotice.bidMethod],
    ["가격/보증금", sampleNotice.minimumBidPrice || sampleNotice.bidDeposit || "원문 확인"],
  ]
    .map(
      ([label, value]) => `<div class="fact-row">
        <span>${label}</span>
        <strong>${value}</strong>
      </div>`,
    )
    .join("");

  byId("deadline-cost-list").innerHTML = [
    ...sampleNotice.alerts.map((item) => ({ ...item, type: "알림" })),
    ...sampleNotice.costs.map((item) => ({ ...item, type: "비용" })),
  ]
    .map((item) => `<details class="compact-row">
      <summary><span>${item.type}</span><strong>${item.title}: ${item.value}</strong></summary>
      <p>${item.note}</p>
    </details>`)
    .join("");

  byId("question-list").innerHTML = sampleNotice.risks
    .map((risk) => `<details class="compact-row">
      <summary><span>문의</span><strong>${risk.title}</strong></summary>
      <p>${risk.question}</p>
      <p class="small-text">근거: ${risk.source}</p>
    </details>`)
    .join("");

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
  byId("source-notes").innerHTML = sourceNotes
    .map((note) => `<div class="source-note"><span>${badge("확인", "safe")}</span><span>${note}</span></div>`)
    .join("");
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

  byId("watch-summary").innerHTML = [
    ["관심 공고", `${savedItems.length}건`],
    ["최근 살펴본 공고", `${recent.length}건`],
    ["현재 공고 진행률", hasBlockingMessage ? "입력 공고 미분석" : formatProgress(summary)],
  ]
    .map(([label, value]) => `<div class="summary-item"><b>${label}</b><strong>${value}</strong></div>`)
    .join("");

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
  const statusType = item.status?.includes("필요") || item.status?.includes("미") ? "warn" : "safe";
  const favoriteButton = options.showFavorite
    ? `<button class="star-button ${item.favorite ? "is-on" : ""}" type="button" data-favorite-id="${item.id}" aria-pressed="${item.favorite ? "true" : "false"}" title="${item.favorite ? "관심 공고에서 해제" : "관심 공고에 추가"}">${item.favorite ? "★" : "☆"}</button>`
    : `<span class="star-placeholder" aria-hidden="true">★</span>`;
  return `<article class="watch-item">
    ${favoriteButton}
    <div>
      <strong>${item.title || item.notice}${item.sample ? ` ${badge("예시", "warn")}` : ""}</strong>
      <span>${item.notice}</span>
      <span>${item.type}</span>
    </div>
    <p>${item.next}</p>
    <div class="watch-actions">
      ${badge(item.status, statusType)}
      <a class="text-action" href="${item.sourceUrl || "https://www.onbid.co.kr/"}" target="_blank" rel="noreferrer">원문</a>
    </div>
  </article>`;
}

function renderAll() {
  renderPipeline();
  renderAnalysisResult();
  renderReport();
  renderWatchlist();
  renderActionState();
}

function getSummaryText() {
  const summary = getTaskSummary();
  const questions = sampleNotice.risks.map((risk) => `- ${risk.title}: ${risk.question}`).join("\n");
  return [
    `[온비드 공고 검토 메모]`,
    `${sampleNotice.noticeId} ${sampleNotice.title}`,
    `${sampleNotice.agency} / ${sampleNotice.assetType} ${sampleNotice.dispositionLabel} / ${sampleNotice.bidMethod}`,
    `준비 진행률: ${formatProgress(summary)}`,
    `다음 액션: ${summary.nextTask.action}`,
    ``,
    `내가 담당기관에 확인할 질문`,
    questions,
    ``,
    `출처: ${sampleNotice.sourceUrl}`,
  ].join("\n");
}

async function copySummary() {
  const feedback = byId("copy-feedback");
  if (getInputWarning() || analysisError || !isAnalyzedInputCurrent()) {
    feedback.className = "copy-feedback is-warn";
    feedback.textContent = "현재 입력값은 분석되지 않았기 때문에 검토 메모를 만들지 않았습니다.";
    return;
  }
  const text = getSummaryText();
  try {
    await navigator.clipboard.writeText(text);
    feedback.className = "copy-feedback is-success";
    feedback.textContent = "검토 메모를 클립보드에 복사했습니다.";
  } catch {
    feedback.className = "copy-feedback is-warn";
    feedback.textContent = "브라우저 권한 때문에 자동 복사는 실패했습니다. 원문과 질문은 준비 보드에서 확인할 수 있습니다.";
  }
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
    renderAll();
    byId("analysis-result").scrollIntoView({ block: "center", behavior: "smooth" });
    return;
  }
  const requestId = ++analysisRequestId;
  const analyzeButton = byId("analyze");
  analyzeButton.disabled = true;
  analyzeButton.textContent = "분석 중";
  analysisError = null;
  boardGenerated = false;
  currentStage = 0;
  renderAll();

  try {
    currentStage = 1;
    renderPipeline();
    const response = await fetch(`/api/analyze?url=${encodeURIComponent(getNoticeInput())}`);
    const payload = await response.json();
    if (requestId !== analysisRequestId) return;
    if (!response.ok || !payload.ok) {
      throw new Error(payload.error || "온비드 페이지 분석에 실패했습니다.");
    }
    currentStage = pipelineSteps.length - 1;
    replaceNotice(payload.notice);
    analyzedInputValue = getNoticeInput();
    window.localStorage.removeItem(taskStorageKey);
    saveRecentNotice();
    renderAll();
    byId("analysis-result").scrollIntoView({ block: "center", behavior: "smooth" });
  } catch (error) {
    if (requestId !== analysisRequestId) return;
    analysisError = error.message || "온비드 페이지 분석에 실패했습니다.";
    boardGenerated = false;
    currentStage = 0;
    renderAll();
    byId("analysis-result").scrollIntoView({ block: "center", behavior: "smooth" });
  } finally {
    if (requestId === analysisRequestId) {
      analyzeButton.disabled = false;
      renderActionState();
    }
  }
}

function init() {
  byId("notice-url").value = sampleNotice.sourceUrl;
  analyzedInputValue = "";
  renderAll();

  document.querySelectorAll(".tab").forEach((button) => {
    button.addEventListener("click", () => setView(button.dataset.view));
  });

  byId("load-sample").addEventListener("click", () => {
    analysisRequestId += 1;
    byId("analyze").disabled = false;
    byId("analyze").textContent = "공고 분석";
    replaceNotice(JSON.parse(JSON.stringify(initialSampleNotice)));
    byId("notice-url").value = sampleNotice.sourceUrl;
    analyzedInputValue = "";
    boardGenerated = false;
    analysisError = null;
    byId("asset-focus").value = "lease";
    currentStage = 0;
    renderAll();
  });

  byId("analyze").addEventListener("click", runAnalysis);
  byId("prepare").addEventListener("click", () => {
    if (!isAnalysisReady()) return;
    boardGenerated = true;
    currentStage = pipelineSteps.length;
    renderPipeline();
    setView("report");
    byId("report-title").setAttribute("tabindex", "-1");
    byId("report-title").focus();
  });
  byId("user-type").addEventListener("change", renderAll);
  byId("asset-focus").addEventListener("change", renderAll);
  byId("notice-url").addEventListener("input", () => {
    analysisError = null;
    boardGenerated = false;
    currentStage = 0;
    renderAll();
  });
  byId("reset-tasks").addEventListener("click", resetTaskState);

  document.addEventListener("change", (event) => {
    const taskId = event.target?.dataset?.taskId;
    if (!taskId) return;
    const state = getTaskState();
    state[taskId] = event.target.checked;
    saveTaskState(state);
    renderReport();
    renderWatchlist();
    document.querySelector(`[data-task-id="${CSS.escape(taskId)}"]`)?.focus();
  });

  document.addEventListener("click", (event) => {
    if (event.target.closest("[data-copy-summary]")) {
      copySummary();
      return;
    }
    const target = event.target.closest("[data-jump]");
    if (!target) {
      const favoriteTarget = event.target.closest("[data-favorite-id]");
      if (favoriteTarget) {
        const favoriteId = favoriteTarget.dataset.favoriteId;
        toggleFavoriteNotice(favoriteId);
        document.querySelector(`[data-favorite-id="${CSS.escape(favoriteId)}"]`)?.focus();
      }
      return;
    }
    setView(target.dataset.jump);
  });

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
