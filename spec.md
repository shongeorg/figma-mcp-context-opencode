target: neural-code-generator
output: playwright tests (typescript)
framework: "@playwright/test"
assertions: [toBe, toContain, toHaveAttribute, custom metrics]
browsers: [chromium, firefox, webkit]
priority: chromium
language: uk-UA

import { test as base, Page } from '@playwright/test';

type PerfHelpers = {
getTTFB: () => Promise<number>;
getCacheHeaders: (url: string) => Promise<Record<string, string>>;
getConnectionInfo: () => Promise<{ protocol: string; tls: string }>;
checkBFCache: () => Promise<boolean>;
getCookieSize: (url: string) => Promise<number>;
};

export const test = base.extend<{ perf: PerfHelpers }>({
perf: async ({ page }, use) => {
await use({
getTTFB: async () => {
return await page.evaluate(() => {
const nav = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
return nav?.responseStart ?? 0;
});
},

      getCacheHeaders: async (url) => {
        const response = await page.request.fetch(url, { method: 'HEAD' });
        return {
          'cache-control': response.headers()['cache-control'] || '',
          'etag': response.headers()['etag'] || '',
          'last-modified': response.headers()['last-modified'] || '',
          'vary': response.headers()['vary'] || ''
        };
      },

      getConnectionInfo: async () => {
        return await page.evaluate(() => {
          const nav = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
          return {
            protocol: (nav as any).nextHopProtocol || 'unknown',
            tls: (nav as any).tlsVersion || 'unknown'
          };
        });
      },

      checkBFCache: async () => {
        await page.goto('/target-page');
        await page.goto('/other-page');
        await page.goBack();
        return await page.evaluate(() => {
          return new Promise((resolve) => {
            window.addEventListener('pageshow', (e) => {
              resolve((e as PageTransitionEvent).persisted);
            }, { once: true });
          });
        });
      },

      getCookieSize: async (url) => {
        const response = await page.request.fetch(url);
        const cookie = response.headers()['cookie'] || '';
        return cookie.length;
      }
    });

}
});
Test Scenarios

1. Click Handler Non-Blocking
   test('click handler non-blocking', async ({ page }) => {
   await page.goto('/');
   await page.addInitScript(() => {
   window.**clickTime = 0;
   window.**navStart = 0;
   });

await page.evaluate(() => {
document.querySelector('#nav-link')?.addEventListener('click', () => {
window.\_\_clickTime = performance.now();
}, { once: true });
});

const [request] = await Promise.all([
page.waitForRequest(/\/target/),
page.click('#nav-link')
]);

const navStart = await page.evaluate(() => performance.now());
const delta = navStart - (await page.evaluate(() => window.\_\_clickTime));
expect(delta).toBeLessThan(50);
});

2. HSTS Enforcement

test('hsts upgrade', async ({ browserName, page }) => {
test.skip(browserName !== 'chromium', 'HSTS preload only reliable in Chromium');

const response = await page.goto('http://your-domain.com');
expect(response?.url()).startsWith('https://');

const securityHeaders = await page.evaluate(() => {
return fetch('/').then(r => r.headers.get('strict-transport-security'));
});
expect(securityHeaders).toContain('max-age=');
expect(securityHeaders).toContain('includeSubDomains');
});

3. Cache-Control Policy

test('cache headers policy', async ({ page, perf }) => {
const htmlHeaders = await perf.getCacheHeaders('/');
expect(htmlHeaders['cache-control']).toContain('no-cache');

const staticUrl = await page.evaluate(() =>
document.querySelector('script[src]')?.getAttribute('src')
);
if (staticUrl && /\.[a-f0-9]{8}\./.test(staticUrl)) {
const staticHeaders = await perf.getCacheHeaders(staticUrl);
expect(staticHeaders['cache-control']).toContain('immutable');
expect(staticHeaders['cache-control']).toContain('max-age=31536000');
}
});

4. DNS Prefetch / Preconnect

test('resource hints present', async ({ page }) => {
await page.goto('/');

const hints = await page.evaluate(() => {
return Array.from(document.querySelectorAll('link[rel="dns-prefetch"], link[rel="preconnect"]'))
.map(el => ({ rel: el.getAttribute('rel'), href: el.getAttribute('href') }));
});

const criticalDomains = ['analytics', 'cdn', 'fonts'];
for (const domain of criticalDomains) {
expect(hints.some(h => h.href?.includes(domain))).toBeTruthy();
}
});

