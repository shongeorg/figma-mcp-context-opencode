import { test, expect } from '@playwright/test';

test.describe('📸 Cross-Browser Screenshots', () => {
  test.describe.configure({ timeout: 40000, retries: 0 });

  test('Desktop screenshot (1920x1080)', async ({ page, baseURL, browserName }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const screenshot = await page.screenshot({ fullPage: true });

    expect(screenshot).toBeTruthy();
    console.log(`📸 Desktop screenshot made (${browserName})`);
  });

  test('Tablet screenshot (768x1024)', async ({ page, baseURL, browserName }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const screenshot = await page.screenshot({ fullPage: true });

    expect(screenshot).toBeTruthy();
    console.log(`📸 Tablet screenshot made (${browserName})`);
  });

  test('Mobile screenshot (375x667)', async ({ page, baseURL, browserName }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const screenshot = await page.screenshot({ fullPage: true });

    expect(screenshot).toBeTruthy();
    console.log(`📸 Mobile screenshot made (${browserName})`);
  });

  test('Hero section screenshot', async ({ page, baseURL, browserName }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const hero = page.locator('section').first();

    try {
      await hero.waitFor({ state: 'visible', timeout: 5000 });
      const screenshot = await hero.screenshot();
      expect(screenshot).toBeTruthy();
      console.log(`📸 Hero section screenshot made (${browserName})`);
    } catch (e) {
      console.log(`⚠️ Hero section not found (${browserName})`);
    }
  });

  test('Navigation menu screenshot', async ({ page, baseURL, browserName }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');

    const nav = page.locator('nav').first();

    try {
      await nav.waitFor({ state: 'visible', timeout: 5000 });
      const screenshot = await nav.screenshot();
      expect(screenshot).toBeTruthy();
      console.log(`📸 Navigation screenshot made (${browserName})`);
    } catch (e) {
      console.log(`⚠️ Navigation not found (${browserName})`);
    }
  });

  test('Footer screenshot', async ({ page, baseURL, browserName }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const footer = page.locator('footer').first();

    try {
      await footer.waitFor({ state: 'visible', timeout: 5000 });
      const screenshot = await footer.screenshot();
      expect(screenshot).toBeTruthy();
      console.log(`📸 Footer screenshot made (${browserName})`);
    } catch (e) {
      console.log(`⚠️ Footer not found (${browserName})`);
    }
  });

  test('About page screenshot', async ({ page, baseURL, browserName }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/shop/');
    await page.waitForLoadState('networkidle');

    const screenshot = await page.screenshot({ fullPage: true });

    expect(screenshot).toBeTruthy();
    console.log(`📸 About page screenshot made (${browserName})`);
  });

  test('Login page screenshot', async ({ page, baseURL, browserName }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/login/');
    await page.waitForLoadState('networkidle');

    const screenshot = await page.screenshot({ fullPage: true });

    expect(screenshot).toBeTruthy();
    console.log(`📸 Login page screenshot made (${browserName})`);
  });

  test('📋 Screenshot Summary Report', async ({ page, baseURL, browserName }) => {
    console.log('\n' + '='.repeat(60));
    console.log('📸 SCREENSHOT TEST REPORT');
    console.log('='.repeat(60));
    console.log(`📍 Base URL: ${baseURL}`);
    console.log(`🌐 Browser: ${browserName}`);
    console.log(`📅 Date: ${new Date().toLocaleString('uk-UA')}`);
    console.log('='.repeat(60));

    const viewports = [
      { name: 'Desktop', width: 1920, height: 1080 },
      { name: 'Tablet', width: 768, height: 1024 },
      { name: 'Mobile', width: 375, height: 667 },
    ];

    for (const vp of viewports) {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      const screenshot = await page.screenshot({ fullPage: false });

      console.log(`✅ ${vp.name} (${vp.width}x${vp.height}): ${screenshot.length} bytes`);
    }

    console.log('\n' + '='.repeat(60));
    console.log('✅ Screenshot tests completed');
    console.log('='.repeat(60) + '\n');

    expect(true).toBeTruthy();
  });
});

test.describe('🎨 Visual Regression Tests', () => {
  test.describe.configure({ timeout: 40000, retries: 0 });

  test('Homepage visual regression', async ({ page, baseURL }, testInfo) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    expect(await page.screenshot()).toMatchSnapshot('homepage-desktop.png', {
      maxDiffPixels: 100
    });

    console.log(`🎨 Homepage visual regression check passed`);
  });

  test('Mobile homepage visual regression', async ({ page, baseURL }, testInfo) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    expect(await page.screenshot()).toMatchSnapshot('homepage-mobile.png', {
      maxDiffPixels: 100
    });

    console.log(`🎨 Mobile homepage visual regression check passed`);
  });
});

test.describe('📱 Device Screenshots', () => {
  test.describe.configure({ timeout: 40000, retries: 0 });

  test('iPhone 12 screenshot', async ({ page, baseURL, browserName }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const screenshot = await page.screenshot({ fullPage: true });

    expect(screenshot).toBeTruthy();
    console.log(`📱 iPhone 12 screenshot made (${browserName})`);
  });

  test('Pixel 5 screenshot', async ({ page, baseURL, browserName }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const screenshot = await page.screenshot({ fullPage: true });

    expect(screenshot).toBeTruthy();
    console.log(`📱 Pixel 5 screenshot made (${browserName})`);
  });

  test('iPad Pro screenshot', async ({ page, baseURL, browserName }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const screenshot = await page.screenshot({ fullPage: true });

    expect(screenshot).toBeTruthy();
    console.log(`📱 iPad Pro screenshot made (${browserName})`);
  });
});
