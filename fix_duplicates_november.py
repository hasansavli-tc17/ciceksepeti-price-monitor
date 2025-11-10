#!/usr/bin/env python3
"""
Kasım 2025 tarihlerindeki çoğalan verileri temizler.
"""
from google.cloud import bigquery
import sys

PROJECT_ID = "tazecicekdb"
DATASET = "order_data"
TABLE = "order_items_clean_v3_enriched_partitioned_clustered"

bq_client = bigquery.Client(project=PROJECT_ID)
table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"

def print_step(step, desc):
    print(f"\n{'='*60}")
    print(f"{step}: {desc}")
    print(f"{'='*60}")

def check_duplicates_for_date(target_date):
    """Belirli bir tarih için çoğalan kayıtları kontrol et"""
    query = f"""
    SELECT 
      COUNT(*) as total_rows,
      COUNT(DISTINCT TO_JSON_STRING(t)) as unique_rows,
      COUNT(*) - COUNT(DISTINCT TO_JSON_STRING(t)) as exact_duplicates
    FROM `{table_id}` t
    WHERE order_created_date_tr = "{target_date}"
    """
    
    result = bq_client.query(query).result()
    row = list(result)[0]
    return row.total_rows, row.unique_rows, row.exact_duplicates

def fix_duplicates_for_date(target_date):
    """Belirli bir tarih için çoğalan kayıtları temizle"""
    print_step(f"TARİH: {target_date}", "Çoğalan Kayıt Temizleme")
    
    # Kontrol
    total, unique, duplicates = check_duplicates_for_date(target_date)
    print(f"Toplam satır: {total:,}")
    print(f"Benzersiz satır: {unique:,}")
    print(f"Çoğalan satır: {duplicates:,}")
    
    if duplicates == 0:
        print("✅ Çoğalan kayıt yok, temizleme gerekmiyor.")
        return True
    
    # Yedek al
    backup_table = f"{table_id}_backup_{target_date.replace('-', '_')}"
    print(f"\n📦 Yedek oluşturuluyor: {backup_table}")
    backup_query = f"""
    CREATE TABLE IF NOT EXISTS `{backup_table}`
    AS 
    SELECT * 
    FROM `{table_id}`
    WHERE order_created_date_tr = "{target_date}"
    """
    bq_client.query(backup_query).result()
    print("✅ Yedek oluşturuldu")
    
    # Temiz veri oluştur
    temp_table = f"{PROJECT_ID}.{DATASET}.temp_clean_{target_date.replace('-', '_')}"
    print(f"\n🧹 Temiz veri oluşturuluyor...")
    clean_query = f"""
    CREATE OR REPLACE TABLE `{temp_table}` AS
    SELECT 
      * EXCEPT(row_num)
    FROM (
      SELECT 
        *,
        ROW_NUMBER() OVER (
          PARTITION BY TO_JSON_STRING(t)
          ORDER BY 
            COALESCE(order_creation_timestamp, CURRENT_TIMESTAMP()) DESC
        ) as row_num
      FROM `{table_id}` t
      WHERE order_created_date_tr = "{target_date}"
    )
    WHERE row_num = 1
    """
    bq_client.query(clean_query).result()
    print("✅ Temiz veri oluşturuldu")
    
    # Eski verileri sil
    print(f"\n🗑️  Eski veriler siliniyor...")
    delete_query = f"""
    DELETE FROM `{table_id}`
    WHERE order_created_date_tr = "{target_date}"
    """
    try:
        bq_client.query(delete_query).result()
        print("✅ Eski veriler silindi")
    except Exception as e:
        if "streaming buffer" in str(e).lower():
            print("⚠️ Streaming buffer hatası! Lütfen 30 dakika bekleyip tekrar deneyin.")
            return False
        else:
            raise
    
    # Temiz verileri geri yükle
    print(f"\n📥 Temiz veriler geri yükleniyor...")
    insert_query = f"""
    INSERT INTO `{table_id}`
    SELECT * FROM `{temp_table}`
    """
    bq_client.query(insert_query).result()
    print("✅ Temiz veriler geri yüklendi")
    
    # Temp tabloyu sil
    print(f"\n🧹 Temp tablo temizleniyor...")
    bq_client.delete_table(temp_table, not_found_ok=True)
    print("✅ Temp tablo silindi")
    
    # Doğrula
    print(f"\n✅ Doğrulama...")
    total_after, unique_after, duplicates_after = check_duplicates_for_date(target_date)
    print(f"Temizleme sonrası:")
    print(f"  Toplam satır: {total_after:,}")
    print(f"  Benzersiz satır: {unique_after:,}")
    print(f"  Çoğalan satır: {duplicates_after:,}")
    
    if duplicates_after == 0:
        print("\n✅ BAŞARILI! Tüm çoğalan kayıtlar temizlendi.")
        return True
    else:
        print(f"\n⚠️ Hala {duplicates_after} çoğalan kayıt var.")
        return False

def main():
    print("\n🔧 Kasım 2025 Çoğalan Veri Temizleme")
    print("="*60)
    
    # Kasım 2025 tarihlerini kontrol et
    query = """
    SELECT 
      DATE(order_created_date_tr) AS order_date,
      COUNT(*) AS row_count,
      COUNT(DISTINCT order_id) AS unique_orders,
      COUNT(*) - COUNT(DISTINCT order_id) AS potential_duplicates
    FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
    WHERE order_created_date_tr IS NOT NULL
      AND EXTRACT(YEAR FROM order_created_date_tr) = 2025
      AND EXTRACT(MONTH FROM order_created_date_tr) = 11
    GROUP BY order_date
    HAVING COUNT(*) > COUNT(DISTINCT order_id)
    ORDER BY order_date DESC
    """
    
    result = bq_client.query(query).result()
    dates_with_duplicates = list(result)
    
    if not dates_with_duplicates:
        print("✅ Çoğalan kayıt bulunamadı!")
        return
    
    print(f"\n📊 Çoğalan kayıt bulunan tarihler:")
    for row in dates_with_duplicates:
        print(f"  {row.order_date}: {row.potential_duplicates:,} çoğalan satır")
    
    # Tüm tarihleri temizle
    if '--yes' in sys.argv or '-y' in sys.argv:
        auto_confirm = True
    else:
        response = input(f"\n{len(dates_with_duplicates)} tarih için temizleme yapılsın mı? (evet/hayır): ")
        auto_confirm = response.lower() in ['evet', 'e', 'yes', 'y']
    
    if not auto_confirm:
        print("❌ İşlem iptal edildi.")
        return
    
    success_count = 0
    for row in dates_with_duplicates:
        if fix_duplicates_for_date(str(row.order_date)):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"✅ {success_count}/{len(dates_with_duplicates)} tarih başarıyla temizlendi!")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()




