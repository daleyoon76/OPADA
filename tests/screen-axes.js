/**
 * 화면 게이트의 «연기 목록»과 «축 표».
 *
 * spec 이 아니라 별도 모듈에 둔다. Playwright 는 테스트가 실패하면 worker 를 버리고 새로
 * 띄우기 때문에, spec 파일 안에서 센 pass/total 은 붉은 실행에서 조각난다 —
 * 그 조각난 수치가 바로 이 게이트가 없애려는 «허위 자기보고»다.
 * 그래서 집계는 tests/gate-reporter.js(메인 프로세스)가 하고, 여기에는 데이터만 둔다.
 */

// 이 게이트가 프로덕션 호출부를 대신 «연기»한 것. 여기 있는 것은 screen.spec.js 가 검증하지 못한다.
const PLAYED = [
  [
    "/api/analyze",
    "실제 온비드 크롤링 대신 window.fetch 를 픽스처로 바꾼다. 서버 추출 로직은 " +
      "tests/test_docs_extraction.py(순수 함수)와 tests/measure_sample_23.py(표본 23건)가 맡는다",
  ],
  ["그 밖의 화면 요소", "연기하지 않는다 — 실제 src/app.js 가 실제 DOM에 그린다"],
  [
    "build_doc_checklist() · build_related_urls()",
    "N1~N6 픽스처의 docChecklist·relatedUrls 는 손으로 적은 것이다. 서버가 그 payload 를 실제로 " +
      "만드는지는 이 게이트가 «검증하지 않는다» — 값은 src/server.py:506-545,1037-1065 를 읽고 옮겼다",
  ],
];

// 축 → 케이스 → 음성 대조 → 커버(Y/N/영구불가) → 지금 예상 상태
const AXES = [
  ["S1", "A/B/C 사전 안내", "A형/B형 문구 + 배지 색(safe/warn)", "A형에 「첨부를 봐야 함」이 뜨지 않을 것 · A형 배지에 warn 이 붙지 않을 것", "Y", "초록"],
  ["S2", "조건별 체크리스트", "그룹·칩·발급처", "추출 성공 화면에 「찾지 못했습니다」가 없을 것", "Y", "초록"],
  ["S3", "못 뽑음 정직 표시", "못 뽑았다 문구", "추출 성공 화면에는 안 뜰 것", "Y", "초록"],
  ["S4", "진행 차단 없음", "누락 상태에서도 다음 단계 가능", "대화상자·disabled 0건", "Y", "초록"],
  ["S5", "최저입찰가 비공개", "「비공개」 표시", "정상 금액에는 안 뜰 것", "Y", "초록"],
  ["S6", "마감 D-day", "배지 노출", "상태 unknown 이면 배지 없을 것", "Y", "초록"],
  ["S7", "첨부 내려받기", "dnldFile.do 링크", "첨부 0건이면 링크 없을 것", "Y", "초록"],
  ["S8", "공고문 항목·용어", "목록 노출", "비어 있으면 안내 문장으로 대체될 것", "N", "축 없음"],
  ["S9", "공동입찰·명도책임", "값 그대로 표시 · 못 읽으면 「원문 확인」", "못 읽었을 때 행이 사라지거나 「불가능」으로 단정될 것 · 명도책임 값이 없는데 행이 생길 것", "N", "축 없음"],
  ["N0", "판정 함수 자체", "J1~J6 을 화면 없이 직접 호출", "각 함수마다 붉히지 «않아야» 하는 입력도 함께 단정", "Y", "초록"],
  ["N1", "「원문에 없음」 단정 + 첨부 동시 노출", "not_in_notice + relatedDocs 3건", "정상 A형(extracted) + 첨부 1건 — 단정 배지가 없으니 붉지 않을 것", "Y", "붉음(의도)"],
  ["N2", "부분 추출을 완전한 것처럼 말함", "extracted + items 1건", "B형 attachment_only — 「범위 한정」 note 를 요구하지 않을 것", "Y", "붉음(의도)"],
  ["N3", "generic 혼합 표에 총평 경고 없음", "tableRows = 실서류명 1행 + generic 3행", "전건 generic + 총평 note 있음 — 혼합이 아니니 붉지 않을 것", "Y", "붉음(의도)"],
  ["N4", "비공개 가격에 숫자 노출", "minimumBidPrice:\"비공개\" — 요약·분석직후 두 창", "정상 금액 450,000,000 — 출처가 비공개가 아니니 숫자가 있어도 붉지 않을 것", "Y", "초록"],
  ["N5", "LLM 미호출인데 AI 완료 단정", "aiCoach.llmStatus:\"rule_based\"", "llmStatus:\"connected\" — 같은 문구가 있어도 붉지 않을 것", "Y", "붉음(의도)"],
  ["N6", "500 링크를 정상 링크와 동급 제시", "relatedUrls.itemDetail 있고 pbctCdtnNo 없음(공고상세 입력)", "물건상세 입력(pbctCdtnNo 있음) — 같은 모양이어도 붉지 않을 것", "Y", "붉음(의도)"],
];

