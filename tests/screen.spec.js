const { test, expect } = require("@playwright/test");

/**
 * 화면 노출 축.
 *
 * 연기 목록(PLAYED)·축 표(AXES)와 pass/total 집계는 tests/screen-axes.js 와
 * tests/gate-reporter.js 가 맡는다. spec 안에서 세면 실패마다 worker 가 재시작되어
 * 수치가 조각난다 — 붉은 실행에서 가장 필요한 줄이 못 쓰게 된다.
 */

const BASE_NOTICE = {
  sourceUrl: "https://www.onbid.co.kr/op/cltrpbancinf/pbanc/pbancdtlinf/PbancDtlInqController/mvmnPbancDtl.do?onbidPbancNo=886933",
  inputUrl: "https://www.onbid.co.kr/op/cltrpbancinf/pbanc/pbancdtlinf/PbancDtlInqController/mvmnPbancDtl.do?onbidPbancNo=886933",
  relatedUrls: {},
  mode: "실제 온비드 페이지 분석",
  pageType: "공고 상세",
  noticeId: "202605-13303-00",
  title: "2026년 제010차 압류재산 공매공고",
  agency: "한국자산관리공사",
  assetType: "압류재산",
  disposition: "매각",
  dispositionLabel: "매각",
  bidMethod: "일반경쟁",
  bidType: "전자입찰",
  noticeDate: "2026-09-01",
  contact: "전북지역본부",
  bidPeriod: "2026-09-14 14:00 ~ 2026-09-16 17:00",
  bidDeadline: "2026-09-16 17:00",
  minimumBidPrice: "450,000,000",
  jointBidAllowed: "가능",
  evictionResponsibility: "매수인",
  appraisalPrice: "411,790,440",
  relatedDocs: [],
  requiredDocs: [],
  noticeOutline: [{ title: "1. 입찰방법", body: "온비드를 이용한 인터넷 공매입니다." }],
  glossary: [{ term: "압류재산", meaning: "체납자의 압류 재산을 캠코가 위임받아 처리하는 재산입니다." }],
  countdown: { state: "urgent", label: "마감 D-2", deadline: "2026-09-16 17:00", daysLeft: 2 },
  costs: [{ title: "입찰보증금", value: "최저입찰가격 X 10%", note: "온비드 원문 표시값입니다." }],
  alerts: [{ title: "입찰기간", value: "2026-09-14 ~ 2026-09-16", note: "원문 재확인", status: "warn" }],
  risks: [{ title: "공고 유형 착오", reason: "r", question: "q", source: "s" }],
  boardTasks: [
    {
      id: "documents",
      title: "제출서류 확인",
      action: "인감증명서 / 주민등록등본",
      due: "입찰 마감 전",
      detail: "이 목록은 참고용이며 빠진 항목이 있어도 진행을 막지 않습니다.",
      question: "제출 조건을 확인했는가?",
      source: "온비드 상세 페이지 > 제출서류",
      cta: "온비드 원문",
      url: "https://www.onbid.co.kr/",
      defaultDone: false,
    },
  ],
  watchlist: [],
  todayActions: [],
  analysisMeta: { finalUrl: "", pageType: "공고 상세", publicData: { status: "missing_key", message: "", services: [] } },
  aiCoach: {
    mode: "AI 누락 점검",
    headline: "미해결 항목",
    plainSummary: "요약",
    confirmedFacts: [],
    unresolvedChecks: [],
    nextSteps: [],
    askAgency: [],
    safeBoundary: "입찰 여부, 법률 판단, 수익성 판단은 제공하지 않습니다.",
    llmStatus: "rule_based",
  },
  docChecklist: {
    status: "extracted",
    headline: "공고 원문에서 서류 5건을 찾았습니다. 확인하셨습니까?",
    profile: { code: "A", label: "공고 본문에서 서류 목록을 찾을 수 있는 유형입니다", detail: "표준 공고입니다.", assetType: "압류재산" },
    items: [
      {
        name: "인감증명서",
        conditions: ["미성년자"],
        conditionKeys: ["minor"],
        copy: "원본",
        validity: "1개월 이내 발급",
        method: "직접제출",
        due: "입찰마감일시 전까지",
        count: "1부",
        stage: "입찰 전",
        howto: "정부24 또는 주민센터",
        howtoUrl: "https://www.gov.kr/",
        sourceSection: "공고문",
        evidence: "① 매수신청인이 미성년자인 경우 : ... 인감증명서",
      },
      {
        name: "대리입찰신청서",
        conditions: ["대리입찰"],
        conditionKeys: ["proxy"],
        copy: "",
        validity: "",
        method: "",
        due: "",
        count: "",
        stage: "입찰 전",
        howto: "",
        howtoUrl: "",
        sourceSection: "공고문",
        evidence: "② 대리인을 선임한 경우 : 대리입찰신청서",
      },
    ],
    groups: [],
    tableRows: [{ category: "공동입찰서류", name: "공동입찰서류", due: "입찰마감일시 전까지", method: "직접제출", generic: true }],
    tableGenericOnly: true,
    notes: ["서류마다 제출기한이 다를 수 있습니다."],
    reference: "이 목록은 참고용입니다. 빠진 항목이 있어도 진행은 막지 않으며, 최종 확인은 온비드 원문과 담당기관 기준입니다.",
  },
};
BASE_NOTICE.docChecklist.groups = [
  { condition: "미성년자", items: [BASE_NOTICE.docChecklist.items[0]] },
  { condition: "대리입찰", items: [BASE_NOTICE.docChecklist.items[1]] },
];

