const { google } = require('googleapis');
const fs = require('fs');

// Google Sheets ID (environment variable veya config'den gelecek)
const SPREADSHEET_ID = process.env.GOOGLE_SHEETS_ID || '';

async function syncToGoogleSheets() {
  try {
    // Benchmark raporunu oku
    const benchmarkData = JSON.parse(fs.readFileSync('./benchmark_report.json', 'utf8'));
    
    if (!benchmarkData.all_products || benchmarkData.all_products.length === 0) {
      console.log('⚠️  Ürün bulunamadı, Google Sheets sync atlandı');
      return null;
    }

    // Önceki fiyatları oku
    let priceHistory = { sites: {} };
    try {
      if (fs.existsSync('./multi_site_price_history.json')) {
        priceHistory = JSON.parse(fs.readFileSync('./multi_site_price_history.json', 'utf8'));
      }
    } catch (err) {
      console.log('⚠️  Fiyat geçmişi okunamadı, sadece güncel fiyatlar gösterilecek');
    }

    // Service Account credentials kontrolü
    if (!process.env.GCP_SERVICE_ACCOUNT_KEY && !fs.existsSync('./gcp-key.json')) {
      console.log('⚠️  Google credentials bulunamadı, GitHub Actions üzerinde çalışacak');
      return null;
    }

    // Auth
    let auth;
    if (process.env.GCP_SERVICE_ACCOUNT_KEY) {
      const credentials = JSON.parse(process.env.GCP_SERVICE_ACCOUNT_KEY);
      auth = new google.auth.GoogleAuth({
        credentials,
        scopes: ['https://www.googleapis.com/auth/spreadsheets'],
      });
    } else {
      auth = new google.auth.GoogleAuth({
        keyFile: './gcp-key.json',
        scopes: ['https://www.googleapis.com/auth/spreadsheets'],
      });
    }

    const sheets = google.sheets({ version: 'v4', auth });

    // Sheet yoksa oluştur
    if (!SPREADSHEET_ID) {
      console.log('❌ GOOGLE_SHEETS_ID environment variable bulunamadı');
      console.log('📝 Lütfen bir Google Sheet oluşturup ID\'sini ekleyin');
      return null;
    }

    // Header row
    const headers = ['Site', 'Ürün Adı', 'Güncel Fiyat (₺)', 'Önceki Fiyat (₺)', 'Fark (₺)', 'Fark (%)', 'Kategori', 'URL', 'Son Güncelleme'];
    
    // Data rows
    const turkeyTime = new Date().toLocaleString('tr-TR', { timeZone: 'Europe/Istanbul' });
    const rows = benchmarkData.all_products.map(product => {
      // Önceki fiyatı bul
      let oldPrice = null;
      let priceDiff = null;
      let priceChangePercent = null;
      
      // Site ID'yi product'tan çıkar (sites-config.json'daki id formatına göre)
      const siteId = product.site.toLowerCase()
        .replace(/\s+/g, '')
        .replace(/ç/g, 'c')
        .replace(/ğ/g, 'g')
        .replace(/ı/g, 'i')
        .replace(/ö/g, 'o')
        .replace(/ş/g, 's')
        .replace(/ü/g, 'u');
      
      if (priceHistory.sites && priceHistory.sites[siteId]) {
        const siteProducts = priceHistory.sites[siteId].products;
        // Ürün ID'sini product name'den oluştur
        const productId = product.name.toLowerCase()
          .replace(/[^a-z0-9]+/g, '-')
          .replace(/^-|-$/g, '');
        
        if (siteProducts[productId]) {
          oldPrice = siteProducts[productId].price;
          priceDiff = product.price - oldPrice;
          priceChangePercent = oldPrice > 0 ? ((priceDiff / oldPrice) * 100).toFixed(2) : 0;
        }
      }
      
      return [
        product.site,
        product.name,
        product.price,
        oldPrice !== null ? oldPrice : '-',
        priceDiff !== null ? priceDiff.toFixed(2) : '-',
        priceChangePercent !== null ? priceChangePercent + '%' : '-',
        product.category || '-',
        product.url || '-',
        turkeyTime
      ];
    });

    // Tüm veriyi hazırla
    const values = [headers, ...rows];

    // İlk 91 satırı güncelle (header + 90 ürün)
    await sheets.spreadsheets.values.update({
      spreadsheetId: SPREADSHEET_ID,
      range: 'A1:I91',
      valueInputOption: 'RAW',
      resource: { values },
    });

    // Fiyatı değişen ürünleri alt satırlara ekle
    const changedProducts = rows.filter((row, idx) => {
      const priceDiff = row[4]; // Fark (₺) kolonu
      return priceDiff !== '-' && parseFloat(priceDiff) !== 0;
    });

    if (changedProducts.length > 0) {
      // Değişiklik başlığı ve satırları
      const changeLogHeader = ['', '', '', '', '', '', '', '', ''];
      const changeLogTitle = ['📊 FİYAT DEĞİŞİKLİK GEÇMİŞİ', '', '', '', '', '', '', '', ''];
      const changeLogRows = changedProducts.map(row => row);

      // Alt satırlara ekle (append)
      await sheets.spreadsheets.values.append({
        spreadsheetId: SPREADSHEET_ID,
        range: 'A93', // 91 ürün + 1 boş satır sonrası
        valueInputOption: 'RAW',
        insertDataOption: 'INSERT_ROWS',
        resource: { 
          values: [changeLogHeader, changeLogTitle, ...changeLogRows]
        },
      });
      
      console.log(`📝 ${changedProducts.length} fiyat değişikliği geçmişe eklendi`);
    }

    // Formatting: Header'ı bold yap ve fiyat değişimlerini renklendir
    await sheets.spreadsheets.batchUpdate({
      spreadsheetId: SPREADSHEET_ID,
      resource: {
        requests: [
          {
            repeatCell: {
              range: {
                sheetId: 0,
                startRowIndex: 0,
                endRowIndex: 1,
              },
              cell: {
                userEnteredFormat: {
                  backgroundColor: { red: 0.2, green: 0.6, blue: 0.86 },
                  textFormat: { bold: true, foregroundColor: { red: 1, green: 1, blue: 1 } },
                  horizontalAlignment: 'CENTER',
                },
              },
              fields: 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)',
            },
          },
          {
            autoResizeDimensions: {
              dimensions: {
                sheetId: 0,
                dimension: 'COLUMNS',
                startIndex: 0,
                endIndex: 9,
              },
            },
          },
        ],
      },
    });

    const sheetUrl = `https://docs.google.com/spreadsheets/d/${SPREADSHEET_ID}`;
    console.log(`✅ Google Sheets güncellendi: ${rows.length} ürün`);
    console.log(`🔗 ${sheetUrl}`);
    
    return sheetUrl;

  } catch (error) {
    console.error('❌ Google Sheets sync hatası:', error.message);
    return null;
  }
}

