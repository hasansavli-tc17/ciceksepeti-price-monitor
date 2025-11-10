-- ============================================
-- 4 KASIM 2025 ÇOĞALAN VERİLERİ SİLME
-- ============================================
-- Bu SQL'i BigQuery Console'da çalıştırın
-- https://console.cloud.google.com/bigquery

-- NOT: Streaming buffer hatası alırsanız, 30 dakika bekleyip tekrar deneyin
-- veya streaming insert'lerin tamamlanmasını bekleyin

-- ÖNCE YEDEK ZATEN ALINMIŞ:
-- tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered_backup_2025_11_04

-- ÇOĞALAN VERİLERİ SİL:
DELETE FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE order_created_date_tr = "2025-11-04";

-- SONUÇLARI KONTROL ET:
SELECT 
  COUNT(*) as total_rows,
  COUNT(DISTINCT TO_JSON_STRING(t)) as unique_rows,
  COUNT(*) - COUNT(DISTINCT TO_JSON_STRING(t)) as remaining_duplicates
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered` t
WHERE order_created_date_tr = "2025-11-04";

-- Temiz veriler zaten eklenmiş durumda, sadece eski çoğalan verileri siliyoruz.
-- Beklenen sonuç: ~2652 benzersiz satır kalmalı