/** 추출 실패(B형·첨부에만 목록) 픽스처. */
function missingDocsNotice() {
  const notice = JSON.parse(JSON.stringify(BASE_NOTICE));
  notice.assetType = "공유재산";
  notice.minimumBidPrice = "비공개";
  // 「입찰방법」 절을 못 읽은 공고. 화면은 「원문 확인」으로 두어야 한다.
  notice.jointBidAllowed = "";
  notice.evictionResponsibility = "";
  notice.requiredDocs = [];
  notice.countdown = { state: "unknown", label: "", deadline: "", daysLeft: null };
  notice.relatedDocs = [
    {
      name: "공유재산 사용수익허가 입찰공고문.pdf",
      downloadUrl:
        "https://www.onbid.co.kr/op/cm/syc/filemng/filemngprcs/FileMngPrcsController/dnldFile.do?atchFileLstNo=17070043&atchSn=3&hashCrpsNo=COGFDOFI",
    },
  ];
  notice.noticeOutline = [];
  notice.glossary = [{ term: "공유재산", meaning: "지방자치단체가 소유한 재산입니다." }];
  notice.docChecklist = {
    status: "attachment_only",
    headline: "본문에서 서류 목록을 찾지 못했습니다. 첨부 공고문을 확인하십시오.",
    profile: {
      code: "B",
      label: "서류 목록이 첨부파일에 있을 가능성이 큰 유형입니다",
      detail: "이용기관이 직접 작성하는 공고입니다.",
      assetType: "공유재산",
    },
    items: [],
    groups: [],
    tableRows: [],
    tableGenericOnly: false,
    notes: ["자동 추출이 목록을 만들지 못한 상태입니다. 준비 보드는 그대로 진행할 수 있습니다."],
    reference: "이 목록은 참고용입니다. 빠진 항목이 있어도 진행은 막지 않으며, 최종 확인은 온비드 원문과 담당기관 기준입니다.",
  };
  notice.boardTasks[0].action = notice.docChecklist.headline;
  return notice;
}

async function analyzeWith(page, notice) {
  const dialogs = [];
  page.on("dialog", (dialog) => {
    dialogs.push(dialog.message());
    dialog.dismiss();
  });
  await page.goto("http://127.0.0.1:8975/");
  await page.evaluate((payload) => {
    window.fetch = async () => ({ ok: true, json: async () => ({ ok: true, notice: payload }) });
  }, notice);
  await page.locator("#notice-url").fill(notice.inputUrl);
  await page.locator("#analyze").click();
  await expect(page.locator("#analysis-result")).toContainText(notice.title);
  return dialogs;
}

test("S1·S2·S5·S6·S7 추출에 성공한 공고를 화면에 그린다", async ({ page }) => {
  await analyzeWith(page, BASE_NOTICE);

  // S1 A형 사전 안내가 분석 직후 화면(공고 가져오기)에 뜬다.
  await expect(page.locator("#analysis-result")).toContainText("본문에서 찾을 수 있음");
  await expect(page.locator("#analysis-result")).not.toContainText("첨부를 봐야 함");
  // S1 배지 «색». 문구만 단언하면 A/B를 같은 색으로 칠해도 초록이라 시각 신호가 무증명이 된다.
  // A형은 safe(초록), B형은 warn(주황)이며 아래 B형 테스트가 반대편을 잡는다.
  const aBadge = page.locator("#analysis-result .doc-source-notice .badge");
  await expect(aBadge).toHaveCount(1);
  await expect(aBadge).toHaveClass(/\bsafe\b/);
  await expect(aBadge).not.toHaveClass(/\bwarn\b/);

  // S6 마감 D-day 배지와 「알림 발송은 하지 않습니다」 표기.
  await expect(page.locator("#analysis-result")).toContainText("마감 D-2");
  await expect(page.locator("#analysis-result")).toContainText("알림 발송은 하지 않습니다");

  await page.locator("#prepare").click();

  // S2 조건별 그룹·부가조건 칩·발급처.
  const checklist = page.locator("#doc-checklist");
  await expect(checklist).toContainText("미성년자");
  await expect(checklist).toContainText("대리입찰");
  await expect(checklist).toContainText("인감증명서");
  await expect(checklist).toContainText("원본");
  await expect(checklist).toContainText("유효기간 1개월 이내 발급");
  await expect(checklist).toContainText("제출 직접제출");
  await expect(checklist).toContainText("기한 입찰마감일시 전까지");
  await expect(checklist).toContainText("발급처: 정부24 또는 주민센터");
  // 발급처를 모르는 서류는 지어내지 않고 확인 대상으로 남긴다.
  await expect(checklist).toContainText("공고 원문·첨부 서식 또는 담당기관 확인");
  // 참고용 성격이 화면에 남아 있어야 한다.
  await expect(checklist).toContainText("참고용");
  await expect(checklist).toContainText("막지 않으며");
  // 온비드 표의 구분명 행은 「구분명 그대로」로 표시한다.
  await expect(checklist).toContainText("구분명 그대로");
  // S3 음성 대조: 추출에 성공한 화면에는 실패 문구가 없어야 한다.
  await expect(checklist).not.toContainText("찾지 못했습니다");

  // S5 음성 대조: 금액이 정상이면 「비공개」가 뜨지 않는다.
  await expect(page.locator("#quick-facts")).toContainText("450,000,000");
  await expect(page.locator("#quick-facts")).not.toContainText("비공개");

  // S9 공동입찰 값과 명도책임을 원문 표시값 그대로 옮긴다.
  await expect(page.locator("#quick-facts")).toContainText("공동입찰");
  await expect(page.locator("#quick-facts")).toContainText("가능");
  await expect(page.locator("#quick-facts")).toContainText("명도책임");
  await expect(page.locator("#quick-facts")).toContainText("매수인 부담");
  // S9 음성 대조: 값을 읽었으면 「원문 확인」으로 흐리지 않는다.
  await expect(page.locator("#quick-facts")).not.toContainText("원문 확인");

  // S7 음성 대조: 첨부가 없으면 내려받기 링크가 없다.
  await expect(page.locator("#attachment-list")).toContainText("첨부파일이 없습니다");
  await expect(page.locator("#attachment-list a")).toHaveCount(0);

  // S8 공고문 항목·용어 안내.
  await expect(page.locator("#notice-outline")).toContainText("1. 입찰방법");
  await expect(page.locator("#glossary-list")).toContainText("압류재산");

  await page.screenshot({ path: "screenshots/validation/20_doc-checklist-extracted.png", fullPage: true });
});

