-- NOT: BigQuery'de location'ı "europe-west3" olarak seçin!
-- 5 Kasım 2025 - Genel Durum
SELECT 
  COUNT(*) as total_rows,
  COUNT(DISTINCT order_id) as unique_orders,
  COUNT(DISTINCT TO_JSON_STRING(t)) as unique_rows,
  COUNT(*) - COUNT(DISTINCT TO_JSON_STRING(t)) as exact_duplicates,
  ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT order_id), 2) AS avg_items_per_order
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered` t
WHERE order_created_date_tr = "2025-11-05";

-- Item sayısına göre order dağılımı
SELECT 
  item_count,
  COUNT(DISTINCT order_id) AS order_count,
  COUNT(*) AS total_items
FROM (
  SELECT 
    order_id,
    COUNT(*) AS item_count
  FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
  WHERE order_created_date_tr = "2025-11-05"
  GROUP BY order_id
)
GROUP BY item_count
ORDER BY item_count;

-- Duplicate olan order'lar
SELECT 
  order_id,
  TO_JSON_STRING(t) as row_json,
  COUNT(*) as duplicate_count,
  MIN(order_creation_timestamp) as first_seen,
  MAX(order_creation_timestamp) as last_seen
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered` t
WHERE order_created_date_tr = "2025-11-05"
GROUP BY order_id, row_json
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC
LIMIT 20;

-- Örnek order detayları (duplicate olanlar)
SELECT 
  order_id,
  user_id,
  city,
  product_code_1,
  additional_products,
  order_creation_timestamp,
  TO_JSON_STRING(t) as row_json
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered` t
WHERE order_created_date_tr = "2025-11-05"
  AND order_id IN (
    SELECT order_id
    FROM (
      SELECT 
        order_id,
        TO_JSON_STRING(t) as row_json,
        COUNT(*) as cnt
      FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered` t
      WHERE order_created_date_tr = "2025-11-05"
      GROUP BY order_id, row_json
      HAVING COUNT(*) > 1
      LIMIT 5
    )
  )
ORDER BY order_id, order_creation_timestamp;

-- Diğer günlerle karşılaştırma
SELECT 
  DATE(order_created_date_tr) AS order_date,
  COUNT(*) AS row_count,
  COUNT(DISTINCT order_id) AS unique_orders,
  ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT order_id), 2) AS avg_items_per_order,
  COUNT(DISTINCT CASE WHEN item_count = 1 THEN order_id END) AS orders_1_item,
  COUNT(DISTINCT CASE WHEN item_count >= 2 THEN order_id END) AS orders_2plus_items
FROM (
  SELECT 
    order_created_date_tr,
    order_id,
    COUNT(*) OVER (PARTITION BY order_id) AS item_count
  FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
  WHERE order_created_date_tr IS NOT NULL
    AND EXTRACT(YEAR FROM order_created_date_tr) = 2025
    AND EXTRACT(MONTH FROM order_created_date_tr) = 11
)
GROUP BY order_date
ORDER BY order_date DESC;

-- Saatlik dağılım (hangi saatlerde veri geldi)
SELECT 
  EXTRACT(HOUR FROM order_creation_timestamp) AS hour,
  COUNT(*) AS row_count,
  COUNT(DISTINCT order_id) AS unique_orders
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE order_created_date_tr = "2025-11-05"
GROUP BY hour
ORDER BY hour;

