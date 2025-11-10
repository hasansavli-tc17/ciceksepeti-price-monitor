const puppeteer = require('puppeteer');
const { google } = require('googleapis');

let CATEGORY_SOURCES = [
  // Çiçek ana kategorileri
  { name: 'Çiçek Buketleri', url: 'https://www.ciceksepeti.com/d/cicek-buketleri' },
  { name: 'Güller', url: 'https://www.ciceksepeti.com/gul' },
  { name: 'Orkideler', url: 'https://www.ciceksepeti.com/orkide' },
  { name: 'Saksı Çiçekleri', url: 'https://www.ciceksepeti.com/saksi-cicekleri' },
  { name: 'Papatyalar', url: 'https://www.ciceksepeti.com/papatya' },
  { name: 'Laleler', url: 'https://www.ciceksepeti.com/lale' },
  { name: 'Gerberalar', url: 'https://www.ciceksepeti.com/gerbera' },
  // Hediyeler
  { name: 'Hediyeler - Genel', url: 'https://www.ciceksepeti.com/hediye' },
  { name: 'Kişiye Özel Hediyeler', url: 'https://www.ciceksepeti.com/kisiye-ozel-hediyeler' },
  { name: 'Çikolata & Lezzet', url: 'https://www.ciceksepeti.com/cikolata' },
];

// Tek kategori modu (ENV ile): CATEGORY_URL ve CATEGORY_NAME verilirse sadece onu işle
if (process.env.CATEGORY_URL) {
  CATEGORY_SOURCES = [{ name: process.env.CATEGORY_NAME || 'Kategori', url: process.env.CATEGORY_URL }];
}

async function discoverHomepageCategories(page) {
  try {
    await page.goto('https://www.ciceksepeti.com/', { waitUntil: 'networkidle2', timeout: 90000 });
    await new Promise(r => setTimeout(r, 1500));
    const cats = await page.evaluate(() => {
      const chips = Array.from(document.querySelectorAll('a[href^="/"], a[href^="https://www.ciceksepeti.com/"]'));
      const wanted = ['çok satanlar','yenilebilir','kişiye özel','premium','gürme','gürme lezzet','aynı gün','doğum günü','orkide','geçmiş olsun'];
      const list = [];
      for (const a of chips) {
        const text = (a.textContent || '').trim().toLowerCase();
        if (!text) continue;
        if (wanted.some(w => text.includes(w))) {
          const href = a.getAttribute('href');
          const url = href.startsWith('http') ? href : `https://www.ciceksepeti.com${href}`;
          list.push({ name: a.textContent.trim(), url });
        }
      }
      // benzersiz
      const m = new Map();
      list.forEach(i => { if (!m.has(i.url)) m.set(i.url, i); });
      return Array.from(m.values());
    });
    if (cats.length) {
      // Sadece istenen başlıkları önceliklendir
      const prioritized = ['Çok Satanlar','Yenilebilir Çiçek','Doğum Günü','Orkide / Saksı Çiçekleri','Hediye','Kişiye Özel','Hediye Setleri','El Yapımı Hediye','Orkide','Geçmiş Olsun'];
      const sorted = [];
      for (const name of prioritized) {
        const found = cats.find(c => (c.name || '').toLowerCase().includes(name.toLowerCase()));
        if (found) sorted.push(found);
      }
      CATEGORY_SOURCES = sorted.length ? sorted : [...CATEGORY_SOURCES, ...cats];
      console.error(`Anasayfa başlıkları bulundu: ${cats.map(c=>c.name).join(', ')}`);
    }
  } catch (e) {
    console.error('Anasayfa keşfi hatası:', e.message);
  }
}

