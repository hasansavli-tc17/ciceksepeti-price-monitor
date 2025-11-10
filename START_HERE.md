# 🌸 Hoş Geldiniz! Buradan Başlayın

## 🎯 Ne Yaptık?

Türkiye'deki **9 farklı çiçek sitesinden** günlük fiyat verilerini toplayıp analiz eden, karşılaştırmalı benchmarking yapan ve fiyat değişikliklerini otomatik bildiren **kapsamlı bir sistem** kurduk.

---

## 🏪 Hangi Siteler?

1. **Çiçek Sepeti** - www.ciceksepeti.com
2. **Hızlı Çiçek** - www.hizlicicek.com
3. **Heryerbitki** - www.heryerbitki.com
4. **İstanbul Çiçekleri** - www.istanbulcicekleri.com
5. **Osevio** - www.osevio.com
6. **Lilyana Flowers** - www.lilyanaflowers.com
7. **Bloom and Fresh** - www.bloomandfresh.com
8. **Çiçek Diyarı** - www.cicekdiyari.com
9. **RoseBox** - www.rosebox.com.tr

**Her siteden top 10 ürün = Toplam 90 ürün takibi!**

---

## ⚡ Hızlı Başlangıç (3 Adım)

### 1️⃣ Bağımlılıkları Yükle

```bash
# Node.js paketleri
npm install

# Python paketleri
pip install -r requirements.txt
```

### 2️⃣ Sistemi Test Et

```bash
# Otomatik test çalıştır
./test-system.sh

# veya hızlı test
node scraper.js
```

### 3️⃣ Quick Start Menüsünü Çalıştır

```bash
./quick-start.sh
```

**Menüden seçenekleri seçerek sistemi kullanabilirsiniz!**

---

## 📊 Sistem Özellikleri

### ✅ Multi-Site Scraping
- Universal Puppeteer scraper
- Cloudflare bypass
- Otomatik kategori tespiti
- Hata toleranslı tarama

### ✅ Fiyat Takibi
- Otomatik fiyat karşılaştırma
- Değişiklik tespiti
- Slack bildirimleri
- Site bazında raporlama

### ✅ Benchmarking Dashboard
- İnteraktif Streamlit UI
- Fiyat karşılaştırma grafikleri
- Kategori analizi
- Heatmap görselleştirme
- Detaylı ürün tabloları

### ✅ Veri Yönetimi
- BigQuery entegrasyonu
- JSON veri saklama
- Tarihsel fiyat tracking
- GitHub Actions backup

---

## 📁 Önemli Dosyalar

| Dosya | Açıklama |
|-------|----------|
| `START_HERE.md` | 👈 Bu dosya - başlangıç kılavuzu |
| `QUICK_REFERENCE.md` | Hızlı komut referansı |
| `MULTI_SITE_SETUP.md` | Detaylı kurulum ve kullanım |
| `README_MULTISITE.md` | Tam sistem dokümantasyonu |
| `quick-start.sh` | İnteraktif menü |
| `test-system.sh` | Sistem test scripti |
| `sites-config.json` | Site konfigürasyonları |

---

## 🎮 Kullanım Senaryoları

### Senaryo 1: İlk Kez Kullanıyorsunuz

```bash
# 1. Test et
./test-system.sh

# 2. İlk tarama
./quick-start.sh
# Menüden: 2) Full Tarama

# 3. Dashboard'u aç
# Menüden: 4) Dashboard'u Aç
```

### Senaryo 2: Günlük Fiyat Takibi

```bash
# Slack webhook'u ayarla
export SLACK_WEBHOOK_URL="your_webhook"

# Monitörü çalıştır
./quick-start.sh
# Menüden: 3) Fiyat Takibi
```

### Senaryo 3: Benchmarking Analizi

```bash
# 1. Verileri güncelle
npm run scrape

# 2. Dashboard'u aç
npm run dashboard

# 3. Tarayıcıda analiz et
# http://localhost:8501
```

### Senaryo 4: GitHub Actions (Otomatik)

