# 🌸 Multi-Site Çiçek Fiyat Benchmarking Sistemi

Bu sistem Türkiye'deki önde gelen çiçek sitelerinden fiyat verilerini toplayıp karşılaştırmalı analiz yapar.

## 🎯 Özellikler

- ✅ **9 Farklı Site:** ÇiçekSepeti, Hızlı Çiçek, Heryerbitki, İstanbul Çiçekleri, Osevio, Lilyana Flowers, Bloom & Fresh, Çiçek Diyarı, RoseBox
- ✅ **Her Siteden Top 10 Ürün:** Toplam 90 ürün takibi
- ✅ **Otomatik Kategori Tespiti:** Gül, Orkide, Papatya, Lilyum, Gerbera, vb.
- ✅ **Fiyat Değişikliği Bildirimleri:** Slack entegrasyonu
- ✅ **İnteraktif Dashboard:** Streamlit tabanlı görsel analiz
- ✅ **BigQuery Entegrasyonu:** Veri saklama ve analiz
- ✅ **GitHub Actions:** 7/24 otomatik çalışma

## 📋 Sistem Bileşenleri

### 1. **sites-config.json**
Tüm sitelerin ayarları, selector'ları ve pagination bilgileri

### 2. **multi-site-scraper.js**
Universal Puppeteer scraper - tüm siteleri tarar

### 3. **multi-site-price-monitor.js**
Fiyat değişikliklerini tespit eder ve bildirim gönderir

### 4. **benchmarking_dashboard.py**
Streamlit dashboard - görsel analiz ve karşılaştırma

### 5. **bigquery_sync.py**
Verileri BigQuery'ye senkronize eder

## 🚀 Kurulum

### Ön Gereksinimler

```bash
# Node.js bağımlılıkları
npm install

# Python bağımlılıkları
pip install -r requirements.txt
```

### Gerekli Paketler

**Node.js:**
- puppeteer
- puppeteer-extra
- puppeteer-extra-plugin-stealth

**Python:**
- streamlit
- plotly
- pandas
- google-cloud-bigquery

## 🎮 Kullanım

### Manuel Test

```bash
# 1. Tüm siteleri tara
node multi-site-scraper.js

# 2. Fiyat takibi ve bildirimi
SLACK_WEBHOOK_URL=your_webhook node multi-site-price-monitor.js

# 3. Dashboard'u başlat
streamlit run benchmarking_dashboard.py

# 4. BigQuery'ye senkronize et (opsiyonel)
python bigquery_sync.py
```

### Test Modu

```bash
# Test için sadece ÇiçekSepeti'ni çalıştır
node scraper.js
```

## 📊 Dashboard Özellikleri

Dashboard'a erişim: `http://localhost:8501`

### Tab'lar:

1. **📊 Site Karşılaştırma**
   - Site bazında ortalama, minimum, maksimum fiyatlar
   - Ürün dağılımı (pie chart)
   - Detaylı site istatistikleri

2. **🎨 Kategori Analizi**
   - Kategorilere göre ortalama fiyatlar
   - Site bazında kategori karşılaştırması
   - Detaylı kategori istatistikleri

3. **🔥 Heatmap**
   - Site ve kategori bazında fiyat haritası
   - Görsel karşılaştırma

4. **📋 Detaylı Tablo**
   - Tüm ürünlerin listesi
   - Filtreleme ve sıralama
   - Doğrudan ürün linklerine erişim

### Filtreler:
- Site seçimi
- Kategori seçimi
- Fiyat sıralaması

## 🤖 GitHub Actions

### Otomatik Çalışma Zamanları (Türkiye Saati)
- 10:00
- 13:00
- 16:00
- 19:00
- 22:00

### Gerekli Secrets

Repository Settings > Secrets > Actions'a ekle:

1. **SLACK_WEBHOOK_URL** (Zorunlu)
   - Slack bildirimleri için
   - Slack webhook URL'i

2. **GCP_PROJECT_ID** (Opsiyonel)
   - BigQuery entegrasyonu için
   - Google Cloud Project ID

3. **GCP_SERVICE_ACCOUNT_KEY** (Opsiyonel)
   - BigQuery entegrasyonu için
   - Service account JSON key (base64 encoded değil, direkt JSON)

### Manuel Çalıştırma

GitHub Actions sekmesinde "Multi-Site Price Monitor" workflow'unu seç ve "Run workflow" butonuna tıkla.

## 📁 Dosya Yapısı

```
├── .github/workflows/
│   └── multi-site-monitor.yml     # GitHub Actions workflow
├── sites-config.json               # Site konfigürasyonları
├── multi-site-scraper.js          # Universal scraper
├── multi-site-price-monitor.js    # Fiyat takip ana script
├── benchmarking_dashboard.py      # Streamlit dashboard
├── bigquery_sync.py               # BigQuery senkronizasyon
├── multi_site_price_history.json  # Fiyat geçmişi (otomatik oluşur)
├── benchmark_report.json          # Analiz raporu (otomatik oluşur)
└── package.json                   # Node.js dependencies
```

## 🔧 Yeni Site Ekleme

`sites-config.json` dosyasına yeni site ekle:

