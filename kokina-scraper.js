const puppeteer = require('puppeteer');
const fs = require('fs');

// Config dosyasını yükle
const config = JSON.parse(fs.readFileSync('./sites-config.json', 'utf8'));

// Site bazında kokina URL'lerini belirle
function getKokinaUrl(site) {
  const kokinaUrls = {
    'ciceksepeti': 'https://www.ciceksepeti.com/d/kokina',
    'hizlicicek': 'https://hizlicicek.com/kokina',
    'bloomandfresh': 'https://www.bloomandfresh.com/c/cicek?cicek-turu=kokina'
  };
  
  return kokinaUrls[site.id] || null;
}

// Kokina sayfası için sayfalama URL pattern'i
function getKokinaPaginationUrl(site, pageNum) {
  const patterns = {
    'ciceksepeti': `https://www.ciceksepeti.com/d/kokina?page=${pageNum}`,
    'hizlicicek': `https://hizlicicek.com/kokina?page=${pageNum}`,
    'bloomandfresh': `https://www.bloomandfresh.com/c/cicek?page=${pageNum}&cicek-turu=kokina`
  };
  
  return patterns[site.id] || null;
}

// Universal selector denemesi - birden fazla selector dene
async function findElements(page, selectors) {
  const selectorList = Array.isArray(selectors) ? selectors : [selectors];
  
  for (const selector of selectorList) {
    try {
      const elements = await page.$$(selector);
      if (elements && elements.length > 0) {
        return { elements, selector };
      }
    } catch (err) {
      continue;
    }
  }
  return { elements: [], selector: null };
}

// Bir sayfadan ürün verilerini çek
async function scrapePageProducts(page, site, pageUrl) {
  console.error(`  📄 Yükleniyor: ${pageUrl}`);
  
  for (let attempt = 1; attempt <= config.scraping_settings.retry_attempts; attempt++) {
    try {
      await page.goto(pageUrl, {
        waitUntil: 'networkidle2',
        timeout: config.scraping_settings.timeout
      });
      break;
    } catch (err) {
      console.error(`    ⚠️  Navigasyon denemesi ${attempt} başarısız: ${err.message}`);
      if (attempt === config.scraping_settings.retry_attempts) throw err;
      await new Promise(r => setTimeout(r, config.scraping_settings.retry_delay));
    }
  }
  
  // Cloudflare ve dinamik içerik yüklenmesi için bekle
  await new Promise(resolve => setTimeout(resolve, config.scraping_settings.wait_after_load));
  
  // Ürünleri çek
  const products = await page.evaluate((siteConfig) => {
    // Helper function - multiple selector denemesi
    function trySelectors(element, selectors) {
      const selectorList = selectors.split(',').map(s => s.trim());
      for (const selector of selectorList) {
        try {
          const el = element.querySelector(selector);
          if (el) return el;
        } catch (e) {
          continue;
        }
      }
      return null;
    }
    
    function trySelectorsAll(element, selectors) {
      const selectorList = selectors.split(',').map(s => s.trim());
      for (const selector of selectorList) {
        try {
          const elements = element.querySelectorAll(selector);
          if (elements && elements.length > 0) return elements;
        } catch (e) {
          continue;
        }
      }
      return [];
    }
    
    // Ürün kutularını bul
    const productElements = Array.from(
      trySelectorsAll(document, siteConfig.selectors.product_box)
    );
    
    return productElements.map((el, index) => {
      // Ürün adını bul
      let title = '';
      const titleEl = trySelectors(el, siteConfig.selectors.product_name);
      if (titleEl) {
        title = titleEl.innerText || titleEl.textContent || '';
      }
      
      // Fiyatı bul
      let price = 0;
      const priceEl = trySelectors(el, siteConfig.selectors.product_price);
      if (priceEl) {
        const priceText = priceEl.innerText || priceEl.textContent || '0';
        // Tüm sayıları bul
        const numbers = priceText.match(/[\d.,]+/g);
        if (numbers && numbers.length > 0) {
          // Son sayıyı al (indirimli fiyat genelde son)
          const lastNumber = numbers[numbers.length - 1];
          price = parseFloat(lastNumber.replace(/\./g, '').replace(',', '.')) || 0;
        }
      }
      
      // URL'yi bul
      let url = '';
      const linkEl = el.querySelector('a[href]') || el;
      if (linkEl && linkEl.href) {
        url = linkEl.href;
      } else if (linkEl && linkEl.getAttribute) {
        const href = linkEl.getAttribute('href');
        if (href) {
          // Relative URL'leri absolute yap
          url = href.startsWith('http') ? href : `${siteConfig.url}${href.startsWith('/') ? '' : '/'}${href}`;
        }
      }
      
      // Product ID oluştur
      let productId = `${siteConfig.id}_${index}`;
      if (url) {
        // URL'den ID çıkarmaya çalış
        const urlParts = url.split('/').filter(p => p);
        const lastPart = urlParts[urlParts.length - 1];
        productId = lastPart ? `${siteConfig.id}_${lastPart.replace(/[^a-zA-Z0-9-]/g, '_')}` : productId;
      }
      
      return {
        id: productId,
        name: title.trim(),
        price: price,
        url: url,
        site_id: siteConfig.id,
        site_name: siteConfig.name,
        timestamp: new Date().toISOString()
      };
    }).filter(p => p.price > 0 && p.name !== '');
  }, site);
  
  return products;
}

