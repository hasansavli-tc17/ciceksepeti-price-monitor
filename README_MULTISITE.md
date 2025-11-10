# 🌸 Multi-Site Çiçek Fiyat Benchmarking & Monitoring

**Türkiye'nin ilk ve en kapsamlı çiçek fiyat karşılaştırma ve takip sistemi!**

9 farklı çiçek sitesinden günlük fiyat verilerini toplayıp analiz eder, fiyat değişikliklerini bildirir ve interaktif dashboard ile görselleştirir.

---

## 🎯 Özellikler

### 🏪 Multi-Site Desteği
- ✅ **9 Site:** ÇiçekSepeti, Hızlı Çiçek, Heryerbitki, İstanbul Çiçekleri, Osevio, Lilyana Flowers, Bloom & Fresh, Çiçek Diyarı, RoseBox
- ✅ **90 Ürün:** Her siteden top 10 ürün
- ✅ **Universal Scraper:** Tek scraper ile tüm siteler

### 📊 Benchmarking & Analiz
- ✅ **Fiyat Karşılaştırma:** Site bazında min/max/avg
- ✅ **Kategori Analizi:** Gül, Orkide, Papatya, vb.
- ✅ **Heatmap Görselleştirme:** Site × Kategori
- ✅ **İnteraktif Dashboard:** Streamlit tabanlı

### 🔔 Bildirimler & Takip
- ✅ **Otomatik Fiyat Takibi:** Günde 5 kez
- ✅ **Slack Bildirimleri:** Fiyat değişikliklerinde anında
- ✅ **Site Bazında Raporlama:** Detaylı bildirimler
- ✅ **No-Change Alerts:** Değişiklik yoksa da bilgilendirme

### 🗄️ Veri Yönetimi
- ✅ **BigQuery Entegrasyonu:** Cloud veri depolama
- ✅ **Tarihsel Veri:** Fiyat geçmişi tracking
- ✅ **JSON Export:** Yerel veri kayıt
- ✅ **GitHub Actions:** Otomatik backup

---

## 🚀 Hızlı Başlangıç

### 1️⃣ Kurulum

```bash
# Repository'yi clone et
git clone <your-repo>
cd n8n-tazecicek

# Node.js bağımlılıkları
npm install

# Python bağımlılıkları
pip install -r requirements.txt
```

### 2️⃣ İlk Çalıştırma

```bash
# Test taraması (tüm siteler)
node multi-site-scraper.js

# Fiyat monitörü (Slack webhook gerekli)
SLACK_WEBHOOK_URL=your_webhook_url node multi-site-price-monitor.js

# Dashboard'u aç
streamlit run benchmarking_dashboard.py
```

### 3️⃣ Dashboard'a Erişim

Tarayıcıda: **http://localhost:8501**

---

## 📊 Dashboard Önizleme

### Site Karşılaştırma
- Bar chart: Ortalama/Min/Max fiyatlar
- Pie chart: Ürün dağılımı
- Detaylı site metrikleri

### Kategori Analizi
- Kategorilere göre fiyat ortalamaları
- Site bazında kategori karşılaştırması
- Kategori istatistikleri

### Heatmap
- Site × Kategori fiyat haritası
- Renkli görsel karşılaştırma

### Detaylı Tablo
- Tüm ürünler listesi
- Filtreleme (site, kategori)
- Sıralama (fiyat, site, kategori)
- Direkt link erişimi

---

## 🤖 GitHub Actions - Otomatik Çalıştırma

### Çalışma Zamanları (Türkiye Saati)
- 🕙 **10:00** - Sabah kontrolü
- 🕐 **13:00** - Öğle kontrolü
- 🕓 **16:00** - Öğleden sonra kontrolü
- 🕖 **19:00** - Akşam kontrolü
- 🕚 **22:00** - Gece kontrolü

### Gerekli GitHub Secrets

**Repository Settings → Secrets and variables → Actions → New repository secret**

