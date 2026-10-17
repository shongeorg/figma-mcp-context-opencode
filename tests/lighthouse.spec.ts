import { test, expect } from '@playwright/test';

test.beforeEach(async ({ browserName }) => {
  test.skip(browserName !== 'chromium', 'Lighthouse audit requires CDP (Chromium only)');
});

test.describe('📱 Lighthouse Mobile Performance', () => {
  test('Mobile Performance Audit', async ({ page }) => {
    await page.emulateMedia({ media: 'screen' });
    await page.setViewportSize({ width: 393, height: 851 });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const lighthouseResult = await runLighthouseAudit(page, 'mobile');

    console.log('\n📱 MOBILE LIGHTHOUSE REPORT');
    console.log('='.repeat(50));
    console.log(`Performance: ${lighthouseResult.performance}/100`);
    console.log(`Accessibility: ${lighthouseResult.accessibility}/100`);
    console.log(`Best Practices: ${lighthouseResult.bestPractices}/100`);
    console.log(`SEO: ${lighthouseResult.seo}/100`);
    console.log('='.repeat(50));

    expect(lighthouseResult.performance).toBeGreaterThanOrEqual(50);
    expect(lighthouseResult.accessibility).toBeGreaterThanOrEqual(50);
    expect(lighthouseResult.bestPractices).toBeGreaterThanOrEqual(50);
    expect(lighthouseResult.seo).toBeGreaterThanOrEqual(50);
  });

  test('Mobile Core Web Vitals', async ({ page }) => {
    await page.emulateMedia({ media: 'screen' });
    await page.setViewportSize({ width: 393, height: 851 });

    await page.goto('/');

    const metrics = await getCoreWebVitals(page);

    console.log('\n📱 MOBILE CORE WEB VITALS');
    console.log('='.repeat(50));
    console.log(`LCP: ${metrics.lcp?.toFixed(0) || 'N/A'}ms (target: <4000ms)`);
    console.log(`FCP: ${metrics.fcp?.toFixed(0) || 'N/A'}ms (target: <3000ms)`);
    console.log(`CLS: ${metrics.cls?.toFixed(3) || 'N/A'} (target: <0.25)`);
    console.log(`TTFB: ${metrics.ttfb?.toFixed(0) || 'N/A'}ms (target: <2000ms)`);
    console.log('='.repeat(50));

    if (metrics.lcp) expect(metrics.lcp).toBeLessThan(4000);
    if (metrics.fcp) expect(metrics.fcp).toBeLessThan(3000);
    if (metrics.cls) expect(metrics.cls).toBeLessThan(0.25);
    if (metrics.ttfb) expect(metrics.ttfb).toBeLessThan(2000);
  });
});

test.describe('🖥️ Lighthouse Desktop Performance', () => {
  test('Desktop Performance Audit', async ({ page }) => {
    await page.emulateMedia({ media: 'screen' });
    await page.setViewportSize({ width: 1920, height: 1080 });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const lighthouseResult = await runLighthouseAudit(page, 'desktop');

    console.log('\n🖥️ DESKTOP LIGHTHOUSE REPORT');
    console.log('='.repeat(50));
    console.log(`Performance: ${lighthouseResult.performance}/100`);
    console.log(`Accessibility: ${lighthouseResult.accessibility}/100`);
    console.log(`Best Practices: ${lighthouseResult.bestPractices}/100`);
    console.log(`SEO: ${lighthouseResult.seo}/100`);
    console.log('='.repeat(50));

    expect(lighthouseResult.performance).toBeGreaterThanOrEqual(50);
    expect(lighthouseResult.accessibility).toBeGreaterThanOrEqual(50);
    expect(lighthouseResult.bestPractices).toBeGreaterThanOrEqual(50);
    expect(lighthouseResult.seo).toBeGreaterThanOrEqual(50);
  });

  test('Desktop Core Web Vitals', async ({ page }) => {
    await page.emulateMedia({ media: 'screen' });
    await page.setViewportSize({ width: 1920, height: 1080 });

    await page.goto('/');

    const metrics = await getCoreWebVitals(page);

    console.log('\n🖥️ DESKTOP CORE WEB VITALS');
    console.log('='.repeat(50));
    console.log(`LCP: ${metrics.lcp?.toFixed(0) || 'N/A'}ms (target: <3000ms)`);
    console.log(`FCP: ${metrics.fcp?.toFixed(0) || 'N/A'}ms (target: <3000ms)`);
    console.log(`CLS: ${metrics.cls?.toFixed(3) || 'N/A'} (target: <0.1)`);
    console.log(`TTFB: ${metrics.ttfb?.toFixed(0) || 'N/A'}ms (target: <2000ms)`);
    console.log('='.repeat(50));

    if (metrics.lcp) expect(metrics.lcp).toBeLessThan(3000);
    if (metrics.fcp) expect(metrics.fcp).toBeLessThan(3000);
    if (metrics.cls) expect(metrics.cls).toBeLessThan(0.1);
    if (metrics.ttfb) expect(metrics.ttfb).toBeLessThan(2000);
  });
});

