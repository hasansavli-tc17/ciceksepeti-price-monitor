-- 📊 2023-2025 Aylık Sipariş ve order_code Özeti

SELECT 
    EXTRACT(YEAR FROM order_delivery_date) as yil,
    EXTRACT(MONTH FROM order_delivery_date) as ay,
    FORMAT_DATE('%Y-%m', order_delivery_date) as yil_ay,
    FORMAT_DATE('%B %Y', order_delivery_date) as ay_adi,
    
    -- Sipariş sayıları
    COUNT(DISTINCT order_id) as toplam_siparis,
    COUNT(*) as toplam_satir,
    
    -- order_code durumu
    COUNT(DISTINCT CASE WHEN order_code IS NOT NULL THEN order_id END) as order_code_olan_siparis,
    COUNT(DISTINCT CASE WHEN order_code IS NULL THEN order_id END) as order_code_olmayan_siparis,
    COUNT(order_code) as order_code_dolu_satir,
    COUNT(*) - COUNT(order_code) as order_code_bos_satir,
    
    -- Yüzdeler
    ROUND(COUNT(DISTINCT CASE WHEN order_code IS NOT NULL THEN order_id END) * 100.0 / NULLIF(COUNT(DISTINCT order_id), 0), 2) as order_code_kapsami_pct,
    
    -- Ortalama
    ROUND(COUNT(*) * 1.0 / NULLIF(COUNT(DISTINCT order_id), 0), 2) as ortalama_urun_per_siparis

FROM 
    `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE 
    order_delivery_date >= '2023-01-01'
    AND order_delivery_date < '2026-01-01'
GROUP BY 
    yil, ay, yil_ay, ay_adi
ORDER BY 
    yil, ay
