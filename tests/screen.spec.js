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
  // baseURL(playwright.config.js의 use.baseURL)을 따라간다 — 워크트리마다 다른 포트를 써도
  // 이 한 줄만 고치면 된다. 절대 URL로 8975를 박아두면 다른 워크트리 포트에서는 영원히 메인
  // 워크트리 서버로 접속해 #profile-next 를 못 찾는 타임아웃이 난다(2026-10-14 phase5).
  await page.goto("/");
  await page.evaluate((payload) => {
    window.fetch = async () => ({ ok: true, json: async () => ({ ok: true, notice: payload }) });
  }, notice);
  // 입력~분석 마법사 1p(유형/목적)를 지나야 2p(URL) 필드가 보인다(2026-10-12 phase1).
  await page.locator("#profile-next").click();
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

  // S2 조건별 그룹·부가조건 칩·발급처. 체크리스트는 기본 접힘이라 먼저 펼친다.
  await page.locator("#doc-checklist-details > summary").click();
  const checklist = page.locator("#doc-checklist");
  // "대리입찰" 조건부 그룹(대리입찰신청서 포함)은 질문에 "예"로 답해야 보인다(2026-10-12 phase3).
  await checklist.locator('button[data-doc-condition="proxy"][data-doc-condition-value="yes"]').click();
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
    // 첨부가 있는 C형의 문안. 서버가 이 형태를 만드는 것은 파이썬 단위가 증명한다
    // (test_docs_extraction.py 「B1 C형 첨부 존재 언급」 + 음성 2건).
    // 관측한 것만 말한다 — 본문은 읽었고 첨부는 열지 않았다. 표본으로 예측하지 않는다.
    headline: "본문에서 서류 목록을 찾지 못했습니다. 첨부 3건이 있습니다.",
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
  // profile A + extracted 이면 서버가 붙이는 note 는 이 둘이다(server.py:546-562).
  // 범위 한정 안내를 서버가 실제로 붙이는 것은 파이썬 단위가 증명한다
  // (test_docs_extraction.py 「B1 A형 인식 범위 한정 안내」 + 음성 대조 1건).
  notice.docChecklist.notes = [
    "자동 인식은 닫힌 어휘 기준이라 인식 범위가 한정적입니다. 목록에 없는 서류가 있을 수 있으니 원문과 대조하십시오.",
    "서류마다 제출기한이 다를 수 있습니다. 각 항목의 기한을 따로 확인하십시오.",
  ];
  return notice;
}

// 온비드 「제출서류」 표의 실제 서류명 칸 값. 표본 15건 전건이 이 셋 중 하나였다.
const REAL_ONBID_GENERIC_NAMES = ["공동입찰서류", "-", "보증서등(공고문 확인)"];

/**
 * N3 양성. 실서류명 1행 + 위 실측 generic 3행.
 * 서버는 이제 any() 로 보므로 섞인 표에도 총평 note 를 붙인다(server.py:546-551).
 * 그 배선은 파이썬 단위가 아니라 여기서 잰다 — 화면이 그 note 를 실제로 그리는지가 축이다.
 */
