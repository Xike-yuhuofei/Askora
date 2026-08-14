const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const screenshotsDir = '/Users/xike/Documents/Docs/Askora/screenshots';

(async () => {
  if (!fs.existsSync(screenshotsDir)) {
    fs.mkdirSync(screenshotsDir, { recursive: true });
  }

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  
  try {
    console.log('=== Step 1: Navigate to library page ===');
    await page.goto('http://localhost:5173/#/library', { waitUntil: 'networkidle', timeout: 30000 });
    console.log('URL:', page.url());
    
    console.log('\n=== Step 2: Wait 3 seconds for full render ===');
    await page.waitForTimeout(3000);
    
    // 截取 library_main
    console.log('\n=== Step 3: Screenshot library_main ===');
    const mainPath = path.join(screenshotsDir, 'library_main.png');
    await page.screenshot({ path: mainPath, fullPage: true });
    console.log('Saved library_main.png, size:', (fs.statSync(mainPath).size/1024).toFixed(2), 'KB');
    
    // 重新截取主页面，确认在正确的页面
    const verifyContent = await page.evaluate(() => {
      return {
        title: document.title,
        h1: document.querySelector('h1')?.textContent?.trim(),
        url: window.location.href,
        gridExists: !!document.querySelector('.library-grid'),
        cardButtonExists: !!document.querySelector('.library-card__button'),
        cardButtons: document.querySelectorAll('.library-card__button').length
      };
    });
    console.log('验证:', JSON.stringify(verifyContent, null, 2));
    
    // 步骤4: 点击中间内容区的 .library-card__button
    console.log('\n=== Step 4: Click .library-card__button in main content ===');
    
    let clickedCorrectly = false;
    const startUrl = page.url();
    
    // 最精确：选择 .library-grid 内的 .library-card__button
    try {
      const selector = '.library-grid .library-card__button';
      const btnCount = await page.locator(selector).count();
      console.log('找到 .library-grid .library-card__button 数量:', btnCount);
      
      if (btnCount > 0) {
        const firstBtn = page.locator(selector).first();
        
        // 获取按钮信息
        const btnInfo = await firstBtn.evaluate(el => ({
          classes: el.className,
          text: el.textContent.trim().substring(0, 150),
          rect: el.getBoundingClientRect()
        }));
        console.log('按钮信息:', JSON.stringify(btnInfo));
        
        // 点击按钮
        await firstBtn.click();
        console.log('已点击 library-card__button');
        clickedCorrectly = true;
      }
    } catch(e) {
      console.log('点击失败:', e.message);
      // 备用方法
      try {
        console.log('尝试备用选择器...');
        await page.click('button.library-card__button');
        clickedCorrectly = true;
      } catch(e2) {
        console.log('备用也失败:', e2.message);
      }
    }
    
    // 步骤5: 等待模态框动画并截图
    console.log('\n=== Step 5: Wait 1.5s for modal animation ===');
    await page.waitForTimeout(1500);
    
    // 检查 URL 和模态框状态
    const afterClickState = await page.evaluate(() => {
      const state = {
        url: window.location.href,
        urlChanged: window.location.href !== 'http://localhost:5173/#/library',
        modalDetected: false,
        modalDetails: null,
        fullscreenOverlays: []
      };
      
      // 检查各种模态框选择器
      const modalSels = [
        '[role=dialog]', '[aria-modal="true"]', '.MuiModal-root',
        '.ant-modal-root', '.modal-overlay', '.dialog-overlay',
        '.ReactModalPortal > div', '[class*="modal"][class*="open"]',
        '.drawer-open', '.sheet-open', '.popup'
      ];
      
      for (const sel of modalSels) {
        const els = document.querySelectorAll(sel);
        els.forEach(el => {
          const rect = el.getBoundingClientRect();
          const cs = window.getComputedStyle(el);
          if (rect.width > 200 && rect.height > 100 && 
              cs.display !== 'none' && cs.visibility !== 'hidden' &&
              parseFloat(cs.opacity || '1') > 0.5) {
            state.modalDetected = true;
            state.modalDetails = {
              selector: sel,
              text: el.textContent.trim().substring(0, 600),
              size: Math.round(rect.width) + 'x' + Math.round(rect.height),
              zIndex: cs.zIndex
            };
          }
        });
        if (state.modalDetected) break;
      }
      
      // 检查固定定位的大元素（覆盖层）
      if (!state.modalDetected) {
        document.querySelectorAll('*').forEach(el => {
          const cs = window.getComputedStyle(el);
          const rect = el.getBoundingClientRect();
          if (cs.position === 'fixed' && 
              rect.width >= window.innerWidth * 0.5 &&
              rect.height >= window.innerHeight * 0.5 &&
              parseInt(cs.zIndex || '0') > 100) {
            state.fullscreenOverlays.push({
              tag: el.tagName,
              size: Math.round(rect.width) + 'x' + Math.round(rect.height),
              zIndex: cs.zIndex,
              bg: cs.backgroundColor,
              text: el.textContent.trim().substring(0, 300)
            });
          }
        });
        if (state.fullscreenOverlays.length > 0) {
          state.modalDetected = true;
          state.modalDetails = state.fullscreenOverlays[0];
        }
      }
      
      return state;
    });
    
    console.log('点击后状态:');
    console.log(JSON.stringify(afterClickState, null, 2).substring(0, 1500));
    
    // 截取 library_modal
    console.log('\n=== Take screenshot library_modal ===');
    const modalPath = path.join(screenshotsDir, 'library_modal.png');
    await page.screenshot({ path: modalPath, fullPage: true });
    console.log('Saved library_modal.png, size:', (fs.statSync(modalPath).size/1024).toFixed(2), 'KB');
    
    // 如果 URL 改变了（路由模态，不是传统 modal DOM），也算成功
    if (afterClickState.urlChanged) {
      console.log('注意: URL 改变了，可能使用路由方式显示详情');
    }
    
    // 步骤6: 关闭模态框
    console.log('\n=== Step 6: Close modal (Escape + 尝试返回) ===');
    await page.keyboard.press('Escape');
    await page.waitForTimeout(600);
    
    // 如果是路由跳转，返回上一页
    const urlAfterEsc = page.url();
    if (urlAfterEsc !== startUrl) {
      console.log('按 ESC 后 URL 仍不同，尝试返回历史');
      await page.goBack();
      await page.waitForTimeout(800);
    }
    
    const finalUrl = page.url();
    console.log('最终 URL:', finalUrl);
    const backToLibrary = finalUrl.includes('/#/library');
    console.log('返回 Library:', backToLibrary ? 'YES' : 'NO');
    
    // 滚动检查
    console.log('\n=== Step 7: Scroll check ===');
    const scrollInfo = await page.evaluate(() => {
      const total = document.documentElement.scrollHeight;
      const view = document.documentElement.clientHeight;
      const canScroll = total > view + 50;
      
      // 尝试滚动到底
      window.scrollTo(0, total);
      
      return {
        totalHeight: total,
        viewportHeight: view,
        canScrollDown: canScroll,
        extraContentPx: total - view,
        // 检查底部内容
        footerContent: document.body.innerText.substring(document.body.innerText.length - 300)
      };
    });
    console.log('滚动信息:', JSON.stringify(scrollInfo, null, 2).substring(0, 800));
    
    await page.waitForTimeout(800);
    
    // 滚动回顶部
    await page.evaluate(() => window.scrollTo(0, 0));
    
    console.log('\n=== TASK COMPLETE ===');
    
  } catch (e) {
    console.error('ERROR:', e.message);
    console.error(e.stack);
  } finally {
    await browser.close();
  }
})();