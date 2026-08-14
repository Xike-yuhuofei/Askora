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
    console.log('=== Navigate to library ===');
    await page.goto('http://localhost:5173/#/library', {
      waitUntil: 'networkidle',
      timeout: 30000
    });
    
    console.log('=== Wait 3 seconds ===');
    await page.waitForTimeout(3000);
    
    // Debug: 列出所有可能的可点击元素
    console.log('\n=== Find clickable elements with askora-start ===');
    const clickables = await page.evaluate(() => {
      const all = Array.from(document.querySelectorAll('*'));
      const results = [];
      for (const el of all) {
        const txt = el.textContent.trim();
        if (txt.includes('askora-start')) {
          const rect = el.getBoundingClientRect();
          const styles = window.getComputedStyle(el);
          results.push({
            tag: el.tagName,
            classes: el.className.toString().substring(0, 100),
            id: el.id,
            text: txt.substring(0, 200),
            width: rect.width,
            height: rect.height,
            clickable: styles.cursor === 'pointer' || el.tagName === 'BUTTON' || el.tagName === 'A' || el.getAttribute('role') === 'button'
          });
        }
      }
      return results;
    });
    console.log('包含 askora-start 的元素:');
    clickables.forEach((c, i) => {
      console.log(i + ':', c.tag, 'classes:', c.classes.substring(0, 50), 'size:', c.width + 'x' + c.height, 'clickable:', c.clickable);
      console.log('   text:', c.text.substring(0, 100));
    });
    
    // 查找包含 MD 徽章和 askora-start.md 的容器元素
    console.log('\n=== Find card containers ===');
    const cards = await page.evaluate(() => {
      // 查找包含 MD 和 askora-start.md 的最近共同祖先
      const mdEls = Array.from(document.querySelectorAll('*')).filter(e => e.textContent.trim() === 'MD');
      const results = [];
      
      for (const md of mdEls) {
        let parent = md.parentElement;
        let levels = 0;
        while (parent && levels < 10) {
          if (parent.textContent.includes('askora-start.md')) {
            const rect = parent.getBoundingClientRect();
            results.push({
              tag: parent.tagName,
              classes: parent.className.toString().substring(0, 150),
              level: levels,
              width: rect.width,
              height: rect.height,
              text: parent.textContent.trim().substring(0, 200)
            });
            break;
          }
          parent = parent.parentElement;
          levels++;
        }
      }
      return results;
    });
    console.log('卡片容器:');
    cards.forEach((c, i) => console.log(i + ':', c.tag, 'classes:', c.classes.substring(0, 80), 'level:', c.level, 'size:', c.width + 'x' + c.height));
    
    // 尝试多种方式点击
    console.log('\n=== Attempt to click card ===');
    let clicked = false;
    
    // 方法1: 点击包含 askora-start.md 文本且面积较大的元素
    try {
      const elements = await page.$$('text=askora-start.md');
      console.log('找到 askora-start.md 文本元素:', elements.length);
      for (let i = 0; i < elements.length; i++) {
        const box = await elements[i].boundingBox();
        console.log('元素 ' + i + ' 位置:', box);
        if (box && box.width > 50 && box.height > 20) {
          await elements[i].click();
          console.log('点击了 askora-start.md 元素 ' + i);
          clicked = true;
          break;
        }
      }
    } catch(e) {
      console.log('方法1失败:', e.message);
    }
    
    // 方法2: 如果没成功，查找可点击的父容器
    if (!clicked) {
      try {
        const cardContainer = await page.evaluateHandle(() => {
          const mdEls = Array.from(document.querySelectorAll('*')).filter(e => e.textContent.trim() === 'MD');
          for (const md of mdEls) {
            let parent = md.parentElement;
            let levels = 0;
            while (parent && levels < 10) {
              if (parent.textContent.includes('askora-start.md') && parent.getBoundingClientRect().width > 100) {
                return parent;
              }
              parent = parent.parentElement;
              levels++;
            }
          }
          return null;
        });
        
        if (cardContainer) {
          await cardContainer.click();
          console.log('通过容器句柄点击成功');
          clicked = true;
        }
      } catch(e) {
        console.log('方法2失败:', e.message);
      }
    }
    
    // 方法3: 使用坐标点击 - 从截图估计卡片位置
    if (!clicked) {
      try {
        console.log('尝试坐标点击 (大约在 x=300, y=250 区域)');
        await page.mouse.click(300, 250);
        console.log('坐标点击完成');
        clicked = true;
      } catch(e) {
        console.log('方法3失败:', e.message);
      }
    }
    
    console.log('\n=== Click result: clicked =', clicked);
    
    // 等待模态框动画
    console.log('=== Wait 1 second for modal animation ===');
    await page.waitForTimeout(1500);
    
    // 检查模态框状态
    const modalCheck = await page.evaluate(() => {
      const modalSelectors = [
        '[role=dialog]', '[aria-modal=true]', '.modal', '.Modal',
        '.dialog', '.Dialog', '.ant-modal', '.MuiModal-root',
        '.drawer', '.overlay', '.popup'
      ];
      
      const result = {
        modalFound: false,
        modalSelector: '',
        modalText: '',
        anyFullScreenChange: false,
        urlChanged: false
      };
      
      result.urlChanged = window.location.href.includes('modal') || 
                         window.location.href.includes('id=') ||
                         window.location.href.includes('doc=') ||
                         window.location.hash.length > 20;
      result.currentUrl = window.location.href;
      
      for (const sel of modalSelectors) {
        const el = document.querySelector(sel);
        if (el) {
          const rect = el.getBoundingClientRect();
          const cs = window.getComputedStyle(el);
          if (rect.width > 200 && rect.height > 200 && cs.display !== 'none' && cs.visibility !== 'hidden') {
            result.modalFound = true;
            result.modalSelector = sel;
            result.modalText = el.textContent.trim().substring(0, 800);
            result.modalSize = rect.width + 'x' + rect.height;
            break;
          }
        }
      }
      
      // 检查是否有可见的覆盖层
      const overlays = document.querySelectorAll('*');
      for (const o of overlays) {
        const cs = window.getComputedStyle(o);
        if (cs.position === 'fixed' && o.offsetWidth >= window.innerWidth * 0.8 && o.offsetHeight >= window.innerHeight * 0.8) {
          if (cs.backgroundColor && cs.backgroundColor.includes('rgba') && cs.zIndex && parseInt(cs.zIndex) > 100) {
            result.anyFullScreenChange = true;
            if (!result.modalFound) {
              result.modalFound = true;
              result.modalText = o.textContent.trim().substring(0, 500);
              result.modalSelector = 'fixed-overlay-z' + cs.zIndex;
            }
          }
        }
      }
      
      return result;
    });
    
    console.log('模态框检查:');
    console.log(JSON.stringify(modalCheck, null, 2));
    
    // 截取模态框截图
    console.log('\n=== Take modal screenshot (library_modal) ===');
    const modalScreenshotPath = path.join(screenshotsDir, 'library_modal.png');
    await page.screenshot({
      path: modalScreenshotPath,
      fullPage: true
    });
    console.log('已保存模态框截图:', modalScreenshotPath);
    const stat = fs.statSync(modalScreenshotPath);
    console.log('文件大小:', (stat.size / 1024).toFixed(2), 'KB');
    
    // 关闭模态框
    console.log('\n=== Close modal (press Escape) ===');
    await page.keyboard.press('Escape');
    await page.waitForTimeout(800);
    
    // 关闭后截图
    const afterClosePath = path.join(screenshotsDir, 'library_after_close.png');
    await page.screenshot({ path: afterClosePath, fullPage: true });
    console.log('关闭后截图已保存');
    
    // 滚动检查
    console.log('\n=== Scroll check ===');
    const scrollResult = await page.evaluate(() => {
      const total = document.documentElement.scrollHeight;
      const viewport = document.documentElement.clientHeight;
      window.scrollTo(0, total);
      return {
        totalHeight: total,
        viewportHeight: viewport,
        scrollable: total > viewport + 50,
        extraScroll: total - viewport
      };
    });
    console.log('滚动结果:', JSON.stringify(scrollResult));
    
    console.log('\n=== DONE ===');
    
  } catch (error) {
    console.error('ERROR:', error.message);
    console.error('STACK:', error.stack);
  } finally {
    await browser.close();
  }
})();