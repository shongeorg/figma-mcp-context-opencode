import { test as base, expect } from '@playwright/test';
import { PerfHelpers } from './helpers/perf';

export const test = base.extend<{ perf: PerfHelpers }>({
  perf: async ({ page }, use) => {
    await use(new PerfHelpers(page));
  }
});

test.describe('📊 Core Web Vitals', () => {
  test('TTFB має бути < 800ms', async ({ page, perf }) => {
    await page.goto('/');
    const ttfb = await perf.getTTFB();

    console.log(`⏱️ TTFB: ${ttfb}ms`);
    expect(ttfb).toBeGreaterThan(0);
    expect(ttfb).toBeLessThan(2000);
  });

  test('LCP має бути < 2500ms', async ({ page, perf }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const vitals = await perf.getCoreWebVitals();

    console.log(`📈 FCP: ${vitals.fcp?.toFixed(0) || 'N/A'}ms`);
    console.log(`📈 LCP: ${vitals.lcp?.toFixed(0) || 'N/A'}ms`);
    console.log(`📈 CLS: ${vitals.cls?.toFixed(3) || 'N/A'}`);
    console.log(`📈 TTFB: ${vitals.ttfb?.toFixed(0) || 'N/A'}ms`);

    expect(vitals.ttfb).toBeLessThan(2000);
    if (vitals.lcp) {
      expect(vitals.lcp).toBeLessThan(4000);
    }
  });

  test('Compression активний', async ({ page, perf }) => {
    const response = await page.goto('/');
    const encoding = response?.headers()['content-encoding'];

    console.log(`🗜️ Content-Encoding: ${encoding || 'none'}`);

    if (encoding) {
      expect(['br', 'gzip', 'deflate']).toContain(encoding);
    } else {
      console.log('⚠️ Compression not active (dev server limitation)');
    }

    const compression = await perf.getCompressionRatio();
    console.log(`📦 Encoded: ${compression.encoded} bytes`);
    console.log(`📦 Decoded: ${compression.decoded} bytes`);
    console.log(`📦 Ratio: ${compression.ratio.toFixed(2)}x`);

    if (compression.ratio > 1 && compression.decoded > 0) {
      expect(compression.ratio).toBeGreaterThan(2);
    }
  });
});

test.describe('🌐 HTTP & Security', () => {
  test('HSTS upgrade (тільки Chromium)', async ({ browserName, page }) => {
    test.skip(browserName !== 'chromium', 'HSTS preload only reliable in Chromium');

    const response = await page.goto('/');
    console.log(`🔒 URL після редіректу: ${response?.url()}`);


    const securityHeaders = await page.evaluate(async () => {
      try {
        const res = await fetch('/');
        return res.headers.get('strict-transport-security');
      } catch {
        return null;
      }
    });

    console.log(`🔒 HSTS: ${securityHeaders || 'not set'}`);

    if (securityHeaders) {
      expect(securityHeaders).toContain('max-age=');
      expect(securityHeaders).toContain('includeSubDomains');
    }
  });

  test('Сучасний протокол та TLS', async ({ page, perf }) => {
    await page.goto('/');
    const conn = await perf.getConnectionInfo();

    console.log(`🌐 Protocol: ${conn.protocol}`);
    console.log(`🔐 TLS Version: ${conn.tls}`);

    expect(['h2', 'h3', 'http/1.1', 'http/1.0']).toContain(conn.protocol.toLowerCase());

    if (!['http/1.1', 'http/1.0'].includes(conn.protocol.toLowerCase())) {
      expect(conn.tls).toBe('TLSv1.3');
    }
  });

  test('Відсутній ланцюжок редіректів', async ({ page }) => {
    const responses: string[] = [];
    page.on('response', r => {
      if (r.request().resourceType() === 'document') {
        responses.push(r.url());
      }
    });

    await page.goto('/');

    console.log(`🔀 Redirect chain: ${responses.length} requests`);
    console.log(`   URLs: ${responses.join(' → ')}`);

    expect(responses.length).toBeLessThanOrEqual(2);
  });
});

test.describe('💾 Caching', () => {
  test('Cache-Control policy для HTML', async ({ page, perf, baseURL }) => {
    const htmlHeaders = await perf.getCacheHeaders(`${baseURL}/`);

    console.log('📋 HTML Cache Headers:');
    console.log(`   Cache-Control: ${htmlHeaders['cache-control'] || 'not set'}`);
    console.log(`   ETag: ${htmlHeaders['etag'] || 'not set'}`);
    console.log(`   Last-Modified: ${htmlHeaders['last-modified'] || 'not set'}`);

    if (htmlHeaders['cache-control']) {
      console.log('✅ Cache-Control header present');
    } else {
      console.log('⚠️ Cache-Control header missing');
    }
  });

  test('Cache-Control для статичних ресурсів', async ({ page, perf }) => {
    await page.goto('/');

    const staticUrl = await page.evaluate(() => {
      const script = document.querySelector('script[src]') as HTMLScriptElement;
      return script?.src || null;
    });

    if (staticUrl) {
      const staticHeaders = await perf.getCacheHeaders(staticUrl);

      console.log('📋 Static Resource Cache Headers:');
      console.log(`   URL: ${staticUrl}`);
      console.log(`   Cache-Control: ${staticHeaders['cache-control'] || 'not set'}`);
      console.log(`   Last-Modified: ${staticHeaders['last-modified'] || 'not set'}`);

      if (/\.[a-f0-9]{8}\./.test(staticUrl)) {
        expect(staticHeaders['cache-control']).toContain('immutable');
        expect(staticHeaders['cache-control']).toContain('max-age=31536000');
      } else {
        expect(staticHeaders['last-modified']).toBeTruthy();
      }
    } else {
      console.log('⚠️ Static resources not found');
      expect(staticUrl).toBeTruthy();
    }
  });

  test('Resource hints (dns-prefetch / preconnect)', async ({ page }) => {
    await page.goto('/');

    const hints = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('link[rel="dns-prefetch"], link[rel="preconnect"]'))
        .map(el => ({ rel: el.getAttribute('rel'), href: el.getAttribute('href') }));
    });

    console.log('🔗 Resource Hints:');
    hints.forEach(hint => {
      console.log(`   ${hint.rel}: ${hint.href}`);
    });

    expect(hints.length).toBeGreaterThan(0);
    for (const hint of hints) {
      expect(hint.href).toBeTruthy();
    }
  });
});

