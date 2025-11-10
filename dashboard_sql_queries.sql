-- ============================================
-- LOOKER STUDIO DASHBOARD - SQL QUERIES
-- ============================================
-- Bu sorgular Looker Studio'da Data Source olarak kullanılabilir
-- Tablo: order_items_clean_v3_enriched_partitioned_clustered

-- ============================================
-- 1. GÜNLÜK SİPARİŞ ÖZETİ (Time Series Chart)
-- ============================================
SELECT
  order_created_date_tr AS date,
  COUNT(DISTINCT order_id) AS unique_orders,
  COUNT(*) AS total_items,
  SUM(order_amount) AS total_revenue,
  AVG(order_amount) AS avg_order_value
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE order_created_date_tr IS NOT NULL
GROUP BY date
ORDER BY date DESC;

-- ============================================
-- 2. AYLIK SİPARİŞ ÖZETİ (Time Series Chart)
-- ============================================
SELECT
  DATE_TRUNC(order_created_date_tr, MONTH) AS month,
  COUNT(DISTINCT order_id) AS unique_orders,
  COUNT(*) AS total_items,
  SUM(order_amount) AS total_revenue,
  AVG(order_amount) AS avg_order_value
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE order_created_date_tr IS NOT NULL
GROUP BY month
ORDER BY month DESC;

-- ============================================
-- 3. ŞEHİR BAZLI DAĞILIM (Bar Chart / Pie Chart)
-- ============================================
SELECT
  city,
  COUNT(DISTINCT order_id) AS unique_orders,
  COUNT(*) AS total_items,
  SUM(order_amount) AS total_revenue
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE city IS NOT NULL
GROUP BY city
ORDER BY unique_orders DESC
LIMIT 20;

-- ============================================
-- 4. ÜRÜN KATEGORİLERİ (Bar Chart)
-- ============================================
SELECT
  CAST(product_category AS STRING) AS category_id,
  COUNT(DISTINCT order_id) AS unique_orders,
  COUNT(*) AS total_items,
  SUM(order_amount) AS total_revenue
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE product_category IS NOT NULL
GROUP BY category_id
ORDER BY unique_orders DESC;

-- ============================================
-- 5. ÖDEME YÖNTEMLERİ (Pie Chart)
-- ============================================
SELECT
  payment_method,
  COUNT(DISTINCT order_id) AS unique_orders,
  SUM(order_amount) AS total_revenue,
  ROUND(SUM(order_amount) * 100.0 / SUM(SUM(order_amount)) OVER (), 2) AS revenue_percentage
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE payment_method IS NOT NULL
GROUP BY payment_method
ORDER BY unique_orders DESC;

-- ============================================
-- 6. TESLİMAT DURUMLARI (Bar Chart)
-- ============================================
SELECT
  delivery_status,
  COUNT(DISTINCT order_id) AS unique_orders,
  COUNT(*) AS total_items
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE delivery_status IS NOT NULL
GROUP BY delivery_status
ORDER BY unique_orders DESC;

-- ============================================
-- 7. TOPLAM METRİKLER (Scorecards)
-- ============================================
SELECT
  COUNT(DISTINCT order_id) AS total_unique_orders,
  COUNT(*) AS total_items,
  SUM(order_amount) AS total_revenue,
  AVG(order_amount) AS avg_order_value,
  COUNT(DISTINCT DATE(order_created_date_tr)) AS days_with_orders
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE order_created_date_tr IS NOT NULL;

-- ============================================
-- 8. SON 30 GÜN TREND (Time Series Chart)
-- ============================================
SELECT
  order_created_date_tr AS date,
  COUNT(DISTINCT order_id) AS unique_orders,
  SUM(order_amount) AS total_revenue
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE order_created_date_tr >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
  AND order_created_date_tr IS NOT NULL
GROUP BY date
ORDER BY date DESC;

-- ============================================
-- 9. GÜN İÇİNDE SAAT BAZLI DAĞILIM (Bar Chart)
-- ============================================
SELECT
  EXTRACT(HOUR FROM order_creation_timestamp) AS hour,
  COUNT(DISTINCT order_id) AS unique_orders,
  SUM(order_amount) AS total_revenue
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE order_creation_timestamp IS NOT NULL
GROUP BY hour
ORDER BY hour;

-- ============================================
-- 10. VENDOR BAZLI PERFORMANS (Table)
-- ============================================
SELECT
  vendor_id,
  COUNT(DISTINCT order_id) AS unique_orders,
  COUNT(*) AS total_items,
  SUM(order_amount) AS total_revenue,
  AVG(order_amount) AS avg_order_value
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE vendor_id IS NOT NULL
GROUP BY vendor_id
ORDER BY unique_orders DESC
LIMIT 50;

-- ============================================
-- 11. TOP ÜRÜNLER (Table)
-- ============================================
SELECT
  product_name,
  product_code_1,
  COUNT(DISTINCT order_id) AS unique_orders,
  COUNT(*) AS total_items_sold,
  SUM(order_amount) AS total_revenue
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE product_name IS NOT NULL
GROUP BY product_name, product_code_1
ORDER BY unique_orders DESC
LIMIT 50;

-- ============================================
-- 12. BÖLGE BAZLI ANALİZ (Geographic)
-- ============================================
SELECT
  city,
  district,
  COUNT(DISTINCT order_id) AS unique_orders,
  SUM(order_amount) AS total_revenue
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE city IS NOT NULL AND district IS NOT NULL
GROUP BY city, district
ORDER BY unique_orders DESC
LIMIT 100;




