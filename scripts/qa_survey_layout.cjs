// Optional browser regression check using an existing Playwright installation.
// Run only against the QA server and an authenticated synthetic manager session.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

const args = process.argv.slice(2);
function argument(name) {
  const index = args.indexOf(name);
  assert(index >= 0 && args[index + 1], `Missing ${name}`);
  return args[index + 1];
}
const base = new URL(argument('--base-url'));
assert(['127.0.0.1', 'localhost'].includes(base.hostname) && base.port === '8002',
       'Use the local QA server on port 8002');
const surveyId = argument('--survey-id');
assert(/^\d+$/.test(surveyId));
const state = argument('--storage-state');
const output = path.resolve(argument('--output'));
fs.mkdirSync(output, { recursive: true });

(async () => {
  const browser = await chromium.launch({ channel: process.env.QA_BROWSER_CHANNEL || 'msedge', headless: true });
  try {
    const context = await browser.newContext({ storageState: state, deviceScaleFactor: 1 });
    const page = await context.newPage();
    await page.setViewportSize({ width: 390, height: 900 });
    const list = await page.goto(new URL('/surveys/manage/', base).href);
    assert.equal(list.status(), 200);
    await page.waitForLoadState('networkidle');
    const region = page.getByRole('region', { name: 'Danh sách khảo sát', exact: true });
    await region.focus();
    await region.press('ArrowRight');
    await page.waitForFunction(() => document.querySelector('.sv-table-scroll').scrollLeft > 0);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth), 390,
                 'Survey list must scroll inside its keyboard-accessible region');
    await page.screenshot({ path: path.join(output, 'survey-list-390.png'), fullPage: true });
    const response = await page.goto(new URL(`/surveys/manage/${surveyId}/stats/`, base).href);
    assert.equal(response.status(), 200);
    assert(page.url().endsWith(`/surveys/manage/${surveyId}/stats/`), 'Manager session required');
    await page.waitForLoadState('networkidle');
    for (const width of [1440, 390]) {
      await page.setViewportSize({ width, height: 900 });
      const metrics = await page.evaluate(() => ({
        width: innerWidth, scroll: document.documentElement.scrollWidth, scale: visualViewport.scale,
      }));
      assert.equal(metrics.scroll, width, 'Statistics must not overflow horizontally');
      assert.equal(metrics.scale, 1);
      assert.equal(await page.locator('.sv-print-title').isVisible(), false);
      const bars = await page.locator('.sv-bar > span').evaluateAll(elements => elements.map(element => ({
        width: element.getBoundingClientRect().width,
        track: element.parentElement.getBoundingClientRect().width,
        css: element.style.width,
      })));
      for (const bar of bars) {
        assert(!bar.css.includes(','), 'CSS percentages must use decimal dots');
        assert(bar.width <= bar.track + 1);
      }
      await page.screenshot({ path: path.join(output, `statistics-${width}.png`), fullPage: true });
    }
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.getByRole('button', { name: 'In báo cáo', exact: true }).click();
    await page.emulateMedia({ media: 'print' });
    assert.equal(await page.locator('.crm-sidebar').isVisible(), false);
    assert.equal(await page.locator('.crm-header').isVisible(), false);
    assert.equal(await page.locator('.sv-print-title').isVisible(), true);
    const print = await page.evaluate(() => ({
      shell: document.querySelector('.crm-shell').getBoundingClientRect().width,
      workspace: document.querySelector('.crm-workspace').getBoundingClientRect().width,
      columns: getComputedStyle(document.querySelector('.sv-grid')).gridTemplateColumns.split(' ').length,
    }));
    assert(print.workspace >= print.shell - 1, 'Printed report must use the full available width');
    assert.equal(print.columns, 4);
    await page.screenshot({ path: path.join(output, 'statistics-print.png'), fullPage: true });
    await page.pdf({ path: path.join(output, 'statistics-print.pdf'), format: 'A4', printBackground: true });
    console.log(JSON.stringify({ result: 'PASS', desktop: 1440, mobile: 390, scale: 1, print }));
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error.message); process.exitCode = 1; });
