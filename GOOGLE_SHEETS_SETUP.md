# 📊 Google Sheets Entegrasyonu Kurulum Rehberi

## 🎯 Amaç
90 ürünün detaylı listesini otomatik olarak Google Sheets'e aktarmak ve Slack bildirimlerinde link paylaşmak.

---

## ⚡ Hızlı Kurulum (3 Adım)

### 1️⃣ Google Sheet Oluştur

1. **Google Sheets'e git:** https://sheets.google.com
2. **Yeni bir sheet oluştur** (boş bırak, otomatik dolacak)
3. **Sheet ID'yi kopyala:**
   - URL'den: `https://docs.google.com/spreadsheets/d/SHEET_ID_BURADA/edit`
   - SHEET_ID_BURADA kısmını kopyala

**Örnek:**
```
URL: https://docs.google.com/spreadsheets/d/1abc-XYZ123_defGHI456/edit
Sheet ID: 1abc-XYZ123_defGHI456
```

---

### 2️⃣ Service Account'a Erişim Ver

Zaten BigQuery için bir service account'un var. Aynısını kullanacağız:

1. **Service Account email'ini al:**
   - Google Cloud Console → IAM & Admin → Service Accounts
   - Email formatı: `something@project-id.iam.gserviceaccount.com`

2. **Sheet'i paylaş:**
   - Google Sheets'te sağ üst → **Share** butonuna tıkla
   - Service account email'ini ekle
   - **Editor** yetkisi ver
   - ✅ Done

---

### 3️⃣ GitHub'a Secret Ekle

GitHub repository'ne git:

1. **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret** ekle:

```
Name: GOOGLE_SHEETS_ID
Value: (1. adımda kopyaladığın Sheet ID)
```

**Örnek:**
```
Name: GOOGLE_SHEETS_ID
Value: 1abc-XYZ123_defGHI456
```

---

## ✅ Test Et

Lokal test için (opsiyonel):

```bash
# Sheet ID'yi environment variable olarak ekle
export GOOGLE_SHEETS_ID="SENIN_SHEET_ID"

# Test çalıştır
node google-sheets-sync.js
```

GitHub Actions'da otomatik çalışacak, test etmene gerek yok!

---

## 🎉 Sonuç

Artık her tarama sonrası:
- ✅ 90 ürün otomatik Google Sheets'e yazılacak
- ✅ Slack bildiriminde "📊 Google Sheets'te Gör" linki çıkacak
- ✅ Sheet'te filtreleme, sıralama, pivot table yapabilirsin!

---

## 🔍 Sık Sorulan Sorular

**Q: Birden fazla sheet kullanabilir miyim?**
A: Evet! Farklı GOOGLE_SHEETS_ID kullanarak birden fazla sheet'e yazabilirsin.

**Q: Sheet'i kim görebilir?**
A: Sen paylaşma ayarlarından kontrol edebilirsin. Service account'a Editor, başkalarına Viewer verebilirsin.

**Q: BigQuery ile aynı service account'u kullanabilir miyim?**
A: Evet! Zaten aynı GCP_SERVICE_ACCOUNT_KEY secret'ı kullanacak.

**Q: Sheet'i manuel düzenleyebilir miyim?**
A: Evet ama her taramada üzerine yazılacak. Manuel değişiklikler kaybolur.

---

## 📱 Yeni Slack Bildirimi Formatı

```
🌸 Multi-Site Fiyat Taraması Tamamlandı

✅ 3 site tarandı
📦 90 ürün kontrol edildi
✨ Fiyat değişikliği yok
🕐 11.11.2025 17:13:23

📊 Benchmarking Özeti

Çiçek Sepeti • Ürün: 30 • Ort: 745.89₺
Hızlı Çiçek • Ürün: 30 • Ort: 1126.00₺
Bloom and Fresh • Ürün: 30 • Ort: 2146.90₺

📊 Google Sheets'te Gör (Tüm 90 ürün) 👈 YENİ!
```

