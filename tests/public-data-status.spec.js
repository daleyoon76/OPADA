const { test, expect } = require("@playwright/test");

// 공공데이터 인증키 유무에 따라 검증 범위가 달라진다.
// 키가 없으면 온비드 공개 원문 분석만 동작하므로 연결 상태 문구는 생성되지 않는다.
const hasApiKey = Boolean(process.env.ONBID_API_SERVICE_KEY);

test("analyzes a real OnBid URL and renders source notes", async ({ page }) => {
  // baseURL(playwright.config.js 의 use.baseURL)을 따라간다 — 절대 URL 로 8975 를 박아 두면
  // 다른 포트로 띄워 돌릴 때 이 테스트만 운영 서버로 접속해 영원히 타임아웃이 난다
  // (screen.spec.js 가 같은 이유로 이미 상대 경로를 쓴다).
  await page.goto("/");
  // #asset-focus는 마법사 1단계(목적 선택) 화면에 있고, #notice-url은 #profile-next로 넘어간
  // 2단계 화면에 있다(src/index.html Step 1-1/1-2). #asset-focus 선택은 #profile-next 클릭
  // «전에» 해야 한다 — 클릭 뒤에는 1단계 화면이 숨겨져 타임아웃이 난다(2026-10-19 확인).
  const profileNext = page.locator("#profile-next");
  if (await profileNext.isVisible().catch(() => false)) {
    await page.locator("#asset-focus").selectOption("sale");
    await profileNext.click();
  }
  await page.locator("#notice-url").fill("https://www.onbid.co.kr/shortcut.do?code=q8ddH9CdE4E7");
  await page.locator("#analyze").click();

  // 원문 분석 결과 (인증키 유무와 무관하게 항상 표시)
  await expect(page.locator("#report-hero")).toContainText("경기도 용인시 수지구 신봉동 202", {
    timeout: 30000,
  });
  // 2026-10-19 3팀 묶음 C(U10 ⑴): 2-1 공고 요약에서 최저입찰가격 칸을 뺐다. 값은 「마감·비용」 탭 비용 행에 남는다.
  await expect(page.locator("#deadline-cost-list")).toContainText("205,575,000");
  // 2026-09-08 변경: 온비드 「제출서류」 표의 구분명(공동입찰서류·대리입찰서류)은 실제
  // 서류명이 아니므로 체크리스트에 서류명으로 싣지 않는다. 본문에서 뽑은 실제 서류명을 쓴다.
  await expect(page.locator("#task-list")).toContainText("농지취득자격증명");
  await expect(page.locator("#task-list")).not.toContainText("공동입찰서류 - 입찰마감일시 전까지 - 직접제출");
  await expect(page.locator("#task-list")).not.toContainText("0076 / 022/001");
  // 구분명 원본은 참고용으로 체크리스트 패널의 접힌 표에만 남는다.
  await expect(page.locator("#doc-checklist")).toContainText("구분명 그대로");
  await expect(page.locator("#source-url-link")).toHaveAttribute("href", /onbidCltrno=1768473/);

  // 보조 데이터(공공데이터 API) 상태 표기는 #report-hero → #source-notes 로 이동했다.
  await expect(page.locator("#source-notes")).toContainText("보조 데이터:");

  // 연결 상태 조회 문구는 인증키가 있는 환경에서만 생성된다.
  if (hasApiKey) {
    await expect(page.locator("#source-notes")).toContainText("보조 데이터 조회:");
  }

  await page.screenshot({
    path: hasApiKey
      ? "screenshots/validation/14_public-data-status-live-key.png"
      : "screenshots/validation/14_public-data-status-live-nokey.png",
    fullPage: true,
  });
});
