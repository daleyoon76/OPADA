const { test, expect } = require("@playwright/test");

test("shows public data API status after real OnBid URL analysis", async ({ page }) => {
  await page.goto("http://127.0.0.1:8975/");
  await page.locator("#notice-url").fill("https://www.onbid.co.kr/shortcut.do?code=q8ddH9CdE4E7");
  await page.locator("#asset-focus").selectOption("sale");
  await page.locator("#analyze").click();
  await expect(page.locator("#report-hero")).toContainText("경기도 용인시 수지구 신봉동 202", {
    timeout: 30000,
  });
  await expect(page.locator("#quick-facts")).toContainText("205,575,000");
  await expect(page.locator("#report-hero")).toContainText(/API (키 없음|오류|보조 없음|권한 대기|일부|연결)/);
  await expect(page.locator("#report-hero")).not.toContainText("API 실패");
  await expect(page.locator("#task-list")).toContainText("공동입찰서류 - 입찰마감일시 전까지 - 직접제출");
  await expect(page.locator("#task-list")).not.toContainText("0076 / 022/001");
  await expect(page.locator("#source-url-link")).toHaveAttribute("href", /onbidCltrno=1768473/);
  await expect(page.locator("#source-notes")).toContainText("공공데이터 API:");
  await page.screenshot({
    path: "screenshots/validation/14_public-data-status-live-key.png",
    fullPage: true,
  });
});
