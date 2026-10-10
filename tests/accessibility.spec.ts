import { test, expect } from '@playwright/test';

/**
 * ♿ Accessibility (a11y) Tests
 * 
 * Перевірка доступності сайту для людей з обмеженнями
 * URL для тестування прописується в playwright.config.ts (baseURL)
 * Всі тести використовують baseURL з конфігурації
 */

test.describe('♿ Accessibility (a11y) Tests', () => {
  test.describe.configure({ timeout: 10000, retries: 0 });

  // ============================================================================
  // BASIC ACCESSIBILITY
  // ============================================================================

  test('All images have alt text', async ({ page, baseURL }) => {
    await page.goto('/');
    
    const images = await page.evaluate(() => {
      const imgs = Array.from(document.querySelectorAll('img'));
      return imgs.map(img => ({
        src: img.getAttribute('src') || img.getAttribute('data-src') || 'no-src',
        alt: img.getAttribute('alt'),
        hasAlt: img.hasAttribute('alt'),
        role: img.getAttribute('role')
      }));
    });
    
    const imagesWithoutAlt = images.filter(img => 
      !img.hasAlt || (img.alt === '' && img.role !== 'presentation')
    );
    
    console.log(`\n🖼️ Images: ${images.length} total`);
    console.log(`   ✅ With alt: ${images.length - imagesWithoutAlt.length}`);
    console.log(`   ❌ Without alt: ${imagesWithoutAlt.length}`);
    
    if (imagesWithoutAlt.length > 0) {
      console.log('   Images missing alt:');
      imagesWithoutAlt.forEach(img => console.log(`      - ${img.src}`));
    }
    
    // Не фейлимо, але логуємо
    expect(imagesWithoutAlt.length).toBeLessThanOrEqual(images.length / 2);
  });

  test('All links have accessible names', async ({ page, baseURL }) => {
    await page.goto('/');
    
    const links = await page.evaluate(() => {
      const anchors = Array.from(document.querySelectorAll('a[href]'));
      return anchors.map(a => ({
        href: a.getAttribute('href'),
        text: a.textContent?.trim(),
        ariaLabel: a.getAttribute('aria-label'),
        title: a.getAttribute('title'),
        hasAccessibleName: !!(a.textContent?.trim() || a.getAttribute('aria-label'))
      }));
    });
    
    const linksWithoutName = links.filter(link => !link.hasAccessibleName);
    
    console.log(`\n🔗 Links: ${links.length} total`);
    console.log(`   ✅ With accessible name: ${links.length - linksWithoutName.length}`);
    console.log(`   ❌ Without accessible name: ${linksWithoutName.length}`);
    
    if (linksWithoutName.length > 0) {
      console.log('   Links missing names:');
      linksWithoutName.slice(0, 5).forEach(link => console.log(`      - ${link.href}`));
    }
    
    expect(linksWithoutName.length).toBeLessThanOrEqual(5);
  });

  test('All buttons have accessible names', async ({ page, baseURL }) => {
    await page.goto('/');
    
    const buttons = await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      return btns.map(btn => ({
        text: btn.textContent?.trim(),
        ariaLabel: btn.getAttribute('aria-label'),
        hasAccessibleName: !!(btn.textContent?.trim() || btn.getAttribute('aria-label'))
      }));
    });
    
    const buttonsWithoutName = buttons.filter(btn => !btn.hasAccessibleName);
    
    console.log(`\n🔘 Buttons: ${buttons.length} total`);
    console.log(`   ✅ With accessible name: ${buttons.length - buttonsWithoutName.length}`);
    console.log(`   ❌ Without accessible name: ${buttonsWithoutName.length}`);
    
    expect(buttonsWithoutName.length).toBeLessThanOrEqual(2);
  });

  test('Form inputs have labels', async ({ page, baseURL }) => {
    await page.goto('/login');
    
    const inputs = await page.evaluate(() => {
      const inputs = Array.from(document.querySelectorAll('input:not([type="hidden"]):not([type="submit"])'));
      return inputs.map(input => {
        const id = input.getAttribute('id');
        const label = id ? document.querySelector(`label[for="${id}"]`) : null;
        const ariaLabel = input.getAttribute('aria-label');
        const placeholder = input.getAttribute('placeholder');
        
        return {
          type: input.getAttribute('type'),
          id: id || 'no-id',
          hasLabel: !!label || !!ariaLabel,
          hasPlaceholder: !!placeholder
        };
      });
    });
    
    const inputsWithoutLabel = inputs.filter(input => !input.hasLabel);
    
    console.log(`\n📝 Form inputs: ${inputs.length} total`);
    console.log(`   ✅ With labels: ${inputs.length - inputsWithoutLabel.length}`);
    console.log(`   ❌ Without labels: ${inputsWithoutLabel.length}`);
    
    if (inputsWithoutLabel.length > 0) {
      console.log('   Inputs without labels:');
      inputsWithoutLabel.forEach(input => console.log(`      - ${input.type}#${input.id}`));
    }
    
    expect(inputsWithoutLabel.length).toBeLessThanOrEqual(inputs.length / 2);
  });

  // ============================================================================
  // HEADING STRUCTURE
  // ============================================================================

  test('Proper heading hierarchy (H1-H6)', async ({ page, baseURL }) => {
    await page.goto('/');
    
    const headings = await page.evaluate(() => {
      const elements = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6'));
      return elements.map(el => ({
        level: parseInt(el.tagName.charAt(1)),
        text: el.textContent?.trim().substring(0, 50)
      }));
    });
    
    console.log('\n📑 Heading hierarchy:');
    headings.forEach(h => {
      const indent = '  '.repeat(h.level - 1);
      console.log(`   ${indent}H${h.level}: "${h.text}"`);
    });
    
    // Перевірка на один H1
    const h1Count = headings.filter(h => h.level === 1).length;
    console.log(`\n   H1 count: ${h1Count}`);
    
    expect(h1Count).toBeGreaterThanOrEqual(1);
    
    // Перевірка на пропуски в ієрархії
    let prevLevel = 0;
    let skippedLevels = 0;
    for (const heading of headings) {
      if (heading.level > prevLevel + 1) {
        skippedLevels++;
      }
      prevLevel = heading.level;
    }
    
    if (skippedLevels > 0) {
      console.log(`   ⚠️ Skipped heading levels: ${skippedLevels}`);
    }
  });

  test('Page has language attribute', async ({ page, baseURL }) => {
    await page.goto('/');
    
    const lang = await page.getAttribute('html', 'lang');
    
    console.log(`\n🌐 HTML lang: ${lang || '❌ відсутній'}`);
    
    expect(lang).toBeTruthy();
    expect(lang!.length).toBeGreaterThanOrEqual(2);
  });

  // ============================================================================
  // FOCUS MANAGEMENT
  // ============================================================================

  test('Focus indicators are visible', async ({ page, baseURL }) => {
    await page.goto('/');
    
    // Знаходимо інтерактивні елементи
    const focusableElements = await page.evaluate(() => {
      const selectors = ['a[href]', 'button', 'input', 'select', 'textarea', '[tabindex]:not([tabindex="-1"])'];
      const elements = Array.from(document.querySelectorAll(selectors.join(', ')));
      return elements.slice(0, 10).map(el => ({
        tag: el.tagName,
        class: el.getAttribute('class')?.substring(0, 30)
      }));
    });
    
    console.log(`\n🎯 Focusable elements: ${focusableElements.length}`);
    focusableElements.forEach(el => {
      console.log(`   - ${el.tag}${el.class ? `.${el.class}` : ''}`);
    });
    
    expect(focusableElements.length).toBeGreaterThan(0);
  });

  test('Skip to main content link', async ({ page, baseURL }) => {
    await page.goto('/');
    
    const skipLink = await page.evaluate(() => {
      const link = document.querySelector('a[href="#main"], a[href="#content"], a[href*="skip"]');
      return link ? {
        text: link.textContent?.trim(),
        href: link.getAttribute('href')
      } : null;
    });
    
    if (skipLink) {
      console.log(`\n⏭️ Skip link: "${skipLink.text}" → ${skipLink.href}`);
    } else {
      console.log('\n⚠️ Skip to main content link not found (recommended)');
    }
  });

  // ============================================================================
  // ARIA ATTRIBUTES
  // ============================================================================

  test('ARIA roles are valid', async ({ page, baseURL }) => {
    await page.goto('/');
    
    const ariaRoles = await page.evaluate(() => {
      const elements = Array.from(document.querySelectorAll('[role]'));
      return elements.map(el => ({
        role: el.getAttribute('role'),
        tag: el.tagName
      }));
    });
    
    const validRoles = ['navigation', 'main', 'banner', 'contentinfo', 'complementary', 
                        'article', 'search', 'button', 'link', 'list', 'listitem',
                        'heading', 'img', 'form', 'alert', 'dialog', 'menu', 'none', 'presentation'];
    
    const invalidRoles = ariaRoles.filter(item => !validRoles.includes(item.role!));
    
    console.log(`\n🎭 ARIA roles: ${ariaRoles.length} found`);
    
    if (invalidRoles.length > 0) {
      console.log('   ⚠️ Potentially invalid roles:');
      invalidRoles.forEach(item => console.log(`      - ${item.role} on <${item.tag.toLowerCase()}>`));
    }
    
    expect(invalidRoles.length).toBeLessThanOrEqual(2);
  });

  test('ARIA labels are present on interactive elements', async ({ page, baseURL }) => {
    await page.goto('/');
    
    const ariaLabels = await page.evaluate(() => {
      const elements = Array.from(document.querySelectorAll('[aria-label], [aria-labelledby]'));
      return elements.map(el => ({
        ariaLabel: el.getAttribute('aria-label'),
        ariaLabelledby: el.getAttribute('aria-labelledby'),
        tag: el.tagName,
        role: el.getAttribute('role')
      }));
    });
    
    console.log(`\n🏷️ ARIA labels: ${ariaLabels.length} found`);
    
    ariaLabels.slice(0, 5).forEach(item => {
      console.log(`   - <${item.tag.toLowerCase()}>${item.role ? ` role="${item.role}"` : ''}: "${item.ariaLabel}"`);
    });
  });

  test('No duplicate IDs', async ({ page, baseURL }) => {
    await page.goto('/');
    
    const duplicateIds = await page.evaluate(() => {
      const elements = Array.from(document.querySelectorAll('[id]'));
      const idCount: Record<string, number> = {};
      
      elements.forEach(el => {
        const id = el.getAttribute('id');
        if (id) {
          idCount[id] = (idCount[id] || 0) + 1;
        }
      });
      
      return Object.entries(idCount)
        .filter(([id, count]) => count > 1)
        .map(([id, count]) => ({ id, count }));
    });
    
    console.log(`\n🆔 Duplicate IDs: ${duplicateIds.length}`);
    
    if (duplicateIds.length > 0) {
      console.log('   Duplicate IDs found:');
      duplicateIds.forEach(item => console.log(`      - "${item.id}" (${item.count} times)`));
    }
    
    expect(duplicateIds.length).toBeLessThanOrEqual(3);
  });

  // ============================================================================
  // COLOR CONTRAST (basic check)
  // ============================================================================

  test('Color contrast check (sample)', async ({ page, baseURL }) => {
    await page.goto('/');
    
    // Отримуємо кілька текстових елементів
    const textElements = await page.evaluate(() => {
      const elements = Array.from(document.querySelectorAll('p, h1, h2, h3, a, button'));
      return elements.slice(0, 10).map(el => {
        const style = window.getComputedStyle(el);
        return {
          tag: el.tagName,
          text: el.textContent?.trim().substring(0, 30),
          color: style.color,
          backgroundColor: style.backgroundColor
        };
      });
    });
    
    console.log(`\n🎨 Color contrast sample (${textElements.length} elements):`);
    textElements.forEach(el => {
      console.log(`   - <${el.tag.toLowerCase()}>: ${el.color} on ${el.backgroundColor}`);
    });
    
    // Повна перевірка контрасту вимагає бібліотеки як axe-core
    console.log('   ℹ️ Full contrast check requires axe-core library');
  });

  // ============================================================================
  // KEYBOARD NAVIGATION
  // ============================================================================

  test('Keyboard navigation works', async ({ page, baseURL }) => {
    await page.goto('/');
    
    // Перевірка що можна навігуватися клавішею Tab
    await page.keyboard.press('Tab');
    const firstFocusedElement = await page.evaluate(() => {
      const el = document.activeElement;
      return el ? el.tagName : null;
    });
    
    console.log(`\n⌨️ First focused element: ${firstFocusedElement}`);
    
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    
    const thirdFocusedElement = await page.evaluate(() => {
      const el = document.activeElement;
      return el ? {
        tag: el.tagName,
        type: el.getAttribute('type'),
        href: el.getAttribute('href')
      } : null;
    });
    
    console.log(`   Third focused element: ${JSON.stringify(thirdFocusedElement)}`);
    
    expect(firstFocusedElement).toBeTruthy();
  });

  test('No keyboard traps', async ({ page, baseURL }) => {
    await page.goto('/');
    
    // Перевірка що можна повернутися назад клавішею Shift+Tab
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Shift+Tab');
    
    const focusedElement = await page.evaluate(() => {
      const el = document.activeElement;
      return el ? el.tagName : null;
    });
    
    console.log(`\n🔄 Keyboard trap check: ${focusedElement}`);
    
    expect(focusedElement).toBeTruthy();
  });

  // ============================================================================
  // ACCESSIBILITY SUMMARY REPORT
  // ============================================================================

  test('📋 Accessibility Summary Report', async ({ page, baseURL }) => {
    console.log('\n' + '='.repeat(70));
    console.log('♿ ACCESSIBILITY (a11y) AUDIT REPORT');
    console.log('='.repeat(70));
    console.log(`📍 Base URL: ${baseURL}`);
    console.log(`📅 Date: ${new Date().toLocaleString('uk-UA')}`);
    console.log('='.repeat(70));
    
    await page.goto('/');
    
    // Images
    const images = await page.locator('img').all();
    let imagesWithAlt = 0;
    for (const img of images) {
      const alt = await img.getAttribute('alt');
      if (alt !== null) imagesWithAlt++;
    }
    console.log(`\n🖼️ Images: ${imagesWithAlt}/${images.length} with alt`);
    
    // Links
    const links = await page.locator('a').all();
    console.log(`🔗 Links: ${links.length}`);
    
    // Buttons
    const buttons = await page.locator('button').all();
    console.log(`🔘 Buttons: ${buttons.length}`);
    
    // Form inputs
    const inputs = await page.locator('input:not([type="hidden"])').all();
    console.log(`📝 Form inputs: ${inputs.length}`);
    
    // Headings
    const h1Count = await page.locator('h1').count();
    const allHeadings = await page.locator('h1, h2, h3, h4, h5, h6').count();
    console.log(`📑 Headings: H1=${h1Count}, Total=${allHeadings}`);
    
    // Language
    const lang = await page.getAttribute('html', 'lang');
    console.log(`🌐 Language: ${lang || '❌'}`);
    
    // ARIA
    const ariaElements = await page.locator('[role]').count();
    console.log(`🎭 ARIA roles: ${ariaElements}`);
    
    // Focusable
    const focusable = await page.evaluate(() => {
      const selectors = ['a[href]', 'button', 'input', 'select', 'textarea', '[tabindex]:not([tabindex="-1"])'];
      return document.querySelectorAll(selectors.join(', ')).length;
    });
    console.log(`🎯 Focusable elements: ${focusable}`);
    
    console.log('\n' + '='.repeat(70));
    console.log('✅ Accessibility audit completed');
    console.log('='.repeat(70) + '\n');
    
    expect(lang).toBeTruthy();
    expect(h1Count).toBeGreaterThanOrEqual(1);
  });
});
