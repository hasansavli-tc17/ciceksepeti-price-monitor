const { exec } = require('child_process');
const fs = require('fs');
const https = require('https');

const PRICE_DB_FILE = './price_history.json';
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
function savePrices(prices) {
  fs.writeFileSync(PRICE_DB_FILE, JSON.stringify(prices, null, 2));
}

// Şu anki çalışmanın scheduled job mu yoksa manuel mi olduğunu kontrol et
function isScheduledRun() {
  const scheduledHours = [10, 12, 15, 18];
  const now = new Date();
  const currentHour = now.getUTCHours() + 3; // UTC'den Türkiye saatine çevir
  const currentMinute = now.getMinutes();
  
  // Scheduled saate yakın mıyız? (±10 dakika tolerans)
  return scheduledHours.some(hour => {
    return Math.abs(currentHour - hour) === 0 && currentMinute <= 10;
  });
}

// Son güncelleme zamanının scheduled job'dan mı yoksa manuel mi olduğunu kontrol et
function checkLastUpdateTime(previousPrices) {
  // Scheduled job saatleri (Türkiye saati - UTC+3)
  const scheduledHours = [10, 12, 15, 18];
  
  // İlk ürünün timestamp'ini al
  const firstProduct = Object.values(previousPrices)[0];
  if (!firstProduct || !firstProduct.timestamp) {
    return { wasManual: false };
  }
  
  const lastUpdate = new Date(firstProduct.timestamp);
  const lastUpdateHour = lastUpdate.getUTCHours() + 3; // UTC'den Türkiye saatine çevir
  const lastUpdateMinute = lastUpdate.getMinutes();
  
  // Bir önceki scheduled saati bul
  const currentHour = new Date().getUTCHours() + 3;
  const reversedHours = [...scheduledHours].reverse();
  const previousScheduledHour = reversedHours.find(h => h < currentHour) || scheduledHours[scheduledHours.length - 1];
  
  // Eğer son güncelleme scheduled saate yakın değilse (±10 dakika tolerans)
  const isScheduledTime = scheduledHours.some(hour => {
    return Math.abs(lastUpdateHour - hour) === 0 && lastUpdateMinute <= 10;
  });
  
  if (!isScheduledTime) {
    const timeStr = `${String(lastUpdateHour).padStart(2, '0')}:${String(lastUpdateMinute).padStart(2, '0')}`;
    const expectedTime = `${String(previousScheduledHour).padStart(2, '0')}:00`;
    
    return {
      wasManual: true,
      timeStr: timeStr,
      expectedTime: expectedTime
    };
  }
  
  return { wasManual: false };
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
        
        // Son güncelleme zamanını kontrol et
        const lastUpdateTime = checkLastUpdateTime(previousPrices);
        
        if (lastUpdateTime.wasManual) {
          console.log(`⚠️ Manuel tetikleme tespit edildi: ${lastUpdateTime.timeStr}`);
          console.log(`   Bu nedenle scheduled saat ${lastUpdateTime.expectedTime} kontrolünde fiyat değişikliği görünmedi`);
        }
        
        // Her durumda bildirim gönder
        const noChangeMessage = `🌸 *Çiçek Sepeti Fiyat Taraması Tamamlandı*\n\n✅ ${currentProducts.length} ürün tarandı\n✨ Fiyat değişikliği yok\n🕐 ${new Date().toLocaleString('tr-TR')}`;
        await sendSlackMessage(noChangeMessage);
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
