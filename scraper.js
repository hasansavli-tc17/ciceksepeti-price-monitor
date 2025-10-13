const puppeteer = require('puppeteer');

async function scrapeCiceksepeti() {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  try {
    const page = await browser.newPage();
    
    // User agent ayarla
    await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
    
    console.error('Sayfa yükleniyor...');
    await page.goto('https://www.ciceksepeti.com/d/cicek-buketleri', {
      waitUntil: 'networkidle2',
      timeout: 30000
    });
    
    // Biraz bekle (Cloudflare challenge için)
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    console.error('Ürünler aranıyor...');
    
    // Ürünleri çek
    const products = await page.evaluate(() => {
      const productElements = Array.from(document.querySelectorAll('[data-cs-product-box="true"]'));
      
      return productElements.slice(0, 30).map((el, index) => {
        const titleEl = el.querySelector('[data-cs-pb-name="true"]');
        const priceEl = el.querySelector('[data-cs-pb-price-text="true"]');
        const href = el.getAttribute('href');
        
        const title = titleEl ? titleEl.innerText : `Ürün ${index + 1}`;
        const priceText = priceEl ? priceEl.innerText : '0';
        const price = parseFloat(priceText.replace(/[^0-9,]/g, '').replace(',', '.')) || 0;
        const url = href ? `https://www.ciceksepeti.com${href}` : '';
        
        // Ürün ID'sini href'ten al
        const productId = href ? href.split('-').pop() || `product_${index}` : `product_${index}`;
        
        return {
          id: productId,
          name: title.trim(),
          price: price,
          url: url,
          timestamp: new Date().toISOString()
        };
      }).filter(p => p.price > 0 && p.name !== '');
    });
    
    console.error(`${products.length} ürün bulundu`);
    
    // JSON olarak çıktı ver
    console.log(JSON.stringify({ products: products }, null, 2));
    
  } catch (error) {
    console.error('Hata:', error.message);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

scrapeCiceksepeti();
