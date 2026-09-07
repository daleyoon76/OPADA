// @ts-check
const { defineConfig } = require("@playwright/test");

module.exports = defineConfig({
  testDir: "tests",
  timeout: 30000,
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