test("S1·S3·S4·S5·S6·S7 못 뽑은 공고는 못 뽑았다고 말하고 진행을 막지 않는다", async ({ page }) => {
  const dialogs = await analyzeWith(page, missingDocsNotice());

  // S1 B형 사전 안내.
  await expect(page.locator("#analysis-result")).toContainText("첨부를 봐야 함");
  await expect(page.locator("#analysis-result")).not.toContainText("본문에서 찾을 수 있음");
  // S1 배지 «색» 음성 대조 — B형은 warn 이어야 한다. A형 테스트의 safe 단언과 짝이다.
  const bBadge = page.locator("#analysis-result .doc-source-notice .badge");
  await expect(bBadge).toHaveCount(1);
  await expect(bBadge).toHaveClass(/\bwarn\b/);
  await expect(bBadge).not.toHaveClass(/\bsafe\b/);

  // S6 음성 대조: 마감 상태를 못 읽으면 D-day 줄 자체를 만들지 않는다(빈 배지도 없다).
  await expect(page.locator("#analysis-result")).not.toContainText("마감 D-");
  await expect(page.locator("#analysis-result")).not.toContainText("알림 발송은 하지 않습니다");
  await expect(page.locator("#analysis-result .deadline-line .badge")).toHaveCount(0);

  // S4 서류가 비어 있어도 다음 단계 버튼이 열려 있어야 한다.
  const prepare = page.locator("#prepare");
  await expect(prepare).toBeEnabled();
  await prepare.click();

  // S3 못 뽑았음을 화면이 그대로 말한다.
  const checklist = page.locator("#doc-checklist");
  await expect(checklist).toContainText("찾지 못했습니다");
  await expect(checklist).toContainText("그대로 진행할 수 있습니다");
  // 「자격이 됩니다 / 자격이 없습니다」로 단정하지 않는다.
  await expect(checklist).not.toContainText("자격이 됩니다");
  await expect(checklist).not.toContainText("자격이 없습니다");

  // S4 준비 보드 어디에도 비활성 컨트롤이 없다.
  await expect(page.locator("#view-report [disabled]")).toHaveCount(0);
  await expect(page.locator("#task-list input[type=checkbox]:disabled")).toHaveCount(0);
  expect(dialogs).toEqual([]);

  // S5 최저입찰가격은 0이 아니라 「비공개」로 표시한다.
  await expect(page.locator("#quick-facts")).toContainText("비공개");
  await expect(page.locator("#quick-facts")).not.toContainText("최저입찰가격0");

  // S9 못 읽었으면 행을 숨기지 않고 「원문 확인」으로 둔다 — 숨기면 「해당 없다」로 읽힌다.
  await expect(page.locator("#quick-facts")).toContainText("공동입찰");
  await expect(page.locator("#quick-facts")).toContainText("원문 확인");
  // S9 음성 대조: 못 읽은 값을 「불가능」·「해당없음」으로 단정하지 않는다.
  await expect(page.locator("#quick-facts")).not.toContainText("불가능");
  await expect(page.locator("#quick-facts")).not.toContainText("해당없음");
  // S9 음성 대조: 명도책임은 값이 없으면 행 자체를 만들지 않는다.
  await expect(page.locator("#quick-facts")).not.toContainText("명도책임");

  // S7 첨부 내려받기 링크가 온비드 다운로드 엔드포인트를 가리킨다.
  const attachment = page.locator("#attachment-list a");
  await expect(attachment).toHaveCount(1);
  await expect(attachment).toHaveAttribute("href", /dnldFile\.do\?.*atchFileLstNo=17070043/);
  await expect(attachment).toHaveAttribute("href", /hashCrpsNo=COGFDOFI/);

  // S8 음성 대조: 목차가 비면 안내 문장으로 대체한다.
  await expect(page.locator("#notice-outline")).toContainText("찾지 못했습니다");

  await page.screenshot({ path: "screenshots/validation/21_doc-checklist-missing.png", fullPage: true });
});

/* ════════════════════════════════════════════════════════════════════════════
 * N1~N6 — 화면 상태 게이트 (2026-09-09 3팀 진단의 거짓 안내 P0 대응)
 *
 * 이 절은 «고치기 전에 붉어지는» 게이트다. N1·N2·N3·N5·N6 은 지금 붉는 것이 정상이고,
 * 붉음을 없애려고 src/** 를 고치는 것은 이 절의 목적이 아니다.
 *
 * 기대 문자열은 전부 아래에 «직접» 적는다. src/server.py 의 상수를 옮겨 오거나 주입한
 * 픽스처에서 되읽지 않는다 — 그러면 상수를 바꿔도 케이스가 함께 움직여 영원히 초록이다.
 * ════════════════════════════════════════════════════════════════════════════ */

// ── 판정 함수 J1~J6. 화면에서 «잰 사실»만 받는 순수 함수다. ────────────────────

/** J1. 「없다」는 단정과 첨부 목록이 같은 화면에 동시에 서면 위반. */
function violatesAbsenceClaimWithAttachments({ absenceClaimCount, attachmentRowCount }) {
  return absenceClaimCount > 0 && attachmentRowCount > 0;
}