| Secret | Zorunluluk | Açıklama |
|--------|-----------|----------|
| `SLACK_WEBHOOK_URL` | ✅ Zorunlu | Slack bildirim webhook URL'i |
| `GCP_PROJECT_ID` | ⚡ Opsiyonel | BigQuery için Google Cloud Project ID |
| `GCP_SERVICE_ACCOUNT_KEY` | ⚡ Opsiyonel | BigQuery için Service Account JSON key |

---

## 🎨 Site Konfigürasyonu

### Yeni Site Ekleme

`sites-config.json` dosyasını düzenle:

```json
{
  "id": "yenisite",
  "name": "Yeni Site",
  "url": "https://www.yenisite.com",
  "category_url": "https://www.yenisite.com/cicekler",
  "enabled": true,
  "scraper_type": "puppeteer",
  "selectors": {
    "product_box": ".product, .product-item",
    "product_name": ".title, .name",
    "product_price": ".price, .product-price",
    "product_link": "a[href]"
  },
  "pagination": {
    "enabled": true,
    "max_pages": 2,
    "url_pattern": "https://www.yenisite.com/cicekler?page={page}"
  }
}
```

### Selector Bulma İpuçları

1. **F12** ile DevTools'u aç
2. **Elements** sekmesine git
3. Ürün kartını **Inspect** et
4. Ürün kutusu, isim, fiyat için selector'ları belirle
5. Birden fazla olası selector ekle (virgülle ayır)

**Örnek:**
```json
"product_box": ".product-item, .product-card, [data-product]"
```

---

## 📈 BigQuery Entegrasyonu

### Setup Adımları

#### 1. Google Cloud Project Oluştur
- https://console.cloud.google.com
- "New Project" → Proje adı gir

#### 2. BigQuery API'yi Aktifleştir
- APIs & Services → Library
- "BigQuery API" ara → Enable

#### 3. Service Account Oluştur
- IAM & Admin → Service Accounts
- Create Service Account
  - Name: `flower-pricing-sync`
  - Role: **BigQuery Admin**
- Create Key → JSON → Download

#### 4. GitHub Secrets'a Ekle
```
GCP_PROJECT_ID: your-project-id
GCP_SERVICE_ACCOUNT_KEY: {paste entire JSON content}
```

### BigQuery Tabloları

Otomatik oluşturulan tablolar:

| Tablo | Açıklama | Partition |
|-------|----------|-----------|
| `products` | Ürün bilgileri | - |
| `price_history` | Fiyat geçmişi | ✅ By date |
| `benchmarks` | Günlük metrikler | ✅ By date |

### Örnek Sorgular

**Son 7 günün fiyat trendi:**
```sql
SELECT 
  site_name,
  DATE(date) as date,
  AVG(avg_price) as avg_price
FROM `your-project.flower_pricing.benchmarks`
WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
GROUP BY site_name, date
ORDER BY date DESC;
```

**En volatil ürünler (en çok fiyat değişen):**
```sql
SELECT 
  p.product_name,
  p.site_name,
  MIN(ph.price) as min_price,
  MAX(ph.price) as max_price,
  MAX(ph.price) - MIN(ph.price) as volatility
FROM `your-project.flower_pricing.products` p
JOIN `your-project.flower_pricing.price_history` ph 
  ON p.product_id = ph.product_id
WHERE ph.date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY p.product_name, p.site_name
HAVING volatility > 0
ORDER BY volatility DESC
LIMIT 20;
```

---

## 📁 Dosya Yapısı

```
n8n-tazecicek/
├── 📄 sites-config.json              # Site konfigürasyonları
├── 🤖 multi-site-scraper.js          # Universal scraper
├── 💰 multi-site-price-monitor.js    # Fiyat takip ana script
├── 📊 benchmarking_dashboard.py      # Streamlit dashboard
├── 🗄️ bigquery_sync.py               # BigQuery senkronizasyon
├── 📈 multi_site_price_history.json  # Fiyat geçmişi (auto)
├── 📋 benchmark_report.json          # Analiz raporu (auto)
├── 📦 package.json                   # Node.js dependencies
├── 🐍 requirements.txt               # Python dependencies
├── 📖 MULTI_SITE_SETUP.md           # Detaylı setup guide
└── .github/workflows/
    └── multi-site-monitor.yml        # GitHub Actions workflow
```