1. GitHub'a push yapın
2. Settings → Secrets → `SLACK_WEBHOOK_URL` ekleyin
3. Actions sekmesinden workflow'u kontrol edin
4. Günde 5 kez otomatik çalışır! ✨

---

## 🔧 Konfigürasyon

### Slack Bildirimleri (Zorunlu)

```bash
# Environment variable olarak
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK"

# veya .env dosyası oluştur
cp env.template .env
# Düzenle: nano .env
```

### BigQuery (Opsiyonel)

```bash
# Google Cloud ayarları
export GCP_PROJECT_ID="your-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="./service-account.json"

# Sync et
npm run sync
```

### Site Ayarları

```bash
# Konfigürasyonu düzenle
nano sites-config.json

# Değiştirebilirsiniz:
# - Ürün sayısı (products_per_site)
# - Timeout süreleri
# - Site enabled/disabled
# - Selector'lar
```

---

## 📊 Dashboard Kullanımı

```bash
npm run dashboard
```

**Açılır:** http://localhost:8501

### Tab'lar:

1. **📊 Site Karşılaştırma**
   - Ortalama/Min/Max fiyatlar
   - Site bazında metrikler

2. **🎨 Kategori Analizi**
   - Gül, Orkide, Papatya vb.
   - Site × Kategori karşılaştırma

3. **🔥 Heatmap**
   - Görsel fiyat haritası
   - Renkli karşılaştırma

4. **📋 Detaylı Tablo**
   - Tüm ürünler
   - Filtreleme & sıralama

---

## 🤖 Otomatik Çalıştırma

### GitHub Actions Zamanları (Türkiye)

- 🕙 10:00
- 🕐 13:00
- 🕓 16:00
- 🕖 19:00
- 🕚 22:00

### Manuel Tetikleme

1. GitHub → Actions
2. "Multi-Site Price Monitor"
3. "Run workflow"

---

## 🆘 Sorun mu Yaşıyorsunuz?

### Hata: "Scraper çalışmıyor"

```bash
# 1. Basit test
node scraper.js

# 2. Timeout artır
# sites-config.json dosyasında:
"timeout": 90000
```

### Hata: "Dashboard açılmıyor"

```bash
# Cache temizle
streamlit cache clear

# Farklı port
streamlit run benchmarking_dashboard.py --server.port 8502
```

### Hata: "Paket bulunamadı"

```bash
# Node.js
npm install

# Python
pip3 install -r requirements.txt
```

### Hata: "Permission denied"

```bash
# Scriptleri executable yap
chmod +x quick-start.sh
chmod +x test-system.sh
```

---

## 📚 Daha Fazla Bilgi

- **Hızlı Komutlar:** `QUICK_REFERENCE.md`
- **Detaylı Setup:** `MULTI_SITE_SETUP.md`
- **Tam Dokümantasyon:** `README_MULTISITE.md`

---

## 🎯 Sonraki Adımlar

1. ✅ Sistemi test edin (`./test-system.sh`)
2. ✅ İlk tarama yapın (`./quick-start.sh → 2`)
3. ✅ Dashboard'u inceleyin (`./quick-start.sh → 4`)
4. ✅ Slack webhook'u ayarlayın
5. ✅ GitHub Actions'ı aktif edin
6. ✅ Günlük raporları kontrol edin

---

## 💡 İpuçları

- **Test için:** Önce tek site (`npm run test`)
- **Production için:** GitHub Actions kullan
- **Dashboard:** Her zaman güncel verileri gösterir
- **Yeni site eklemek:** `sites-config.json` dosyasını düzenle
- **Yardım:** `./quick-start.sh` menüsünde "6) Sistem Durumu"

---

## 🎉 Başarılar!

Artık Türkiye'nin en kapsamlı çiçek fiyat takip sistemine sahipsiniz! 🌸

**Sorularınız için:** GitHub Issues açabilirsiniz.

---

**Quick Start:** `./quick-start.sh` 🚀

