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
    const headers = ['Site', 'Ürün Adı', 'Fiyat (₺)', 'Kategori', 'URL', 'Son Güncelleme'];
    
    // Data rows
    const turkeyTime = new Date().toLocaleString('tr-TR', { timeZone: 'Europe/Istanbul' });
    const rows = benchmarkData.all_products.map(product => [
      product.site,
      product.name,
      product.price,
      product.category || '-',
      product.url || '-',
      turkeyTime
    ]);

    // Tüm veriyi hazırla
    const values = [headers, ...rows];

    // Sheet'i güncelle
    await sheets.spreadsheets.values.clear({
      spreadsheetId: SPREADSHEET_ID,
      range: 'A1:Z10000',
    });

    await sheets.spreadsheets.values.update({
      spreadsheetId: SPREADSHEET_ID,
      range: 'A1',
      valueInputOption: 'RAW',
      resource: { values },
    });

    // Formatting: Header'ı bold yap
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
                endIndex: 6,
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

module.exports = { syncToGoogleSheets };

