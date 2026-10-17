import { Page } from '@playwright/test';

export class PerfHelpers {
  constructor(private page: Page) {}

  async getTTFB(): Promise<number> {
    return await this.page.evaluate(() => {
      const nav = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      return nav?.responseStart ?? 0;
    });
  }

  async getCacheHeaders(url: string): Promise<Record<string, string>> {
    const response = await this.page.request.fetch(url, { method: 'HEAD' });
    return {
      'cache-control': response.headers()['cache-control'] || '',
      'etag': response.headers()['etag'] || '',
      'last-modified': response.headers()['last-modified'] || '',
      'vary': response.headers()['vary'] || ''
    };
  }

  async getConnectionInfo(): Promise<{ protocol: string; tls: string }> {
    return await this.page.evaluate(() => {
      const nav = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      return {
        protocol: (nav as any).nextHopProtocol || 'unknown',
        tls: (nav as any).tlsVersion || 'unknown'
      };
    });
  }

  async checkBFCache(): Promise<boolean> {
    await this.page.goto('/shop/');
    await this.page.goto('/cart/');
    await this.page.goBack();
    return await this.page.evaluate(() => {
      return new Promise((resolve) => {
        window.addEventListener('pageshow', (e) => {
          resolve((e as PageTransitionEvent).persisted);
        }, { once: true });
      });
    });
  }

  async getCookieSize(url: string): Promise<number> {
    const response = await this.page.request.fetch(url);
    const cookie = response.headers()['cookie'] || '';
    return cookie.length;
  }

  async getCoreWebVitals(): Promise<Record<string, number>> {
    return await this.page.evaluate(() => {
      return new Promise<Record<string, number>>((resolve) => {
        const result: Record<string, number> = {};
        let observer: PerformanceObserver | null = null;

        const timeout = setTimeout(() => {
          if (observer) observer.disconnect();
          resolve(result);
        }, 5000);

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

          observer.observe({ entryTypes: ['paint', 'largest-contentful-paint', 'layout-shift'] });

          setTimeout(() => {
            const nav = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
            result.ttfb = nav.responseStart;

            if (observer) observer.disconnect();
            clearTimeout(timeout);
            resolve(result);
          }, 2000);
        } catch (e) {
          clearTimeout(timeout);
          resolve(result);
        }
      });
    });
  }

  async getCompressionRatio(): Promise<{ encoded: number; decoded: number; ratio: number }> {
    return await this.page.evaluate(() => {
      const nav = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      const encoded = nav.encodedBodySize || 0;
      const decoded = nav.decodedBodySize || 0;
      return {
        encoded,
        decoded,
        ratio: decoded > 0 ? decoded / encoded : 0
      };
    });
  }

  async getServiceWorkerStatus(): Promise<string> {
    return await this.page.evaluate(async () => {
      if (!('serviceWorker' in navigator)) return 'unsupported';
      const reg = await navigator.serviceWorker.getRegistration();
      return reg?.active?.state || 'none';
    });
  }

  async getRedirectChain(): Promise<string[]> {
    const responses: string[] = [];
    this.page.on('response', r => responses.push(r.url()));
    await this.page.goto('/');
    return responses;
  }

  async getResourceHints(): Promise<Array<{ rel: string; href: string | null }>> {
    return await this.page.evaluate(() => {
      return Array.from(document.querySelectorAll('link[rel="dns-prefetch"], link[rel="preconnect"]'))
        .map(el => ({ rel: el.getAttribute('rel') ?? '', href: el.getAttribute('href') }));
    });
  }
}
