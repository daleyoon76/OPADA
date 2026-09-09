/**
 * 화면 게이트 리포터.
 *
 * spec 안에서 세면 실패마다 worker 가 재시작되어 pass/total 이 조각난다. 집계는 메인
 * 프로세스인 이 리포터가 «한 번» 한다.
 *
 * 그리고 「지금 붉어야 정상」이라고 적어 둔 축(EXPECTED_RED)과 실제 실패를 대조한다 —
 * 표에 「붉음(의도)」라고 적고 실제로는 아무것도 안 도는 상태를 잡기 위한 것이다.
 */

const {
  AXES,
  EXPECTED_RED,
  bannerLines,
  axisCodes,
  measureAxisCoverage,
  p0WithoutAxis,
} = require("./screen-axes");

const SCREEN_SPEC = "screen.spec.js";

// 이 spec 이 가진 test 의 «정확한» 수. 하한(>=)이 아니라 일치(!==)로 본다 —
// 하한이 실제보다 낮으면 그 차이만큼 «공짜 삭제»가 생긴다(2026-09-09 r2 실측: 하한 15 ·
// 실제 16 이라 커버리지 측정 테스트 하나가 소리 없이 빠져도 경고 0건이었다).
// 값은 축 표에서 파생시키지 않는다 — 파생시키면 축을 지울 때 기대값이 같이 내려가 항상 통과한다.
const EXPECTED_TEST_COUNT = 16;

class GateReporter {
  onBegin(config, suite) {
    this.hasScreenSpec = suite
      .allTests()
      .some((testCase) => testCase.location.file.endsWith(SCREEN_SPEC));
    if (!this.hasScreenSpec) return;
    console.log(bannerLines().join("\n"));
  }