/** 「지금 붉어야 정상」이라고 선언한 축. 이 목록이 실제 실패와 어긋나면 리포터가 알린다. */
const EXPECTED_RED = AXES.filter((axis) => axis[5].startsWith("붉음")).map((axis) => axis[0]);

// 거짓 안내 P0 6건 ↔ 축. 축 표의 「커버 Y」는 «축을 선언했다»는 뜻이지 «P0 을 덮었다»는 뜻이
// 아니다. 배너가 둘을 같은 말처럼 읽히게 해서 이 표를 따로 둔다 — 축이 없는 P0 은 null 이다.
const P0_AXES = [
  ["P0-1", "부분 추출을 완전한 것처럼 말함", "N2"],
  ["P0-2", "첨부를 열지 않고 「원문에 없음」을 단정", "N1"],
  ["P0-3", "LLM 미호출인데 「AI 누락 점검」", "N5"],
  ["P0-4", "500 이 뜰 링크를 정상 링크로 제시", "N6"],
  ["P0-5", "「최대 30분 지연」 안내 부재", null],
  ["P0-6", "저장하지 않은 관심공고를 「2건」으로 셈", null],
];

function bannerLines() {
  const lines = [`PLAYED — 이 게이트가 대신 연기한 것 ${PLAYED.length}개`];
  for (const [symbol, note] of PLAYED) lines.push(`  · ${symbol} — ${note}`);
  lines.push(`AXES — 축 ${AXES.length}개 (축 → 케이스 → 음성 대조 → 커버 → 지금 예상)`);
  for (const [code, name, useCase, negative, covered, now] of AXES) {
    lines.push(`  ${code} ${name} → ${useCase} → ${negative} → ${covered} → ${now}`);
  }
  lines.push(`P0 — 거짓 안내 ${P0_AXES.length}건 ↔ 축`);
  for (const [code, name, axis] of P0_AXES) {
    lines.push(`  ${code} ${name} → ${axis ?? "축 없음 — 이 게이트가 보지 못한다"}`);
  }
  return lines;
}

/** 제목에서 축 코드를 뽑는다. "S1·S2·S5" 처럼 한 제목이 여러 축을 덮는다. */
function axisCodes(title) {
  return [...new Set(title.match(/\b[SN]\d\b/g) || [])];
}

/**
 * 커버리지를 «실행된 테스트 제목»에서 «센다». 축 표의 「커버 Y」 열은 손으로 적은 선언이라
 * 그것을 되읽으면 항진명제가 된다(2026-09-09 리뷰 P0-1) — 여기서는 읽지 않는다.
 *
 * 반환의 declaredButAbsent 가 그 선언과 실측의 어긋남이다.
 */
function measureAxisCoverage(titles) {
  const positive = new Map();
  const negative = new Map();
  for (const axis of AXES) {
    positive.set(axis[0], 0);
    negative.set(axis[0], 0);
  }
  for (const title of titles) {
    const bucket = title.includes("음성") ? negative : positive;
    for (const code of axisCodes(title)) {
      if (bucket.has(code)) bucket.set(code, bucket.get(code) + 1);
    }
  }
  const absent = AXES.filter((axis) => positive.get(axis[0]) === 0).map((axis) => `${axis[0]} ${axis[1]}`);
  return {
    positive,
    negative,
    absent,
    // 표가 「커버 Y」라고 적었는데 실제로 그 축을 도는 테스트가 없는 것.
    declaredButAbsent: AXES.filter((axis) => axis[4] === "Y" && positive.get(axis[0]) === 0).map((axis) => axis[0]),
    // 양성만 있고 「붉히면 안 되는 입력」이 없는 축.
    noNegative: AXES.filter((axis) => positive.get(axis[0]) > 0 && negative.get(axis[0]) === 0).map((axis) => axis[0]),
  };
}

/** 축이 아예 없는 P0. 「미커버 0개」가 「P0 전부 덮음」으로 읽히는 것을 막는다. */
function p0WithoutAxis() {
  return P0_AXES.filter((row) => row[2] === null).map((row) => `${row[0]} ${row[1]}`);
}

module.exports = {
  PLAYED,
  AXES,
  P0_AXES,
  EXPECTED_RED,
  bannerLines,
  axisCodes,
  measureAxisCoverage,
  p0WithoutAxis,
};
