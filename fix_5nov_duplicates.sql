-- 5 Kasım duplicate temizleme
-- 1. Önce durumu kontrol et:
SELECT 
  COUNT(*) as total_rows,
  COUNT(DISTINCT TO_JSON_STRING(t)) as unique_rows,
  COUNT(*) - COUNT(DISTINCT TO_JSON_STRING(t)) as exact_duplicates
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered` t
WHERE order_created_date_tr = "2025-11-05";

-- 2. Temiz veri oluştur (bu sorguyu çalıştır):
CREATE OR REPLACE TABLE `tazecicekdb.order_data.temp_clean_5nov_20251105`
PARTITION BY order_created_date_tr
CLUSTER BY order_id
AS
SELECT * EXCEPT(row_num)
FROM (
  SELECT *,
    ROW_NUMBER() OVER (
      PARTITION BY TO_JSON_STRING(t)
      ORDER BY COALESCE(order_creation_timestamp, CURRENT_TIMESTAMP()) DESC
    ) as row_num
  FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered` t
  WHERE order_created_date_tr = "2025-11-05"
)
WHERE row_num = 1;

-- 3. Yeni tablo oluştur (diğer günler + temiz 5 Kasım):
CREATE OR REPLACE TABLE `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered_new_20251105`
PARTITION BY order_created_date_tr
CLUSTER BY order_id
AS
SELECT * FROM (
  SELECT * FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
  WHERE order_created_date_tr != "2025-11-05"
  
  UNION ALL
  
  SELECT * FROM `tazecicekdb.order_data.temp_clean_5nov_20251105`
);

-- 4. Yedek oluştur, eski tabloyu sil, yeni tabloyu kopyala
-- Bu adımları BigQuery Console'dan MANUEL yap:
-- a) Yedek: order_items_clean_v3_enriched_partitioned_clustered -> order_items_clean_v3_enriched_partitioned_clustered_backup_20251105
-- b) Sil: order_items_clean_v3_enriched_partitioned_clustered
-- c) Kopyala: order_items_clean_v3_enriched_partitioned_clustered_new_20251105 -> order_items_clean_v3_enriched_partitioned_clustered

-- 5. Kontrol et:
SELECT 
  COUNT(*) as total_rows,
  COUNT(DISTINCT TO_JSON_STRING(t)) as unique_rows,
  COUNT(*) - COUNT(DISTINCT TO_JSON_STRING(t)) as exact_duplicates
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered` t
WHERE order_created_date_tr = "2025-11-05";