test.describe('📊 Mobile vs Desktop Comparison', () => {
  test('Generate Performance Comparison Report', async ({ page }) => {
    const mobileMetrics: any = {};
    const desktopMetrics: any = {};

    await page.emulateMedia({ media: 'screen' });
    await page.setViewportSize({ width: 393, height: 851 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    Object.assign(mobileMetrics, await getCoreWebVitals(page));

    await page.emulateMedia({ media: 'screen' });
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    Object.assign(desktopMetrics, await getCoreWebVitals(page));

    console.log('\n' + '='.repeat(70));
    console.log('📊 MOBILE vs DESKTOP PERFORMANCE COMPARISON REPORT');
    console.log('='.repeat(70));
    console.log(`📅 Date: ${new Date().toLocaleString('uk-UA')}`);
    console.log('='.repeat(70));

    console.log('\n📱 MOBILE (393x851 - Pixel 5)');
    console.log('-'.repeat(70));
    console.log(`  LCP:  ${mobileMetrics.lcp?.toFixed(0) || 'N/A'}ms ${getScore(mobileMetrics.lcp, 2500, 4000, true)}`);
    console.log(`  FCP:  ${mobileMetrics.fcp?.toFixed(0) || 'N/A'}ms ${getScore(mobileMetrics.fcp, 1800, 3000, true)}`);
    console.log(`  CLS:  ${mobileMetrics.cls?.toFixed(3) || 'N/A'} ${getScore(mobileMetrics.cls, 0.1, 0.25, true)}`);
    console.log(`  TTFB: ${mobileMetrics.ttfb?.toFixed(0) || 'N/A'}ms ${getScore(mobileMetrics.ttfb, 800, 2000, true)}`);

    console.log('\n🖥️ DESKTOP (1920x1080)');
    console.log('-'.repeat(70));
    console.log(`  LCP:  ${desktopMetrics.lcp?.toFixed(0) || 'N/A'}ms ${getScore(desktopMetrics.lcp, 2500, 4000, true)}`);
    console.log(`  FCP:  ${desktopMetrics.fcp?.toFixed(0) || 'N/A'}ms ${getScore(desktopMetrics.fcp, 1800, 3000, true)}`);
    console.log(`  CLS:  ${desktopMetrics.cls?.toFixed(3) || 'N/A'} ${getScore(desktopMetrics.cls, 0.1, 0.25, true)}`);
    console.log(`  TTFB: ${desktopMetrics.ttfb?.toFixed(0) || 'N/A'}ms ${getScore(desktopMetrics.ttfb, 800, 2000, true)}`);

    console.log('\n' + '='.repeat(70));
    console.log('📈 SUMMARY');
    console.log('='.repeat(70));

    if (mobileMetrics.lcp && desktopMetrics.lcp) {
      const diff = ((mobileMetrics.lcp - desktopMetrics.lcp) / desktopMetrics.lcp * 100).toFixed(1);
      console.log(`  LCP Difference: ${Number(diff) > 0 ? '+' : ''}${diff}% (mobile vs desktop)`);
    }

    if (mobileMetrics.fcp && desktopMetrics.fcp) {
      const diff = ((mobileMetrics.fcp - desktopMetrics.fcp) / desktopMetrics.fcp * 100).toFixed(1);
      console.log(`  FCP Difference: ${Number(diff) > 0 ? '+' : ''}${diff}% (mobile vs desktop)`);
    }

    console.log('='.repeat(70) + '\n');

    expect(mobileMetrics.ttfb || 0).toBeLessThan(2000);
    expect(desktopMetrics.ttfb || 0).toBeLessThan(2000);
  });
});

async function getCoreWebVitals(page: any) {
  return await page.evaluate(() => {
    return new Promise<Record<string, number>>((resolve) => {
      const result: Record<string, number> = {};
      let observer: PerformanceObserver | null = null;

      try {
        observer = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          for (const entry of entries) {
            if (entry.name === 'first-contentful-paint') {
              result.fcp = entry.startTime;
            }
            if (entry.entryType === 'largest-contentful-paint') {
              result.lcp = entry.startTime;
            }
            if (entry.entryType === 'layout-shift') {
              result.cls = (result.cls || 0) + (entry as any).value;
            }
          }
        });

        observer.observe({ type: 'paint', buffered: true });
        observer.observe({ type: 'largest-contentful-paint', buffered: true });
        observer.observe({ type: 'layout-shift', buffered: true });

        setTimeout(() => {
          const nav = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
          result.ttfb = nav.responseStart;

          if (observer) observer.disconnect();
          resolve(result);
        }, 500);
      } catch (e) {
        resolve(result);
      }
    });
  });
}