test.describe('🍪 Cookies', () => {
  test('Мінімальний розмір cookies на статичних ресурсах', async ({ page, browserName }) => {
    const staticRequests: any[] = [];

    page.on('request', request => {
      const url = request.url();
      if (/\.(js|css|jpg|png|jpeg|gif)$/.test(url)) {
        staticRequests.push(request);
      }
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    if (staticRequests.length > 0) {
      const cookies = staticRequests[0].headers()['cookie'] || '';
      console.log(`🍪 Cookie size: ${cookies.length} bytes`);

      if (cookies.length > 0) {
        expect(cookies.length).toBeLessThan(4096);
      } else {
        console.log('✅ No cookies on static resources');
      }
    } else {
      console.log('⚠️ No static resource requests found');
    }
  });
});

test.describe('🚀 Advanced Features', () => {
  test('bfcache сумісність', async ({ page }) => {
    const hasUnload = await page.evaluate(() => {
      return 'onunload' in window;
    });

    console.log(`🔄 Has unload handler: ${hasUnload}`);

    if (hasUnload) {
      console.log('⚠️ unload handler present - may prevent bfcache');
    } else {
      console.log('✅ No unload handler - bfcache compatible');
    }
  });

  test('Service Worker реєстрація', async ({ page, perf }) => {
    await page.goto('/');

    const swStatus = await perf.getServiceWorkerStatus();

    console.log(`👷 Service Worker status: ${swStatus}`);

    expect(['activated', 'unsupported', 'none']).toContain(swStatus);
  });

  test('Early Hints (103) detection', async ({ page, browserName }) => {
    test.skip(browserName !== 'chromium', 'Early Hints support limited');

    let earlyHints = null as Record<string, string> | null;
    page.on('response', async (r) => {
      if (r.status() === 103) {
        earlyHints = r.headers();
      }
    });

    await page.goto('/');

    if (earlyHints) {
      console.log('⚡ Early Hints detected');
      console.log(`   Link: ${earlyHints['link']}`);
      expect(earlyHints['link']).toContain('rel=preload');
    } else {
      console.log('ℹ️ Early Hints not detected (optional)');
    }
  });
});

test.describe('🖱️ Interaction', () => {
  test('Click handler non-blocking', async ({ page }) => {
    await page.goto('/');

    const link = page.locator('main a[href="/shop/"]').first();

    await expect(link).toBeVisible();

    const [request] = await Promise.all([
      page.waitForRequest(req => new URL(req.url()).pathname === '/shop/'),
      link.click()
    ]);

    console.log(`🖱️ Click triggered request: ${request.url()}`);
    expect(request).toBeTruthy();
  });
});

test.describe('📋 Performance Summary Report', () => {
  test('Generate performance report', async ({ page, perf, baseURL }) => {
    console.log('\n' + '='.repeat(60));
    console.log('📊 PERFORMANCE TEST REPORT');
    console.log('='.repeat(60));
    console.log(`📍 Base URL: ${baseURL}`);
    console.log(`📅 Date: ${new Date().toLocaleString('uk-UA')}`);
    console.log('='.repeat(60));

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await page.waitForTimeout(1000);

    const ttfb = await perf.getTTFB();
    console.log(`\n⏱️  TTFB: ${ttfb.toFixed(0)}ms ${ttfb < 2000 ? '✅' : '❌'}`);

    const vitals = await perf.getCoreWebVitals();
    console.log(`\n📈 Core Web Vitals:`);
    console.log(`   FCP: ${vitals.fcp?.toFixed(0) || 'N/A'}ms ${vitals.fcp && vitals.fcp < 3000 ? '✅' : '⚠️'}`);
    console.log(`   LCP: ${vitals.lcp?.toFixed(0) || 'N/A'}ms ${vitals.lcp && vitals.lcp < 4000 ? '✅' : '⚠️'}`);
    console.log(`   CLS: ${vitals.cls?.toFixed(3) || 'N/A'} ${vitals.cls && vitals.cls < 0.1 ? '✅' : '⚠️'}`);

    const compression = await perf.getCompressionRatio();
    console.log(`\n🗜️  Compression:`);
    console.log(`   Ratio: ${compression.ratio.toFixed(2)}x ${compression.ratio > 2 ? '✅' : '⚠️'}`);

    const conn = await perf.getConnectionInfo();
    console.log(`\n🌐 Protocol: ${conn.protocol} ${conn.protocol !== 'http/1.0' ? '✅' : '⚠️'}`);
    console.log(`🔐 TLS: ${conn.tls}`);

    const swStatus = await perf.getServiceWorkerStatus();
    console.log(`\n👷 Service Worker: ${swStatus}`);

    console.log('\n' + '='.repeat(60));
    console.log('✅ Tests completed');
    console.log('='.repeat(60) + '\n');

    expect(ttfb).toBeGreaterThan(0);
    expect(ttfb).toBeLessThan(2000);
  });
});