// 「인식 범위가 한정적」 취지를 말하는 어휘. 여기 적힌 것이 기대값이다.
const SCOPE_LIMIT_NOTE_RE =
  /(?:인식|추출)[^.]{0,24}(?:범위|목록)[^.]{0,24}(?:한정|제한)|닫힌\s*(?:어휘|목록)|목록에\s*없는\s*서류|빠진\s*(?:서류|항목)[^.]{0,10}있을\s*수/;

/** J2. 추출됨이라고 말하면서 인식 범위가 한정적이라는 안내가 패널에 없으면 위반. */
function violatesMissingScopeNote({ status, panelNoteTexts }) {
  if (status !== "extracted") return false;
  return !panelNoteTexts.some((text) => SCOPE_LIMIT_NOTE_RE.test(text));
}

// 제출서류 표의 구분명 총평 경고 어휘. 서버가 전건 generic 일 때 쓰는 말과 같은 계열로 적었다.
const GENERIC_MIX_WARNING_RE = /구분명|실제\s*준비할\s*서류명/;

/** J3. 표에 실서류명과 구분명이 섞였는데 총평 경고가 패널에 없으면 위반. */
function violatesMissingGenericMixWarning({ tableRowCount, genericRowCount, panelNoteTexts }) {
  const realRowCount = tableRowCount - genericRowCount;
  if (!(genericRowCount > 0 && realRowCount > 0)) return false;
  return !panelNoteTexts.some((text) => GENERIC_MIX_WARNING_RE.test(text));
}

/** J4. 원문 값이 「비공개」인데 화면 칸에 숫자가 하나라도 보이면 위반. */
function violatesUndisclosedPriceShowsDigit({ sourceIsUndisclosed, cellText }) {
  if (!sourceIsUndisclosed) return false;
  return /[0-9]/.test(cellText);
}

/** J5. LLM 에 붙지 않았는데 「AI 가 했다」는 문구가 화면에 있으면 위반. */
function violatesAiClaimWithoutLlm({ llmStatus, claimHits }) {
  if (llmStatus === "connected") return false;
  return claimHits.length > 0;
}

// 링크가 「정상 링크와 다르다」고 말하는 표기 어휘.
const LINK_CAUTION_RE = /열리지\s*않을\s*수|확인\s*필요|미확인|물건번호\s*없음|500/;

/**
 * J6. pbctCdtnNo 가 없는 물건상세 링크를, 정상 링크와 같은 모양·같은 확신으로 제시하면 위반.
 * 「같은 확신」은 태그·class·속성 구성이 정상 링크와 동일하고 주의 표기도 없는 상태로 잰다.
 */
function violatesItemDetailSameConfidence({ itemDetailSignature, noticeDetailSignature, hasPbctCdtnNo, cautionTextPresent }) {
  if (!itemDetailSignature) return false;
  if (hasPbctCdtnNo) return false;
  if (cautionTextPresent) return false;
  return itemDetailSignature === noticeDetailSignature;
}

// ── 픽스처. 값은 src/server.py 를 읽고 옮겼다(PLAYED 2번 항목). ────────────────

function copyBase() {
  return JSON.parse(JSON.stringify(BASE_NOTICE));
}

/** N1 양성. 파산자산(profile C) → items 0 이면 attachments 검사보다 C 가 먼저 걸린다. */
function absenceClaimNotice() {
  const notice = copyBase();
  notice.assetType = "파산자산";
  notice.docChecklist = {
    status: "not_in_notice",
    headline: "이 공고에서는 서류 목록을 찾지 못했습니다.",
    profile: {
      code: "C",
      label: "원문에 서류 목록이 없을 수 있는 유형입니다",
      detail: "파산관재인이 개별 작성하는 공고라 본문과 첨부 어디에도 목록이 없는 표본이 있었습니다.",
      assetType: "파산자산",
    },
    items: [],
    groups: [],
    tableRows: [],
    tableGenericOnly: false,
    notes: [
      "자동 추출이 목록을 만들지 못한 상태입니다. 준비 보드는 그대로 진행할 수 있습니다.",
      "서류마다 제출기한이 다를 수 있습니다. 각 항목의 기한을 따로 확인하십시오.",
    ],
    reference: "이 목록은 참고용입니다. 빠진 항목이 있어도 진행은 막지 않으며, 최종 확인은 온비드 원문과 담당기관 기준입니다.",
  };
  notice.relatedDocs = [
    { name: "파산재단 공매공고문.pdf", downloadUrl: "https://www.onbid.co.kr/op/cm/syc/filemng/filemngprcs/FileMngPrcsController/dnldFile.do?atchFileLstNo=1&atchSn=1&hashCrpsNo=A" },
    { name: "입찰유의사항.pdf", downloadUrl: "https://www.onbid.co.kr/op/cm/syc/filemng/filemngprcs/FileMngPrcsController/dnldFile.do?atchFileLstNo=1&atchSn=2&hashCrpsNo=B" },
    { name: "감정평가서 요약.pdf", downloadUrl: "https://www.onbid.co.kr/op/cm/syc/filemng/filemngprcs/FileMngPrcsController/dnldFile.do?atchFileLstNo=1&atchSn=3&hashCrpsNo=C" },
  ];
  return notice;
}