  onEnd(result) {
    if (!this.hasScreenSpec) return;
    const tests = this.suiteTests || [];
    const passed = tests.filter((entry) => entry.ok).length;
    const skipped = tests.filter((entry) => entry.skipped).length;
    const coverage = measureAxisCoverage(tests.map((entry) => entry.title));
    const p0Uncovered = p0WithoutAxis();

    const failedPositive = new Set();
    const failedNegative = [];
    const failedReach = [];
    for (const entry of tests) {
      if (entry.ok) continue;
      // 「도달 단정」이 깨진 실패는 위반이 아니라 픽스처·측정이 깨진 것이다.
      // 축 대조만 보면 둘이 같은 붉음으로 보인다 — 그래서 갈라 센다.
      if (entry.reachFailed) failedReach.push(entry.title);
      if (entry.title.includes("음성")) failedNegative.push(entry.title);
      else for (const code of axisCodes(entry.title)) failedPositive.add(code);
    }

    const lines = [
      `\n${passed}/${tests.length} 통과 · 축 ${AXES.length}개 중 «실행된» 축 ` +
        `${AXES.length - coverage.absent.length}개 · 도는 테스트가 없는 축 ${coverage.absent.length}개` +
        `${coverage.absent.length ? ` — ${coverage.absent.join(", ")}` : ""}`,
      `거짓 안내 P0 6건 중 축이 아예 없는 것 ${p0Uncovered.length}건` +
        `${p0Uncovered.length ? ` — ${p0Uncovered.join(", ")} · 이 게이트는 이것을 보지 못한다` : ""}`,
    ];

    // 배너가 붉은데 종료코드가 0 이면 CI 는 초록으로 읽는다 — 이 게이트가 없애려는 바로 그
    // 부류다. process.exitCode 는 Playwright 가 덮어쓰므로(2026-09-09 실측: 2/2 통과 ·
    // 모수 미달 2/15 인데 종료코드 0) onEnd 의 반환값으로 상태를 뒤집는다.
    let forcedFailure = false;

    // 모수. 빈 입력에서 나는 초록을 판정으로 세지 않는다. 더해도 붉는다 — 표를 같은
    // 커밋에서 갱신하게 하기 위해서다.
    if (tests.length !== EXPECTED_TEST_COUNT) {
      lines.push(
        `🔴 모수 어긋남 ${tests.length}/${EXPECTED_TEST_COUNT} — 이 실행은 판정이 아니다. ` +
          `축을 지웠거나, --grep 으로 걸렀거나, 크래시로 뒤 축이 돌지 않았다. ` +
          `test 를 더했으면 EXPECTED_TEST_COUNT 를 같은 커밋에서 갱신한다`,
      );
      forcedFailure = true;
    }
    if (skipped) {
      lines.push(`🔴 건너뛴 테스트 ${skipped}건 — 통과로 세지 않았다`);
      forcedFailure = true;
    }
    if (coverage.declaredButAbsent.length) {
      lines.push(
        `🔴 표가 「커버 Y」라고 적었는데 도는 테스트가 없는 축: ${coverage.declaredButAbsent.join(", ")}` +
          ` — 선언이 코드보다 넓다. 축을 만들거나 표의 커버 칸을 N 으로 내린다`,
      );
      forcedFailure = true;
    }
    if (coverage.noNegative.length) {
      lines.push(
        `🔴 「붉히면 안 되는 입력」이 없는 축: ${coverage.noNegative.join(", ")}` +
          ` — 양성만 있는 축은 무엇이든 붉히는 검사와 구분되지 않는다`,
      );
      forcedFailure = true;
    }

    const expected = new Set(EXPECTED_RED);
    const unexpectedRed = [...failedPositive].filter((code) => !expected.has(code)).sort();
    const unexpectedGreen = [...expected].filter((code) => !failedPositive.has(code)).sort();

    lines.push(`「붉음(의도)」로 선언한 축 ${EXPECTED_RED.length}개: ${EXPECTED_RED.join(", ")}`);
    lines.push(`실제로 붉은 축 ${failedPositive.size}개: ${[...failedPositive].sort().join(", ") || "없음"}`);
    if (unexpectedRed.length) {
      lines.push(`🔴 선언에 없는데 붉은 축: ${unexpectedRed.join(", ")} — 회귀다`);
      forcedFailure = true;
    }
    if (unexpectedGreen.length) {
      lines.push(
        `🔴 「붉음(의도)」인데 초록인 축: ${unexpectedGreen.join(", ")} — 고쳐서 초록이면 표의 「지금 예상」을 ` +
          `같은 커밋에서 「초록」으로 바꾼다. 안 고쳤는데 초록이면 그 축은 «돌지 않은» 것이다`,
      );
      forcedFailure = true;
    }
    if (failedReach.length) {
      lines.push(
        `🔴 도달 단정 실패 ${failedReach.length}건 — 이 축들의 붉음은 «위반» 이 아니라 픽스처·측정이 ` +
          `깨진 것이다. 판정 함수는 이 실행에서 «증명되지 않았다»:`,
      );
      for (const title of failedReach) lines.push(`  · ${title}`);
    }
    if (failedNegative.length) {
      lines.push(`🔴 음성 대조 실패 ${failedNegative.length}건 — 음성은 어느 상태에서도 초록이어야 한다:`);
      for (const title of failedNegative) lines.push(`  · ${title}`);
    }
    if (failedReach.length || failedNegative.length) forcedFailure = true;

    const finalStatus = forcedFailure && result.status === "passed" ? "failed" : result.status;
    lines.push(`실행 상태: ${finalStatus}${finalStatus !== result.status ? ` (게이트가 ${result.status} 를 뒤집었다)` : ""}`);
    console.log(lines.join("\n"));
    if (finalStatus !== result.status) return { status: finalStatus };
  }

  onTestEnd(testCase, testResult) {
    if (!testCase.location.file.endsWith(SCREEN_SPEC)) return;
    this.suiteTests = this.suiteTests || [];
    // 재시도가 있으면 마지막 결과로 덮어쓴다.
    const existing = this.suiteTests.find((entry) => entry.title === testCase.title);
    // status === expectedStatus 로 세면 skip 이 «통과»로 들어온다(둘 다 "skipped").
    // 통과는 실제로 돌아서 초록인 것만이다.
    const skippedTest = testResult.status === "skipped";
    const ok = !skippedTest && testResult.status === testCase.expectedStatus;
    // 도달 단정에는 "도달: …" 표를 달아 뒀다(screen.spec.js). 그 표가 실패 메시지에 있으면
    // 이 실패는 판정이 아니라 픽스처·측정이 깨진 것이다.
    const reachFailed = (testResult.errors || []).some((error) => (error.message || "").includes("도달:"));
    if (existing) Object.assign(existing, { ok, reachFailed, skipped: skippedTest });
    else this.suiteTests.push({ title: testCase.title, ok, reachFailed, skipped: skippedTest });
  }
}

module.exports = GateReporter;
