const { test, expect } = require("@playwright/test");

/**
 * 화면 노출 축.
 *
 * 연기한 것(PLAYED)과 축 표(AXES)는 아래 상수에 두고 실행할 때마다 stdout 에 찍는다.
 * 주석에만 두면 로그를 받은 사람이 무엇이 연기됐는지 알 수 없다.
 */

// 이 게이트가 프로덕션 호출부를 대신 «연기»한 것. 여기 있는 것은 이 파일이 검증하지 못한다.
const PLAYED = [
  [
    "/api/analyze",
    "실제 온비드 크롤링 대신 window.fetch 를 픽스처로 바꾼다. 서버 추출 로직은 " +
      "tests/test_docs_extraction.py(순수 함수)와 tests/measure_sample_23.py(표본 23건)가 맡는다",
  ],
  ["그 밖의 화면 요소", "연기하지 않는다 — 실제 src/app.js 가 실제 DOM에 그린다"],
];

// 축 → 케이스 → 음성 대조 → 커버(Y/N/영구불가)
const AXES = [
  ["S1", "A/B/C 사전 안내", "A형/B형", "A형에 「첨부를 봐야 함」이 뜨지 않을 것", "Y"],
  ["S2", "조건별 체크리스트", "그룹·칩·발급처", "추출 성공 화면에 「찾지 못했습니다」가 없을 것", "Y"],
  ["S3", "못 뽑음 정직 표시", "못 뽑았다 문구", "추출 성공 화면에는 안 뜰 것", "Y"],
  ["S4", "진행 차단 없음", "누락 상태에서도 다음 단계 가능", "대화상자·disabled 0건", "Y"],
  ["S5", "최저입찰가 비공개", "「비공개」 표시", "정상 금액에는 안 뜰 것", "Y"],
  ["S6", "마감 D-day", "배지 노출", "상태 unknown 이면 배지 없을 것", "Y"],
  ["S7", "첨부 내려받기", "dnldFile.do 링크", "첨부 0건이면 링크 없을 것", "Y"],
  ["S8", "공고문 항목·용어", "목록 노출", "비어 있으면 안내 문장으로 대체될 것", "Y"],
];

test.beforeAll(() => {
  const lines = [`PLAYED — 이 게이트가 대신 연기한 것 ${PLAYED.length}개`];
  for (const [symbol, note] of PLAYED) lines.push(`  · ${symbol} — ${note}`);
  lines.push(`AXES — 축 ${AXES.length}개 (축 → 케이스 → 음성 대조 → 커버)`);
  for (const [code, name, useCase, negative, covered] of AXES) {
    lines.push(`  ${code} ${name} → ${useCase} → ${negative} → ${covered}`);
  }
  const uncovered = AXES.filter((axis) => axis[4] !== "Y").map((axis) => `${axis[0]} ${axis[1]}`);
  lines.push(
    `연기 ${PLAYED.length}개 · 축 ${AXES.length}개 중 미커버 ${uncovered.length}개 — ` +
      `미커버 축: ${uncovered.length ? uncovered.join(", ") : "없음"}`,
  );
  console.log(lines.join("\n"));
});

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

  // S7 첨부 내려받기 링크가 온비드 다운로드 엔드포인트를 가리킨다.
  const attachment = page.locator("#attachment-list a");
  await expect(attachment).toHaveCount(1);
  await expect(attachment).toHaveAttribute("href", /dnldFile\.do\?.*atchFileLstNo=17070043/);
  await expect(attachment).toHaveAttribute("href", /hashCrpsNo=COGFDOFI/);

  // S8 음성 대조: 목차가 비면 안내 문장으로 대체한다.
  await expect(page.locator("#notice-outline")).toContainText("찾지 못했습니다");

  await page.screenshot({ path: "screenshots/validation/21_doc-checklist-missing.png", fullPage: true });
});