/** N2 양성. items 1건이면 서버는 무조건 extracted 로 말한다(server.py:517-519). */
function partialExtractNotice() {
  const notice = copyBase();
  notice.docChecklist.status = "extracted";
  notice.docChecklist.headline = "공고 원문에서 서류 1건을 찾았습니다. 확인하셨습니까?";
  notice.docChecklist.items = [notice.docChecklist.items[0]];
  notice.docChecklist.groups = [{ condition: "미성년자", items: [notice.docChecklist.items[0]] }];
  notice.docChecklist.tableRows = [];
  notice.docChecklist.tableGenericOnly = false;
  // profile A + extracted 이면 서버가 붙이는 note 는 이 한 줄뿐이다(server.py:530-539).
  notice.docChecklist.notes = ["서류마다 제출기한이 다를 수 있습니다. 각 항목의 기한을 따로 확인하십시오."];
  return notice;
}

// 온비드 「제출서류」 표의 실제 서류명 칸 값. 표본 15건 전건이 이 셋 중 하나였다.
const REAL_ONBID_GENERIC_NAMES = ["공동입찰서류", "-", "보증서등(공고문 확인)"];

/** N3 양성. 실서류명 1행 + 위 실측 generic 3행. all() 이 False 라 총평 note 가 붙지 않는다. */
function mixedTableNotice() {
  const notice = partialExtractNotice();
  notice.docChecklist.tableRows = [
    { category: "매수신청", name: "인감증명서", due: "입찰마감일시 전까지", method: "직접제출", generic: false },
    { category: "공동입찰서류", name: REAL_ONBID_GENERIC_NAMES[0], due: "입찰마감일시 전까지", method: "직접제출", generic: true },
    { category: "보증금", name: REAL_ONBID_GENERIC_NAMES[1], due: "", method: "", generic: true },
    { category: "보증", name: REAL_ONBID_GENERIC_NAMES[2], due: "", method: "", generic: true },
  ];
  notice.docChecklist.tableGenericOnly = false;
  return notice;
}

/** N3 음성. 전건 generic → generic_only 가 True 라 서버가 총평 note 를 붙인다. */
function allGenericTableNotice() {
  const notice = partialExtractNotice();
  notice.docChecklist.tableRows = REAL_ONBID_GENERIC_NAMES.map((name, index) => ({
    category: ["공동입찰서류", "보증금", "보증"][index],
    name,
    due: "",
    method: "",
    generic: true,
  }));
  notice.docChecklist.tableGenericOnly = true;
  notice.docChecklist.notes = [
    "온비드 제출서류 표의 서류명 칸은 구분명(예: 공동입찰서류)이라 실제 준비할 서류명이 아닙니다.",
    "서류마다 제출기한이 다를 수 있습니다. 각 항목의 기한을 따로 확인하십시오.",
  ];
  return notice;
}

/** N4 양성. lowstBidPrc = 0 또는 비공개 코드일 때 서버가 넣는 값(server.py:667-672). */
function undisclosedPriceNotice() {
  const notice = copyBase();
  notice.minimumBidPrice = "비공개";
  return notice;
}

/** N5 양성/음성. llmStatus 만 바꾼다. */
function coachNotice(llmStatus) {
  const notice = copyBase();
  notice.aiCoach.llmStatus = llmStatus;
  return notice;
}

/**
 * N6. 공고상세 입력이면 pbctCdtnNo 가 비어 make_onbid_url 이 그 파라미터를 버린다.
 * 그래도 build_related_urls 는 onbidCltrno 만 보고 itemDetail 을 연다(server.py:1061).
 */
function linkNotice({ withPbctCdtnNo }) {
  const notice = copyBase();
  const itemBase =
    "https://www.onbid.co.kr/op/cltrpbancinf/cltrdtl/CltrDtlController/mvmnCltrDtl.do" +
    "?cltrScrnGrpCd=0001&onbidCltrno=1413572&onbidPbancNo=886933&pbctNo=10032196";
  notice.pageType = withPbctCdtnNo ? "물건 상세" : "공고 상세";
  notice.relatedUrls = {
    source: notice.sourceUrl,
    noticeDetail:
      "https://www.onbid.co.kr/op/cltrpbancinf/pbanc/pbancdtlinf/PbancDtlInqController/mvmnPbancDtl.do?onbidPbancNo=886933",
    itemDetail: withPbctCdtnNo ? `${itemBase}&pbctCdtnNo=5988631` : itemBase,
  };
  return notice;
}

// ── 화면 측정 헬퍼. 창은 전부 «그 블록» 으로 좁힌다. ──────────────────────────

async function openBoard(page, notice) {
  await analyzeWith(page, notice);
  await page.locator("#prepare").click();
  await expect(page.locator("#doc-checklist .doc-panel")).toHaveCount(1);
}

/** 패널 «수준» 의 안내 문장만 모은다. 접힌 details 안 행별 표기는 제외한다. */
async function panelNoteTexts(page) {
  return page.locator("#doc-checklist .doc-panel > .doc-notes li, #doc-checklist .doc-panel > .doc-reference").allTextContents();
}

async function anchorSignature(locator) {
  return locator.evaluate((el) => {
    const attributeNames = [...el.attributes].map((attr) => attr.name).sort().join(",");
    return `${el.tagName}|${el.className}|${attributeNames}`;
  });
}

// ── N0. 판정 함수를 화면 없이 직접 부른다. ────────────────────────────────────
// 배선 단정과 별개다. J1~J6 의 본문을 `return false` 로 비우면 이 케이스가 붉는다.

