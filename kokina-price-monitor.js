const { exec } = require('child_process');
const fs = require('fs');
const https = require('https');
const { syncKokinaToGoogleSheets } = require('./google-sheets-sync');

const PRICE_DB_FILE = './kokina_price_history.json';
const SLACK_WEBHOOK = process.env.SLACK_WEBHOOK_URL;

// Önceki fiyatları yükle
function loadPreviousPrices() {
  try {
    if (fs.existsSync(PRICE_DB_FILE)) {
      return JSON.parse(fs.readFileSync(PRICE_DB_FILE, 'utf8'));
    }
  } catch (error) {
    console.error('Önceki fiyatlar yüklenemedi:', error.message);
  }
  return {};
}

// Yeni fiyatları kaydet
function savePrices(priceData) {
  fs.writeFileSync(PRICE_DB_FILE, JSON.stringify(priceData, null, 2));
}

// Slack'e mesaj gönder
function sendSlackMessage(message) {
  if (!SLACK_WEBHOOK) {
    console.error('⚠️  SLACK_WEBHOOK_URL bulunamadı, mesaj gönderilmedi');
    return Promise.resolve();
  }
  
  const payload = JSON.stringify({ text: message });
  
  return new Promise((resolve, reject) => {
    const req = https.request(SLACK_WEBHOOK, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(payload)
      }
    }, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        if (res.statusCode === 200) {
          console.log('✅ Slack mesajı gönderildi');
          resolve();
        } else {
          console.error('Slack response:', body);
          reject(new Error(`Slack HTTP ${res.statusCode}: ${body}`));
        }
      });
    });
    
    req.on('error', reject);
    req.write(payload);
    req.end();
  });
}

