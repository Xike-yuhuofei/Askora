const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const screenshotsDir = '/Users/xike/Documents/Docs/Askora/screenshots';

(async () => {
  if (!fs.existsSync(screenshotsDir)) {
    fs.mkdirSync(screenshotsDir, { recursive: true });
  }

  console.log('=== Launching browser ===');
  const browser = await chromium.launch({
    headless: true,
  });
  
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
  });
  
  const page = await context.newPage();
  
  try {
    console.log('=== Step 1: Navigate to library page ===');
    await page.goto('http://localhost:5173/#/library', {
      waitUntil: 'networkidle',
      timeout: 30000
    });
    
    console.log('=== Step 2: Wait 3 seconds for render ===');
    await page.waitForTimeout(3000);
    
    const pageTitle = await page.title();
    const pageURL = page.url();
    console.log('Page title:', pageTitle);
    console.log('Current URL:', pageURL);
    
    console.log('=== Step 3: Take full page screenshot (library_main) ===');
    const mainScreenshotPath = path.join(screenshotsDir, 'library_main.png');
    await page.screenshot({
      path: mainScreenshotPath,
      fullPage: true
    });
    console.log('Saved:', mainScreenshotPath);
    console.log('Size:', (fs.statSync(mainScreenshotPath).size / 1024).toFixed(2), 'KB');
    
    console.log('\n=== Analyze page structure ===');
    const pageContent = await page.evaluate(() => {
      const result = {
        title: document.title,
        headingTexts: [],
        buttons: [],
        navigation: [],
        cardCount: 0,
        cards: [],
        hasEmptyState: false,
        emptyStateText: '',
        searchBox: false,
        bodyText: document.body.innerText.substring(0, 2000),
        scrollHeight: document.documentElement.scrollHeight,
        clientHeight: document.documentElement.clientHeight
      };
      
      document.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach(h => {
        const t = h.textContent.trim();
        if (t) result.headingTexts.push(h.tagName + ': ' + t.substring(0, 100));
      });
      
      document.querySelectorAll('nav a, [role=navigation] a, aside a, .sidebar a, .menu a').forEach(a => {
        const t = a.textContent.trim();
        if (t && t.length < 50) result.navigation.push(t);
      });
      
      document.querySelectorAll('button, [role=button]').forEach(b => {
        const t = (b.textContent || b.getAttribute('aria-label') || '').trim();
        if (t && t.length < 50) result.buttons.push(t.substring(0, 100));
      });
      
      const navLinks = Array.from(document.querySelectorAll('a')).map(a => a.textContent.trim()).filter(t => t && t.length < 30);
      if (result.navigation.length === 0 && navLinks.length > 0) {
        result.navigation = navLinks.slice(0, 20);
      }
      
      const cardSelectors = [
        '.document-card', '.doc-card', '.card', '.grid-item',
        '.library-item', '.MuiCard-root', '.ant-card',
        '[data-testid*=card]', 'article', '.item', '.list-item'
      ];
      
      for (const sel of cardSelectors) {
        const cards = document.querySelectorAll(sel);
        if (cards.length > 0) {
          result.cardCount = cards.length;
          cards.forEach((card, i) => {
            if (i < 10) {
              result.cards.push({
                selector: sel,
                index: i,
                text: card.textContent.trim().substring(0, 200),
                hasImg: !!card.querySelector('img')
              });
            }
          });
          break;
        }
      }
      
      if (result.cardCount === 0) {
        const emptyPatterns = ['空', '暂无', '没有文档', '暂无数据', 'empty', 'no data', 'no document', 'nothing here'];
        const bodyLower = result.bodyText.toLowerCase();
        for (const ep of emptyPatterns) {
          if (bodyLower.includes(ep.toLowerCase())) {
            result.hasEmptyState = true;
            result.emptyStateText = 'Found empty keyword: ' + ep;
            break;
          }
        }
      }
      
      result.searchBox = !!document.querySelector('input[type=search], input[placeholder*=搜索], input[placeholder*=search]');
      
      return result;
    });
    
    console.log('Page Analysis:');
    console.log(JSON.stringify(pageContent, null, 2));
    
    console.log('\n=== Step 4: Click on document card ===');
    let modalOpened = false;
    let clickedCardInfo = null;
    
    const clickSelectors = [
      '.document-card', '.doc-card', '.card', '.grid-item',
      '.library-item', '.MuiCard-root', '.ant-card',
      'article', '.item', '.list-item',
      'a[href*="doc"]', 'a[href*="document"]', 'a[href*="note"]'
    ];
    
    for (const sel of clickSelectors) {
      try {
        const elements = await page.$$(sel);
        if (elements.length > 0) {
          console.log('Found selector:', sel, 'count:', elements.length);
          const textContent = await elements[0].evaluate(el => el.textContent.trim().substring(0, 200));
          clickedCardInfo = { selector: sel, text: textContent };
          console.log('Card text:', textContent);
          await elements[0].scrollIntoViewIfNeeded();
          await elements[0].click();
          modalOpened = true;
          break;
        }
      } catch(e) {
        console.log('Selector', sel, 'failed:', e.message.substring(0, 100));
        continue;
      }
    }
    
    if (!modalOpened && pageContent.cardCount === 0) {
      console.log('No document cards found. Empty state.');
    }
    
    console.log('\n=== Step 5: Wait 1s for modal animation and take screenshot (library_modal) ===');
    await page.waitForTimeout(1000);
    
    const modalScreenshotPath = path.join(screenshotsDir, 'library_modal.png');
    await page.screenshot({
      path: modalScreenshotPath,
      fullPage: true
    });
    console.log('Saved:', modalScreenshotPath);
    console.log('Size:', (fs.statSync(modalScreenshotPath).size / 1024).toFixed(2), 'KB');
    
    const modalContent = await page.evaluate(() => {
      const modalSelectors = [
        '.modal', '.Modal', '.dialog', '.Dialog', '.popup',
        '[role=dialog]', '.ant-modal', '.MuiModal-root',
        '.modal-content', '[aria-modal=true]', '.drawer', '.overlay'
      ];
      
      let result = { modalFound: false, modalText: '', closeButton: false, selector: '' };
      
      for (const sel of modalSelectors) {
        const el = document.querySelector(sel);
        if (el && el.getBoundingClientRect().width > 0) {
          result.modalFound = true;
          result.modalText = el.textContent.trim().substring(0, 500);
          result.selector = sel;
          const closeBtn = el.querySelector('button[aria-label*="关闭"], button[aria-label*="Close"], button[class*="close"], .close');
          result.closeButton = !!closeBtn;
          break;
        }
      }
      
      result.urlAfterClick = window.location.href;
      return result;
    });
    
    console.log('Modal Analysis:', JSON.stringify(modalContent, null, 2));
    
    console.log('\n=== Step 6: Close modal and scroll page ===');
    await page.keyboard.press('Escape');
    await page.waitForTimeout(500);
    console.log('Pressed Escape key');
    
    console.log('\n=== Scroll page to see more content ===');
    const scrollInfo = await page.evaluate(() => {
      const scrollH = document.documentElement.scrollHeight;
      const clientH = document.documentElement.clientHeight;
      window.scrollTo(0, scrollH);
      return {
        scrollHeight: scrollH,
        clientHeight: clientH,
        canScroll: scrollH > clientH + 50
      };
    });
    console.log('Scroll info:', JSON.stringify(scrollInfo));
    
    await page.waitForTimeout(1000);
    
    console.log('\n=== Final summary ===');
    const finalInfo = {
      pageTitle: pageTitle,
      pageURL: pageURL,
      cardCount: pageContent.cardCount,
      hasDocuments: pageContent.cardCount > 0,
      hasEmptyState: pageContent.hasEmptyState,
      emptyStateText: pageContent.emptyStateText,
      clickedCard: clickedCardInfo,
      modalFound: modalContent.modalFound,
      modalText: modalContent.modalText,
      navigation: pageContent.navigation,
      headings: pageContent.headingTexts,
      searchBox: pageContent.searchBox,
      scrollable: scrollInfo.canScroll,
      bodyText: pageContent.bodyText,
      screenshotsCreated: {
        library_main: fs.existsSync(mainScreenshotPath),
        library_modal: fs.existsSync(modalScreenshotPath)
      }
    };
    
    console.log('FINAL_SUMMARY_START');
    console.log(JSON.stringify(finalInfo, null, 2));
    console.log('FINAL_SUMMARY_END');
    
  } catch (error) {
    console.error('ERROR:', error.message);
    console.error('STACK:', error.stack);
  } finally {
    await browser.close();
  }
})();