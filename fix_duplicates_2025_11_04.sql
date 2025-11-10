-- ============================================
-- DUPLICATE FIX FOR 2025-11-04
-- ============================================
-- Bu script 4 Kasım 2025 tarihindeki çoğalan verileri temizler

-- ============================================
-- ADIM 1: Önce çoğalan kayıtları kontrol et
-- ============================================
-- Kaç adet çoğalan kayıt var görmek için:
SELECT 
  COUNT(*) as total_rows,
  COUNT(DISTINCT order_id) as unique_orders,
  COUNT(*) - COUNT(DISTINCT order_id) as potential_duplicates
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE order_created_date_tr = "2025-11-04";

-- Detaylı çoğalan kayıt analizi (hangi order_id'ler çoğalmış):
SELECT 
  order_id,
  COUNT(*) as duplicate_count,
  ARRAY_AGG(TO_JSON_STRING(STRUCT(*))) as sample_records
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE order_created_date_tr = "2025-11-04"
GROUP BY order_id
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC
LIMIT 20;

-- ============================================
-- ADIM 2: Çoğalan kayıtları sil (en yeni olanı koru)
-- ============================================
-- Not: BigQuery partitioned tablolarda DELETE kullanılabilir
-- Her order_id için sadece bir kayıt kalacak şekilde temizle

-- Önce yedek al (isteğe bağlı ama önerilir):
-- CREATE TABLE `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered_backup_2025_11_04`
-- AS SELECT * FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
-- WHERE order_created_date_tr = "2025-11-04";

-- Çoğalan kayıtları sil (ROW_NUMBER ile en son eklenen kayıtları koru):
DELETE FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE (
  SELECT row_num
  FROM (
    SELECT 
      *,
      ROW_NUMBER() OVER (
        PARTITION BY order_id 
        ORDER BY 
          -- Eğer timestamp varsa en yeni olanı koru
          COALESCE(order_creation_timestamp, CURRENT_TIMESTAMP()) DESC,
          -- Yoksa rastgele birini koru (ilk sıraya göre)
          1
      ) as row_num
    FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
    WHERE order_created_date_tr = "2025-11-04"
  ) ranked
  WHERE ranked.row_num > 1
  AND ranked.order_id = `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`.order_id
);

-- ============================================
-- ADIM 3: Alternatif Yöntem - MERGE kullanarak
-- ============================================
-- Eğer DELETE çalışmazsa, bu yöntemi kullan:
/*
MERGE `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered` AS target
USING (
  SELECT 
    * EXCEPT(row_num)
  FROM (
    SELECT 
      *,
      ROW_NUMBER() OVER (
        PARTITION BY order_id 
        ORDER BY COALESCE(order_creation_timestamp, CURRENT_TIMESTAMP()) DESC
      ) as row_num
    FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
    WHERE order_created_date_tr = "2025-11-04"
  )
  WHERE row_num = 1
) AS source
ON FALSE
WHEN NOT MATCHED BY SOURCE 
  AND target.order_created_date_tr = "2025-11-04"
THEN DELETE;
*/

-- ============================================
-- ADIM 4: Daha basit yöntem - Tüm günü sil ve tekrar ekle
-- ============================================
-- Eğer yukarıdaki yöntemler çalışmazsa, bu yöntemi kullan:
-- 1. Önce temiz veriyi bir temp tabloya kaydet:
/*
CREATE OR REPLACE TABLE `tazecicekdb.order_data.temp_2025_11_04_clean` AS
SELECT DISTINCT * FROM (
  SELECT 
    * EXCEPT(row_num)
  FROM (
    SELECT 
      *,
      ROW_NUMBER() OVER (
        PARTITION BY order_id 
        ORDER BY COALESCE(order_creation_timestamp, CURRENT_TIMESTAMP()) DESC
      ) as row_num
    FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
    WHERE order_created_date_tr = "2025-11-04"
  )
  WHERE row_num = 1
);
*/

-- 2. O günkü verileri sil:
/*
DELETE FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE order_created_date_tr = "2025-11-04";
*/

-- 3. Temiz verileri geri yükle:
/*
INSERT INTO `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
SELECT * FROM `tazecicekdb.order_data.temp_2025_11_04_clean`;
*/

-- 4. Temp tabloyu sil:
/*
DROP TABLE IF EXISTS `tazecicekdb.order_data.temp_2025_11_04_clean`;
*/

-- ============================================
-- ADIM 5: Sonuçları doğrula
-- ============================================
-- Temizleme sonrası kontrol:
SELECT 
  COUNT(*) as total_rows_after_cleanup,
  COUNT(DISTINCT order_id) as unique_orders_after_cleanup,
  COUNT(*) - COUNT(DISTINCT order_id) as remaining_duplicates
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE order_created_date_tr = "2025-11-04";



