-- ============================================
-- 4 KASIM 2025 ÇOĞALAN VERİLERİ SİLME
-- Streaming Buffer Sorunu Çözümü
-- ============================================

-- ÖNEMLİ: Bu SQL'i çalıştırmadan önce streaming buffer'ın temizlenmesini bekleyin
-- Streaming buffer genellikle son insert'ten sonra 30 dakika içinde temizlenir

-- ============================================
-- ADIM 1: Streaming buffer kontrolü
-- ============================================
-- Eğer bu sorgu 0 dönerse, DELETE yapabilirsiniz
-- Eğer > 0 dönerse, biraz daha bekleyin

SELECT 
  COUNT(*) as streaming_rows,
  'Streaming buffer kontrolü - 0 olmalı' as note
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE order_created_date_tr = "2025-11-04"
AND _PARTITIONTIME IS NULL;

-- ============================================
-- ADIM 2: ÇOĞALAN VERİLERİ SİL
-- ============================================
-- Bu sorguyu sadece ADIM 1'deki sonuç 0 ise çalıştırın!

DELETE FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE order_created_date_tr = "2025-11-04";

-- ============================================
-- ADIM 3: SONUÇLARI KONTROL ET
-- ============================================
-- Temizleme sonrası kontrol
-- Beklenen: ~2652 benzersiz satır

SELECT 
  COUNT(*) as total_rows,
  COUNT(DISTINCT TO_JSON_STRING(t)) as unique_rows,
  COUNT(*) - COUNT(DISTINCT TO_JSON_STRING(t)) as remaining_duplicates,
  'Beklenen: 2652 unique_rows, 0 remaining_duplicates' as expected
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered` t
WHERE order_created_date_tr = "2025-11-04";

-- ============================================
-- NOT: Temp tablo zaten oluşturulmuş
-- Temiz veriler zaten eklenmiş durumda
-- Sadece eski çoğalan verileri siliyoruz
-- ============================================



