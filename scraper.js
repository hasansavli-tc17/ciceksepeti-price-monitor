const puppeteer = require('puppeteer');

// Kategori kelime eşleştirmeleri
function detectCategory(productName) {
  const nameLower = productName.toLowerCase();
  
  if (nameLower.includes('gül') || nameLower.includes('gul') || nameLower.includes('rose')) {
    return 'Gül';
  } else if (nameLower.includes('orkide') || nameLower.includes('orkid')) {
    return 'Orkide';
  } else if (nameLower.includes('papatya')) {
    return 'Papatya';
  } else if (nameLower.includes('lilyum') || nameLower.includes('lilium')) {
    return 'Lilyum';
  } else if (nameLower.includes('gerbera')) {
    return 'Gerbera';
  } else if (nameLower.includes('lisyantus') || nameLower.includes('lisianthus')) {
    return 'Lisyantus';
  } else if (nameLower.includes('karanfil')) {
    return 'Karanfil';
  } else if (nameLower.includes('lale') || nameLower.includes('tulip')) {
    return 'Lale';
  } else {
    return 'Karma/Diğer';
  }
}

async function scrapePageProducts(page, pageUrl) {
  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      await page.goto(pageUrl, {
        waitUntil: 'networkidle2',
        timeout: 60000
      });
      break;
    } catch (err) {
      console.error(`  Navigasyon denemesi ${attempt} başarısız: ${err.message}`);
      if (attempt === 3) throw err;
      await new Promise(r => setTimeout(r, 4000));
    }
  }
  
  // Cloudflare beklemesi
  await new Promise(resolve => setTimeout(resolve, 5000));
  
  // Ürünleri çek
  const products = await page.evaluate(() => {
    const productElements = Array.from(document.querySelectorAll('[data-cs-product-box="true"]'));
    
    return productElements.map((el, index) => {
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
  
  return products;
}

async function scrapeCiceksepeti() {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  try {
    const page = await browser.newPage();
    
    // User agent ayarla
    await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
    page.setDefaultNavigationTimeout(90000);
    page.setDefaultTimeout(90000);
    
    console.error('🌸 Çiçek Sepeti Fiyat Taraması Başlıyor...');
    console.error('📋 100 ürün alınacak (birden fazla sayfadan)\n');
    
    let allProducts = [];
    const pagesToScrape = 4; // 4 sayfa = ~100 ürün (her sayfada ~25-30 ürün)
    
    for (let pageNum = 1; pageNum <= pagesToScrape; pageNum++) {
      const targetUrl = `https://www.ciceksepeti.com/cicek-buketleri?page=${pageNum}`;
      console.error(`📄 Sayfa ${pageNum} yükleniyor...`);
      
      const products = await scrapePageProducts(page, targetUrl);
      console.error(`  ✅ ${products.length} ürün bulundu`);
      
      allProducts = allProducts.concat(products);
      
      // Sayfalar arası kısa bekleme
      if (pageNum < pagesToScrape) {
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    }
    
    // İlk 100 ürünü al
    const products = allProducts.slice(0, 100);
    
    // Kategorileri otomatik tespit et
    const productsWithCategory = products.map(p => ({
      ...p,
      category: detectCategory(p.name)
    }));
    
    console.error(`\n🎉 Toplam ${productsWithCategory.length} ürün bulundu`);
    console.error(`📊 Kategori dağılımı:`);
    
    // Kategori sayılarını hesapla
    const categoryCount = {};
    productsWithCategory.forEach(p => {
      categoryCount[p.category] = (categoryCount[p.category] || 0) + 1;
    });
    
    Object.entries(categoryCount).sort((a, b) => b[1] - a[1]).forEach(([cat, count]) => {
      console.error(`   - ${cat}: ${count} ürün`);
    });
    
    // JSON olarak çıktı ver
    console.log(JSON.stringify({ products: productsWithCategory }, null, 2));
    
  } catch (error) {
    console.error('❌ Genel Hata:', error.message);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

scrapeCiceksepeti();