// Kokina benchmark'ını ayrı bir sayfaya (Kokina tabı) yaz
async function syncKokinaToGoogleSheets() {
  try {
    // Benchmark raporunu oku
    const benchmarkData = JSON.parse(fs.readFileSync('./kokina_benchmark_report.json', 'utf8'));
    
    if (!benchmarkData.all_products || benchmarkData.all_products.length === 0) {
      console.log('⚠️  Kokina ürünü bulunamadı, Google Sheets sync atlandı');
      return null;
    }

    // Fiyat geçmişi (kokina için ayrı dosya)
    let priceHistory = { sites: {} };
    try {
      if (fs.existsSync('./kokina_price_history.json')) {
        priceHistory = JSON.parse(fs.readFileSync('./kokina_price_history.json', 'utf8'));
      }
    } catch (err) {
      console.log('⚠️  Kokina fiyat geçmişi okunamadı, sadece güncel fiyatlar gösterilecek');
    }

    // Service Account credentials kontrolü
    if (!process.env.GCP_SERVICE_ACCOUNT_KEY && !fs.existsSync('./gcp-key.json')) {
      console.log('⚠️  Google credentials bulunamadı, GitHub Actions üzerinde çalışacak');
      return null;
    }

    // Auth
    let auth;
    if (process.env.GCP_SERVICE_ACCOUNT_KEY) {
      const credentials = JSON.parse(process.env.GCP_SERVICE_ACCOUNT_KEY);
      auth = new google.auth.GoogleAuth({
        credentials,
        scopes: ['https://www.googleapis.com/auth/spreadsheets'],
      });
    } else {
      auth = new google.auth.GoogleAuth({
        keyFile: './gcp-key.json',
        scopes: ['https://www.googleapis.com/auth/spreadsheets'],
      });
    }

    const sheets = google.sheets({ version: 'v4', auth });

    // Sheet yoksa oluştur
    if (!SPREADSHEET_ID) {
      console.log('❌ GOOGLE_SHEETS_ID environment variable bulunamadı');
      console.log('📝 Lütfen bir Google Sheet oluşturup ID\'sini ekleyin');
      return null;
    }

    const sheetName = 'Kokina';

    // Header row
    const headers = ['Site', 'Ürün Adı', 'Güncel Fiyat (₺)', 'Önceki Fiyat (₺)', 'Fark (₺)', 'Fark (%)', 'Kategori', 'URL', 'Son Güncelleme'];
    
    // Data rows
    const turkeyTime = new Date().toLocaleString('tr-TR', { timeZone: 'Europe/Istanbul' });
    const rows = benchmarkData.all_products.map(product => {
      // Önceki fiyatı bul (kokina history üzerinden)
      let oldPrice = null;
      let priceDiff = null;
      let priceChangePercent = null;
      
      const siteId = (product.site || '').toLowerCase()
        .replace(/\s+/g, '')
        .replace(/ç/g, 'c')
        .replace(/ğ/g, 'g')
        .replace(/ı/g, 'i')
        .replace(/ö/g, 'o')
        .replace(/ş/g, 's')
        .replace(/ü/g, 'u');
      
      if (priceHistory.sites && priceHistory.sites[siteId]) {
        const siteProducts = priceHistory.sites[siteId].products || {};
        const productId = (product.name || '').toLowerCase()
          .replace(/[^a-z0-9]+/g, '-')
          .replace(/^-|-$/g, '');
        
        if (siteProducts[productId]) {
          oldPrice = siteProducts[productId].price;
          priceDiff = product.price - oldPrice;
          priceChangePercent = oldPrice > 0 ? ((priceDiff / oldPrice) * 100).toFixed(2) : 0;
        }
      }
      
      return [
        product.site,
        product.name,
        product.price,
        oldPrice !== null ? oldPrice : '-',
        priceDiff !== null ? priceDiff.toFixed(2) : '-',
        priceChangePercent !== null ? priceChangePercent + '%' : '-',
        product.category || '-', // Burada Görünür/Gizli etiketi geliyor
        product.url || '-',
        turkeyTime
      ];
    });

    const values = [headers, ...rows];

    // İlk 91 satırı güncelle (header + 90 ürün) - Kokina tabında
    await sheets.spreadsheets.values.update({
      spreadsheetId: SPREADSHEET_ID,
      range: `${sheetName}!A1:I91`,
      valueInputOption: 'RAW',
      resource: { values },
    });

    // Fiyatı değişen ürünleri alt satırlara ekle
    const changedProducts = rows.filter((row) => {
      const priceDiff = row[4]; // Fark (₺) kolonu
      return priceDiff !== '-' && parseFloat(priceDiff) !== 0;
    });

    if (changedProducts.length > 0) {
      const changeLogHeader = ['', '', '', '', '', '', '', '', ''];
      const changeLogTitle = ['🎄 KOKİNA FİYAT DEĞİŞİKLİK GEÇMİŞİ', '', '', '', '', '', '', '', ''];
      const changeLogRows = changedProducts.map(row => row);

      await sheets.spreadsheets.values.append({
        spreadsheetId: SPREADSHEET_ID,
        range: `${sheetName}!A93`,
        valueInputOption: 'RAW',
        insertDataOption: 'INSERT_ROWS',
        resource: { 
          values: [changeLogHeader, changeLogTitle, ...changeLogRows]
        },
      });

      console.log(`📝 Kokina için ${changedProducts.length} fiyat değişikliği geçmişe eklendi`);
    }

    const sheetUrl = `https://docs.google.com/spreadsheets/d/${SPREADSHEET_ID}`;
    console.log(`✅ Kokina Google Sheets güncellendi: ${rows.length} ürün`);
    console.log(`🔗 ${sheetUrl}`);
    
    return sheetUrl;

  } catch (error) {
    console.error('❌ Kokina Google Sheets sync hatası:', error.message);
    return null;
  }
}

// Eğer direkt çalıştırılırsa
if (require.main === module) {
  syncToGoogleSheets()
    .then(url => {
      if (url) {
        console.log('🎉 Sync başarılı!');
      }
      process.exit(0);
    })
    .catch(err => {
      console.error('Hata:', err);
      process.exit(1);
    });
}

module.exports = { syncToGoogleSheets, syncKokinaToGoogleSheets };

      