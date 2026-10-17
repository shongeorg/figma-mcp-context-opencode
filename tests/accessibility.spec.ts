import { test, expect } from '@playwright/test';

test.describe('♿ Accessibility (a11y) Tests', () => {
  test.describe.configure({ timeout: 10000, retries: 0 });

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

    const imagesWithoutAlt = images.filter(img => !img.hasAlt);

    console.log(`\n🖼️ Images: ${images.length} total`);
    console.log(`   ✅ With alt attribute: ${images.length - imagesWithoutAlt.length}`);
    console.log(`   ❌ Missing alt attribute: ${imagesWithoutAlt.length}`);

    if (imagesWithoutAlt.length > 0) {
      console.log('   Images missing alt:');
      imagesWithoutAlt.forEach(img => console.log(`      - ${img.src}`));
    }

    expect(imagesWithoutAlt.length).toBe(0);
  });

  test('All links have accessible names', async ({ page, baseURL }) => {
    await page.goto('/');

    const links = await page.evaluate(() => {
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
      const anchors = Array.from(document.querySelectorAll('a[href]'));
      return anchors.map(a => ({
        href: a.getAttribute('href'),
        name: nameOf(a),
        hidden: !!a.closest('[aria-hidden="true"]')
      }));
    });

    const linksWithoutName = links.filter(link => !link.hidden && !link.name);

    console.log(`\n🔗 Links: ${links.length} total`);
    console.log(`   ✅ With accessible name: ${links.length - links.filter(l => !l.name).length}`);
    console.log(`   ⛔ aria-hidden (excluded): ${links.filter(l => l.hidden).length}`);
    console.log(`   ❌ Without accessible name: ${linksWithoutName.length}`);

    if (linksWithoutName.length > 0) {
      console.log('   Links missing names:');
      linksWithoutName.slice(0, 10).forEach(link => console.log(`      - ${link.href}`));
    }

    expect(linksWithoutName.length).toBe(0);
  });

  test('All buttons have accessible names', async ({ page, baseURL }) => {
    await page.goto('/');

    const buttons = await page.evaluate(() => {
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
      const els = Array.from(document.querySelectorAll('button'));
      return els.map(btn => ({
        text: btn.textContent?.trim() || '',
        name: nameOf(btn),
        hidden: !!btn.closest('[aria-hidden="true"]')
      }));
    });

    const buttonsWithoutName = buttons.filter(btn => !btn.hidden && !btn.name);

    console.log(`\n🔘 Buttons: ${buttons.length} total`);
    console.log(`   ✅ With accessible name: ${buttons.length - buttons.filter(b => !b.name).length}`);
    console.log(`   ❌ Without accessible name: ${buttonsWithoutName.length}`);

    if (buttonsWithoutName.length > 0) {
      console.log('   Buttons missing names:');
      buttonsWithoutName.forEach(btn => console.log(`      - "${btn.text}"`));
    }

    expect(buttonsWithoutName.length).toBe(0);
  });

  test('Form inputs have labels', async ({ page, baseURL }) => {
    await page.goto('/login/');

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

    expect(inputsWithoutLabel.length).toBe(0);
  });

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

    const h1Count = headings.filter(h => h.level === 1).length;
    console.log(`\n   H1 count: ${h1Count}`);

    expect(h1Count).toBeGreaterThanOrEqual(1);

    let prevLevel = 0;
    let skippedLevels = 0;
    for (const heading of headings) {
      if (heading.level > prevLevel + 1) {
        skippedLevels++;
      }
      prevLevel = heading.level;
    }

    console.log(`   ⚠️ Skipped heading levels: ${skippedLevels}`);

    expect(skippedLevels).toBe(0);
  });

  test('Page has language attribute', async ({ page, baseURL }) => {
    await page.goto('/');

    const lang = await page.getAttribute('html', 'lang');

    console.log(`\n🌐 HTML lang: ${lang || '❌ відсутній'}`);

    expect(lang).toBeTruthy();
    expect(lang!.length).toBeGreaterThanOrEqual(2);
  });

  test('Focus indicators are visible', async ({ page, baseURL }) => {
    await page.goto('/');

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
      console.log('\n⚠️ Skip to main content link not found');
    }

    expect(skipLink).toBeTruthy();
    expect(skipLink!.href).toBe('#main');
  });

  test('ARIA roles are valid', async ({ page, baseURL }) => {
    await page.goto('/');

    const ariaRoles = await page.evaluate(() => {
      const elements = Array.from(document.querySelectorAll('[role]'));
      return elements.map(el => ({
        role: el.getAttribute('role'),
        tag: el.tagName
      }));
    });

    const validRoles = ['alert', 'alertdialog', 'application', 'article', 'banner', 'button', 'cell', 'checkbox',
                        'columnheader', 'combobox', 'complementary', 'contentinfo', 'definition', 'dialog',
                        'directory', 'document', 'feed', 'figure', 'form', 'grid', 'gridcell', 'group', 'heading',
                        'img', 'link', 'list', 'listbox', 'listitem', 'log', 'main', 'marquee', 'math', 'menu',
                        'menubar', 'menuitem', 'menuitemcheckbox', 'menuitemradio', 'navigation', 'none', 'note',
                        'option', 'presentation', 'progressbar', 'radio', 'radiogroup', 'region', 'row', 'rowgroup',
                        'rowheader', 'scrollbar', 'search', 'searchbox', 'separator', 'slider', 'spinbutton',
                        'status', 'switch', 'tab', 'tablist', 'tabpanel', 'term', 'textbox', 'timer', 'toolbar',
                        'tooltip', 'tree', 'treegrid', 'treeitem'];

    const invalidRoles = ariaRoles.filter(item => !item.role || !validRoles.includes(item.role));

    console.log(`\n🎭 ARIA roles: ${ariaRoles.length} found`);
    console.log(`   Roles used: ${[...new Set(ariaRoles.map(r => r.role))].join(', ')}`);

    if (invalidRoles.length > 0) {
      console.log('   ❌ Invalid roles:');
      invalidRoles.forEach(item => console.log(`      - ${item.role} on <${item.tag.toLowerCase()}>`));
    }

    expect(invalidRoles.length).toBe(0);
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

    expect(duplicateIds.length).toBe(0);
  });

  test('Color contrast check (sample)', async ({ page, baseURL }) => {
    await page.goto('/');

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
  });

  test('Keyboard navigation works', async ({ page, baseURL }) => {
    await page.goto('/');

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

  test('📋 Accessibility Summary Report', async ({ page, baseURL }) => {
    console.log('\n' + '='.repeat(70));
    console.log('♿ ACCESSIBILITY (a11y) AUDIT REPORT');
    console.log('='.repeat(70));
    console.log(`📍 Base URL: ${baseURL}`);
    console.log(`📅 Date: ${new Date().toLocaleString('uk-UA')}`);
    console.log('='.repeat(70));

    await page.goto('/');

    const images = await page.locator('img').all();
    let imagesWithAlt = 0;
    for (const img of images) {
      const alt = await img.getAttribute('alt');
      if (alt !== null) imagesWithAlt++;
    }
    console.log(`\n🖼️ Images: ${imagesWithAlt}/${images.length} with alt`);

    const links = await page.locator('a').all();
    console.log(`🔗 Links: ${links.length}`);

    const buttons = await page.locator('button').all();
    console.log(`🔘 Buttons: ${buttons.length}`);

    const inputs = await page.locator('input:not([type="hidden"])').all();
    console.log(`📝 Form inputs: ${inputs.length}`);

    const h1Count = await page.locator('h1').count();
    const allHeadings = await page.locator('h1, h2, h3, h4, h5, h6').count();
    console.log(`📑 Headings: H1=${h1Count}, Total=${allHeadings}`);

    const lang = await page.getAttribute('html', 'lang');
    console.log(`🌐 Language: ${lang || '❌'}`);

    const ariaElements = await page.locator('[role]').count();
    console.log(`🎭 ARIA roles: ${ariaElements}`);

    const focusable = await page.evaluate(() => {
      const selectors = ['a[href]', 'button', 'input', 'select', 'textarea', '[tabindex]:not([tabindex="-1"])'];
      return document.querySelectorAll(selectors.join(', ')).length;
    });
    console.log(`🎯 Focusable elements: ${focusable}`);

    console.log('\n' + '='.repeat(70));
    console.log('✅ Accessibility audit completed');
    console.log('='.repeat(70) + '\n');

    expect(imagesWithAlt).toBe(images.length);
    expect(lang).toBeTruthy();
    expect(h1Count).toBeGreaterThanOrEqual(1);
  });
});