function mixedTableNotice() {
  const notice = partialExtractNotice();
  notice.docChecklist.tableRows = [
    { category: "매수신청", name: "인감증명서", due: "입찰마감일시 전까지", method: "직접제출", generic: false },
    { category: "공동입찰서류", name: REAL_ONBID_GENERIC_NAMES[0], due: "입찰마감일시 전까지", method: "직접제출", generic: true },
    { category: "보증금", name: REAL_ONBID_GENERIC_NAMES[1], due: "", method: "", generic: true },
    { category: "보증", name: REAL_ONBID_GENERIC_NAMES[2], due: "", method: "", generic: true },
  ];
  notice.docChecklist.tableGenericOnly = false;
  notice.docChecklist.notes = [
    "온비드 제출서류 표의 서류명 칸은 구분명(예: 공동입찰서류)이라 실제 준비할 서류명이 아닙니다.",
    ...notice.docChecklist.notes,
  ];
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
 * build_related_urls 는 itemDetail 을 지우지 않고 itemDetailUncertain 플래그를 함께
 * 보낸다(server.py:1084-1091) — 링크를 없애면 물건상세로 가는 길이 통째로 사라진다.
 * 서버가 그 플래그를 실제로 세우는 것은 파이썬 단위가 증명한다.
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
    ...(withPbctCdtnNo ? {} : { itemDetailUncertain: true }),
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

async function docStatusBadgeTexts(page) {
  const texts = await page.locator("#doc-checklist .doc-panel > .doc-head .badge").allTextContents();
  return texts.map((text) => text.trim());
}

/** 「원문 전체에 없다」고 단정하는 배지의 수. 「본문에 없음」은 관측 진술이라 세지 않는다. */
async function absenceClaimCount(page) {
  return (await docStatusBadgeTexts(page)).filter((text) => ABSENCE_CLAIM_BADGES.includes(text)).length;
}

/**
 * not_in_notice 분기에 «닿았는지» 를 잰다. 판정(단정했는가)과 별개다 —
 * 도달을 「단정 배지 > 0」으로 재면 고친 뒤 그 단정이 깨져서, 위반이 사라진 것과
 * 픽스처가 분기에 못 닿은 것이 같은 붉음으로 보인다(2026-09-10 실측).
 */
async function absenceBranchReached(page) {
  return (await docStatusBadgeTexts(page)).some((text) => text.includes("없음"));
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
  expect(await absenceBranchReached(page), "도달: not_in_notice 배지").toBe(true);
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

  // 축 코드를 손으로 박는다. AXES 에서 축을 지우면 아래 full 묶음의 입력과 기대가 «함께»
  // 줄어 아무도 붉지 않는다 — 이 한 줄이 그 자리를 막는다(2026-09-09 r2 P2-2).
  expect(AXES.map((axis) => axis[0])).toEqual([
    "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10", "S11", "S12", "S13",
    "N0", "N1", "N2", "N3", "N4", "N5", "N6",
  ]);

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

/* ════════════════════════════════════════════════════════════════════════════
 * 준비 단계 스테퍼 · 단계 잠금(3팀 UIUX품질팀, team-reports/2026-10-09-uiux-agentic-journey).
 *
 * 아래 테스트는 위 S/N 축 표·커버리지 집계(screen-axes.js)와 무관하다 — 제목에 S<숫자>·N<숫자>
 * 패턴을 쓰지 않아 axisCodes()에 걸리지 않는다(기존 축 집계를 오염시키지 않기 위한 의도적 선택).
 *
 * server.py build_tasks()가 만드는 4개 고정 id(notice-type·bid-period·price·documents)를
 * 모두 채운 픽스처가 필요하다 — BASE_NOTICE는 documents 하나만 가진 "단계 밖" 픽스처라, 1단계
 * (notice-type·bid-period)가 공집합이 되어 매번 공집합 완료(vacuous done)로 통과해 버린다.
 * phase4(2026-10-13)에서 "agency" task(담당기관에 물어볼 질문 정리)를 build_tasks()에서
 * 제거했다 — 3단계는 이제 price 하나만 남고, 그 자리는 renderBidParticipationInfo()/
 * renderBidAskBox()(정보 리스트 + AI 질문창)가 대신한다.
 * ════════════════════════════════════════════════════════════════════════════ */

function stagedNotice() {
  const notice = copyBase();
  const task = (id, title, action) => ({
    id,
    title,
    action,
    due: "입찰 전",
    detail: "참고용 상세 설명입니다.",
    question: "문의 문장입니다.",
    source: "온비드 상세 페이지",
    cta: "온비드 원문",
    url: "https://www.onbid.co.kr/",
    defaultDone: false,
  });
  notice.boardTasks = [
    task("notice-type", "공고 유형 확인", "국유재산 / 임대"),
    task("bid-period", "입찰기간 확인", "2026-10-10 ~ 2026-10-12"),
    task("documents", "제출서류 확인", "인감증명서 / 주민등록등본"),
    task("price", "최저입찰가격 확인", "100,000,000"),
  ];
  notice.boardTasks[2].detail = "이 목록은 참고용이며 빠진 항목이 있어도 진행을 막지 않습니다.";
  return notice;
}

test("준비 단계 — 1단계를 모두 체크해야 2단계 체크박스가 열리고, 되돌리면 다시 잠긴다", async ({ page }) => {
  await analyzeWith(page, stagedNotice());
  await page.locator("#prepare").click();

  const noticeType = page.locator('[data-task-id="notice-type"]');
  const bidPeriod = page.locator('[data-task-id="bid-period"]');
  const documents = page.locator('[data-task-id="documents"]');
  const price = page.locator('[data-task-id="price"]');

  // 배치: 단계 표시·진행률은 할 일 목록 바로 아래, AI 코치 카드는 보드 맨 아래다(2026-10-19 동원님 지시).
  await expect(page.locator(".task-panel > #task-list + #board-status")).toHaveCount(1);
  await expect(page.locator("#view-report > .panel > #board-coach:last-child")).toHaveCount(1);

  // 도달: 1단계는 열려 있고 2·3단계는 잠겨 있다.
  await expect(noticeType).toBeEnabled();
  await expect(bidPeriod).toBeEnabled();
  await expect(documents).toBeDisabled();
  await expect(price).toBeDisabled();
  await expect(page.locator(".stage-group-heading.is-locked")).toHaveCount(2);

  // 잠긴 단계는 기본으로 접혀 있다(2026-10-11 설계, "한 번에 너무 많다" 체감 해소) —
  // 눌러서 미리 볼 수 있는 길만 남겨 두므로, 먼저 단계 헤딩을 눌러 펼친다.
  const documentsCard = documents.locator("xpath=ancestor::article[contains(@class,'task-item')]");
  await documentsCard.locator("xpath=ancestor::details[contains(@class,'stage-group')]").locator("> summary").click();
  // 펼친 뒤에는 "자세히"·원문 값이 항상 보인다(ux-audit §⑴).
  // 「자세히」 자체는 기본으로 접혀 있다(2026-10-19 · 텍스트가 너무 많다는 지적). 원문 링크는
  // 그 안에 있으므로 한 번 눌러 펼쳐야 보인다.
  const documentsDetail = documentsCard.locator("details.task-detail");
  await expect(documentsDetail.locator("> summary")).toBeVisible();
  expect(await documentsDetail.evaluate((el) => el.open)).toBe(false);
  await expect(documentsCard.locator("a", { hasText: "온비드 원문" })).toBeHidden();
  await expect(documentsCard.locator(".task-action-value")).toBeVisible();
  await documentsDetail.locator("> summary").click();
  await expect(documentsCard.locator("a", { hasText: "온비드 원문" })).toBeVisible();

  // 1단계를 모두 체크하면 2단계(문서)만 열리고 3단계(가격)는 그대로 잠긴다.
  await noticeType.check();
  await bidPeriod.check();
  await expect(documents).toBeEnabled();
  await expect(price).toBeDisabled();
  await expect(page.locator(".stage-group-heading.is-done")).toHaveCount(1);

  // 2단계(문서)까지 체크하면 3단계가 열린다.
  await documents.check();
  await expect(price).toBeEnabled();

  // 되돌리기: 1단계 체크를 해제하면 2단계는 즉시 재잠김 — 단, documents 체크값은 보존된다.
  await noticeType.uncheck();
  await expect(documents).toBeDisabled();
  await expect(documents).toBeChecked();
  await expect(page.locator(".stage-group-heading.is-locked")).toHaveCount(2);

  // 「안내 수준」 버튼은 「자세히」를 모두 펼치고 다시 접는다. 완료된 카드(bid-period·documents)는
  // 펼치지 않는다. 버튼은 경험 수준 질문에 답한 뒤에만 보인다.
  const detailOpen = (taskId) =>
    page.locator(`article.task-item:has([data-task-id="${taskId}"]) details.task-detail`).evaluate((el) => el.open);
  await page.locator("[data-experience-skip]").click();
  expect(await detailOpen("notice-type")).toBe(false);
  await page.locator("[data-experience-toggle]").click();
  expect(await detailOpen("notice-type")).toBe(true);
  expect(await detailOpen("documents")).toBe(false);
  await page.locator("[data-experience-toggle]").click();
  expect(await detailOpen("notice-type")).toBe(false);
});

// AI 코치 질문창이 서버의 온비드 용어 설명(references)을 그리는가. /api/ask 응답은 픽스처다 —
// 서버가 실제로 references 를 싣는지는 tests/test_docs_extraction.py 의 D3 축이 본다.
test("AI 코치 질문 — 온비드 용어 설명이 오면 「담당기관 문의 필요」 대신 그 설명과 출처를 보여 준다", async ({ page }) => {
  await analyzeWith(page, stagedNotice());
  await page.locator("#prepare").click();
  const answerBox = page.locator("#coach-question-result");
  const askWith = async (result) => {
    await page.evaluate((payload) => {
      window.fetch = async () => ({ ok: true, json: async () => ({ ok: true, result: payload }) });
    }, result);
    await page.locator("#coach-question-input").fill("매각결정기일이 뭐지?");
    await page.locator("#board-coach [data-ask-question]").click();
  };
  const ref = (text, scope = "") => ({ term: "매각결정기일", text, source: "시험용 출처", scope });
  const declinedNote = "이 질문에는 답하지 않았습니다. 질문에 나온 용어의 온비드 설명만 보여 드립니다.";
  const partialNote = "질문하신 내용 가운데 위 설명에 없는 것은 공고 원문이나 담당기관에서 확인하세요.";
  const offlineNote = "AI 코치에 연결되지 않아 질문에 나온 용어의 온비드 설명만 보여 드립니다.";
  const declined = { connected: true, answerable: false, answerType: "none", answer: "", sourceField: "" };

  // 모델이 답하지 못해도(none) 설명이 있으면 그것을 «보이게» 둔다. 답하지 않았다는 사실도 함께 적는다.
  // 재산유형 전용 설명이면 용어 옆에 그 사실을 붙인다.
  await askWith({ ...declined, references: [ref("설명 하나입니다.", "압류재산")] });
  await expect(answerBox.getByText("설명 하나입니다.")).toBeVisible();
  await expect(answerBox.getByText("출처: 시험용 출처")).toBeVisible();
  await expect(answerBox.getByText("온비드 안내 기준 용어 설명")).toBeVisible();
  await expect(answerBox.getByText(declinedNote)).toBeVisible();
  await expect(answerBox.getByText("(압류재산 기준)")).toBeVisible();
  await expect(answerBox).not.toContainText("담당기관 문의 필요");

  // AI 가 연결되지 않아도 같다. scope 가 common 이면 꼬리표를 붙이지 않는다.
  await askWith({ ...declined, connected: false, references: [ref("설명 둘입니다.", "common")] });
  await expect(answerBox.getByText("설명 둘입니다.")).toBeVisible();
  // 연결이 안 된 것은 거절과 다르다. 「답하지 않았습니다」 대신 연결 안내를 쓴다(리뷰 r2 P2-c).
  await expect(answerBox.getByText(offlineNote)).toBeVisible();
  await expect(answerBox).not.toContainText(declinedNote);
  await expect(answerBox).not.toContainText("AI 연결 안 됨");
  await expect(answerBox.locator("p > strong + span.small-text")).toHaveCount(0);

  // 제도·용어 질문(general)에 설명이 있으면 모델이 풀어 쓴 답 대신 온비드 설명을 그대로 보인다.
  // 국유재산·수탁재산 전용 설명에도 꼬리표를 붙인다.
  await askWith({ connected: true, answerable: true, answerType: "general", answer: "모델이 풀어 쓴 답입니다.", sourceField: "시험용 출처", references: [ref("설명 넷입니다.", "국유재산"), ref("설명 다섯입니다.", "수탁재산")] });
  await expect(answerBox.getByText("설명 넷입니다.")).toBeVisible();
  await expect(answerBox.getByText("(국유재산 기준)")).toBeVisible();
  await expect(answerBox.getByText("(수탁재산 기준)")).toBeVisible();
  await expect(answerBox.getByText(partialNote)).toBeVisible();
  await expect(answerBox).not.toContainText("모델이 풀어 쓴 답입니다.");
  await expect(answerBox).not.toContainText(declinedNote);
  await expect(answerBox).not.toContainText(offlineNote);

  // 공고 사실 답(notice)이면 답 아래에 설명을 «접어서» 붙인다 — 펼쳐 두면 글이 너무 길어진다.
  await askWith({ connected: true, answerable: true, answerType: "notice", answer: "모델 답 문장입니다.", sourceField: "bidDeadline", references: [ref("설명 셋입니다.")] });
  await expect(answerBox.getByText("모델 답 문장입니다.")).toBeVisible();
  await expect(answerBox).not.toContainText(partialNote);
  await expect(answerBox).not.toContainText(declinedNote);
  const folded = answerBox.locator(".coach-ask-answer > p + details.coach-ask-reference");
  await expect(folded).toHaveCount(1);
  expect(await folded.evaluate((el) => el.open)).toBe(false);
  await expect(answerBox.getByText("설명 셋입니다.")).toBeHidden();
  await folded.locator("> summary").click();
  await expect(answerBox.getByText("설명 셋입니다.")).toBeVisible();

  // 음성 대조: 설명이 없으면 예전처럼 담당기관 문의·AI 미연결 안내가 뜬다.
  await askWith({ ...declined, references: [] });
  await expect(answerBox).toContainText("담당기관 문의 필요");
  await expect(answerBox).not.toContainText("시험용 출처");
  await askWith({ ...declined, connected: false });
  await expect(answerBox).toContainText("AI 연결 안 됨");
});

test("준비 단계 — 잠긴 task의 data-task-id로 change 이벤트를 직접 보내도 체크 상태가 바뀌지 않는다", async ({ page }) => {
  await analyzeWith(page, stagedNotice());
  await page.locator("#prepare").click();

  // 체크박스 클릭 핸들러의 이중 방어(ux-audit §⑴ "구현 시 반드시 지킬 것")를 disabled 속성과
  // 무관하게 직접 잰다 — disabled 속성을 런타임에 지운 뒤 change 이벤트를 강제로 보낸다.
  const result = await page.evaluate(() => {
    const input = document.querySelector('[data-task-id="price"]');
    input.disabled = false;
    input.checked = true;
    input.dispatchEvent(new Event("change", { bubbles: true }));
    return window.getTaskState().price;
  });
  expect(result).not.toBe(true);
});

test("준비 단계 — getPrepStageStatus()를 화면 체크 없이 직접 호출해 단계 파생값을 단정한다", async ({ page }) => {
  await analyzeWith(page, stagedNotice());
  await page.locator("#prepare").click();

  const initial = await page.evaluate(() => window.getPrepStageStatus());
  expect(initial).toEqual([
    { num: 1, title: "공고 확인", taskIds: ["notice-type", "bid-period"], notYet: false, done: false, locked: false },
    { num: 2, title: "입찰 전 준비", taskIds: ["documents"], notYet: false, done: false, locked: true },
    { num: 3, title: "입찰 참여", taskIds: ["price"], notYet: false, done: false, locked: true },
    // 4단계는 build_tasks() 가 만드는 task 가 없어 taskIds 가 비어 있다. 그래도 done 은 false 다
    // — notYet 이 done 보다 먼저 판정되기 때문이다(P0-1).
    { num: 4, title: "낙찰 후 준비", taskIds: [], notYet: true, done: false, locked: false },
  ]);

  await page.locator('[data-task-id="notice-type"]').check();
  await page.locator('[data-task-id="bid-period"]').check();
  const afterStage1 = await page.evaluate(() => window.getPrepStageStatus());
  expect(afterStage1[0]).toMatchObject({ num: 1, done: true, locked: false });
  expect(afterStage1[1]).toMatchObject({ num: 2, done: false, locked: false });
  expect(afterStage1[2]).toMatchObject({ num: 3, done: false, locked: true });
  // 앞 단계를 다 채워도 4단계는 열리지도 완료되지도 않는다 — 낙찰은 체크박스로 만들 수 없다.
  expect(afterStage1[3]).toMatchObject({ num: 4, notYet: true, done: false, locked: false });
});

/* ────────────────────────────────────────────────────────────────────────────
 * P0-1 — 항목이 0개인 단계가 「완료」로 표시되지 않는다.
 *
 * 이 단정이 필요한 이유: getPrepStageStatus() 는 `taskIds.every(...)` 로 완료를 판정하고,
 * `[].every()` 는 참이다. 4단계는 서버가 만드는 task 가 하나도 없어 taskIds 가 «항상» 빈
 * 배열이므로, notYet 판정이 없으면 사용자가 낙찰도 되지 않았고 서류도 한 장 내지 않은
 * 상태에서 「4단계 · 낙찰 후 준비 ✅ 완료」를 읽는다. 돈이 걸린 체크리스트의 허위 완료 표시다.
 *
 * 변이 투입(2026-10-18): getPrepStageStatus() 의 `done: notYet ? false : done` 을 `done` 으로
 * 되돌리고 renderStageHeading()·renderPrepStageStepper() 의 notYet 분기를 지우면 이 테스트가
 * 실패해야 한다. 실제로 실패하는 것을 확인했다(아래 §검증 참조).
 * ──────────────────────────────────────────────────────────────────────────── */
test("준비 단계 — 항목이 0개인 4단계가 「완료」로 표시되지 않고 「아직 할 일이 아닙니다」로 표시된다", async ({ page }) => {
  await analyzeWith(page, stagedNotice());
  await page.locator("#prepare").click();

  // ⑴ 파생값: 4단계는 taskIds 가 비어 있는데도 done 이 아니다.
  const stage4 = await page.evaluate(() => window.getPrepStageStatus().find((stage) => stage.num === 4));
  expect(stage4.taskIds).toEqual([]);
  expect(stage4.done).toBe(false);
  expect(stage4.notYet).toBe(true);
  expect(stage4.locked).toBe(false);

  // ⑵ 스테퍼: 4단계 칸에 「완료」가 아니라 「아직 할 일이 아닙니다」가 적힌다.
  const stepperItem = page.locator(".prep-stage-stepper li").nth(3);
  await expect(stepperItem).toContainText("낙찰 후 준비");
  await expect(stepperItem).toContainText("아직 할 일이 아닙니다");
  await expect(stepperItem).not.toContainText("완료");
  await expect(stepperItem).toHaveClass(/is-not-yet/);
  await expect(stepperItem).not.toHaveClass(/is-done/);

  // ⑶ 단계 헤딩: 4단계 헤딩이 is-done 이 아니다. 1~3단계가 미완이므로 is-done 은 0건이어야 한다.
  await expect(page.locator(".stage-group-heading.is-not-yet")).toHaveCount(1);
  await expect(page.locator(".stage-group-heading.is-not-yet")).toContainText("4단계 · 낙찰 후 준비");
  await expect(page.locator(".stage-group-heading.is-done")).toHaveCount(0);

  // ⑷ 1~3단계를 모두 체크해도 4단계는 여전히 「완료」가 아니다 — 낙찰은 사용자가 만들 수 없다.
  await page.locator('[data-task-id="notice-type"]').check();
  await page.locator('[data-task-id="bid-period"]').check();
  await page.locator('[data-task-id="documents"]').check();
  await page.locator('[data-task-id="price"]').check();
  await expect(page.locator(".stage-group-heading.is-done")).toHaveCount(3);
  await expect(page.locator(".stage-group-heading.is-not-yet")).toContainText("아직 할 일이 아닙니다");
  await expect(page.locator(".prep-stage-stepper li").nth(3)).not.toContainText("완료");
});

test("준비 단계 — 4단계 블록에 머리 안내가 보이고, 낙찰 후 서류가 2단계가 아니라 4단계에 들어간다", async ({ page }) => {
  await analyzeWith(page, stagedNotice());
  await page.locator("#prepare").click();

  // 4단계 블록은 잠겨 있지 않으므로 기본으로 펼쳐져 있고, 머리 안내가 바로 보인다.
  // 이 안내는 과설명이 아니라 단계 판정(resolve_doc_stage) 오분류의 안전망이다(P0-2).
  const postAward = page.locator(".post-award-panel");
  await expect(postAward).toBeVisible();
  await expect(postAward.locator(".post-award-caution")).toContainText("2단계 목록도 함께 확인하십시오");

  // D(P1-2) 일반 안내가 4단계를 채운다 — 기한을 놓치면 낙찰이 취소되는 묶음이 맨 위다.
  const groupHeadings = postAward.locator(".doc-group > summary h4");
  await expect(groupHeadings.first()).toContainText("매각결정기일 전까지");
  await expect(postAward).toContainText("농지 매수자격 증명 서류");
  await expect(postAward).toContainText("소유권이전 단계");
  await expect(postAward).toContainText("등기사항전부증명서");
  // 제출처는 재산유형마다 다르다 — 압류재산은 캠코가 등기를 촉탁하고 매수인이 직접 등기소에 낼 수
  // 없다(온비드 이용안내 「낙찰절차 안내」 · 2026-10-19 정합성 대조로 사실 10 의 미확인이 닫혔다).
  await expect(postAward).toContainText("등기촉탁은 캠코가 합니다");
  await expect(postAward).toContainText("매수인이 등기소에 직접 낼 수는 없습니다");

  // 2단계 체크리스트에는 낙찰 후 서류가 «없다» — 두 블록이 물리적으로 갈린다.
  await page
    .locator('[data-task-id="documents"]')
    .locator("xpath=ancestor::details[contains(@class,'stage-group')]")
    .locator("> summary")
    .click();
  const preBidChecklist = page.locator("#doc-checklist");
  await expect(preBidChecklist).toContainText("인감증명서");
  await expect(preBidChecklist).not.toContainText("등기사항전부증명서");
  await expect(preBidChecklist).not.toContainText("농지 매수자격 증명 서류");

  // E-3 제출기한 교정: 온비드 화면 표와 공고문 본문의 기한이 어긋나는 공고가 있다.
  await expect(preBidChecklist).toContainText("공고문 원문의 기한이 더 이를 수 있으니");
});

test("준비 단계 — 4단계 서류를 체크해도 2단계 진행률과 단계 잠금에 영향이 없다", async ({ page }) => {
  await analyzeWith(page, stagedNotice());
  await page.locator("#prepare").click();

  const before = await page.evaluate(() => ({
    pre: window.getDocSummary().totalCount,
    post: window.getPostAwardDocSummary().totalCount,
  }));
  // 4단계 서류가 2단계 분모에 섞이면 「서류를 전부 체크하면 documents 를 켠다」는 보조 동작이
  // 낙찰 후 서류까지 요구해, 2단계 완료가 조건인 3단계가 열리지 않는 교착이 된다(§4-⑺).
  expect(before.post).toBeGreaterThan(0);

  const postNames = await page.evaluate(() => window.getPostAwardDocSummary().names);
  const preNames = await page.evaluate(() => window.getDocSummary().names);
  for (const name of postNames) expect(preNames).not.toContain(name);

  // 4단계 서류를 전부 체크해도 documents task 는 켜지지 않고 3단계는 잠긴 채다.
  for (const name of postNames) {
    await page.locator(`[data-doc-name="${name}"]`).first().check();
  }
  expect(await page.evaluate(() => window.getTaskState().documents)).not.toBe(true);
  expect(await page.evaluate(() => window.getPrepStageStatus()[2].locked)).toBe(true);
  expect(await page.evaluate(() => window.getDocSummary().totalCount)).toBe(before.pre);
});

// S10 — 낙찰 후 안내의 재산유형 분기. 「매각결정기일 전까지」 묶음은 압류재산 공매공고문에
// 근거한 것이라 다른 재산유형에는 해당하지 않을 수 있다. 접어 두고 그 사실을 적되 숨기지는
// 않는다. 숨기면 재산유형 추출이 틀렸을 때 사용자가 그 묶음의 존재조차 모르고 지나간다.
test("S10 준비 단계 — 4단계 압류재산 묶음이 재산유형에 따라 접히고, 숨겨지지는 않는다", async ({ page }) => {
  const SEIZED_GROUP = "낙찰 직후 · 매각결정기일 전까지 (압류재산)";
  const NOT_APPLICABLE_TEXT = "해당하지 않을 수 있습니다";

  const readGroup = async () => {
    const group = page.locator(`details.doc-group:has(h4:text-is("${SEIZED_GROUP}"))`);
    return {
      exists: (await group.count()) > 0,
      open: (await group.count()) > 0 ? await group.first().evaluate((el) => el.open) : null,
      noteCount: await page.locator(`.post-award-not-applicable:has-text("${NOT_APPLICABLE_TEXT}")`).count(),
      // 묶음 안의 서류가 실제로 마크업에 있는지 — 「접었다」와 「지웠다」를 가른다.
      itemCount: (await group.count()) > 0 ? await group.first().locator("li").count() : 0,
    };
  };

  // ⑴ 압류재산 — 해당하므로 펼쳐지고 안내 문구가 없다.
  const seized = stagedNotice();
  seized.assetType = "압류재산";
  await analyzeWith(page, seized);
  const onSeized = await readGroup();
  expect(onSeized.exists).toBe(true);
  expect(onSeized.open).toBe(true);
  expect(onSeized.noteCount).toBe(0);

  // ⑵ 국유재산 — 해당하지 않으므로 접히고 안내가 붙는다. 그래도 서류는 마크업에 남는다.
  const stateOwned = stagedNotice();
  stateOwned.assetType = "국유재산";
  await analyzeWith(page, stateOwned);
  const onStateOwned = await readGroup();
  expect(onStateOwned.exists).toBe(true);
  expect(onStateOwned.open).toBe(false);
  expect(onStateOwned.noteCount).toBe(1);
  expect(onStateOwned.itemCount).toBeGreaterThan(0);
  // 소유권이전 묶음은 assetTypes 선언이 없어 모든 재산유형에 해당한다 — 함께 접히지 않는다.
  const transferGroup = page.locator('details.doc-group:has(h4:text-is("소유권이전 단계"))');
  expect(await transferGroup.count()).toBe(1);
  expect(await transferGroup.first().evaluate((el) => el.open)).toBe(true);

  // ⑶ 🔴 비대칭 기본값 — 재산유형을 읽지 못했으면 해당하는 것으로 보고 펼친다. 접는 쪽이
  //    비싼 오류다(압류재산인데 접히면 매각결정기일을 놓친다).
  const unknown = stagedNotice();
  unknown.assetType = "재산유형 확인";
  await analyzeWith(page, unknown);
  const onUnknown = await readGroup();
  expect(onUnknown.open).toBe(true);
  expect(onUnknown.noteCount).toBe(0);

  // 판정 함수를 화면과 별개로 직접 부른다 — 본문을 비워도 위 단정이 통과하면 그 함수는
  // 아무것도 증명하지 못한다.
  const direct = await page.evaluate(() => ({
    noDeclaration: window.isPostAwardGroupApplicable({ condition: "소유권이전 단계" }),
    unknownType: window.isPostAwardGroupApplicable({ assetTypes: ["압류재산"] }),
  }));
  expect(direct.noDeclaration).toBe(true);
  expect(direct.unknownType).toBe(true);
});

// S12 — 소유권이전 묶음은 매각 절차의 서류다. 임대·대부 공고에는 소유권이전이 없으므로 접고
// 처분방식 안내를 붙인다(2026-10-19 정합성 대조 · 임대 공고에도 펼쳐져 나가던 문제).
// 접기만 하고 지우지는 않는다 — 처분방식을 잘못 읽었을 때도 사용자가 묶음을 열어 볼 수 있게.
test("S12 준비 단계 — 임대 공고에서는 소유권이전 묶음이 접히고 처분방식 안내가 붙는다", async ({ page }) => {
  const TRANSFER_GROUP = 'details.doc-group:has(h4:text-is("소유권이전 단계"))';
  const DISPOSITION_NOTE = '.post-award-not-applicable:has-text("처분방식")';
  const readTransfer = async () => {
    const group = page.locator(TRANSFER_GROUP);
    const count = await group.count();
    return {
      exists: count > 0,
      open: count > 0 ? await group.first().evaluate((el) => el.open) : null,
      itemCount: count > 0 ? await group.first().locator("li").count() : 0,
      noteCount: await page.locator(DISPOSITION_NOTE).count(),
    };
  };

  // ⑴ 임대 — 접히고 처분방식 안내가 붙는다. 서류는 마크업에 남는다.
  const lease = stagedNotice();
  lease.assetType = "공유재산";
  lease.dispositionLabel = "임대";
  await analyzeWith(page, lease);
  const onLease = await readTransfer();
  expect(onLease.exists).toBe(true);
  expect(onLease.open).toBe(false);
  expect(onLease.noteCount).toBe(1);
  expect(onLease.itemCount).toBeGreaterThan(0);
  // 안내는 자기 묶음 «바로 뒤»에 있어야 한다. 앞에 있으면 위 묶음의 설명처럼 읽힌다(2026-10-19 여정 점검).
  const noteFollowsGroup = await page
    .locator('.post-award-not-applicable:has-text("처분방식")')
    .first()
    .evaluate((el) => el.previousElementSibling?.matches?.('details.doc-group') && el.previousElementSibling.querySelector("h4")?.textContent.trim() === "소유권이전 단계");
  expect(noteFollowsGroup).toBe(true);

  // 판정 함수 직접 호출 — 화면 단정과 별개로 이유 값을 본다.
  const direct = await page.evaluate(() => {
    const transfer = { condition: "소유권이전 단계", dispositions: ["매각"] };
    sampleNotice.dispositionLabel = "임대/대부입찰";
    const lease = window.postAwardNotApplicableReason(transfer);
    sampleNotice.dispositionLabel = "매각/공매";
    const sale = window.postAwardNotApplicableReason(transfer);
    // 「임대」와 「매각」이 함께 적힌 라벨은 매각 절차가 섞였을 수 있어 접지 않는다.
    sampleNotice.dispositionLabel = "임대 및 매각";
    const mixed = window.postAwardNotApplicableReason(transfer);
    return { lease, sale, mixed };
  });
  expect(direct.lease).toBe("disposition");
  expect(direct.sale).toBe("");
  expect(direct.mixed).toBe("");
});

test("S12 음성 — 매각 공고와 처분방식을 읽지 못한 공고에서는 소유권이전 묶음이 펼쳐진다", async ({ page }) => {
  const TRANSFER_GROUP = 'details.doc-group:has(h4:text-is("소유권이전 단계"))';
  const DISPOSITION_NOTE = '.post-award-not-applicable:has-text("처분방식")';
  const readTransfer = async () => ({
    open: await page.locator(TRANSFER_GROUP).first().evaluate((el) => el.open),
    noteCount: await page.locator(DISPOSITION_NOTE).count(),
  });

  // ⑴ 매각 공고에서는 펼쳐지고 안내가 없다.
  const sale = stagedNotice();
  sale.assetType = "공유재산";
  sale.dispositionLabel = "매각";
  await analyzeWith(page, sale);
  const onSale = await readTransfer();
  expect(onSale.open).toBe(true);
  expect(onSale.noteCount).toBe(0);

  // ⑵ 처분방식을 읽지 못했으면 해당하는 것으로 보고 펼친다(재산유형과 같은 비대칭 기본값).
  const unknown = stagedNotice();
  unknown.dispositionLabel = "처분방식 확인";
  await analyzeWith(page, unknown);
  const onUnknown = await readTransfer();
  expect(onUnknown.open).toBe(true);
  expect(onUnknown.noteCount).toBe(0);

});

// S13 — 3단계 「입찰 참여」에 온비드 공통 입찰 규칙(제출 뒤 수정·취소 불가, 제출 뒤 발급되는 계좌로
// 마감 전 보증금 납부·미납 시 무효, 나의온비드 직접 확인)을 고정 문구로 보여 준다. 근거는 온비드
// 이용안내 「입찰참가 안내」와 입찰참가자 준수규칙이다(2026-10-19 정합성 대조).
test("S13 준비 단계 — 3단계에 온비드 입찰 규칙 세 줄이 보인다", async ({ page }) => {
  await analyzeWith(page, stagedNotice());
  const rules = page.locator(".bid-participation-info .bid-rules li");
  await expect(rules).toHaveCount(3);
  const text = (await rules.allInnerTexts()).join(" ");
  expect(text).toContain("수정하거나 취소할 수 없는");
  expect(text).toContain("입찰서를 제출한 뒤에 발급");
  expect(text).toContain("무효");
  expect(text).toContain("직접 확인");
});

// S11 — 공공데이터 API 연동 블록 세 개가 설계한 자리에 놓이고, 질문 답·기한 어긋남을
// 제대로 다루는지 본다. 2026-10-18 브라우저 측정에서 이 테스트가 결함 1건을 잡았다 —
// 공동입찰 질문에 「아니오」로 답했는데도 공동입찰 제출기한이 화면에 남아 있었다.
test("S11 API 연동 블록 — 자리·질문 답 거르기·기한 어긋남 경고", async ({ page }) => {
  const notice = stagedNotice();
  notice.assetType = "국유재산";
  notice.bidParticipationApply = {
    required: true, docs: "입찰참가신청서, 사업자등록증", due: "2026-10-19 17:00", method: "직접제출",
    source: "공공데이터 온비드 물건 입찰상세(getCltrBidInf2) · bidPtctAplyYn",
  };
  notice.apiDocTerms = [
    { kind: "공동입찰", due: "입찰마감일시 전까지", method: "직접제출" },
    { kind: "대리입찰", due: "입찰마감일시 전까지", method: "온라인/직접제출" },
  ];
  notice.bidLimits = [
    { key: "qualification", label: "자격 제한", value: "주택건설사업자만 참가 가능", restricted: true },
    { key: "region", label: "지역 제한", value: "부산광역시", restricted: true },
  ];
  // 화면 표 기한을 API 기한과 다르게 둬서 어긋남 경고를 끌어낸다. 실제로 같은 공고에서 화면
  // 표와 공고문 본문이 어긋난 사례가 확인됐다(researcher-fact-check 사실 4-③).
  notice.docChecklist.groups.push({
    condition: "공동입찰",
    items: [{ name: "공동입찰참가신청서", conditions: ["공동입찰"], conditionKeys: [], copy: "", validity: "",
      method: "직접제출", due: "우편으로 17:00까지", count: "", stage: "입찰 전",
      howto: "온비드", howtoUrl: "https://www.onbid.co.kr/", sourceSection: "제출서류", evidence: "근거" }],
  });
  await analyzeWith(page, notice);

  // ⑴ 자리 — 자격 조건은 1단계, 입찰참가신청은 2단계이고 서류 패널보다 앞이다.
  const places = await page.evaluate(() => {
    const stages = [...document.querySelectorAll("#task-list details.stage-group")];
    const applyStage = stages.findIndex((s) => s.querySelector(".bid-apply-panel"));
    const stage = stages[applyStage];
    const apply = stage?.querySelector(".bid-apply-panel");
    const docs = stage?.querySelector(".doc-panel");
    return {
      limitsStage: stages.findIndex((s) => s.querySelector(".bid-limits-panel")),
      applyStage,
      applyBeforeDocs: apply && docs
        ? Boolean(apply.compareDocumentPosition(docs) & Node.DOCUMENT_POSITION_FOLLOWING)
        : null,
    };
  });
  expect(places.limitsStage).toBe(0);
  expect(places.applyStage).toBe(1);
  expect(places.applyBeforeDocs).toBe(true);

  // ⑵ 질문 답 거르기 — 기본값(둘 다 「아니오」)에서는 두 구분 모두 보이지 않는다.
  expect(await page.evaluate(() => window.getApiDocTerms().length)).toBe(0);

  // 공동입찰만 「예」로 답하면 공동입찰만 보인다. 대리입찰은 계속 걸러진다.
  await page.evaluate(() => {
    document.querySelector('[data-doc-condition="joint"][data-doc-condition-value="yes"]')?.click();
  });
  await page.waitForTimeout(300);
  const kinds = await page.evaluate(() => window.getApiDocTerms().map((t) => t.kind));
  expect(kinds).toEqual(["공동입찰"]);

  // ⑶ 기한 어긋남 — 두 값을 모두 보여주고 더 이른 기한 기준 안내를 붙인다.
  await page.evaluate(() => document.querySelectorAll("details").forEach((d) => (d.open = true)));
  const conflict = page.locator(".api-term-conflict");
  await expect(conflict).toHaveCount(1);
  const conflictText = await conflict.innerText();
  expect(conflictText).toContain("우편으로 17:00까지");
  expect(conflictText).toContain("더 이른 기한");
  // API 쪽 값도 같은 블록에 남아 있어야 한다 — 한쪽만 보여주면 이 규칙의 뜻이 사라진다.
  expect(await page.locator(".api-doc-terms").innerText()).toContain("입찰마감일시 전까지");

  // 음성 대조 — 화면 표 기한이 API 기한과 «같으면» 경고를 띄우지 않는다. 이것이 없으면
  // 「같은 값 제외」 판정을 지워도 테스트가 통과한다(2026-10-18 변이 m4 가 살아남아 보강).
  const same = stagedNotice();
  same.assetType = "국유재산";
  same.apiDocTerms = [{ kind: "공동입찰", due: "입찰마감일시 전까지", method: "직접제출" }];
  same.docChecklist.groups.push({
    condition: "공동입찰",
    items: [{ name: "공동입찰참가신청서", conditions: ["공동입찰"], conditionKeys: [], copy: "", validity: "",
      method: "직접제출", due: "입찰마감일시 전까지", count: "", stage: "입찰 전",
      howto: "온비드", howtoUrl: "https://www.onbid.co.kr/", sourceSection: "제출서류", evidence: "근거" }],
  });
  await analyzeWith(page, same);
  await page.evaluate(() => {
    document.querySelector('[data-doc-condition="joint"][data-doc-condition-value="yes"]')?.click();
  });
  await page.waitForTimeout(300);
  await page.evaluate(() => document.querySelectorAll("details").forEach((d) => (d.open = true)));
  // 블록 자체는 보이는데 경고만 없어야 한다 — 블록이 사라져서 경고가 0인 것과 가른다.
  expect(await page.locator(".api-doc-terms").count()).toBe(1);
  expect(await page.locator(".api-term-conflict").count()).toBe(0);

  // ⑷ 값이 없으면 블록을 그리지 않는다 — 가장 눈에 띄는 자리에 「우리가 모른다」를 두지 않는다.
  const blank = stagedNotice();
  blank.assetType = "국유재산";
  await analyzeWith(page, blank);
  expect(await page.locator(".bid-apply-panel").count()).toBe(0);
  expect(await page.locator(".bid-limits-panel").count()).toBe(0);
  expect(await page.locator(".api-doc-terms").count()).toBe(0);
});

/* ────────────────────────────────────────────────────────────────────────────
 * team-reports/2026-10-18-bid-doc-timeline/e2e-design.md §3 시나리오 1·3·5(신규)와
 * 시나리오 2(보강). 시나리오 4·6은 그 설계서가 이미 §3에서 S10·P0-1 테스트로 커버된
 * 것으로 판정했으므로 여기서 다시 쓰지 않는다 — 두 테스트는 그대로 회귀 가드다.
 * ──────────────────────────────────────────────────────────────────────────── */

// 공동입찰 조건 그룹(실제 서류 1건 포함)을 더한 압류재산 공고. 시나리오 1·3 공용 — 두
// 시나리오 모두 "조건에 답하지 않으면 숨는다"를 공동입찰쪽에서 함께 확인해야 한다.
function jointAndProxyNotice() {
  const notice = copyBase();
  notice.docChecklist.groups.push({
    condition: "공동입찰",
    items: [
      {
        name: "공동입찰서류 원문 항목",
        conditions: ["공동입찰"],
        conditionKeys: [],
        copy: "",
        validity: "",
        method: "직접제출",
        due: "입찰마감일시 전까지",
        count: "",
        stage: "입찰 전",
        howto: "",
        howtoUrl: "",
        sourceSection: "제출서류",
        evidence: "온비드 제출서류 표 · 공동입찰서류 행",
      },
    ],
  });
  return notice;
}

// 시나리오 1 — 본인 단독 현금 입찰(신규). 근거: 압류재산 인터넷공매 입찰참가자준수규칙
// 제7조②③ — 대리·공동입찰 서류 요구는 "대리인이 매수신청하려는 경우"·"여러 사람이
// 공동으로 입찰에 참가하려는 경우"로 조건이 걸려 있어, 단독 입찰자에게는 요구되지 않는다.
test("E2E design 시나리오 1 — 조건 질문에 답하지 않은 기본 상태에서 대리입찰·공동입찰 서류가 0건이다 (준수규칙 제7조②③)", async ({ page }) => {
  await analyzeWith(page, jointAndProxyNotice());
  await page.locator("#prepare").click();
  await page.locator("#doc-checklist-details > summary").click();
  const checklist = page.locator("#doc-checklist");

  // 단정 — 기본 상태(미답변)에는 대리입찰·공동입찰 서류가 보이지 않는다.
  await expect(checklist).not.toContainText("대리입찰신청서");
  await expect(checklist).not.toContainText("공동입찰서류 원문 항목");
  await expect(checklist).not.toContainText("공동입찰 추가 안내");

  // 음성 대조 — 같은 화면에서 대리입찰 질문에 「예」를 누르면 대리입찰신청서가 떠야 한다
  // (S2가 이미 검증한 반대쪽과 짝이다 — 숨기는 로직이 과잉 동작해 "예"를 눌러도 계속
  // 숨기면 이 단정이 잡는다).
  await checklist.locator('button[data-doc-condition="proxy"][data-doc-condition-value="yes"]').click();
  await expect(checklist).toContainText("대리입찰신청서");
  // 공동입찰은 여전히 답하지 않았으므로 이 상태에서도 보이면 안 된다.
  await expect(checklist).not.toContainText("공동입찰서류 원문 항목");
});

// 시나리오 2 — 대리입찰(보강). S2(위 "S1·S2·S5·S6·S7..." 테스트)가 대리입찰신청서 노출과
// 기한 문구를 이미 단정한다. 이 테스트는 그 테스트가 확인하지 않은 "또는 본인서명사실확인서"
// 대체 표기만 보강한다. 근거: 준수규칙 제7조② "대리 매수신청인(위임인)의 인감증명서 또는
// 본인서명사실확인서". 인감증명서로만 좁혀 적으면 본인서명사실확인서로 대신할 수 있다는
// 사실을 사용자가 모르고 지나간다(researcher-fact-check 사실 3).
test("E2E design 시나리오 2 보강 — 대리입찰 서류에 \"인감증명서 또는 본인서명사실확인서\" 대체 표기가 그대로 남는다 (준수규칙 제7조②)", async ({ page }) => {
  await analyzeWith(page, jointAndProxyNotice());
  await page.locator("#prepare").click();
  await page.locator("#doc-checklist-details > summary").click();
  const checklist = page.locator("#doc-checklist");

  await checklist.locator('button[data-doc-condition="proxy"][data-doc-condition-value="yes"]').click();
  // "또는" 대체 관계가 서류명 자체에 살아 있어야 한다 — "인감증명서"로만 줄이면 대체
  // 수단(본인서명사실확인서)이 있다는 사실이 화면에서 사라진다.
  await expect(checklist).toContainText("입찰자의 인감증명서 또는 본인서명사실확인서");
  await expect(checklist).toContainText("인감증명서가 없으면 본인서명사실확인서로 대신할 수 있습니다");
});

// 시나리오 3 — 공동입찰(압류재산, 온비드 등록 예외)(신규). 근거: 압류재산 공매공고문
// 「16. 주의사항」 자항 ③호 단서 — "다만, 인터넷 공매의 경우에는 공동입찰신청을 온비드
// 등록으로 대신할 수 있습니다". 이 예외를 빼면 사용자가 하지 않아도 되는 우편·방문 제출을
// 하게 된다(researcher-fact-check 사실 1).
test("E2E design 시나리오 3 — 압류재산 공동입찰에 온비드 등록 대체 예외 문구가 뜬다 (공매공고문 16. 주의사항 자항 ③호 단서)", async ({ page }) => {
  await analyzeWith(page, jointAndProxyNotice());
  await page.locator("#prepare").click();
  await page.locator("#doc-checklist-details > summary").click();
  const checklist = page.locator("#doc-checklist");

  await checklist.locator('button[data-doc-condition="joint"][data-doc-condition-value="yes"]').click();
  await expect(checklist).toContainText("공동입찰서류 원문 항목");
  await expect(checklist).toContainText(
    "압류재산 공매는 인터넷 공매이므로, 공동입찰신청을 온비드 등록으로 대신할 수 있습니다",
  );
});

// 시나리오 3 음성 대조 — 국유재산 공고문은 이 단서가 없고 "전자서명방식 또는 서류제출방식
// 중 선택"을 제시한다(researcher-fact-check 사실 3). 재산유형을 조건으로 가르지 않으면
// 압류재산 전용 예외가 국유재산 화면에도 새어 나갈 수 있다 — 이 테스트는 그 새어 나감을
// 잡는 음성 대조다.
test("E2E design 시나리오 3 음성 대조 — 국유재산 공동입찰에는 압류재산 전용 온비드 등록 예외 문구가 뜨지 않는다", async ({ page }) => {
  const notice = jointAndProxyNotice();
  notice.assetType = "국유재산";
  await analyzeWith(page, notice);
  await page.locator("#prepare").click();
  await page.locator("#doc-checklist-details > summary").click();
  const checklist = page.locator("#doc-checklist");

  await checklist.locator('button[data-doc-condition="joint"][data-doc-condition-value="yes"]').click();
  await expect(checklist).not.toContainText(
    "압류재산 공매는 인터넷 공매이므로, 공동입찰신청을 온비드 등록으로 대신할 수 있습니다",
  );
});

// 시나리오 5 — 공고문이 시점을 적지 않은 서류(신규). 근거: resolve_doc_stage()
// (src/server.py)가 서식명·조항 표제·문장 사전 모두에서 못 정하면 "미분류"를 반환한다
// (stage-classification-design.md §3 "미분류를 1급 상태로 두는 설계"). 추측으로 입찰
// 전/낙찰 후 어느 쪽에도 넣지 않는다. E2E는 window.fetch를 가로채는 고정 표본이라, 서버의
// 사전 판정 자체가 아니라 그 결과("미분류" stage)를 화면이 올바르게 분리해 보여주는지만
// 검증한다(사전이 실제로 못 찾는 입력을 만드는 것은 tests/measure_stage_classification.py
// 쪽 책임이다).
test("E2E design 시나리오 5 — 사전에 없는 서류는 \"단계를 확정하지 못한 서류\" 구획에만 나타난다 (resolve_doc_stage 말단 분기)", async ({ page }) => {
  const notice = copyBase();
  notice.docChecklist.items = [
    ...notice.docChecklist.items,
    {
      name: "㉮ 사전에 없는 특수 제출물",
      conditions: [],
      conditionKeys: [],
      copy: "",
      validity: "",
      method: "",
      due: "",
      count: "",
      stage: "미분류",
      howto: "",
      howtoUrl: "",
      sourceSection: "공고문",
      evidence: "조항 표제·문장 사전 어디에도 없는 표제라 단계를 정하지 못했습니다.",
    },
  ];
  notice.docChecklist.groups.push({ condition: "미분류 서류", items: [notice.docChecklist.items[2]] });
  await analyzeWith(page, notice);
  await page.locator("#prepare").click();
  await page.locator("#doc-checklist-details > summary").click();
  const checklist = page.locator("#doc-checklist");

  const unclassified = checklist.locator(".doc-group-unclassified");
  await expect(unclassified).toContainText("단계를 확정하지 못한 서류");
  await expect(unclassified).toContainText("단계를 확정하지 못했습니다. 공고문 원문을 확인하십시오.");
  await expect(unclassified).toContainText("㉮ 사전에 없는 특수 제출물");

  // 음성 대조 — 사전에 있는 표제를 가진 서류(stage: "입찰 전")는 이 구획에 들어가지 않는다.
  // BASE_NOTICE의 기존 두 항목(인감증명서·대리입찰신청서)이 그 반대쪽이다.
  await expect(unclassified).not.toContainText("대리입찰신청서");
  expect(await checklist.locator(".doc-group-unclassified li").count()).toBe(1);
});