5. HTTP Protocol & TLS Version

test('modern protocol and tls', async ({ page, perf }) => {
await page.goto('/');
const conn = await perf.getConnectionInfo();

expect(['h2', 'h3', 'http/1.1']).toContain(conn.protocol.toLowerCase());
if (conn.protocol !== 'http/1.1') {
expect(conn.tls).toBe('TLSv1.3');
}
});

6. Cookie Bloat Check

test('minimal cookies on static', async ({ page }) => {
const staticReq = await page.waitForRequest(/\.js$|\.css$|\.png$/);
const cookies = staticReq.headers()['cookie'];

if (cookies) {
expect(cookies.length).toBeLessThan(100);
}
});

7. Redirect Chain Detection
   test('no redirect chain', async ({ page }) => {
   const responses: string[] = [];
   page.on('response', r => responses.push(r.url()));

await page.goto('/');
expect(responses.filter(url => url.startsWith(page.url().split('/')[0]))).toHaveLength(1);
});

8. Compression Verification
   test('compression active', async ({ page }) => {
   const response = await page.goto('/');
   const encoding = response?.headers()['content-encoding'];
   expect(['br', 'gzip']).toContain(encoding);

const sizes = await page.evaluate(() => {
const nav = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
return { encoded: nav.encodedBodySize, decoded: nav.decodedBodySize };
});

if (sizes.decoded > 0) {
expect(sizes.decoded / sizes.encoded).toBeGreaterThan(2);
}
}); 9. Early Hints (103) Detection

test('early hints present', async ({ page, browserName }) => {
test.skip(browserName !== 'chromium', 'Early Hints support limited');

let earlyHints: Record<string, string> | null = null;
page.on('response', async (r) => {
if (r.status() === 103) {
earlyHints = r.headers();
}
});

await page.goto('/');
if (earlyHints) {
expect(earlyHints['link']).toContain('rel=preload');
}
});

10. bfcache Compatibility
    test('bfcache support', async ({ page, perf }) => {
    const isPersisted = await perf.checkBFCache();
    expect(isPersisted).toBeTruthy();

const hasUnload = await page.evaluate(() => {
return window.listenerCount?.('unload') > 0 ||
'onunload' in window;
});
expect(hasUnload).toBeFalsy();
}); 11. Service Worker Registration

test('service worker active', async ({ page }) => {
await page.goto('/');

const swStatus = await page.evaluate(async () => {
if (!('serviceWorker' in navigator)) return 'unsupported';
const reg = await navigator.serviceWorker.getRegistration();
return reg?.active?.state || 'none';
});

expect(['activated', 'unsupported']).toContain(swStatus);
});

12. Performance Metrics Collection

test('core web vitals thresholds', async ({ page }) => {
await page.goto('/');
await page.waitForLoadState('networkidle');

const metrics = await page.evaluate(() => {
return new Promise<Record<string, number>>((resolve) => {
new PerformanceObserver((list) => {
const entries = list.getEntries();
const result: Record<string, number> = {};
for (const entry of entries) {
if (entry.name === 'first-contentful-paint') result.fcp = entry.startTime;
if (entry.entryType === 'largest-contentful-paint') result.lcp = entry.startTime;
if (entry.entryType === 'layout-shift') result.cls = (result.cls || 0) + (entry as any).value;
}
const nav = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
result.ttfb = nav.responseStart;
resolve(result);
}).observe({ entryTypes: ['paint', 'largest-contentful-paint', 'layout-shift'] });

      setTimeout(() => resolve({}), 5000);
    });

});

expect(metrics.ttfb).toBeLessThan(800);
if (metrics.lcp) expect(metrics.lcp).toBeLessThan(2500);
});

Execution Config
import { defineConfig } from '@playwright/test';

export default defineConfig({
use: {
launchOptions: {
args: ['--enable-features=NetworkService,Preconnect']
},
contextOptions: {
permissions: ['geolocation']
}
},
reporter: [['list'], ['html', { open: 'never' }]],
timeout: 30000
});
Fail Conditions
TTFB > 800ms → fail
Redirect chain > 1 → fail
Cache-Control missing on static → fail
Protocol = http/1.1 without justification → warn
Cookie size > 4KB on any request → fail
No compression on text assets > 1KB → fail

npx playwright test performance --project=chromium --retries=1
