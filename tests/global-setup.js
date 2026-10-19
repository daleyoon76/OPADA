// e2e 가 «이 작업 트리의 코드»를 검사하는지 시작 전에 확인한다.
//
// 🔴 왜 필요한가 — playwright.config.js 는 reuseExistingServer: true 와 고정 포트 8975 를
// 쓴다. 그래서 다른 경로(운영 경로 등)의 서버가 그 포트를 이미 점유하고 있으면, 작업 트리의
// e2e 가 그 서버를 그대로 재사용해 «남의 코드»를 검사한다. 더 나쁜 것은 그 결과가 실패가
// 아니라 통과로 끝난다는 점이다. 2026-10-18 에 실제로 그 일이 일어났다 — 4단계 구조를
// 단정하는 toEqual 이 통과했는데, curl 로 재어 보니 서버가 주는 app.js 에 그 단계 제목이
// 0건이었다(team-reports/2026-10-18-bid-doc-timeline/implementation.md §3).
//
// 특징 문자열("낙찰 후 준비" 등)로 확인하지 않는다. 그 방식은 다음 변경에서 낡고, 낡은
// 뒤에는 조용히 통과한다. 대신 작업 트리의 src/app.js 와 서버가 주는 /app.js 의 바이트를
// 직접 비교한다 — 어떤 변경을 해도 이 단정은 함께 움직인다.
const crypto = require("crypto");
const fs = require("fs");
const path = require("path");

// 서비스 경로 ↔ 작업 트리 파일. 두 개를 보는 이유는 한쪽만 맞는 배포 상태를 가리지 않기
// 위해서다(app.js 는 작업 트리, server.py 는 운영 경로인 혼합 상태가 있을 수 있다).
const SERVED_FILES = [
  { url: "/app.js", file: path.join(__dirname, "..", "src", "app.js") },
  { url: "/styles.css", file: path.join(__dirname, "..", "src", "styles.css") },
];

function sha256(buffer) {
  return crypto.createHash("sha256").update(buffer).digest("hex");
}

module.exports = async function globalSetup(config) {
  const baseURL =
    process.env.OPADA_BASE_URL ||
    config?.projects?.[0]?.use?.baseURL ||
    "http://127.0.0.1:8975";

  const mismatches = [];
  for (const target of SERVED_FILES) {
    const local = fs.readFileSync(target.file);
    const response = await fetch(new URL(target.url, baseURL));
    if (!response.ok) {
      mismatches.push(`${target.url} 를 받지 못했습니다 (HTTP ${response.status})`);
      continue;
    }
    const served = Buffer.from(await response.arrayBuffer());
    const localHash = sha256(local);
    const servedHash = sha256(served);
    if (localHash !== servedHash) {
      mismatches.push(
        `${target.url} 가 이 작업 트리의 파일과 다릅니다. ` +
          `작업 트리 ${localHash.slice(0, 12)} (${local.length}바이트) ↔ ` +
          `서버 ${servedHash.slice(0, 12)} (${served.length}바이트)`,
      );
    }
  }

  if (mismatches.length) {
    throw new Error(
      [
        `🔴 ${baseURL} 의 서버가 이 작업 트리의 코드를 서비스하지 않습니다. e2e 를 중단합니다.`,
        ...mismatches.map((line) => `  · ${line}`),
        "",
        "다른 경로의 서버가 이 포트를 점유하고 있을 가능성이 높습니다. 확인 방법:",
        "  lsof -nP -iTCP:8975 -sTCP:LISTEN",
        "",
        "해결 방법 가운데 하나를 고르십시오.",
        "  ⑴ 그 서버를 멈춘 뒤 다시 돌립니다.",
        "  ⑵ 빈 포트로 띄워 돌립니다 — OPADA_PORT=8986 npx playwright test",
        "     (서버는 포트를 첫 명령행 인자로 받고, playwright.config.js 가 그 값을 넘깁니다)",
        "",
        "이 검사를 끄지 마십시오. 이것이 없으면 e2e 가 남의 코드를 검사하고 «통과»로 끝납니다.",
      ].join("\n"),
    );
  }
};
