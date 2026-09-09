// @ts-check
const { defineConfig } = require("@playwright/test");

module.exports = defineConfig({
  testDir: "tests",
  timeout: 30000,
  // 게이트 자기보고(PLAYED·AXES·pass/total)는 worker 밖에서 «한 번만» 낸다.
  // spec 안에서 세면 실패마다 worker 가 재시작되어 수치가 조각난다.
  reporter: [["line"], [require.resolve("./tests/gate-reporter.js")]],
  use: {
    baseURL: "http://127.0.0.1:8975",
  },
  webServer: {
    command: "python3 src/server.py",
    url: "http://127.0.0.1:8975/",
    reuseExistingServer: true,
    timeout: 20000,
  },
});
