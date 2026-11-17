// A screenshot of an interactive HTML BOM, the page KiBot's ibom output writes, with one row
// of the BOM selected so that its parts light up on the board.
//
//   NODE_PATH=<node_modules with playwright> node scripts/screenshots/browser/ibom.cjs IBOM.html OUT.png [REFS]
//
// REFS is the References cell of the row to select, as the page shows it (default "R1, R2").
// It opens the page in headless Chromium at 1280 x 720, in the page's own default (light)
// theme, clicks the row and saves the window. Lab 05's figure,
// docs/assets/img/kibot-ibom-simproc-pmod.png, is this script run on the reference's ibom,
// which `python3 labs/lab-05-fab-outputs-in-ci/src/selftest.py` writes into
// labs/lab-05-fab-outputs-in-ci/results/selftest/reference/out/kibot/pmod-ibom.html.
// Playwright and its Chromium come from npm (`npm install playwright`, then
// `npx playwright install chromium`); the course repo doesn't install them.
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const [input, output, refs = 'R1, R2'] = process.argv.slice(2);
  if (!input || !output) {
    console.error('usage: node ibom.cjs IBOM.html OUT.png [REFS]');
    process.exit(2);
  }
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage({ viewport: { width: 1280, height: 720 }, colorScheme: 'light' });
    const errors = [];
    page.on('pageerror', e => errors.push(String(e)));
    await page.goto('file://' + path.resolve(input));
    await page.waitForSelector('#bombody tr');
    const row = page.locator('#bombody tr', { hasText: refs }).first();
    if (await row.count() === 0) throw new Error(`no BOM row with ${refs}`);
    await row.click();
    await page.waitForTimeout(300);
    await page.screenshot({ path: output });
    if (errors.length) throw new Error('errors on the page: ' + errors.join('; '));
    console.log(`ibom.cjs: ${output}, row "${refs}" selected`);
  } finally {
    await browser.close();
  }
})().catch(e => { console.error('ibom.cjs: ' + e.message); process.exit(1); });
