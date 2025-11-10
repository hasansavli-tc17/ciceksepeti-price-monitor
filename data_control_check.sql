-- ============================================================
-- DATA KONTROL SORGUSU
-- 5 Kasım ve sonrası için duplicate, veri kalitesi kontrolü
-- ============================================================

-- 1. GENEL DURUM - Son 7 gün
SELECT 
  DATE(order_created_date_tr) AS tarih,
  COUNT(*) AS toplam_satir,
  COUNT(DISTINCT order_id) AS benzersiz_order,
  COUNT(DISTINCT TO_JSON_STRING(t)) AS benzersiz_satir,
  COUNT(*) - COUNT(DISTINCT TO_JSON_STRING(t)) AS duplicate_sayisi,
  ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT order_id), 2) AS avg_item_per_order,
  COUNT(DISTINCT CASE WHEN item_count = 1 THEN order_id END) AS tek_itemli_order,
  COUNT(DISTINCT CASE WHEN item_count >= 2 THEN order_id END) AS coklu_itemli_order,
  CASE 
    WHEN COUNT(*) - COUNT(DISTINCT TO_JSON_STRING(t)) = 0 THEN '✅ Temiz'
    ELSE '⚠️ Duplicate var!'
  END AS durum
FROM (
  SELECT 
    *,
    COUNT(*) OVER (PARTITION BY order_id) AS item_count
  FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
  WHERE order_created_date_tr >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
) t
GROUP BY tarih
ORDER BY tarih DESC;

-- 2. BUGÜNKÜ DETAYLI KONTROL
SELECT 
  '📊 Bugünkü Veri Durumu' AS kontrol,
  COUNT(*) AS toplam_satir,
  COUNT(DISTINCT order_id) AS benzersiz_order,
  COUNT(DISTINCT TO_JSON_STRING(t)) AS benzersiz_satir,
  COUNT(*) - COUNT(DISTINCT TO_JSON_STRING(t)) AS duplicate_sayisi,
  MIN(order_creation_timestamp) AS ilk_veri,
  MAX(order_creation_timestamp) AS son_veri,
  TIMESTAMP_DIFF(MAX(order_creation_timestamp), MIN(order_creation_timestamp), HOUR) AS veri_araligi_saat
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered` t
WHERE order_created_date_tr = CURRENT_DATE();

-- 3. DUPLICATE ÖRNEKLER (Eğer varsa)
SELECT 
  '🔍 Duplicate Örnekler (İlk 10)' AS kontrol,
  order_id,
  product_code_1,
  user_id,
  city,
  COUNT(*) as tekrar_sayisi,
  MIN(order_creation_timestamp) AS ilk_kayit,
  MAX(order_creation_timestamp) AS son_kayit
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE order_created_date_tr = CURRENT_DATE()
GROUP BY order_id, product_code_1, user_id, city, TO_JSON_STRING(t)
HAVING COUNT(*) > 1
ORDER BY tekrar_sayisi DESC
LIMIT 10;

-- 4. SAATLİK DAĞILIM (Schedule düzgün çalışıyor mu?)
SELECT 
  EXTRACT(HOUR FROM order_creation_timestamp) AS saat,
  COUNT(*) AS satir_sayisi,
  COUNT(DISTINCT order_id) AS benzersiz_order,
  COUNT(*) - COUNT(DISTINCT TO_JSON_STRING(t)) AS duplicate_sayisi
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE order_created_date_tr = CURRENT_DATE()
GROUP BY saat
ORDER BY saat;

-- 5. VERİ KALİTESİ - Eksik/NULL alanlar
SELECT 
  'Veri Kalitesi Kontrolü' AS kontrol,
  COUNT(*) AS toplam,
  COUNT(CASE WHEN order_id IS NULL THEN 1 END) AS order_id_null,
  COUNT(CASE WHEN user_id IS NULL OR user_id = '' THEN 1 END) AS user_id_bos,
  COUNT(CASE WHEN product_code_1 IS NULL OR product_code_1 = '' THEN 1 END) AS product_code_bos,
  COUNT(CASE WHEN city IS NULL OR city = '' THEN 1 END) AS city_bos,
  COUNT(CASE WHEN order_creation_timestamp IS NULL THEN 1 END) AS timestamp_null
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE order_created_date_tr = CURRENT_DATE();

-- 6. SON 24 SAAT TRENDİ (Her saat kaç veri geldi)
SELECT 
  TIMESTAMP_TRUNC(order_creation_timestamp, HOUR) AS saat,
  COUNT(*) AS yeni_satir,
  COUNT(DISTINCT order_id) AS yeni_order
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE order_creation_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
GROUP BY saat
ORDER BY saat DESC
LIMIT 24;

-- ============================================================
-- HIZLI KONTROL (Tek satırda özet)
-- ============================================================
SELECT 
  CURRENT_DATE() AS tarih,
  COUNT(*) AS satir,
  COUNT(DISTINCT order_id) AS order,
  COUNT(*) - COUNT(DISTINCT TO_JSON_STRING(t)) AS duplicate,
  CASE 
    WHEN COUNT(*) - COUNT(DISTINCT TO_JSON_STRING(t)) = 0 THEN '✅ TEMİZ'
    ELSE CONCAT('⚠️ ', CAST(COUNT(*) - COUNT(DISTINCT TO_JSON_STRING(t)) AS STRING), ' DUPLICATE VAR!')
  END AS durum
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered` t
WHERE order_created_date_tr = CURRENT_DATE();