test("N0 판정 함수 J1~J6 을 직접 호출해 단정한다", () => {
  expect(violatesAbsenceClaimWithAttachments({ absenceClaimCount: 1, attachmentRowCount: 3 })).toBe(true);
  expect(violatesAbsenceClaimWithAttachments({ absenceClaimCount: 0, attachmentRowCount: 3 })).toBe(false);
  expect(violatesAbsenceClaimWithAttachments({ absenceClaimCount: 1, attachmentRowCount: 0 })).toBe(false);

  expect(violatesMissingScopeNote({ status: "extracted", panelNoteTexts: ["서류마다 제출기한이 다를 수 있습니다."] })).toBe(true);
  expect(
    violatesMissingScopeNote({
      status: "extracted",
      panelNoteTexts: ["자동으로 인식하는 서류명 범위가 한정적입니다. 원문과 첨부를 대조하십시오."],
    }),
  ).toBe(false);
  expect(violatesMissingScopeNote({ status: "attachment_only", panelNoteTexts: [] })).toBe(false);

  expect(violatesMissingGenericMixWarning({ tableRowCount: 4, genericRowCount: 3, panelNoteTexts: ["서류마다 제출기한이 다를 수 있습니다."] })).toBe(true);
  expect(violatesMissingGenericMixWarning({ tableRowCount: 4, genericRowCount: 3, panelNoteTexts: ["서류명 칸이 구분명이라 실제 준비할 서류명이 아닙니다."] })).toBe(false);
  expect(violatesMissingGenericMixWarning({ tableRowCount: 3, genericRowCount: 3, panelNoteTexts: [] })).toBe(false);
  expect(violatesMissingGenericMixWarning({ tableRowCount: 3, genericRowCount: 0, panelNoteTexts: [] })).toBe(false);

  expect(violatesUndisclosedPriceShowsDigit({ sourceIsUndisclosed: true, cellText: "0" })).toBe(true);
  expect(violatesUndisclosedPriceShowsDigit({ sourceIsUndisclosed: true, cellText: "비공개" })).toBe(false);
  expect(violatesUndisclosedPriceShowsDigit({ sourceIsUndisclosed: false, cellText: "450,000,000" })).toBe(false);

  expect(violatesAiClaimWithoutLlm({ llmStatus: "rule_based", claimHits: ["AI 분석 완료"] })).toBe(true);
  expect(violatesAiClaimWithoutLlm({ llmStatus: "connected", claimHits: ["AI 분석 완료"] })).toBe(false);
  expect(violatesAiClaimWithoutLlm({ llmStatus: "rule_based", claimHits: [] })).toBe(false);

  const same = "A||href,rel,target";
  expect(violatesItemDetailSameConfidence({ itemDetailSignature: same, noticeDetailSignature: same, hasPbctCdtnNo: false, cautionTextPresent: false })).toBe(true);
  expect(violatesItemDetailSameConfidence({ itemDetailSignature: same, noticeDetailSignature: same, hasPbctCdtnNo: true, cautionTextPresent: false })).toBe(false);
  expect(violatesItemDetailSameConfidence({ itemDetailSignature: same, noticeDetailSignature: same, hasPbctCdtnNo: false, cautionTextPresent: true })).toBe(false);
  expect(violatesItemDetailSameConfidence({ itemDetailSignature: "A|caution|class,href,rel,target", noticeDetailSignature: same, hasPbctCdtnNo: false, cautionTextPresent: false })).toBe(false);
  expect(violatesItemDetailSameConfidence({ itemDetailSignature: "", noticeDetailSignature: same, hasPbctCdtnNo: false, cautionTextPresent: false })).toBe(false);
});

// ── N1~N6 배선. 픽스처를 실제 화면에 태우고 J1~J6 으로 판정한다. ───────────────
//
// N0 이 초록인 것은 «판정 함수가 산다»는 뜻일 뿐이다. 화면이 그 위반을 실제로 만드는지는
// 이 절에서만 잰다. 여기가 없으면 AXES 의 N1~N6 「커버 Y」는 무증명이다.
//
// 기대 문자열은 전부 아래에 «직접» 적는다 — src/app.js 의 docChecklistStatusBadge 나
// 픽스처에서 되읽으면 그 상수를 바꿔도 케이스가 함께 움직여 영원히 초록이 된다.

/**
 * 「원문에 없음」 같은 «단정» 배지를 패널 머리에서만 센다.
 *
 * 창을 `.doc-panel > .doc-head` 로 좁힌다 — 같은 `.badge` 가 사전 안내(.doc-source-notice)와
 * 접힌 details 안에도 있다.
 * 완전일치로 센다 — profile C 배지 「원문에 없을 수 있음」은 «에두른» 표기라 위반이 아니고,
 * 부분일치로 세면 그 둘이 같은 것으로 뭉개진다.
 */
const ABSENCE_CLAIM_BADGES = ["원문에 없음", "원문에 없습니다"];

async function absenceClaimCount(page) {
  const texts = await page.locator("#doc-checklist .doc-panel > .doc-head .badge").allTextContents();
  return texts.filter((text) => ABSENCE_CLAIM_BADGES.includes(text.trim())).length;
}

async function attachmentRowCount(page) {
  return page.locator("#attachment-list .attachment-row").count();
}

/** 접힌 온비드 표의 행 수와 그중 「구분명 그대로」로 표기된 행 수. */
async function tableRowCounts(page) {
  const rows = await page.locator("#doc-checklist .doc-panel .doc-table p").allTextContents();
  return { tableRowCount: rows.length, genericRowCount: rows.filter((text) => text.includes("구분명 그대로")).length };
}

/** 화면에 뜬 상태 배지 라벨. status 를 픽스처에서 되읽지 않고 «화면에서» 되돌린다. */
const STATUS_BADGE_TO_STATUS = {
  추출됨: "extracted",
  "본문 미기재": "attachment_only",
  "원문에 없음": "not_in_notice",
  "추출 실패": "not_found",
};

async function statusFromScreen(page) {
  const texts = await page.locator("#doc-checklist .doc-panel > .doc-head .badge").allTextContents();
  for (const text of texts) {
    const status = STATUS_BADGE_TO_STATUS[text.trim()];
    if (status) return status;
  }
  return "unknown";
}

