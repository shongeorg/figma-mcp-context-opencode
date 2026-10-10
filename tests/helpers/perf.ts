import { Page } from '@playwright/test';

/**
 * Performance Helpers для тестування веб-віталів та метрик
 */
export class PerfHelpers {
  constructor(private page: Page) {}

  /**
   * Отримує Time To First Byte (TTFB) — час до першого байту
   * @returns TTFB в мілісекундах
   */
  async getTTFB(): Promise<number> {
    return await this.page.evaluate(() => {
      const nav = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      return nav?.responseStart ?? 0;
    });
  }

  /**
   * Отримує заголовки кешування для вказаного URL
   * @param url — URL для перевірки
   * @returns Об'єкт з заголовками cache-control, etag, last-modified, vary
   */
  async getCacheHeaders(url: string): Promise<Record<string, string>> {
    const response = await this.page.request.fetch(url, { method: 'HEAD' });
    return {
      'cache-control': response.headers()['cache-control'] || '',
      'etag': response.headers()['etag'] || '',
      'last-modified': response.headers()['last-modified'] || '',
      'vary': response.headers()['vary'] || ''
    };
  }

  /**
   * Отримує інформацію про з'єднання (протокол, TLS версія)
   * @returns Об'єкт з protocol та tls
   */
  async getConnectionInfo(): Promise<{ protocol: string; tls: string }> {
    return await this.page.evaluate(() => {
      const nav = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      return {
        protocol: (nav as any).nextHopProtocol || 'unknown',
        tls: (nav as any).tlsVersion || 'unknown'
      };
    });
  }

  /**
   * Перевіряє чи працює bfcache (Back-Forward Cache)
   * @returns true якщо сторінка завантажилася з bfcache
   */
  async checkBFCache(): Promise<boolean> {
    await this.page.goto('/target-page');
    await this.page.goto('/other-page');
    await this.page.goBack();
    return await this.page.evaluate(() => {
      return new Promise((resolve) => {
        window.addEventListener('pageshow', (e) => {
          resolve((e as PageTransitionEvent).persisted);
        }, { once: true });
      });
    });
  }

  /**
   * Отримує розмір cookies для вказаного URL
   * @param url — URL для перевірки
   * @returns Розмір cookies в байтах
   */
  async getCookieSize(url: string): Promise<number> {
    const response = await this.page.request.fetch(url);
    const cookie = response.headers()['cookie'] || '';
    return cookie.length;
  }

  /**
   * Отримує Core Web Vitals метрики
   * @returns Об'єкт з FCP, LCP, CLS, TTFB
   */
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

          // Чекаємо завантаження сторінки
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

  /**
   * Перевіряє чи є розширення стиснення
   * @returns Об'єкт з encodedBodySize та decodedBodySize
   */
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

  /**
   * Перевіряє статус Service Worker
   * @returns 'activated', 'installing', 'activating', 'unsupported', або 'none'
   */
  async getServiceWorkerStatus(): Promise<string> {
    return await this.page.evaluate(async () => {
      if (!('serviceWorker' in navigator)) return 'unsupported';
      const reg = await navigator.serviceWorker.getRegistration();
      return reg?.active?.state || 'none';
    });
  }

  /**
   * Отримує ланцюжок редіректів
   * @returns Масив URL в ланцюжку редіректів
   */
  async getRedirectChain(): Promise<string[]> {
    const responses: string[] = [];
    this.page.on('response', r => responses.push(r.url()));
    await this.page.goto('/');
    return responses;
  }

  /**
   * Перевіряє наявність resource hints (dns-prefetch, preconnect)
   * @returns Масив об'єктів з rel та href
   */
  async getResourceHints(): Promise<Array<{ rel: string; href: string | null }>> {
    return await this.page.evaluate(() => {
      return Array.from(document.querySelectorAll('link[rel="dns-prefetch"], link[rel="preconnect"]'))
        .map(el => ({ rel: el.getAttribute('rel') ?? '', href: el.getAttribute('href') }));
    });
  }
}
