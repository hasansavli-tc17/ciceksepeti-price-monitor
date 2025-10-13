# 🌸 Çiçek Sepeti Fiyat Takip Sistemi

Bu sistem Çiçek Sepeti'nden ürün fiyatlarını takip eder ve fiyat değişikliklerini Slack'e bildirir.

## 🚀 Özellikler

- ✅ 30 ürün otomatik takip
- ✅ Fiyat değişikliklerini tespit etme
- ✅ Slack bildirimleri
- ✅ GitHub Actions ile 7/24 çalışma
- ✅ Cloudflare bypass
- ✅ Puppeteer ile güvenilir scraping
- ✅ Test modu

## 📅 Çalışma Zamanları

- **Her gün 09:00** (Türkiye saati)
- **Her gün 18:00** (Türkiye saati)

## 🔧 Kurulum

### GitHub Actions için:

1. Bu repository'yi GitHub'a yükle
2. Repository Settings > Secrets > Actions'a git
3. `SLACK_WEBHOOK_URL` secret'ını ekle
4. Webhook URL'ini ekle

## 📁 Dosya Yapısı

```
├── .github/workflows/
│   └── price-monitor.yml      # GitHub Actions workflow
├── scraper.js                 # Puppeteer scraper
├── price_monitor_github.js    # GitHub Actions için ana script
├── price_history.json         # Fiyat geçmişi
└── package.json               # Node.js dependencies
```

## 🎯 Kullanım

Sistem otomatik çalışır. Manuel test için:

```bash
# Normal test (gerçek fiyat değişiklikleri)
SLACK_WEBHOOK_URL=your_webhook_url node price_monitor_github.js

# Test modu (yapay fiyat değişikliği oluşturur)
TEST_MODE=true SLACK_WEBHOOK_URL=your_webhook_url node price_monitor_github.js
```

## 📊 Loglar

GitHub Actions sekmesinden çalışma loglarını görebilirsin.

## 🔒 Güvenlik

Slack webhook URL'i GitHub Secrets'da güvenli şekilde saklanır. Kodda hardcoded URL bulunmaz.

## 🐛 Sorun Giderme

### Slack bildirimleri gelmiyor

1. `SLACK_WEBHOOK_URL` environment variable'ının doğru ayarlandığından emin ol
2. Test modunu kullanarak test et: `TEST_MODE=true SLACK_WEBHOOK_URL=xxx node price_monitor_github.js`
3. GitHub Actions loglarını kontrol et
4. Slack webhook URL'inin geçerli olduğunu doğrula

### GitHub Actions push hatası

- Repository Settings > Actions > General > Workflow permissions
- "Read and write permissions" seçeneğini işaretle
