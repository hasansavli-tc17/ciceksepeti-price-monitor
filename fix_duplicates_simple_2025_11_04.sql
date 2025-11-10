-- ============================================
-- BASİT VE GÜVENLİ ÇOĞALAN VERİ TEMİZLEME
-- Tarih: 2025-11-04
-- ============================================

-- ============================================
-- ADIM 1: ÖNCE YEDEK AL (ÖNERİLİR)
-- ============================================
CREATE TABLE IF NOT EXISTS `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered_backup_2025_11_04`
AS 
SELECT * 
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE order_created_date_tr = "2025-11-04";

-- ============================================
-- ADIM 2: ÇOĞALAN KAYITLARI TESPİT ET
-- ============================================
-- Önce kaç adet çoğalan kayıt var görelim:
SELECT 
  COUNT(*) as total_rows,
  COUNT(DISTINCT TO_JSON_STRING(t)) as unique_rows,
  COUNT(*) - COUNT(DISTINCT TO_JSON_STRING(t)) as exact_duplicates
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered` t
WHERE order_created_date_tr = "2025-11-04";

-- ============================================
-- ADIM 3: TEMİZ VERİYİ OLUŞTUR
-- ============================================
-- Çoğalan kayıtları temizle (her benzersiz kayıt için sadece birini koru)
-- Hash fonksiyonu ile benzersiz kayıtları tespit et
CREATE OR REPLACE TABLE `tazecicekdb.order_data.temp_2025_11_04_clean` AS
SELECT 
  * EXCEPT(row_num, row_hash)
FROM (
  SELECT 
    *,
    FARM_FINGERPRINT(TO_JSON_STRING(t)) as row_hash,
    ROW_NUMBER() OVER (
      PARTITION BY FARM_FINGERPRINT(TO_JSON_STRING(t))
      ORDER BY 
        -- Eğer insertion timestamp veya benzeri bir alan varsa, en yeni olanı koru
        COALESCE(order_creation_timestamp, CURRENT_TIMESTAMP()) DESC
    ) as row_num
  FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered` t
  WHERE order_created_date_tr = "2025-11-04"
)
WHERE row_num = 1;

-- ============================================
-- ADIM 4: ESKİ VERİLERİ SİL
-- ============================================
DELETE FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE order_created_date_tr = "2025-11-04";

-- ============================================
-- ADIM 5: TEMİZ VERİLERİ GERİ YÜKLE
-- ============================================
INSERT INTO `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
SELECT * FROM `tazecicekdb.order_data.temp_2025_11_04_clean`;

-- ============================================
-- ADIM 6: TEMP TABLOYU SİL
-- ============================================
DROP TABLE IF EXISTS `tazecicekdb.order_data.temp_2025_11_04_clean`;

-- ============================================
-- ADIM 7: SONUÇLARI DOĞRULA
-- ============================================
SELECT 
  COUNT(*) as total_rows_after_cleanup,
  COUNT(DISTINCT TO_JSON_STRING(t)) as unique_rows_after_cleanup,
  COUNT(*) - COUNT(DISTINCT TO_JSON_STRING(t)) as remaining_duplicates
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered` t
WHERE order_created_date_tr = "2025-11-04";
