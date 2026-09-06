const { test, expect } = require("@playwright/test");

// 공공데이터 인증키 유무에 따라 검증 범위가 달라진다.
// 키가 없으면 온비드 공개 원문 분석만 동작하므로 연결 상태 문구는 생성되지 않는다.
const hasApiKey = Boolean(process.env.ONBID_API_SERVICE_KEY);

test("analyzes a real OnBid URL and renders source notes", async ({ page }) => {
  await page.goto("http://127.0.0.1:8975/");
  await page.locator("#notice-url").fill("https://www.onbid.co.kr/shortcut.do?code=q8ddH9CdE4E7");
  await page.locator("#asset-focus").selectOption("sale");
  await page.locator("#analyze").click();

  // 원문 분석 결과 (인증키 유무와 무관하게 항상 표시)
  await expect(page.locator("#report-hero")).toContainText("경기도 용인시 수지구 신봉동 202", {
    timeout: 30000,
  });
  await expect(page.locator("#quick-facts")).toContainText("205,575,000");
  await expect(page.locator("#task-list")).toContainText("공동입찰서류 - 입찰마감일시 전까지 - 직접제출");
  await expect(page.locator("#task-list")).not.toContainText("0076 / 022/001");
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
