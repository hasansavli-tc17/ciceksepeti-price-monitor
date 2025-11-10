-- HIZLI FİX: 5 Kasım duplicate temizleme
-- BigQuery Console'dan çalıştır: https://console.cloud.google.com/bigquery?project=tazecicekdb

-- ADIM 1: Temiz veri oluştur (2-3 dakika)
CREATE OR REPLACE TABLE `tazecicekdb.order_data.temp_5nov_clean`
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

-- ADIM 2: Yeni ana tablo oluştur (diğer günler + temiz 5 Kasım) (3-4 dakika)
CREATE OR REPLACE TABLE `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered_NEW`
PARTITION BY order_created_date_tr
CLUSTER BY order_id
AS
SELECT * FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE order_created_date_tr != "2025-11-05"
UNION ALL
SELECT * FROM `tazecicekdb.order_data.temp_5nov_clean`;

-- ADIM 3: BigQuery UI'dan MANUEL:
-- 1. order_items_clean_v3_enriched_partitioned_clustered → order_items_clean_v3_enriched_partitioned_clustered_BACKUP_5NOV (Copy table)
-- 2. order_items_clean_v3_enriched_partitioned_clustered → Sil (Delete)
-- 3. order_items_clean_v3_enriched_partitioned_clustered_NEW → order_items_clean_v3_enriched_partitioned_clustered (Copy table)
-- 4. temp_5nov_clean ve order_items_clean_v3_enriched_partitioned_clustered_NEW → Sil

-- ADIM 4: Kontrol et
SELECT 
  COUNT(*) as total_rows,
  COUNT(DISTINCT TO_JSON_STRING(t)) as unique_rows,
  COUNT(*) - COUNT(DISTINCT TO_JSON_STRING(t)) as exact_duplicates
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered` t
WHERE order_created_date_tr = "2025-11-05";
-- Beklenen: exact_duplicates = 0