async function scrapeCategory(page, category) {
  const limitPerCategory = Number(process.env.LIMIT_PER_CATEGORY || 20);
  const url = category.url;
  try {
    await page.goto(url, { waitUntil: 'networkidle2', timeout: 90000 });
  } catch (e) {
    console.error(`Sayfa açma hatası (${category.name}):`, e.message);
    return [];
  }
  for (let i = 0; i < 8; i++) {
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await new Promise(r => setTimeout(r, 800));
  }
  const products = await page.evaluate((categoryName, limit) => {
    function pickText(el, selectors) {
      for (const sel of selectors) {
        const n = el.querySelector(sel);
        if (n && n.textContent) return n.textContent.trim();
      }
      return '';
    }
    const cards = Array.from(document.querySelectorAll('[data-cs-product-box="true"], a.product__anchor, a[href*="/p/"], a[data-product-id], .products__grid a'));
    const rows = [];
    for (let i = 0; i < cards.length && rows.length < limit; i++) {
      const el = cards[i];
      const href = el.getAttribute('href') || (el.closest('a') && el.closest('a').getAttribute('href')) || '';
      const url = href ? (href.startsWith('http') ? href : `https://www.ciceksepeti.com${href}`) : '';
      if (!url) continue;
      const title = pickText(el, ['[data-cs-pb-name="true"]', '.product__title', '[itemprop="name"]', 'h3', 'h2', '.title', '.name']);
      const priceText = pickText(el, ['[data-cs-pb-price-text="true"]', '.price__integer-value', '.price__integer-val', '.price__value', '.price', '[data-price]']);
      const numMatch = (priceText.match(/[0-9.,]+/) || ['0'])[0];
      const price = parseFloat(numMatch.replace(/\./g, '').replace(',', '.')) || 0;
      const id = href.split('-').pop() || `p_${i}`;
      if (title && price > 0) rows.push({ id, name: title, price, url, category: categoryName });
    }
    return rows;
  }, category.name, limitPerCategory);
  console.error(`Kategori ${category.name}: ${products.length} ürün`);
  return products;
}

async function scrapeAll() {
  const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  const page = await browser.newPage();
  await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
  page.setDefaultTimeout(90000);
  page.setDefaultNavigationTimeout(90000);

  await discoverHomepageCategories(page);
  const results = [];
  for (const cat of CATEGORY_SOURCES) {
    try {
      const prods = await scrapeCategory(page, cat);
      results.push(...prods);
      console.error(`Kategori ${cat.name}: ${prods.length} ürün`);
    } catch (e) {
      console.error(`Kategori hatası (${cat.name}):`, e.message);
    }
  }
  await browser.close();
  return results;
}

async function writeToSheets(rows) {
  const sheetId = process.env.SHEET_ID;
  const credentialsPath = process.env.GOOGLE_SHEETS_CREDENTIALS_PATH;
  const tab = process.env.SHEET_TAB || 'Catalog';
  if (!sheetId || !credentialsPath) throw new Error('SHEET_ID veya GOOGLE_SHEETS_CREDENTIALS_PATH eksik');

  const auth = new google.auth.GoogleAuth({ keyFile: credentialsPath, scopes: ['https://www.googleapis.com/auth/spreadsheets'] });
  const sheets = google.sheets({ version: 'v4', auth });

  // Sekme yoksa oluştur
  try {
    const meta = await sheets.spreadsheets.get({ spreadsheetId: sheetId });
    const exists = (meta.data.sheets || []).some(s => (s.properties && s.properties.title) === tab);
    if (!exists) {
      await sheets.spreadsheets.batchUpdate({
        spreadsheetId: sheetId,
        requestBody: { requests: [{ addSheet: { properties: { title: tab } } }] },
      });
    }
  } catch (e) {
    console.error('Sheet tab kontrol/oluşturma hatası:', e.message);
  }

  // Başlık satırı
  const header = [['Timestamp', 'Category', 'Product ID', 'Product name', 'Price', 'Product Link']];
  await sheets.spreadsheets.values.update({
    spreadsheetId: sheetId,
    range: `${tab}!A1:F1`,
    valueInputOption: 'USER_ENTERED',
    requestBody: { values: header },
  });

  // Veriler
  const now = new Date().toISOString();
  const values = rows.map(r => [now, r.category, r.id, r.name, r.price, r.url]);
  if (values.length === 0) return;
  await sheets.spreadsheets.values.update({
    spreadsheetId: sheetId,
    range: `${tab}!A2:F${values.length + 1}`,
    valueInputOption: 'USER_ENTERED',
    requestBody: { values },
  });
}

async function main() {
  console.log('📦 Katalog taraması başlıyor...');
  const all = await scrapeAll();
  console.log(`✅ Toplam ürün: ${all.length}`);
  await writeToSheets(all);
  console.log('📄 Google Sheets Catalog güncellendi');
}

main().catch(e => { console.error('Hata:', e.message); process.exit(1); });


