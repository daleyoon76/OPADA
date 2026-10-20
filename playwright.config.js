// @ts-check
const { defineConfig } = require("@playwright/test");

// 포트를 환경변수로 바꿀 수 있게 둔다. 운영 서버가 8975 를 점유한 채여도 작업 트리를
// 빈 포트로 띄워 돌릴 수 있다 — OPADA_PORT=8986 npx playwright test
const PORT = process.env.OPADA_PORT || "8975";
const BASE_URL = process.env.OPADA_BASE_URL || `http://127.0.0.1:${PORT}`;

module.exports = defineConfig({
  testDir: "tests",
  timeout: 30000,
  // 게이트 자기보고(PLAYED·AXES·pass/total)는 worker 밖에서 «한 번만» 낸다.
  // spec 안에서 세면 실패마다 worker 가 재시작되어 수치가 조각난다.
  reporter: [["line"], [require.resolve("./tests/gate-reporter.js")]],
  // 🔴 reuseExistingServer: true 와 고정 포트의 조합 때문에, 다른 경로의 서버가 이 포트를
  // 점유하고 있으면 e2e 가 그 서버를 재사용해 «남의 코드»를 검사하고 «통과»로 끝난다.
  // 그래서 시작 전에 서버가 주는 app.js·styles.css 가 이 작업 트리의 파일과 바이트까지
  // 같은지 확인하고, 다르면 즉시 실패시킨다(tests/global-setup.js).
  globalSetup: require.resolve("./tests/global-setup.js"),
  use: {
    baseURL: BASE_URL,
  },
  webServer: {
    command: `python3 src/server.py ${PORT}`,
    url: `${BASE_URL}/`,
    reuseExistingServer: true,
    timeout: 20000,
  },
});