// Bir siteyi tamamen tara - kokina özel sayfasından
async function scrapeSite(browser, site) {
  console.error(`\n🎄 ${site.name} taranıyor (Kokina sayfası)...`);
  
  const page = await browser.newPage();
  await page.setUserAgent(config.scraping_settings.user_agent);
  page.setDefaultNavigationTimeout(config.scraping_settings.timeout);
  page.setDefaultTimeout(config.scraping_settings.timeout);
  
  let allProducts = [];
  
  try {
    // Kokina özel URL'sini al
    const kokinaUrl = getKokinaUrl(site);
    if (!kokinaUrl) {
      console.error(`  ⚠️  ${site.name} için kokina URL'si tanımlı değil, atlanıyor`);
      return {
        site_id: site.id,
        site_name: site.name,
        success: false,
        error: 'Kokina URL tanımlı değil',
        products: [],
        scraped_at: new Date().toISOString()
      };
    }
    
    // Sayfalama: kokina sayfalarında genelde daha fazla ürün var, o yüzden üst limite biz karar verelim
    // Çiçek Sepeti için 5 sayfaya kadar dene, diğerleri için config'teki değeri kullan ya da en az 3 sayfa tara
    let maxPages = 3;
    if (site.id === 'ciceksepeti') {
      maxPages = 5;
    } else if (site.pagination && site.pagination.enabled && site.pagination.max_pages > 3) {
      maxPages = site.pagination.max_pages;
    }
    
    for (let pageNum = 1; pageNum <= maxPages; pageNum++) {
      let pageUrl;
      if (pageNum === 1) {
        pageUrl = kokinaUrl;
      } else {
        // Sayfalama URL'i oluştur
        const paginationUrl = getKokinaPaginationUrl(site, pageNum);
        if (paginationUrl) {
          pageUrl = paginationUrl;
        } else {
          // Fallback: genel pattern kullan
          pageUrl = kokinaUrl + (kokinaUrl.includes('?') ? '&' : '?') + `page=${pageNum}`;
        }
      }
      
      const products = await scrapePageProducts(page, site, pageUrl);
      console.error(`    ✅ Sayfa ${pageNum}: ${products.length} ürün bulundu`);
      allProducts = allProducts.concat(products);
      
      // Eğer bu sayfada ürün yoksa dur
      if (products.length === 0) {
        break;
      }
      
      // Sayfalar arası kısa bekleme
      if (pageNum < maxPages) {
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    }
    
    console.error(`  🎯 Toplam ${allProducts.length} kokina ürünü bulundu`);
    
    return {
      site_id: site.id,
      site_name: site.name,
      success: true,
      products: allProducts,
      scraped_at: new Date().toISOString()
    };
    
  } catch (error) {
    console.error(`  ❌ Hata: ${error.message}`);
    return {
      site_id: site.id,
      site_name: site.name,
      success: false,
      error: error.message,
      products: [],
      scraped_at: new Date().toISOString()
    };
  } finally {
    await page.close();
  }
}

// Ana fonksiyon - tüm sitelerin kokina sayfalarını tara
async function scrapeKokinaProducts() {
  console.error('🎄 Kokina Çiçek Fiyat Taraması Başlıyor...\n');
  console.error(`📋 ${config.sites.filter(s => s.enabled).length} site taranacak`);
  console.error(`🎯 Her sitenin kokina özel sayfasından ürünler alınacak\n`);
  
  const browser = await puppeteer.launch({
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-accelerated-2d-canvas',
      '--no-first-run',
      '--no-zygote',
      '--disable-gpu'
    ]
  });
  
  const results = [];
  
  try {
    const enabledSites = config.sites.filter(s => s.enabled);
    
    for (const site of enabledSites) {
      const result = await scrapeSite(browser, site);
      results.push(result);
      
      // Siteler arası bekleme
      await new Promise(resolve => setTimeout(resolve, 3000));
    }
    
    // Özet
    const successCount = results.filter(r => r.success).length;
    const totalProducts = results.reduce((sum, r) => sum + r.products.length, 0);
    
    console.error(`\n✨ Kokina Taraması Tamamlandı!`);
    console.error(`   ✅ Başarılı: ${successCount}/${enabledSites.length} site`);
    console.error(`   🎄 Toplam Kokina: ${totalProducts} ürün`);
    
    // Başarısız siteleri göster
    const failed = results.filter(r => !r.success);
    if (failed.length > 0) {
      console.error(`\n   ⚠️  Başarısız siteler:`);
      failed.forEach(f => {
        console.error(`      - ${f.site_name}: ${f.error}`);
      });
    }
    
    // Site bazında kokina sayılarını göster
    console.error(`\n   📊 Site Bazında Kokina Ürünleri:`);
    results.forEach(r => {
      if (r.success) {
        console.error(`      - ${r.site_name}: ${r.products.length} ürün`);
      }
    });
    
    // JSON çıktı
    const output = {
      scrape_date: new Date().toISOString(),
      product_type: 'kokina',
      total_sites: enabledSites.length,
      successful_sites: successCount,
      total_products: totalProducts,
      sites: results
    };
    
    console.log(JSON.stringify(output, null, 2));
    
  } catch (error) {
    console.error('❌ Genel Hata:', error.message);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

// Çalıştır
scrapeKokinaProducts();

