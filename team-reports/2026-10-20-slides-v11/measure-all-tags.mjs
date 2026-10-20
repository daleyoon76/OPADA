import pkg from '/Users/user/Documents/Dev/Hometest_op/node_modules/@playwright/test/index.js';
const { chromium } = pkg;
const deck = process.argv[2];
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
await p.goto('file://' + deck, { waitUntil: 'networkidle' });
const out = await p.evaluate(() => {
  const res = [];
  document.querySelectorAll('.slide').forEach((s, i) => {
    const cs = getComputedStyle(s);
    const sr = s.getBoundingClientRect();
    const innerTop = sr.top + parseFloat(cs.paddingTop);
    const innerBottom = sr.bottom - parseFloat(cs.paddingBottom);
    // 글자를 담은 말단 요소를 모두 본다. 태그 종류를 가리지 않는다.
    const leaves = [...s.querySelectorAll('*')].filter(el => {
      if (!(el.textContent || '').trim()) return false;
      if (el.closest('.pagefoot')) return false;  // 쪽 바닥글은 설계상 아래 여백에 놓인다
      if ([...el.children].some(c => (c.textContent || '').trim())) return false;
      const r = el.getBoundingClientRect();
      return r.width > 1 && r.height > 1;
    });
    let clipped = 0, overlap = 0;
    const samples = [];
    leaves.forEach(el => {
      const r = el.getBoundingClientRect();
      if (r.bottom > innerBottom + 1 || r.top < innerTop - 1 ||
          r.right > sr.right - 1 || r.left < sr.left + 1) {
        clipped++;
        if (samples.length < 4) samples.push(['안쪽영역 벗어남', el.className || el.tagName,
          (el.textContent || '').trim().slice(0, 18)]);
      }
    });
    for (let a = 0; a < leaves.length; a++) for (let c = a + 1; c < leaves.length; c++) {
      const A = leaves[a], B = leaves[c];
      if (A.contains(B) || B.contains(A)) continue;
      const ra = A.getBoundingClientRect(), rb = B.getBoundingClientRect();
      const ox = Math.min(ra.right, rb.right) - Math.max(ra.left, rb.left);
      const oy = Math.min(ra.bottom, rb.bottom) - Math.max(ra.top, rb.top);
      if (ox > 2 && oy > 2) {
        overlap++;
        if (samples.length < 6) samples.push(['겹침',
          (A.textContent||'').trim().slice(0,14), (B.textContent||'').trim().slice(0,14)]);
      }
    }
    res.push({ slide: i + 1, leaves: leaves.length, clipped, overlap, samples });
  });
  return res;
});
console.log(JSON.stringify(out, null, 1));
await b.close();