---

## 🔔 Slack Bildirim Örnekleri

### Fiyat Değişikliği
```
🌸 Multi-Site Fiyat Güncellemesi

*12 ürünün fiyatı değişti!*
📊 3 sitede değişiklik var

🏪 Çiçek Sepeti - 5 değişiklik

*Kırmızı Gül Buketi*
• Eski: 299.99₺ → Yeni: 279.99₺
• Fark: 📉 -20.00₺
🔗 Ürüne Git

...
```

### Tarama Tamamlandı (Değişiklik Yok)
```
🌸 Multi-Site Fiyat Taraması Tamamlandı

✅ 9 site tarandı
📦 87 ürün kontrol edildi
✨ Fiyat değişikliği yok
🕐 10/11/2025 10:05:23

📊 Benchmarking Özeti

*Çiçek Sepeti*
• Ürün: 10
• Ort: 425.50₺ | Min: 199.99₺ | Max: 899.99₺

*Hızlı Çiçek*
• Ürün: 9
• Ort: 398.75₺ | Min: 179.99₺ | Max: 799.99₺
...
```

---

## 🐛 Sorun Giderme

### Scraper Çalışmıyor

**Cloudflare Challenge:**
```json
// sites-config.json içinde artır:
"wait_after_load": 8000  // 5000'den 8000'e
```

**Selector Bulunamıyor:**
- Site yapısı değişmiş olabilir
- DevTools ile yeni selector'ları bul
- `sites-config.json` dosyasını güncelle

**Timeout:**
```json
"timeout": 90000  // 60000'den 90000'e artır
```

### Dashboard Açılmıyor

```bash
# Port kullanımda mı?
lsof -i :8501

# Farklı port dene
streamlit run benchmarking_dashboard.py --server.port 8502

# Cache temizle
streamlit cache clear
```

### BigQuery Hatası

**Authentication Error:**
- Service account JSON key'i doğru mu?
- Project ID doğru mu?

**Permission Denied:**
- Service account'a "BigQuery Admin" rolü ver
- Dataset location'ı kontrol et (europe-west3)

---

## ⚡ Performans

| Metrik | Değer |
|--------|-------|
| Tek site tarama | ~25 saniye |
| 9 site toplam | ~5-6 dakika |
| Dashboard yükleme | < 2 saniye |
| BigQuery sync | ~10 saniye |
| Bellek kullanımı | ~500 MB |

---

## 🔒 Güvenlik

- ✅ Webhook URL'leri environment variable
- ✅ API keys GitHub Secrets'ta
- ✅ Service account ile sınırlı yetki
- ✅ Hassas data commit edilmiyor
- ✅ `.gitignore` ile korunmuş dosyalar

---

## 🎯 Gelecek Özellikler

- [ ] Email bildirimleri
- [ ] WhatsApp entegrasyonu
- [ ] Fiyat öngörü (ML)
- [ ] Stok takibi
- [ ] Mobil uygulama
- [ ] API endpoint'leri

---

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/AmazingFeature`)
3. Commit edin (`git commit -m 'Add some AmazingFeature'`)
4. Push edin (`git push origin feature/AmazingFeature`)
5. Pull Request açın

---

## 📞 Destek

- 📧 Email: [your-email]
- 💬 Slack: [your-slack]
- 🐛 Issues: GitHub Issues

---

## 📄 Lisans

MIT License - Detaylar için `LICENSE` dosyasına bakın.

---

## 👨‍💻 Geliştirici

**Multi-Site Flower Price Monitoring System**  
Versiyon: 1.0.0  
Tarih: Kasım 2025

---

## 🙏 Teşekkürler

Bu projeyi geliştirirken kullanılan teknolojiler:
- **Puppeteer** - Web scraping
- **Streamlit** - Dashboard
- **Plotly** - Görselleştirme
- **BigQuery** - Veri depolama
- **GitHub Actions** - CI/CD

---

**⭐ Projeyi beğendiyseniz yıldız vermeyi unutmayın!**