```json
{
  "id": "yenisite",
  "name": "Yeni Site",
  "url": "https://www.yenisite.com",
  "category_url": "https://www.yenisite.com/cicekler",
  "enabled": true,
  "scraper_type": "puppeteer",
  "selectors": {
    "product_box": ".product-item, .product-card",
    "product_name": ".product-title, .product-name",
    "product_price": ".product-price, .price",
    "product_link": "a[href]"
  },
  "pagination": {
    "enabled": true,
    "max_pages": 2,
    "url_pattern": "https://www.yenisite.com/cicekler?page={page}"
  }
}
```

### Selector Bulma İpuçları:

1. Siteyi tarayıcıda aç
2. F12 ile DevTools'u aç
3. Ürün kartını seç (Inspect)
4. HTML yapısını incele
5. Ürün kutusu, isim, fiyat ve link için selector'ları belirle
6. Birden fazla selector ekleyebilirsin (virgülle ayır)

## 📈 BigQuery Entegrasyonu

### Setup:

1. **Google Cloud Project Oluştur**
   - https://console.cloud.google.com
   - Yeni proje oluştur

2. **BigQuery API'yi Aktifleştir**
   - APIs & Services > Enable APIs
   - BigQuery API'yi aktif et

3. **Service Account Oluştur**
   - IAM & Admin > Service Accounts
   - Create Service Account
   - Role: BigQuery Admin
   - JSON key oluştur ve indir

4. **GitHub Secrets'a Ekle**
   ```
   GCP_PROJECT_ID: your-project-id
   GCP_SERVICE_ACCOUNT_KEY: {JSON key içeriği}
   ```

### BigQuery Tabloları:

1. **products** - Ürün bilgileri
2. **price_history** - Fiyat geçmişi (partitioned by date)
3. **benchmarks** - Günlük benchmark metrikleri

### Örnek Sorgular:

```sql
-- Son 7 günün fiyat trendleri
SELECT 
  site_name,
  DATE(date) as date,
  AVG(avg_price) as avg_price
FROM `project.flower_pricing.benchmarks`
WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
GROUP BY site_name, date
ORDER BY date DESC, site_name;

-- En çok fiyat değişen ürünler
SELECT 
  p.product_name,
  p.site_name,
  MIN(ph.price) as min_price,
  MAX(ph.price) as max_price,
  MAX(ph.price) - MIN(ph.price) as price_difference
FROM `project.flower_pricing.products` p
JOIN `project.flower_pricing.price_history` ph 
  ON p.product_id = ph.product_id
WHERE ph.date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY p.product_name, p.site_name
HAVING price_difference > 0
ORDER BY price_difference DESC
LIMIT 20;
```

## 🎨 Slack Bildirimleri

### Bildirim Tipleri:

1. **Fiyat Değişikliği Bildirimi**
   - Hangi sitede kaç ürün değişti
   - Site bazında detaylı değişiklikler
   - Eski fiyat → Yeni fiyat
   - Değişim miktarı ve yönü (📈/📉)

2. **Tarama Tamamlandı Bildirimi**
   - Taranan site sayısı
   - Kontrol edilen ürün sayısı
   - Değişiklik yoksa bilgi mesajı

3. **Benchmarking Özeti** (değişiklik yoksa)
   - Site bazında ürün sayıları
   - Ortalama, minimum, maksimum fiyatlar

## 🐛 Sorun Giderme

### Scraper Çalışmıyor

1. **Cloudflare Challenge:**
   - `sites-config.json` içinde `wait_after_load` süresini artır
   - Puppeteer stealth plugin aktif

2. **Selector Bulunamıyor:**
   - Site yapısı değişmiş olabilir
   - DevTools ile yeni selector'ları bul
   - `sites-config.json` dosyasını güncelle

3. **Timeout Hataları:**
   - `timeout` değerini artır (default: 60000ms)
   - İnternet bağlantısını kontrol et

### Dashboard Açılmıyor

```bash
# Port kullanımda mı kontrol et
lsof -i :8501

# Farklı port kullan
streamlit run benchmarking_dashboard.py --server.port 8502
```

### BigQuery Hatası

1. **Authentication Error:**
   - Service account key'i kontrol et
   - Doğru project ID kullanıldığından emin ol

2. **Permission Denied:**
   - Service account'a BigQuery Admin rolü ver
   - Dataset'in location'ını kontrol et

## 📊 Performans

- **Tek site tarama süresi:** ~20-30 saniye
- **9 site toplam:** ~5-6 dakika
- **Dashboard yükleme:** < 2 saniye
- **BigQuery sync:** ~10-15 saniye

## 🔒 Güvenlik

- ✅ Webhook URL'leri environment variable olarak
- ✅ BigQuery credentials GitHub Secrets'ta
- ✅ Service account ile sınırlı erişim
- ✅ Hassas bilgi commit edilmiyor

## 📝 Notlar

- Her site için maksimum 10 ürün alınır
- Fiyat değişiklikleri otomatik tespit edilir
- Kategori tespiti ürün adına göre yapılır
- Dashboard verileri 5 dakikada bir güncellenir (cache)

## 🤝 Katkıda Bulunma

Yeni site eklemek veya özellik geliştirmek için:

1. Fork yapın
2. Feature branch oluşturun
3. Değişikliklerinizi commit edin
4. Pull request gönderin

## 📞 İletişim

Sorularınız için issue açabilirsiniz.

---

**Yapım:** Multi-Site Price Monitoring System v1.0
**Tarih:** 2025

