-- ============================================
-- 4 KASIM 2025 VERİ KONTROLÜ - DOĞRULAMA
-- ============================================

-- Ekim-Kasım 2025 genel görünüm
SELECT 
  DATE(order_created_date_tr) AS order_date,
  COUNT(*) AS row_count,
  COUNT(DISTINCT order_id) AS unique_orders
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE order_created_date_tr IS NOT NULL
  AND EXTRACT(YEAR FROM order_created_date_tr) = 2025
  AND EXTRACT(MONTH FROM order_created_date_tr) IN (10, 11)
GROUP BY order_date
ORDER BY order_date DESC;

-- 4 Kasım özel kontrol
SELECT 
  DATE(order_created_date_tr) AS order_date,
  COUNT(*) AS row_count,
  COUNT(DISTINCT order_id) AS unique_orders,
  'Beklenen: ~2652 satır, ~2593 unique order' AS expected
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE order_created_date_tr = "2025-11-04"
GROUP BY DATE(order_created_date_tr);

-- 4 Kasım çevresi kontrolü (3-5 Kasım)
SELECT 
  DATE(order_created_date_tr) AS order_date,
  COUNT(*) AS row_count,
  COUNT(DISTINCT order_id) AS unique_orders
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE order_created_date_tr >= "2025-11-03"
  AND order_created_date_tr <= "2025-11-05"
GROUP BY DATE(order_created_date_tr)
ORDER BY order_date DESC;



