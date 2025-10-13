const { exec } = require('child_process');
const fs = require('fs');
const https = require('https');

const PRICE_DB_FILE = './price_history.json';
// GitHub Actions'ta environment variable'dan al, yoksa local URL'i kullan
const SLACK_WEBHOOK = process.env.SLACK_WEBHOOK_URL || 'https://hooks.slack.com/services/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';

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
function savePrices(prices) {
  fs.writeFileSync(PRICE_DB_FILE, JSON.stringify(prices, null, 2));
}

// Slack'e bildirim gönder
function sendSlackNotification(changes) {
  if (changes.length === 0) return Promise.resolve();
  
  // Ana mesaj
  const headerMessage = `🌸 *Çiçek Sepeti Fiyat Güncellemesi*\n\n*${changes.length} ürünün fiyatı değişti!*`;
  
  // İlk mesajı gönder
  sendSlackMessage(headerMessage).then(() => {
    // Her ürün için ayrı mesaj gönder (maksimum 5'er)
    for (let i = 0; i < changes.length; i += 5) {
      const batch = changes.slice(i, i + 5);
      let batchMessage = '';
      
      batch.forEach(change => {
        const emoji = change.change > 0 ? '📈' : '📉';
        const changeText = change.change > 0 ? `+${change.change.toFixed(2)}` : change.change.toFixed(2);
        
        batchMessage += `*${change.name}*\n`;
        batchMessage += `• Eski: ${change.oldPrice.toFixed(2)}₺ → Yeni: ${change.newPrice.toFixed(2)}₺\n`;
        batchMessage += `• Fark: ${emoji} ${changeText}₺\n`;
        batchMessage += `<${change.url}|Ürüne Git>\n\n`;
      });
      
      sendSlackMessage(batchMessage);
    }
  });
}

// Tek mesaj gönderen yardımcı fonksiyon
function sendSlackMessage(message) {
  const payload = JSON.stringify({ 
    text: message
  });
  
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

// Ana fonksiyon
async function main() {
  console.log('🔍 Fiyat takibi başlatılıyor...');
  
  // Scraper'ı çalıştır
  console.log('📡 Ürünler çekiliyor...');
  
  exec('node scraper.js', async (error, stdout, stderr) => {
    if (error) {
      console.error('Scraper hatası:', error.message);
      process.exit(1);
    }
    
    try {
      const data = JSON.parse(stdout);
      const currentProducts = data.products;
      
      console.log(`✅ ${currentProducts.length} ürün çekildi`);
      
      // Önceki fiyatları yükle
      const previousPrices = loadPreviousPrices();
      const changes = [];
      const newPrices = {};
      
      // Fiyat değişikliklerini tespit et
      currentProducts.forEach(product => {
        newPrices[product.id] = {
          name: product.name,
          price: product.price,
          url: product.url,
          timestamp: product.timestamp
        };
        
        if (previousPrices[product.id]) {
          const oldPrice = previousPrices[product.id].price;
          if (oldPrice !== product.price) {
            changes.push({
              id: product.id,
              name: product.name,
              oldPrice: oldPrice,
              newPrice: product.price,
              change: product.price - oldPrice,
              url: product.url
            });
          }
        }
      });
      
      // Sonuçları göster
      if (changes.length > 0) {
        console.log(`\n💰 ${changes.length} fiyat değişikliği tespit edildi:`);
        changes.forEach(c => {
          const emoji = c.change > 0 ? '📈' : '📉';
          console.log(`${emoji} ${c.name}: ${c.oldPrice}₺ → ${c.newPrice}₺`);
        });
        
        // Slack'e bildir
        await sendSlackNotification(changes);
      } else {
        console.log('\n✨ Fiyat değişikliği yok');
      }
      
      // Yeni fiyatları kaydet
      savePrices(newPrices);
      console.log('💾 Fiyatlar kaydedildi');
      
    } catch (parseError) {
      console.error('JSON parse hatası:', parseError.message);
      process.exit(1);
    }
  });
}

main();
