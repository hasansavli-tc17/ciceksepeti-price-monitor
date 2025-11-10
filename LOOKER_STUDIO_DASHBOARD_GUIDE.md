# Looker Studio Dashboard Oluşturma Rehberi

## 📊 Adım 1: BigQuery Data Source Bağlama

1. **Looker Studio'ya git**: https://lookerstudio.google.com
2. **"Create" → "Data Source"** tıkla
3. **"BigQuery"** seç
4. **Bağlantı Bilgileri:**
   - **Project**: `tazecicekdb`
   - **Dataset**: `order_data`
   - **Table**: `order_items_clean_v3_enriched_partitioned_clustered`
5. **"Connect"** tıkla

## 📈 Adım 2: Dashboard Oluşturma

1. **"Create" → "Report"** tıkla
2. Az önce oluşturduğun **Data Source**'u seç
3. **"Add to report"** tıkla

## 🎨 Adım 3: Grafikler ve Metrikler Ekleme

### 3.1. Toplam Metrikler (Scorecards)
- **Scorecard** ekle
- **Metric**: `Total Unique Orders` (COUNT DISTINCT order_id)
- **Metric**: `Total Revenue` (SUM order_amount)
- **Metric**: `Average Order Value` (AVG order_amount)

### 3.2. Günlük Sipariş Trendi (Time Series Chart)
- **Time Series Chart** ekle
- **Dimension**: `order_created_date_tr`
- **Metric**: `Unique Orders` (COUNT DISTINCT order_id)
- **Metric**: `Total Revenue` (SUM order_amount)
- **Date Range**: Son 30 gün / Son 90 gün

### 3.3. Aylık Özet (Time Series Chart)
- **Time Series Chart** ekle
- **Dimension**: `order_created_date_tr` (MONTH grouping)
- **Metric**: `Unique Orders`, `Total Revenue`

### 3.4. Şehir Dağılımı (Bar Chart)
- **Bar Chart** ekle
- **Dimension**: `city`
- **Metric**: `Unique Orders` (COUNT DISTINCT order_id)
- **Sort**: Descending by Unique Orders
- **Limit**: Top 20

### 3.5. Ödeme Yöntemleri (Pie Chart)
- **Pie Chart** ekle
- **Dimension**: `payment_method`
- **Metric**: `Unique Orders`
- **Show**: Percentage

### 3.6. Teslimat Durumları (Bar Chart)
- **Bar Chart** ekle
- **Dimension**: `delivery_status`
- **Metric**: `Unique Orders`

### 3.7. Ürün Kategorileri (Bar Chart)
- **Bar Chart** ekle
- **Dimension**: `product_category` (as STRING)
- **Metric**: `Unique Orders`

### 3.8. Gün İçi Saat Dağılımı (Bar Chart)
- **Bar Chart** ekle
- **Dimension**: `order_creation_timestamp` (HOUR extract)
- **Metric**: `Unique Orders`

### 3.9. Top Ürünler (Table)
- **Table** ekle
- **Dimension**: `product_name`
- **Metrics**: 
  - `Unique Orders` (COUNT DISTINCT order_id)
  - `Total Items` (COUNT)
  - `Total Revenue` (SUM order_amount)
- **Sort**: Descending by Unique Orders
- **Limit**: Top 50

### 3.10. Vendor Performansı (Table)
- **Table** ekle
- **Dimension**: `vendor_id`
- **Metrics**: 
  - `Unique Orders`
  - `Total Revenue`
  - `Average Order Value`
- **Sort**: Descending by Unique Orders

## 🔍 Adım 4: Filtreler Ekleme

1. **Date Range Control** ekle
   - `order_created_date_tr` için tarih filtresi
2. **Dropdown Filter** ekle
   - `city` için şehir filtresi
   - `payment_method` için ödeme yöntemi filtresi
   - `delivery_status` için teslimat durumu filtresi

## 🎨 Adım 5: Stil ve Tema

1. **Theme** ayarla:
   - Renk paleti seç
   - Font ayarları
2. **Layout** düzenle:
   - Grafikleri yerleştir
   - Boyutları ayarla
3. **Interactive Elements**:
   - Grafikler arası cross-filtering aktif et

## 📱 Adım 6: Paylaşım

1. **"Share"** butonuna tıkla
2. **Permissions** ayarla:
   - "Anyone with the link can view" (public)
   - Veya belirli email'lere erişim ver
3. **Embed** kodunu al (isteğe bağlı)

## 🚀 Hızlı Başlangıç: SQL Custom Queries

Eğer daha karmaşık analizler yapmak istersen, **dashboard_sql_queries.sql** dosyasındaki hazır SQL sorgularını kullanabilirsin:

1. Looker Studio'da **"Add Data" → "Custom Query"**
2. SQL sorgusunu yapıştır
3. **"Connect"** tıkla

## 💡 Öneriler

- **Partitioning**: Tablo `order_created_date_tr` bazlı partition edilmiş, bu yüzden tarih filtreleri çok hızlı çalışır
- **Clustering**: Veri optimize edilmiş, büyük sorgular hızlı çalışır
- **Caching**: Looker Studio otomatik cache yapar, ilk yükleme biraz yavaş olabilir
- **Refresh**: Data source'u manuel refresh edebilirsin veya otomatik refresh ayarla

## 📞 Sorun Giderme

- **Veri görünmüyor**: Data source permissions kontrol et
- **Yavaş yükleme**: Filtreleri daralt, limit ekle
- **Hata mesajları**: SQL sorgularını kontrol et, kolon isimlerini doğrula




