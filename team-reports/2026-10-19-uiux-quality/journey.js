const { chromium } = require(process.argv[2] + "/node_modules/@playwright/test");
const OUT = process.argv[3];
const CASES = {
  rentB: "https://www.onbid.co.kr/op/cltrpbancinf/cltrdtl/CltrDtlController/mvmnCltrDtl.do?onbidCltrno=1147301&pbctCdtnNo=6247576&onbidPbancNo=909691&pbctNo=10110341",
  demo1: "https://www.onbid.co.kr/op/cltrpbancinf/cltrdtl/CltrDtlController/mvmnCltrDtl.do?onbidCltrno=1837008&cltrHisNo=6153148&pbctCdtnNo=5988361&onbidPbancNo=887335&pbctNo=10061009",
  seized: "https://www.onbid.co.kr/op/cltrpbancinf/cltrdtl/CltrDtlController/mvmnCltrDtl.do?onbidCltrno=2039341&pbctCdtnNo=6244105&onbidPbancNo=909295&pbctNo=10109384",
};
const VIEWPORTS = { desk: { width: 1280, height: 900 }, mob: { width: 390, height: 844 } };
(async () => {
  const browser = await chromium.launch();
  for (const [key, url] of Object.entries(CASES)) {
    for (const [vp, size] of Object.entries(VIEWPORTS)) {
      const page = await browser.newPage({ viewport: size });
      const errors = [];
      page.on("pageerror", (e) => errors.push(String(e)));
      page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
      const t0 = Date.now();
      await page.goto("http://127.0.0.1:19240/");
      await page.screenshot({ path: `${OUT}/${key}-${vp}-0-profile.png`, fullPage: true });
      await page.locator("#profile-next").click();
      await page.locator("#notice-url").fill(url);
      await page.locator("#analyze").click();
      await page.locator("#prepare:not([disabled])").waitFor({ timeout: 90000 });
      await page.screenshot({ path: `${OUT}/${key}-${vp}-1-result.png`, fullPage: true });
      await page.locator("#prepare").click();
      await page.locator("#view-report.is-visible, #view-report:not([hidden])").first().waitFor({ timeout: 30000 }).catch(() => {});
      await page.waitForTimeout(1500);
      await page.screenshot({ path: `${OUT}/${key}-${vp}-2-board.png`, fullPage: true });
      const overflowX = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
      const text = await page.locator("body").innerText();
      require("fs").writeFileSync(`${OUT}/${key}-${vp}-board.txt`, text);
      console.log(key, vp, `${((Date.now() - t0) / 1000).toFixed(1)}s`, "가로넘침", overflowX, "콘솔오류", errors.length, errors.slice(0, 2).join(" | ").slice(0, 200));
      await page.close();
    }
  }
  await browser.close();
})().catch((e) => { console.error("FAIL", e.message.slice(0, 300)); process.exit(1); });
