-- ============================================
-- 4 KASIM 2025 VERİ KONTROLÜ
-- ============================================

-- ÖNCE: Enriched tabloda kontrol (bizim temizlediğimiz tablo)
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

-- İKİNCİ: Partitioned_v1 tablosunda kontrol (kullandığınız tablo)
SELECT 
  DATE(order_created_date) AS order_date,
  COUNT(*) AS row_count,
  COUNT(DISTINCT order_id) AS unique_orders
FROM `tazecicekdb.order_data.order_items_clean_v3_partitioned_v1`
WHERE order_created_date IS NOT NULL
  AND EXTRACT(YEAR FROM DATE(order_created_date)) = 2025
  AND EXTRACT(MONTH FROM DATE(order_created_date)) IN (10, 11)
GROUP BY order_date
ORDER BY order_date DESC;

-- 4 KASIM ÖZEL KONTROL: Enriched tabloda
SELECT 
  order_created_date_tr AS order_date,
  COUNT(*) AS row_count,
  COUNT(DISTINCT order_id) AS unique_orders,
  MIN(order_created_date_tr) AS min_date,
  MAX(order_created_date_tr) AS max_date
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE order_created_date_tr = "2025-11-04"
GROUP BY order_created_date_tr;

-- 4 KASIM ÖZEL KONTROL: Partitioned_v1 tabloda
SELECT 
  DATE(order_created_date) AS order_date,
  COUNT(*) AS row_count,
  COUNT(DISTINCT order_id) AS unique_orders,
  MIN(order_created_date) AS min_date,
  MAX(order_created_date) AS max_date
FROM `tazecicekdb.order_data.order_items_clean_v3_partitioned_v1`
WHERE DATE(order_created_date) = "2025-11-04"
GROUP BY DATE(order_created_date);

-- TARIH FORMATI KONTROLÜ: Enriched tablo
SELECT 
  order_created_date_tr,
  COUNT(*) as count
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE order_created_date_tr >= "2025-11-01"
  AND order_created_date_tr <= "2025-11-05"
GROUP BY order_created_date_tr
ORDER BY order_created_date_tr;

-- TARIH FORMATI KONTROLÜ: Partitioned_v1 tablo
SELECT 
  DATE(order_created_date) as order_date,
  COUNT(*) as count
FROM `tazecicekdb.order_data.order_items_clean_v3_partitioned_v1`
WHERE DATE(order_created_date) >= "2025-11-01"
  AND DATE(order_created_date) <= "2025-11-05"
GROUP BY DATE(order_created_date)
ORDER BY DATE(order_created_date);



