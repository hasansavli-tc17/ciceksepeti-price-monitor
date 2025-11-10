# 🚀 Hızlı Referans Kılavuzu

## ⚡ Hızlı Komutlar

```bash
# Hızlı başlangıç menüsü
./quick-start.sh

# veya npm scriptleri
npm run test          # Test taraması (tek site)
npm run scrape        # Tüm siteleri tara
npm run monitor       # Fiyat takibi başlat
npm run dashboard     # Dashboard'u aç
npm run sync          # BigQuery'ye sync
```

## 📋 Manuel Komutlar

### 1. Test Taraması (Hızlı)
```bash
node scraper.js
```
- Sadece ÇiçekSepeti
- ~30 saniye
- Hızlı test için ideal

### 2. Multi-Site Tarama
```bash
node multi-site-scraper.js
```
- Tüm 9 site
- ~5-6 dakika
- JSON çıktı alır

### 3. Fiyat Monitörü
```bash
SLACK_WEBHOOK_URL=your_webhook node multi-site-price-monitor.js
```
- Fiyat değişikliklerini tespit eder
- Slack bildirimi gönderir
- Benchmark raporu oluşturur

### 4. Dashboard
```bash
streamlit run benchmarking_dashboard.py
```
- http://localhost:8501
- İnteraktif analiz
- Gerçek zamanlı veriler

### 5. BigQuery Sync
```bash
GCP_PROJECT_ID=your-project python3 bigquery_sync.py
```
- Verileri cloud'a yükler
- Tarihsel analiz için

## 🔧 Ayar Dosyaları

### sites-config.json
Tüm site ayarları:
```json
{
  "sites": [...],
  "scraping_settings": {
    "products_per_site": 10,
    "timeout": 60000,
    "wait_after_load": 5000
  }
}
```

### Hızlı Değişiklikler

**Timeout artır:**
```json
"timeout": 90000  // 60000'den 90000'e
```

**Bekleme süresi artır:**
```json
"wait_after_load": 8000  // 5000'den 8000'e
```

**Ürün sayısını değiştir:**
```json
"products_per_site": 15  // 10'dan 15'e
```

**Siteyi devre dışı bırak:**
```json
"enabled": false
```

## 📊 Çıktı Dosyaları

| Dosya | Açıklama | Otomatik |
|-------|----------|----------|
| `multi_site_price_history.json` | Fiyat geçmişi | ✅ |
| `benchmark_report.json` | Analiz raporu | ✅ |
| `price_history.json` | Eski sistem | ✅ |

## 🎨 Dashboard Kısayolları

- **Ctrl+C** - Dashboard'u kapat
- **R** - Sayfayı yenile
- **C** - Cache temizle
- **⚙️ Settings** (sidebar) - Port ve tema ayarları

## 🔍 Hata Ayıklama

### Scraper çalışmıyor
```bash
# Verbose mode
NODE_DEBUG=* node multi-site-scraper.js

# Tek site test
node scraper.js
```

### Dashboard açılmıyor
```bash
# Port değiştir
streamlit run benchmarking_dashboard.py --server.port 8502

# Cache temizle
streamlit cache clear
```

### BigQuery hatası
```bash
# Credentials test
python3 -c "from google.cloud import bigquery; client = bigquery.Client()"
```

## 📅 Zamanlanmış Görevler

GitHub Actions otomatik çalışır:
- 10:00 (TR)
- 13:00 (TR)
- 16:00 (TR)
- 19:00 (TR)
- 22:00 (TR)

Manuel tetikleme:
1. GitHub > Actions
2. Multi-Site Price Monitor
3. Run workflow

## 🎯 En İyi Pratikler

### Test Yaparken
1. İlk `npm run test` ile test et
2. Başarılıysa `npm run scrape` ile full tarama
3. Dashboard ile sonuçları kontrol et

### Production'da
1. GitHub Actions'ı aktif et
2. Secrets'ı ekle
3. İlk çalıştırmayı manuel tetikle
4. Slack'te bildirimleri kontrol et

### Sorun Çözümde
1. `./quick-start.sh` ile sistem durumunu kontrol et
2. Log dosyalarını incele
3. Selector'ları kontrol et
4. Timeout'ları artır

## 🔐 Secrets Yönetimi

### Local Development
```bash
# .env dosyası oluştur
cp env.template .env
# Düzenle
nano .env
```

### GitHub
Repository Settings → Secrets → Actions:
- `SLACK_WEBHOOK_URL`
- `GCP_PROJECT_ID` (opsiyonel)
- `GCP_SERVICE_ACCOUNT_KEY` (opsiyonel)

## 📦 Paket Güncelleme

```bash
# Node.js paketleri
npm update
npm audit fix

# Python paketleri
pip install --upgrade -r requirements.txt
```

## 🆘 Acil Durum Komutları

```bash
# Tüm process'leri durdur
pkill -f "node multi-site"
pkill -f "streamlit"

# Port'u temizle
lsof -ti:8501 | xargs kill -9

# Cache temizle
rm -rf .streamlit/
rm -rf __pycache__/

# Git reset (dikkatli!)
git reset --hard HEAD
git clean -fd
```

## 📞 Hızlı Yardım

```bash
# Sistem durumu
./quick-start.sh  # Seçenek 6

# Versiyon kontrol
node --version
python3 --version
npm --version

# Paket kontrolü
npm list
pip list
```

---

**💡 İpucu:** Bu kılavuzu her zaman `QUICK_REFERENCE.md` dosyasında bulabilirsiniz.

