#!/usr/bin/env node
const { chromium } = require('playwright');
const path = require('path');
const { pathToFileURL } = require('url');

const input = process.argv[2];
if (!input) {
  console.error('usage: node adco_visualization_browser_audit.cjs <standalone-html> [screenshot-dir]');
  process.exit(2);
}

const screenshotDir = process.argv[3] || null;
const cases = [
  { name: 'desktop-light', width: 736, height: 900, colorScheme: 'light' },
  { name: 'mobile-dark', width: 320, height: 900, colorScheme: 'dark' },
];

(async () => {
  const browser = await chromium.launch({ headless: true });
  const failures = [];
  for (const item of cases) {
    const page = await browser.newPage({
      viewport: { width: item.width, height: item.height },
      colorScheme: item.colorScheme,
      reducedMotion: 'reduce',
    });
    await page.addInitScript(() => {
      window.__adcoFollowUps = [];
      window.openai = {
        sendFollowUpMessage: async (payload) => {
          window.__adcoFollowUps.push(payload);
        },
      };
    });
    await page.goto(pathToFileURL(path.resolve(input)).href);
    await page.waitForLoadState('domcontentloaded');

    const frame = page.frames().find((candidate) => candidate !== page.mainFrame());
    if (!frame) {
      failures.push(`${item.name}: official wrapper iframe missing`);
      await page.close();
      continue;
    }
    const root = frame.locator('[data-adco-visual]');
    if (await root.count() !== 1) failures.push(`${item.name}: expected one visualization root`);
    const layout = await frame.evaluate(() => {
      const rootNode = document.querySelector('[data-adco-visual]');
      const overflow = [...document.querySelectorAll('[data-adco-visual] *')].filter((node) => {
        const style = getComputedStyle(node);
        return /(auto|scroll)/.test(`${style.overflow}${style.overflowX}${style.overflowY}`) &&
          (node.scrollWidth > node.clientWidth + 1 || node.scrollHeight > node.clientHeight + 1);
      });
      return {
        bodyOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
        rootOverflow: rootNode.scrollWidth > rootNode.clientWidth + 1,
        nestedScroll: overflow.length,
      };
    });
    if (layout.bodyOverflow || layout.rootOverflow) failures.push(`${item.name}: horizontal overflow`);
    if (layout.nestedScroll) failures.push(`${item.name}: nested scrolling detected`);

    const images = root.locator('img');
    for (let index = 0; index < await images.count(); index += 1) {
      if (!(await images.nth(index).evaluate((node) => node.complete && node.naturalWidth > 0))) {
        failures.push(`${item.name}: preview image ${index + 1} did not load`);
      }
      if (!(await images.nth(index).getAttribute('alt'))) failures.push(`${item.name}: preview image ${index + 1} lacks alt text`);
    }

    const previewStatus = root.locator('.adco-preview-status');
    if (await previewStatus.count()) {
      const statusText = (await previewStatus.first().innerText()).trim();
      const visibleText = await root.innerText();
      const actionLabels = await root.locator('[data-adco-action]').allInnerTexts();
      if (await root.locator('.adco-creative-brief').count() !== 1) {
        failures.push(`${item.name}: asset review lacks ADCO creative brief`);
      }
      if (await root.locator('.adco-creative-lens').count() !== 3) {
        failures.push(`${item.name}: asset review lacks customer/product/brand reading`);
      }
      if (!visibleText.includes('消费者时刻') || !visibleText.includes('产品证明') || !visibleText.includes('品牌记忆')) {
        failures.push(`${item.name}: ADCO creative lenses are not visible`);
      }
      if (await root.locator('.adco-channel-card').count() < 1) {
        failures.push(`${item.name}: asset review lacks channel placement plan`);
      }
      if (await root.locator('[data-adco-finding]').count() < 1) {
        failures.push(`${item.name}: asset review lacks visible region findings`);
      }
      const hotspots = root.locator('[data-adco-hotspot]');
      if (await hotspots.count()) {
        await hotspots.first().focus();
        await page.keyboard.press('Enter');
        if (!(await root.locator('[data-adco-finding="1"]').evaluate((node) => node.classList.contains('is-active')))) {
          failures.push(`${item.name}: image hotspot did not focus its creative finding`);
        }
        if (await hotspots.first().getAttribute('aria-pressed') !== 'true') {
          failures.push(`${item.name}: image hotspot lacks pressed selection semantics`);
        }
      }
      if (statusText === '演示占位图') {
        if (!visibleText.includes('暂不能确认使用')) failures.push(`${item.name}: placeholder lacks fail-closed availability`);
        if (actionLabels.some((label) => label.trim() === '确认使用')) failures.push(`${item.name}: placeholder exposes a use-confirmation action`);
      }
    }

    const choices = root.locator('[data-adco-option]');
    let selectedLabel = null;
    if (await choices.count()) {
      const selectedIndex = Math.min(1, (await choices.count()) - 1);
      selectedLabel = (await choices.nth(selectedIndex).innerText()).trim();
      await choices.nth(selectedIndex).focus();
      await page.keyboard.press('Enter');
      if ((await choices.nth(selectedIndex).getAttribute('aria-pressed')) !== 'true') {
        failures.push(`${item.name}: keyboard selection did not update`);
      }
      const detail = await root.locator('[data-adco-detail]').innerText();
      if (!detail.includes(selectedLabel)) failures.push(`${item.name}: selected detail did not update`);
    }

    const actions = root.locator('[data-adco-action]');
    for (let actionIndex = 0; actionIndex < await actions.count(); actionIndex += 1) {
      const actionLabel = (await actions.nth(actionIndex).innerText()).trim();
      await actions.nth(actionIndex).click();
      const messages = await frame.evaluate(() => window.__adcoFollowUps);
      if (messages.length !== actionIndex + 1) {
        failures.push(`${item.name}: action ${actionIndex + 1} did not produce exactly one follow-up`);
        continue;
      }
      const message = messages[messages.length - 1];
      if (message.title !== actionLabel) failures.push(`${item.name}: action ${actionIndex + 1} follow-up title mismatch`);
      if (!message.prompt.includes('请先确认我看到的是最新内容')) {
        failures.push(`${item.name}: action ${actionIndex + 1} lacks latest-state recheck`);
      }
      if (!message.prompt.includes('不代表对外发送或项目完成')) {
        failures.push(`${item.name}: action ${actionIndex + 1} lacks non-authority boundary`);
      }
      if (await previewStatus.count() && !message.prompt.includes('本次请重点检查：')) {
        failures.push(`${item.name}: asset action ${actionIndex + 1} lacks ADCO review focus`);
      }
      if (selectedLabel && !message.prompt.includes(selectedLabel)) {
        failures.push(`${item.name}: follow-up did not include the selected value`);
      }
    }
    if (screenshotDir) {
      await page.screenshot({ path: path.join(screenshotDir, `${item.name}.png`), fullPage: true });
    }
    await page.close();
  }
  await browser.close();
  console.log(`ADCO_VISUALIZATION_BROWSER_AUDIT: ${failures.length ? 'FAIL' : 'PASS'}`);
  for (const failure of failures) console.log(`- ${failure}`);
  process.exit(failures.length ? 1 : 0);
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