/** 「AI 가 했다」고 읽히는 문구. 여기 적힌 것이 기대값이다. */
const AI_CLAIM_PHRASES = ["AI 분석 완료", "AI 누락 점검", "AI가 미해결 항목만 골랐습니다", "AI가 먼저 볼 빈칸"];

async function aiClaimHits(page, scope) {
  const text = (await page.locator(scope).innerText()).replace(/\s+/g, " ");
  return AI_CLAIM_PHRASES.filter((phrase) => text.includes(phrase.replace(/\s+/g, " ")));
}

/** 최저입찰가격 칸의 «보이는» 값. 요약(#quick-facts)과 분석 직후 두 창을 따로 잰다. */
async function minimumBidCellTexts(page) {
  const quick = page.locator("#quick-facts .fact-row", { hasText: "최저입찰가격" }).locator("strong");
  const preview = page.locator("#analysis-result .preview-grid div", { hasText: "최저입찰가격" }).locator("strong");
  return { quick: (await quick.innerText()).trim(), preview: (await preview.innerText()).trim() };
}

test("N1 「원문에 없음」 단정과 첨부 목록을 같은 화면에 함께 세우지 않는다", async ({ page }) => {
  await openBoard(page, absenceClaimNotice());
  const claims = await absenceClaimCount(page);
  const attachments = await attachmentRowCount(page);
  // 픽스처가 의도한 자리에 «도달했는지» 먼저 단정한다 — 못 닿으면 J1 은 영구 초록이다.
  expect(claims, "도달: 단정 배지").toBeGreaterThan(0);
  expect(attachments, "도달: 첨부 3건").toBe(3);
  expect(violatesAbsenceClaimWithAttachments({ absenceClaimCount: claims, attachmentRowCount: attachments })).toBe(false);
});

test("N1 음성 — 정상 A형 + 첨부 1건은 붉지 않는다", async ({ page }) => {
  const notice = copyBase();
  notice.relatedDocs = [{ name: "공고문.pdf", downloadUrl: "https://www.onbid.co.kr/x/dnldFile.do?atchFileLstNo=9&atchSn=1&hashCrpsNo=Z" }];
  await openBoard(page, notice);
  const claims = await absenceClaimCount(page);
  const attachments = await attachmentRowCount(page);
  expect(claims, "도달: 단정 배지 없음").toBe(0);
  expect(attachments, "도달: 첨부 1건").toBe(1);
  expect(violatesAbsenceClaimWithAttachments({ absenceClaimCount: claims, attachmentRowCount: attachments })).toBe(false);
});

test("N2 「추출됨」이라고 말하면 인식 범위가 한정적이라는 안내를 함께 세운다", async ({ page }) => {
  await openBoard(page, partialExtractNotice());
  const status = await statusFromScreen(page);
  const notes = await panelNoteTexts(page);
  expect(status, "도달: 추출됨 배지").toBe("extracted");
  expect(notes.length, "도달: 패널 note 존재").toBeGreaterThan(0);
  expect(violatesMissingScopeNote({ status, panelNoteTexts: notes })).toBe(false);
});

test("N2 음성 — B형(본문 미기재)에는 범위 한정 안내를 요구하지 않는다", async ({ page }) => {
  await openBoard(page, missingDocsNotice());
  const status = await statusFromScreen(page);
  expect(status, "도달: 본문 미기재 배지").toBe("attachment_only");
  expect(violatesMissingScopeNote({ status, panelNoteTexts: await panelNoteTexts(page) })).toBe(false);
});

test("N3 실서류명과 구분명이 섞인 표에는 총평 경고를 세운다", async ({ page }) => {
  await openBoard(page, mixedTableNotice());
  const { tableRowCount, genericRowCount } = await tableRowCounts(page);
  const notes = await panelNoteTexts(page);
  expect(tableRowCount, "도달: 표 4행").toBe(4);
  expect(genericRowCount, "도달: 혼합 구분명 3행").toBe(3);
  expect(violatesMissingGenericMixWarning({ tableRowCount, genericRowCount, panelNoteTexts: notes })).toBe(false);
});

test("N3 음성 — 전건 구분명이면 서버가 붙인 총평이 있어 붉지 않는다", async ({ page }) => {
  await openBoard(page, allGenericTableNotice());
  const { tableRowCount, genericRowCount } = await tableRowCounts(page);
  expect(tableRowCount, "도달: 표 3행").toBe(3);
  expect(genericRowCount, "도달: 전건 구분명").toBe(3);
  expect(violatesMissingGenericMixWarning({ tableRowCount, genericRowCount, panelNoteTexts: await panelNoteTexts(page) })).toBe(false);
});

test("N4 최저입찰가격이 비공개면 두 창 어디에도 숫자를 쓰지 않는다", async ({ page }) => {
  await openBoard(page, undisclosedPriceNotice());
  const cells = await minimumBidCellTexts(page);
  expect(violatesUndisclosedPriceShowsDigit({ sourceIsUndisclosed: true, cellText: cells.quick })).toBe(false);
  expect(violatesUndisclosedPriceShowsDigit({ sourceIsUndisclosed: true, cellText: cells.preview })).toBe(false);
});

test("N4 음성 — 정상 금액은 숫자가 있어도 붉지 않는다", async ({ page }) => {
  await openBoard(page, copyBase());
  const cells = await minimumBidCellTexts(page);
  // 도달 확인 — 칸에 숫자가 «실제로» 있어야 이 음성 대조가 의미를 가진다.
  expect(cells.quick, "도달: 요약 칸 숫자").toMatch(/[0-9]/);
  expect(cells.preview, "도달: 분석직후 칸 숫자").toMatch(/[0-9]/);
  expect(violatesUndisclosedPriceShowsDigit({ sourceIsUndisclosed: false, cellText: cells.quick })).toBe(false);
  expect(violatesUndisclosedPriceShowsDigit({ sourceIsUndisclosed: false, cellText: cells.preview })).toBe(false);
});

