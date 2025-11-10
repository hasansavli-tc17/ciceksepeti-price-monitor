# 🔧 Çoğalan Veri Düzeltme Kılavuzu

## Problem
4 Kasım 2025 (`2025-11-04`) tarihindeki veriler BigQuery tablosunda çoğalmış (duplicate).

## Çözüm

### Yöntem 1: Basit ve Önerilen SQL Script (Hızlı)

1. BigQuery Console'a git: https://console.cloud.google.com/bigquery
2. `fix_duplicates_simple_2025_11_04.sql` dosyasını aç
3. Script'i adım adım çalıştır:

#### Adım 1: Yedek Al (ÖNERİLİR)
```sql
CREATE TABLE IF NOT EXISTS `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered_backup_2025_11_04`
AS 
SELECT * 
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE order_created_date_tr = "2025-11-04";
```

#### Adım 2: Çoğalan Kayıtları Tespit Et
```sql
SELECT 
  COUNT(*) as total_rows,
  COUNT(DISTINCT TO_JSON_STRING(t)) as unique_rows,
  COUNT(*) - COUNT(DISTINCT TO_JSON_STRING(t)) as exact_duplicates
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered` t
WHERE order_created_date_tr = "2025-11-04";
```

#### Adım 3-6: Temizleme İşlemi
Script'teki kalan adımları sırayla çalıştır:
- Adım 3: Temiz veriyi oluştur
- Adım 4: Eski verileri sil
- Adım 5: Temiz verileri geri yükle
- Adım 6: Temp tabloyu sil

#### Adım 7: Doğrula
```sql
SELECT 
  COUNT(*) as total_rows_after_cleanup,
  COUNT(DISTINCT TO_JSON_STRING(t)) as unique_rows_after_cleanup,
  COUNT(*) - COUNT(DISTINCT TO_JSON_STRING(t)) as remaining_duplicates
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered` t
WHERE order_created_date_tr = "2025-11-04";
```

### Yöntem 2: Python Script ile (Otomatik)

Eğer Python script ile çalıştırmak istersen:

```bash
# BigQuery credentials ayarla
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"

# Script'i çalıştır
python fix_duplicates.py --date 2025-11-04
```

## Önleme

`main.py` dosyası güncellenmiştir. Artık:
1. ✅ Aynı batch içindeki çoğalan kayıtlar filtreleniyor
2. ✅ BigQuery'de mevcut olan kayıtlar kontrol ediliyor
3. ✅ Çoğalan kayıtlar insert edilmeden önce atlanıyor

Bu sayede gelecekte aynı sorunun yaşanması önlenmiş oldu.

## Dikkat Edilmesi Gerekenler

⚠️ **ÖNEMLİ:** 
- İşlem öncesi mutlaka yedek alın
- Production ortamında test etmeden çalıştırma
- Büyük tablolarda işlem zaman alabilir (partitioned tablo olduğu için hızlı olmalı)

## Sorun Giderme

### "Permission denied" hatası alıyorsan:
- BigQuery'de `BigQuery Data Editor` ve `BigQuery Job User` rollerinin olduğundan emin ol

### "Table not found" hatası alıyorsan:
- Tablo adını kontrol et: `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
- Project ID'nin doğru olduğundan emin ol

### İşlem çok uzun sürüyorsa:
- Partitioned tablo olduğu için normalde hızlı olmalı
- Eğer yavaşsa, sadece o günkü verileri işlediğinden emin ol
- `order_created_date_tr = "2025-11-04"` filtresinin çalıştığından emin ol

## Geri Alma (Rollback)

Eğer bir sorun olursa, yedekten geri yükle:

```sql
-- Önce mevcut verileri sil
DELETE FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE order_created_date_tr = "2025-11-04";

-- Yedekten geri yükle
INSERT INTO `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
SELECT * FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered_backup_2025_11_04`;
```