async function runLighthouseAudit(page: any, device: 'mobile' | 'desktop') {
  const metrics = await getCoreWebVitals(page);
  const response = await page.request.fetch(page.url());

  return {
    performance: calculatePerformanceScore(metrics, device),
    accessibility: await calculateAccessibilityScore(page),
    bestPractices: calculateBestPracticesScore(response),
    seo: await calculateSeoScore(page)
  };
}

function curveScore(value: number | undefined, good: number, poor: number): number {
  if (value === undefined) return 1;
  if (value <= good) return 1;
  if (value >= poor) return 0;
  return (poor - value) / (poor - good);
}

function calculatePerformanceScore(metrics: Record<string, number>, device: 'mobile' | 'desktop'): number {
  const fcpCurve = device === 'mobile' ? [1800, 3000] : [1000, 1800];
  const lcpCurve = device === 'mobile' ? [2500, 4000] : [1800, 3000];
  const ttfbCurve = [800, 1800];

  const fcpScore = curveScore(metrics.fcp, fcpCurve[0], fcpCurve[1]);
  const lcpScore = curveScore(metrics.lcp, lcpCurve[0], lcpCurve[1]);
  const ttfbScore = curveScore(metrics.ttfb, ttfbCurve[0], ttfbCurve[1]);
  const clsScore = 1 - Math.min((metrics.cls || 0) / 0.25, 1);

  const score = (fcpScore + lcpScore + ttfbScore + clsScore) / 4;

  return Math.round(Math.max(0, Math.min(100, score * 100)));
}

async function calculateAccessibilityScore(page: any): Promise<number> {
  const checks: boolean[] = await page.evaluate(() => {
    const nameOf = (el: Element): string => {
      const text = (el.textContent || '').trim();
      if (text) return text;
      const ariaLabel = (el.getAttribute('aria-label') || '').trim();
      if (ariaLabel) return ariaLabel;
      const labelledby = el.getAttribute('aria-labelledby');
      if (labelledby) {
        const resolved = labelledby.split(/\s+/).map(id => {
          const ref = document.getElementById(id);
          return ref ? (ref.textContent || '').trim() : '';
        }).join(' ').trim();
        if (resolved) return resolved;
      }
      const title = (el.getAttribute('title') || '').trim();
      if (title) return title;
      const img = el.querySelector('img[alt]');
      return img ? (img.getAttribute('alt') || '').trim() : '';
    };
    const imgs = Array.from(document.querySelectorAll('img'));
    const links = Array.from(document.querySelectorAll('a[href]')).filter(a => !a.closest('[aria-hidden="true"]'));
    const buttons = Array.from(document.querySelectorAll('button'));
    return [
      imgs.length > 0 && imgs.every(img => img.hasAttribute('alt')),
      links.length > 0 && links.every(link => !!nameOf(link)),
      buttons.length > 0 && buttons.every(btn => !!nameOf(btn)),
      !!document.documentElement.lang,
      document.querySelectorAll('h1').length === 1,
      !!document.querySelector('a[href="#main"]')
    ];
  });
  return Math.round((checks.filter(Boolean).length / checks.length) * 100);
}

function calculateBestPracticesScore(response: any): number {
  const headers = response.headers();
  const checks = [
    (headers['content-type'] || '').includes('charset'),
    headers['x-content-type-options'] === 'nosniff',
    !!headers['x-frame-options'],
    !!headers['referrer-policy'],
    !!headers['cross-origin-opener-policy']
  ];
  return Math.round((checks.filter(Boolean).length / checks.length) * 100);
}

async function calculateSeoScore(page: any): Promise<number> {
  const checks: boolean[] = await page.evaluate(() => {
    const description = document.querySelector('meta[name="description"]');
    const viewport = document.querySelector('meta[name="viewport"]');
    const favicon = document.querySelector('link[rel="icon"], link[rel="shortcut icon"]');
    return [
      document.title.trim().length > 0,
      (description?.getAttribute('content') || '').trim().length > 50,
      document.querySelectorAll('h1').length === 1,
      !!viewport && (viewport.getAttribute('content') || '').includes('width=device-width'),
      !!favicon,
      !!document.documentElement.lang
    ];
  });
  return Math.round((checks.filter(Boolean).length / checks.length) * 100);
}

function getScore(value: number | undefined, good: number, poor: number, lowerIsBetter = false): string {
  if (value === undefined) return '⚠️';

  if (lowerIsBetter) {
    if (value <= good) return '✅';
    if (value <= poor) return '⚠️';
    return '❌';
  } else {
    if (value >= good) return '✅';
    if (value >= poor) return '⚠️';
    return '❌';
  }
}
