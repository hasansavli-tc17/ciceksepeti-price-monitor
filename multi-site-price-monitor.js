const { exec } = require('child_process');
const fs = require('fs');
const https = require('https');

const PRICE_DB_FILE = './multi_site_price_history.json';
const SLACK_WEBHOOK = process.env.SLACK_WEBHOOK_URL;

// Config dosyasını yükle
const config = JSON.parse(fs.readFileSync('./sites-config.json', 'utf8'));

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

// Fiyat değişikliği bildirimi
async function sendPriceChangeNotification(changes, siteResults, reportUrl, benchmarkReport) {
  if (changes.length === 0) {
    // Değişiklik yok bildirimi
    const totalProducts = siteResults.reduce((sum, s) => sum + s.products.length, 0);
    let message = `🌸 *Multi-Site Fiyat Taraması Tamamlandı*\n\n` +
      `✅ ${siteResults.filter(s => s.success).length} site tarandı\n` +
      `📦 ${totalProducts} ürün kontrol edildi\n` +
      `✨ Fiyat değişikliği yok\n` +
      `🕐 ${new Date().toLocaleString('tr-TR')}\n\n` +
      `📊 *Benchmarking Özeti*\n\n`;
    
    // Benchmarking özeti ekle
    Object.entries(benchmarkReport.price_analysis.by_site).forEach(([site, data]) => {
      message += `*${site}*\n`;
      message += `• Ürün: ${data.product_count}\n`;
      message += `• Ort: ${data.avg_price}₺ | Min: ${data.min_price}₺ | Max: ${data.max_price}₺\n\n`;
    });
    
    message += `📋 <${reportUrl}|Detaylı Raporu Gör> (Tüm ürünler ve kategoriler)`;
    
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
  const headerMessage = `🌸 *Multi-Site Fiyat Güncellemesi*\n\n` +
    `*${changes.length} ürünün fiyatı değişti!*\n` +
    `📊 ${Object.keys(changeBySite).length} sitede değişiklik var\n` +
    `🕐 ${new Date().toLocaleString('tr-TR')}\n\n` +
    `📋 <${reportUrl}|Detaylı Raporu Gör> (Tüm ürünler ve kategoriler)`;
  
  await sendSlackMessage(headerMessage);
  
  // Site bazında mesajlar
  for (const [siteName, siteChanges] of Object.entries(changeBySite)) {
    let siteMessage = `\n*🏪 ${siteName}* - ${siteChanges.length} değişiklik\n\n`;
    
    siteChanges.slice(0, 5).forEach(change => {
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
    
    if (siteChanges.length > 5) {
      siteMessage += `_... ve ${siteChanges.length - 5} ürün daha_\n`;
    }
    
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
        category: product.category,
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
            url: product.url,
            category: product.category
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
    summary: {
      total_sites: siteResults.length,
      successful_sites: siteResults.filter(s => s.success).length,
      total_products: siteResults.reduce((sum, s) => sum + s.products.length, 0)
    },
    price_analysis: {
      by_site: {},
      by_category: {}
    }
  };
  
  // Site bazında analiz
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
    
    // Kategori bazında
    siteResult.products.forEach(product => {
      if (!report.price_analysis.by_category[product.category]) {
        report.price_analysis.by_category[product.category] = {
          count: 0,
          total_price: 0,
          prices_by_site: {}
        };
      }
      
      const catData = report.price_analysis.by_category[product.category];
      catData.count++;
      catData.total_price += product.price;
      
      if (!catData.prices_by_site[siteResult.site_name]) {
        catData.prices_by_site[siteResult.site_name] = [];
      }
      catData.prices_by_site[siteResult.site_name].push(product.price);
    });
  });
  
  // Kategori ortalamalarını hesapla
  Object.keys(report.price_analysis.by_category).forEach(category => {
    const catData = report.price_analysis.by_category[category];
    catData.avg_price = (catData.total_price / catData.count).toFixed(2);
    
    // Site bazında kategori ortalamaları
    Object.keys(catData.prices_by_site).forEach(site => {
      const sitePrices = catData.prices_by_site[site];
      catData.prices_by_site[site] = {
        count: sitePrices.length,
        avg: (sitePrices.reduce((s, p) => s + p, 0) / sitePrices.length).toFixed(2)
      };
    });
    
    delete catData.total_price;
  });
  
  return report;
}

// Ana fonksiyon
async function main() {
  console.log('🔍 Multi-Site Fiyat Takibi Başlatılıyor...');
  
  // Multi-site scraper'ı çalıştır
  console.log('📡 Siteler taranıyor...');
  
  exec('node multi-site-scraper.js', async (error, stdout, stderr) => {
    if (error) {
      console.error('Scraper hatası:', error.message);
      await sendSlackMessage(`❌ *Scraper Hatası*\n\n${error.message}`);
      process.exit(1);
    }
    
    try {
      const data = JSON.parse(stdout);
      const siteResults = data.sites;
      
      console.log(`✅ Tarama tamamlandı: ${data.total_products} ürün`);
      
      // Fiyat değişikliklerini tespit et
      const { changes, currentData } = checkPriceUpdates(siteResults);
      
      // Sonuçları göster
      if (changes.length > 0) {
        console.log(`\n💰 ${changes.length} fiyat değişikliği tespit edildi:`);
        changes.forEach(c => {
          const emoji = c.change > 0 ? '📈' : '📉';
          console.log(`${emoji} [${c.site_name}] ${c.name}: ${c.oldPrice}₺ → ${c.newPrice}₺`);
        });
      } else {
        console.log('\n✨ Fiyat değişikliği yok');
      }
      
      // Benchmarking raporu oluştur
      const benchmarkReport = generateBenchmarkingReport(siteResults);
      fs.writeFileSync('./benchmark_report.json', JSON.stringify(benchmarkReport, null, 2));
      console.log('📊 Benchmarking raporu oluşturuldu: benchmark_report.json');
      
      // GitHub rapor linki
      const reportUrl = 'https://github.com/hasansavli-tc17/ciceksepeti-price-monitor/blob/main/benchmark_report.json';
      
      // Slack'e bildir
      await sendPriceChangeNotification(changes, siteResults, reportUrl, benchmarkReport);
      
      // Yeni fiyatları kaydet
      savePrices(currentData);
      console.log('💾 Fiyatlar kaydedildi');
      
    } catch (parseError) {
      console.error('JSON parse hatası:', parseError.message);
      await sendSlackMessage(`❌ *Parse Hatası*\n\n${parseError.message}`);
      process.exit(1);
    }
  });
}

main();

