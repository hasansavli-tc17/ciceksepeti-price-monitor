const { exec } = require('child_process');
const fs = require('fs');
const https = require('https');

const PRICE_DB_FILE = './price_history.json';
// GitHub Actions'ta environment variable'dan al
const SLACK_WEBHOOK = process.env.SLACK_WEBHOOK_URL;

if (!SLACK_WEBHOOK) {
  console.error('❌ HATA: SLACK_WEBHOOK_URL environment variable tanımlanmamış!');
  console.error('Kullanım: SLACK_WEBHOOK_URL=your_webhook_url node price_monitor_github.js');
  process.exit(1);
}

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
async function sendSlackNotification(changes) {
  if (changes.length === 0) return;
  
  // Ana mesaj
  const headerMessage = `🌸 *Çiçek Sepeti Fiyat Güncellemesi*\n\n*${changes.length} ürünün fiyatı değişti!*`;
  
  try {
    // İlk mesajı gönder
    await sendSlackMessage(headerMessage);
    
    // Her ürün için ayrı mesaj gönder (maksimum 5'er) - hepsini paralel gönder
    const messagePromises = [];
    
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
      
      messagePromises.push(sendSlackMessage(batchMessage));
    }
    
    // Tüm mesajların gönderilmesini bekle
    await Promise.all(messagePromises);
    console.log(`✅ ${messagePromises.length + 1} Slack mesajı gönderildi`);
    
  } catch (error) {
    console.error('❌ Slack bildirim hatası:', error.message);
    throw error;
  }
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
      
      // Test modu kontrolü
      const TEST_MODE = process.env.TEST_MODE === 'true';
      
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
      
      // Test modu: Eğer değişiklik yoksa yapay bir tane oluştur
      if (TEST_MODE && changes.length === 0 && currentProducts.length > 0) {
        const testProduct = currentProducts[0];
        const fakeOldPrice = testProduct.price + 50;
        changes.push({
          id: testProduct.id,
          name: testProduct.name + ' (TEST)',
          oldPrice: fakeOldPrice,
          newPrice: testProduct.price,
          change: testProduct.price - fakeOldPrice,
          url: testProduct.url
        });
        console.log('🧪 Test modu: Yapay fiyat değişikliği oluşturuldu');
      }
      
      // Sonuçları göster
      if (changes.length > 0) {
        console.log(`\n💰 ${changes.length} fiyat değişikliği tespit edildi:`);
        changes.forEach(c => {
          const emoji = c.change > 0 ? '📈' : '📉';
          console.log(`${emoji} ${c.name}: ${c.oldPrice}₺ → ${c.newPrice}₺`);
        });
        
        // Slack'e bildir
        try {
          await sendSlackNotification(changes);
        } catch (slackError) {
          console.error('❌ Slack bildirim gönderilirken hata:', slackError.message);
          // Slack hatası olsa bile devam et
        }
      } else {
        console.log('\n✨ Fiyat değişikliği yok');
      }
      
      // Yeni fiyatları kaydet (test modunda kaydetme)
      if (!TEST_MODE) {
        savePrices(newPrices);
        console.log('💾 Fiyatlar kaydedildi');
      } else {
        console.log('🧪 Test modu: Fiyatlar kaydedilmedi');
      }
      
    } catch (parseError) {
      console.error('JSON parse hatası:', parseError.message);
      process.exit(1);
    }
  });
}

main();
