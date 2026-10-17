import { test, expect } from '@playwright/test';

test.describe('🔍 SEO Audit', () => {
  test.describe.configure({ timeout: 10000, retries: 0 });

  test('Title tag', async ({ page, baseURL }) => {
    await page.goto('/');
    const title = await page.title();
    console.log(`📝 Title: "${title}" (${title.length} символів)`);
    expect(title).toBeTruthy();
    expect(title).toContain('GreenShop');
  });

  test('Meta description', async ({ page, baseURL }) => {
    await page.goto('/');
    const description = await page.evaluate(() =>
      document.querySelector('meta[name="description"]')?.getAttribute('content')?.trim()
    );
    console.log(`📝 Description: ${description ? description.substring(0, 120) : '❌ відсутній'}`);
    expect(description).toBeTruthy();
    expect(description!.length).toBeGreaterThan(50);
  });

  test('Meta viewport', async ({ page, baseURL }) => {
    await page.goto('/');
    const viewport = await page.evaluate(() =>
      document.querySelector('meta[name="viewport"]')?.getAttribute('content')
    );
    console.log(`📱 Viewport: ${viewport}`);
    expect(viewport).toBeTruthy();
    expect(viewport).toContain('width=device-width');
  });

  test('Open Graph tags', async ({ page, baseURL }) => {
    await page.goto('/');
    const ogTags = await page.evaluate(() =>
      Array.from(document.querySelectorAll('meta[property^="og:"]')).map(m => ({
        property: m.getAttribute('property') || '',
        content: (m.getAttribute('content') || '').trim()
      }))
    );
    console.log(`📱 OG tags: ${ogTags.length}`);
    ogTags.forEach(tag => console.log(`   ${tag.property}: ${tag.content}`));
    for (const tag of ogTags) {
      expect(tag.property).toMatch(/^og:[a-z:]+$/);
      expect(tag.content).not.toBe('');
    }
  });

  test('Canonical URL', async ({ page, baseURL }) => {
    await page.goto('/');
    const canonical = await page.evaluate(() =>
      document.querySelector('link[rel="canonical"]')?.getAttribute('href')
    );
    console.log(`🔗 Canonical: ${canonical ? canonical : '❌ відсутній'}`);
    if (canonical) {
      expect(canonical.startsWith('/')).toBe(true);
    }
  });

  test('H1 heading', async ({ page, baseURL }) => {
    await page.goto('/');
    const h1Count = await page.locator('h1').count();
    const h1Text = await page.locator('h1').first().textContent();
    console.log(`📑 H1 (${h1Count} шт.): "${h1Text?.trim()}"`);
    expect(h1Count).toBe(1);
    expect(h1Text?.trim()).toBeTruthy();
  });

  test('Images alt attributes', async ({ page, baseURL }) => {
    await page.goto('/');
    const images = await page.locator('img').all();
    let withAlt = 0;
    for (const img of images) {
      const alt = await img.getAttribute('alt');
      if (alt !== null) withAlt++;
    }
    console.log(`🖼️ Images: ${withAlt}/${images.length} з alt`);
    expect(images.length).toBeGreaterThan(0);
    expect(withAlt).toBe(images.length);
  });

  test('HTML lang attribute', async ({ page, baseURL }) => {
    await page.goto('/');
    const lang = await page.getAttribute('html', 'lang');
    console.log(`🌐 HTML lang: ${lang || '❌ відсутній'}`);
    expect(lang).toBeTruthy();
    expect(lang).toBe('en');
  });

  test('Favicon', async ({ page, baseURL }) => {
    await page.goto('/');
    const favicon = await page.evaluate(() =>
      document.querySelector('link[rel="icon"]')?.getAttribute('href') ||
      document.querySelector('link[rel="shortcut icon"]')?.getAttribute('href')
    );
    console.log(`🔖 Favicon: ${favicon ? favicon : '❌ відсутній'}`);
    expect(favicon).toBeTruthy();
  });

  test('Structured Data JSON-LD', async ({ page, baseURL }) => {
    await page.goto('/');
    const structuredData = await page.locator('script[type="application/ld+json"]').count();
    console.log(`📊 Structured Data: ${structuredData > 0 ? `${structuredData} схем` : '❌ відсутній'}`);
    for (let i = 0; i < structuredData; i++) {
      const raw = await page.locator('script[type="application/ld+json"]').nth(i).textContent();
      expect(raw?.trim().length ?? 0).toBeGreaterThan(0);
    }
  });

  test('Robots.txt', async ({ page, baseURL }) => {
    const response = await page.request.get(`${baseURL}/robots.txt`);
    console.log(`🤖 robots.txt: ${response.status() === 200 ? '✅ доступний' : `статус ${response.status()}`}`);
    expect(response.status()).toBeLessThan(500);
  });

  test('Sitemap.xml', async ({ page, baseURL }) => {
    const response = await page.request.get(`${baseURL}/sitemap.xml`);
    console.log(`🗺️ sitemap.xml: ${response.status() === 200 ? '✅ доступний' : `статус ${response.status()}`}`);
    expect(response.status()).toBeLessThan(500);
  });

  test('Internal links check', async ({ page, baseURL }) => {
    await page.goto('/');
    const links = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('a[href^="/"]'))
        .slice(0, 5)
        .map(a => a.getAttribute('href'));
    });
    console.log(`🔗 Internal links: ${links.length}`);
    expect(links.length).toBeGreaterThan(0);

    for (const link of links) {
      if (link && !link.startsWith('#')) {
        const clean = link.split('#')[0] || '/';
        const response = await page.request.get(`${baseURL}${clean}`);
        console.log(`   ${response.ok() ? '✅' : '❌'} ${clean} → ${response.status()}`);
        expect(response.status()).toBeLessThan(500);
      }
    }
  });

  test('📋 SEO Summary Report', async ({ page, baseURL }) => {
    console.log('\n' + '='.repeat(60));
    console.log('🔍 SEO AUDIT REPORT');
    console.log('='.repeat(60));
    console.log(`📍 Base URL: ${baseURL}`);
    console.log(`📅 Date: ${new Date().toLocaleString('uk-UA')}`);
    console.log('='.repeat(60));

    await page.goto('/');

    const [title, description, h1Count, images, lang, canonical] = await Promise.all([
      page.title(),
      page.evaluate(() => document.querySelector('meta[name="description"]')?.getAttribute('content')),
      page.locator('h1').count(),
      page.locator('img').all(),
      page.getAttribute('html', 'lang'),
      page.evaluate(() => document.querySelector('link[rel="canonical"]')?.getAttribute('href'))
    ]);

    console.log(`\n📝 Title: ${title.length} символів`);
    console.log(`📝 Description: ${description ? '✅' : '❌'}`);
    console.log(`📑 H1: ${h1Count} шт.`);
    console.log(`🖼️ Images: ${images.length} шт.`);
    console.log(`🌐 Lang: ${lang || '❌'}`);
    console.log(`🔗 Canonical: ${canonical ? '✅' : '❌'}`);

    console.log('\n' + '='.repeat(60));
    console.log('✅ SEO Audit completed');
    console.log('='.repeat(60) + '\n');

    expect(title).toBeTruthy();
    expect(lang).toBeTruthy();
    expect(h1Count).toBe(1);
  });
});
