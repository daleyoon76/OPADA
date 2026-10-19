// @ts-check
// 이 워크트리(Hometest_op-agentic) 전용 e2e 설정. 메인 워크트리(Hometest_op)의
// playwright.config.js(포트 8975 고정)는 건드리지 않고, 포트만 다르게 분리했다.
const { defineConfig } = require("@playwright/test");

const PORT = process.env.OPADA_E2E_PORT || "19005";

module.exports = defineConfig({
  testDir: "tests",
  timeout: 30000,
  // 병렬 워커로 돌리면 헤드리스 크로미움 여러 개가 이 맥미니에서 자원을 다투며 매번
  // 다른 테스트가 간헐적으로 타임아웃났다(2026-10-14 phase5 실측 — N3·N4 음성 테스트가
  // 단독 실행에서는 항상 통과하는데 전체 실행에서만 번갈아 실패). 순차 실행으로 고정한다.
  workers: 1,
  reporter: [["line"], [require.resolve("./tests/gate-reporter.js")]],
  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
  },
  webServer: {
    command: `python3 src/server.py ${PORT}`,
    url: `http://127.0.0.1:${PORT}/`,
    reuseExistingServer: true,
    timeout: 20000,
  },
});