// Kokina fiyat değişikliği bildirimi
async function sendKokinaPriceChangeNotification(changes, siteResults, reportUrl, sheetsUrl) {
  if (changes.length === 0) {
    // Değişiklik yok bildirimi
    const totalProducts = siteResults.reduce((sum, s) => sum + s.products.length, 0);
    const turkeyTime = new Date().toLocaleString('tr-TR', { timeZone: 'Europe/Istanbul' });
    let message = `🎄 *Kokina Çiçek Fiyat Taraması Tamamlandı*\n\n` +
      `✅ ${siteResults.filter(s => s.success).length} site tarandı\n` +
      `🎄 ${totalProducts} kokina ürünü kontrol edildi\n` +
      `✨ Fiyat değişikliği yok\n` +
      `🕐 ${turkeyTime}\n\n`;
    
    // Site bazında özet
    siteResults.forEach(siteResult => {
      if (siteResult.success && siteResult.products.length > 0) {
        const prices = siteResult.products.map(p => p.price).filter(p => p > 0);
        if (prices.length > 0) {
          const avgPrice = prices.reduce((sum, p) => sum + p, 0) / prices.length;
          const minPrice = Math.min(...prices);
          const maxPrice = Math.max(...prices);
          
          message += `*${siteResult.site_name}*\n`;
          message += `• Ürün: ${siteResult.products.length}\n`;
          message += `• Ort: ${avgPrice.toFixed(2)}₺ | Min: ${minPrice.toFixed(2)}₺ | Max: ${maxPrice.toFixed(2)}₺\n\n`;
        }
      }
    });
    
    if (sheetsUrl) {
      message += `📊 <${sheetsUrl}|Google Sheets'te Tüm Kokina Ürünlerini Gör>`;
    } else if (reportUrl) {
      message += `📋 <${reportUrl}|Detaylı Raporu Gör>`;
    }
    
    await sendSlackMessage(message);
    return;
  }
  
  // Site bazında değişiklikleri grupla
  const changeBySite = {};
  changes.forEach(change => {
    if (!changeBySite[change.site_name]) {
      changeBySite[change.site_name] = [];
    }
    changeBySite[change.site_name].push(change);
  });
  
  // Ana mesaj
  const turkeyTime = new Date().toLocaleString('tr-TR', { timeZone: 'Europe/Istanbul' });
  let headerMessage = `🎄 *Kokina Çiçek Fiyat Güncellemesi*\n\n` +
    `*${changes.length} kokina ürününün fiyatı değişti!*\n` +
    `📊 ${Object.keys(changeBySite).length} sitede değişiklik var\n` +
    `🕐 ${turkeyTime}\n\n`;
  
  if (sheetsUrl) {
    headerMessage += `📊 <${sheetsUrl}|Google Sheets'te Tüm Kokina Ürünlerini Gör>`;
  } else if (reportUrl) {
    headerMessage += `📋 <${reportUrl}|Detaylı Raporu Gör>`;
  }
  
  await sendSlackMessage(headerMessage);
  
  // Site bazında mesajlar
  for (const [siteName, siteChanges] of Object.entries(changeBySite)) {
    let siteMessage = `\n*🏪 ${siteName}* - ${siteChanges.length} değişiklik\n\n`;
    
    // Tüm değişiklikleri göster
    siteChanges.forEach(change => {
      const emoji = change.change > 0 ? '📈' : '📉';
      const changeText = change.change > 0 ? `+${change.change.toFixed(2)}` : change.change.toFixed(2);
      
      siteMessage += `*${change.name}*\n`;
      siteMessage += `• Eski: ${change.oldPrice.toFixed(2)}₺ → Yeni: ${change.newPrice.toFixed(2)}₺\n`;
      siteMessage += `• Fark: ${emoji} ${changeText}₺\n`;
      if (change.url) {
        siteMessage += `<${change.url}|Ürüne Git>\n`;
      }
      siteMessage += `\n`;
    });
    
    await sendSlackMessage(siteMessage);
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
}

// Fiyat güncellemesi kontrolü
function checkPriceUpdates(siteResults) {
  const previousData = loadPreviousPrices();
  const changes = [];
  const currentData = {
    last_update: new Date().toISOString(),
    product_type: 'kokina',
    sites: {}
  };
  
  siteResults.forEach(siteResult => {
    if (!siteResult.success) return;
    
    const siteId = siteResult.site_id;
    currentData.sites[siteId] = {
      name: siteResult.site_name,
      products: {},
      scraped_at: siteResult.scraped_at
    };
    
    siteResult.products.forEach(product => {
      // Mevcut fiyatı kaydet
      currentData.sites[siteId].products[product.id] = {
        name: product.name,
        price: product.price,
        url: product.url,
        timestamp: product.timestamp
      };
      
      // Önceki fiyatla karşılaştır
      if (previousData.sites && previousData.sites[siteId]) {
        const previousProduct = previousData.sites[siteId].products[product.id];
        if (previousProduct && previousProduct.price !== product.price) {
          changes.push({
            site_id: siteId,
            site_name: siteResult.site_name,
            id: product.id,
            name: product.name,
            oldPrice: previousProduct.price,
            newPrice: product.price,
            change: product.price - previousProduct.price,
            url: product.url
          });
        }
      }
    });
  });
  
  return { changes, currentData };
}

// Benchmarking analizi
function generateBenchmarkingReport(siteResults) {
  const report = {
    date: new Date().toISOString(),
    product_type: 'kokina',
    summary: {
      total_sites: siteResults.length,
      successful_sites: siteResults.filter(s => s.success).length,
      total_products: siteResults.reduce((sum, s) => sum + s.products.length, 0)
    },
    all_products: [],
    price_analysis: {
      by_site: {}
    }
  };
  
  // Site bazında analiz
  const siteCounters = {};
  const visibleLimits = {
    'Çiçek Sepeti': 23, // Sayfada görünen kokina ürün sayısı
  };
  
  siteResults.forEach(siteResult => {
    if (!siteResult.success || siteResult.products.length === 0) return;
    
    const prices = siteResult.products.map(p => p.price).filter(p => p > 0);
    if (prices.length === 0) return;
    
    const avgPrice = prices.reduce((sum, p) => sum + p, 0) / prices.length;
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    
    report.price_analysis.by_site[siteResult.site_name] = {
      product_count: siteResult.products.length,
      avg_price: avgPrice.toFixed(2),
      min_price: minPrice.toFixed(2),
      max_price: maxPrice.toFixed(2)
    };
    
    // Tüm ürünleri listeye ekle (Kategori kolonunu "Görünür / Gizli" label olarak kullan)
    siteResult.products.forEach(product => {
      const siteName = siteResult.site_name;
      const currentIndex = (siteCounters[siteName] || 0) + 1;
      siteCounters[siteName] = currentIndex;
      
      let visibilityLabel = '-';
      if (visibleLimits[siteName]) {
        visibilityLabel = currentIndex <= visibleLimits[siteName]
          ? 'Görünür'
          : 'Gizli/ekstra';
      }
      
      report.all_products.push({
        site: siteName,
        name: product.name,
        price: product.price,
        url: product.url,
        category: visibilityLabel
      });
    });
  });
  
  return report;
}

// Ana fonksiyon
async function main() {
  console.log('🎄 Kokina Çiçek Fiyat Takibi Başlatılıyor...');
  
  // Kokina scraper'ı çalıştır
  console.log('📡 Siteler taranıyor (kokina ürünleri)...');
  
  exec('node kokina-scraper.js', async (error, stdout, stderr) => {
    if (error) {
      console.error('Scraper hatası:', error.message);
      await sendSlackMessage(`❌ *Kokina Scraper Hatası*\n\n${error.message}`);
      process.exit(1);
    }
    
    try {
      const data = JSON.parse(stdout);
      const siteResults = data.sites;
      
      console.log(`✅ Kokina taraması tamamlandı: ${data.total_products} ürün`);
      
      if (data.total_products === 0) {
        console.log('⚠️  Hiç kokina ürünü bulunamadı');
        await sendSlackMessage(`⚠️ *Kokina Taraması*\n\nHiç kokina ürünü bulunamadı. Siteler kontrol ediliyor...`);
        process.exit(0);
      }
      
      // Fiyat değişikliklerini tespit et
      const { changes, currentData } = checkPriceUpdates(siteResults);
      
      // Sonuçları göster
      if (changes.length > 0) {
        console.log(`\n💰 ${changes.length} kokina fiyat değişikliği tespit edildi:`);
        changes.forEach(c => {
          const emoji = c.change > 0 ? '📈' : '📉';
          console.log(`${emoji} [${c.site_name}] ${c.name}: ${c.oldPrice}₺ → ${c.newPrice}₺`);
        });
      } else {
        console.log('\n✨ Kokina fiyat değişikliği yok');
      }
      
      // Benchmarking raporu oluştur
      const benchmarkReport = generateBenchmarkingReport(siteResults);
      fs.writeFileSync('./kokina_benchmark_report.json', JSON.stringify(benchmarkReport, null, 2));
      console.log('📊 Kokina benchmarking raporu oluşturuldu: kokina_benchmark_report.json');
      
      // GitHub rapor linki
      const reportUrl = 'https://github.com/hasansavli-tc17/ciceksepeti-price-monitor/blob/main/kokina_benchmark_report.json';
      
      // Google Sheets'e sync (başarısız olursa bile sheet URL'ini fallback olarak kullan)
      console.log('📊 Kokina ürünleri Google Sheets\'e gönderiliyor...');
      let sheetsUrl = null;
      try {
        sheetsUrl = await syncKokinaToGoogleSheets();
      } catch (e) {
        console.log('⚠️  Kokina Sheets sync hatası, sadece link gösterilecek:', e.message);
      }
      if (!sheetsUrl && process.env.GOOGLE_SHEETS_ID) {
        sheetsUrl = `https://docs.google.com/spreadsheets/d/${process.env.GOOGLE_SHEETS_ID}`;
      }
      
      // Slack'e bildir
      await sendKokinaPriceChangeNotification(changes, siteResults, reportUrl, sheetsUrl);
      
      // Yeni fiyatları kaydet
      savePrices(currentData);
      console.log('💾 Kokina fiyatları kaydedildi');
      
    } catch (parseError) {
      console.error('JSON parse hatası:', parseError.message);
      await sendSlackMessage(`❌ *Kokina Parse Hatası*\n\n${parseError.message}`);
      process.exit(1);
    }
  });
}

main();