test("N5 LLM 에 붙지 않았으면 「AI 가 했다」는 문구를 세우지 않는다", async ({ page }) => {
  await analyzeWith(page, coachNotice("rule_based"));
  const hits = await aiClaimHits(page, "#analysis-result");
  expect(violatesAiClaimWithoutLlm({ llmStatus: "rule_based", claimHits: hits })).toBe(false);
});

test("N5 음성 — LLM 에 붙었으면 같은 문구가 있어도 붉지 않는다", async ({ page }) => {
  await analyzeWith(page, coachNotice("connected"));
  const hits = await aiClaimHits(page, "#analysis-result");
  // 도달 확인 — 문구가 «있는» 상태에서만 이 음성 대조가 llmStatus 분기를 잰다.
  expect(hits.length, "도달: AI 문구 존재").toBeGreaterThan(0);
  expect(violatesAiClaimWithoutLlm({ llmStatus: "connected", claimHits: hits })).toBe(false);
});

test("N6 pbctCdtnNo 가 없는 물건상세 링크를 정상 링크와 같은 확신으로 세우지 않는다", async ({ page }) => {
  await analyzeWith(page, linkNotice({ withPbctCdtnNo: false }));
  const itemDetail = page.locator("#analysis-result .linked-pages a", { hasText: "물건상세" });
  const noticeDetail = page.locator("#analysis-result .linked-pages a", { hasText: "공고보기" });
  await expect(itemDetail).toHaveCount(1);
  await expect(noticeDetail).toHaveCount(1);
  const href = await itemDetail.getAttribute("href");
  expect(href, "도달: pbctCdtnNo 없음").not.toContain("pbctCdtnNo");
  const linkedText = (await page.locator("#analysis-result .linked-pages").innerText()).replace(/\s+/g, " ");
  expect(
    violatesItemDetailSameConfidence({
      itemDetailSignature: await anchorSignature(itemDetail),
      noticeDetailSignature: await anchorSignature(noticeDetail),
      hasPbctCdtnNo: false,
      cautionTextPresent: LINK_CAUTION_RE.test(linkedText),
    }),
  ).toBe(false);
});

test("N6 음성 — pbctCdtnNo 가 있으면 같은 모양이어도 붉지 않는다", async ({ page }) => {
  await analyzeWith(page, linkNotice({ withPbctCdtnNo: true }));
  const itemDetail = page.locator("#analysis-result .linked-pages a", { hasText: "물건상세" });
  const noticeDetail = page.locator("#analysis-result .linked-pages a", { hasText: "공고보기" });
  const href = await itemDetail.getAttribute("href");
  expect(href, "도달: pbctCdtnNo 있음").toContain("pbctCdtnNo=5988631");
  // 도달 확인 — 두 링크가 «같은 모양» 인 상태에서만 이 음성 대조가 hasPbctCdtnNo 분기를 잰다.
  expect(await anchorSignature(itemDetail)).toBe(await anchorSignature(noticeDetail));
  expect(
    violatesItemDetailSameConfidence({
      itemDetailSignature: await anchorSignature(itemDetail),
      noticeDetailSignature: await anchorSignature(noticeDetail),
      hasPbctCdtnNo: true,
      cautionTextPresent: false,
    }),
  ).toBe(false);
});

// ── N0. 커버리지 «측정» 함수를 화면 없이 직접 부른다. ─────────────────────────
// 배너의 「도는 테스트가 없는 축」은 measureAxisCoverage 가 «센» 결과다. 그 함수 본문을
// 비우면 배너가 「0개」라고 거짓말하는데, 배선 단정만으로는 잡히지 않는다(2026-09-09 자작 변이).
// 그래서 여기서 함수를 직접 부른다.

test("N0 커버리지 측정 함수를 직접 호출해 단정한다", () => {
  const { AXES, measureAxisCoverage, p0WithoutAxis } = require("./screen-axes");

  // 양성 하나·음성 하나만 있는 제목 묶음.
  const sparse = measureAxisCoverage(["S1·S2 무언가를 그린다", "N1 무언가", "N1 음성 — 붉지 않는다"]);
  expect(sparse.positive.get("S1")).toBe(1);
  expect(sparse.positive.get("N1")).toBe(1);
  expect(sparse.negative.get("N1")).toBe(1);
  // 음성 제목은 양성으로 세지 않는다.
  expect(sparse.positive.get("N1")).not.toBe(2);
  expect(sparse.absent).toContain("N2 부분 추출을 완전한 것처럼 말함");
  // 표가 「커버 Y」라고 적은 축인데 제목에 없으면 어긋남으로 잡힌다.
  expect(sparse.declaredButAbsent).toContain("N2");
  // 양성만 있고 음성이 없는 축.
  expect(sparse.noNegative).toContain("S1");
  expect(sparse.noNegative).not.toContain("N1");

  // 붉히면 안 되는 입력 — 모든 축에 양성·음성이 하나씩 있으면 어긋남이 없다.
  const full = measureAxisCoverage(AXES.flatMap((axis) => [`${axis[0]} 양성`, `${axis[0]} 음성 — 붉지 않는다`]));
  expect(full.absent).toEqual([]);
  expect(full.declaredButAbsent).toEqual([]);
  expect(full.noNegative).toEqual([]);

  // P0 ↔ 축 표. 축이 null 인 것만 세고, 매핑이 있는 것은 세지 않는다.
  expect(p0WithoutAxis()).toEqual([
    "P0-5 「최대 30분 지연」 안내 부재",
    "P0-6 저장하지 않은 관심공고를 「2건」으로 셈",
  ]);
});
