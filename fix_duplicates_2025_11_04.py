#!/usr/bin/env python3
"""
4 Kasım 2025 tarihindeki çoğalan verileri otomatik temizler.
"""
import os
from google.cloud import bigquery
from datetime import datetime

PROJECT_ID = "tazecicekdb"
DATASET = "order_data"
TABLE = "order_items_clean_v3_enriched_partitioned_clustered"
TARGET_DATE = "2025-11-04"

bq_client = bigquery.Client(project=PROJECT_ID)
table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"
backup_table = f"{PROJECT_ID}.{DATASET}.order_items_clean_v3_enriched_partitioned_clustered_backup_2025_11_04"
temp_table = f"{PROJECT_ID}.{DATASET}.temp_2025_11_04_clean"

def print_step(step_num, description):
    print(f"\n{'='*60}")
    print(f"ADIM {step_num}: {description}")
    print(f"{'='*60}")

def check_duplicates():
    """Çoğalan kayıtları kontrol et"""
    print_step(1, "Çoğalan Kayıtları Kontrol Etme")
    
    query = f"""
    SELECT 
      COUNT(*) as total_rows,
      COUNT(DISTINCT TO_JSON_STRING(t)) as unique_rows,
      COUNT(*) - COUNT(DISTINCT TO_JSON_STRING(t)) as exact_duplicates
    FROM `{table_id}` t
    WHERE order_created_date_tr = "{TARGET_DATE}"
    """
    
    result = bq_client.query(query).result()
    row = list(result)[0]
    
    print(f"Toplam satır sayısı: {row.total_rows}")
    print(f"Benzersiz satır sayısı: {row.unique_rows}")
    print(f"Çoğalan satır sayısı: {row.exact_duplicates}")
    
    return row.total_rows, row.unique_rows, row.exact_duplicates

def create_backup():
    """Yedek oluştur"""
    print_step(2, "Yedek Oluşturma")
    
    query = f"""
    CREATE TABLE IF NOT EXISTS `{backup_table}`
    AS 
    SELECT * 
    FROM `{table_id}`
    WHERE order_created_date_tr = "{TARGET_DATE}"
    """
    
    job = bq_client.query(query)
    job.result()  # Wait for completion
    print(f"✅ Yedek oluşturuldu: {backup_table}")

def create_clean_data():
    """Temiz veriyi oluştur"""
    print_step(3, "Temiz Veriyi Oluşturma")
    
    query = f"""
    CREATE OR REPLACE TABLE `{temp_table}` AS
    SELECT 
      * EXCEPT(row_num, row_hash)
    FROM (
      SELECT 
        *,
        FARM_FINGERPRINT(TO_JSON_STRING(t)) as row_hash,
        ROW_NUMBER() OVER (
          PARTITION BY FARM_FINGERPRINT(TO_JSON_STRING(t))
          ORDER BY 
            COALESCE(order_creation_timestamp, CURRENT_TIMESTAMP()) DESC
        ) as row_num
      FROM `{table_id}` t
      WHERE order_created_date_tr = "{TARGET_DATE}"
    )
    WHERE row_num = 1
    """
    
    job = bq_client.query(query)
    job.result()
    print(f"✅ Temiz veri oluşturuldu: {temp_table}")

def check_streaming_buffer():
    """Streaming buffer kontrolü"""
    query = f"""
    SELECT COUNT(*) as streaming_rows
    FROM `{table_id}`
    WHERE order_created_date_tr = "{TARGET_DATE}"
    AND _PARTITIONTIME IS NULL
    """
    try:
        result = bq_client.query(query).result()
        row = list(result)[0]
        return row.streaming_rows > 0
    except:
        return False

def delete_old_data():
    """Eski verileri sil - Streaming buffer sorunu için alternatif yöntem"""
    print_step(4, "Eski Verileri Silme")
    
    # Önce DELETE denemesi yap
    query = f"""
    DELETE FROM `{table_id}`
    WHERE order_created_date_tr = "{TARGET_DATE}"
    """
    
    try:
        job = bq_client.query(query)
        job.result()
        print("✅ Eski veriler silindi")
    except Exception as e:
        error_msg = str(e).lower()
        if "streaming buffer" in error_msg:
            print("⚠️ Streaming buffer hatası alındı!")
            print("📝 Çözüm: BigQuery'de son 30 dakikada streaming insert yapılmış.")
            print("   30 dakika bekleyip tekrar deneyin veya şu SQL'i BigQuery Console'da çalıştırın:\n")
            print(f"   DELETE FROM `{table_id}`")
            print(f"   WHERE order_created_date_tr = \"{TARGET_DATE}\";\n")
            print("⚠️ Şimdilik DELETE adımını atlayıp, sadece temiz veriyi INSERT ediyorum...")
            print("   (Bu durumda eski çoğalan veriler kalabilir, sonra manuel silmeniz gerekebilir)")
            # DELETE başarısız olsa bile devam et, INSERT yapılsın
            return
        else:
            raise

def restore_clean_data():
    """Temiz verileri geri yükle"""
    print_step(5, "Temiz Verileri Geri Yükleme")
    
    query = f"""
    INSERT INTO `{table_id}`
    SELECT * FROM `{temp_table}`
    """
    
    job = bq_client.query(query)
    job.result()
    print("✅ Temiz veriler geri yüklendi")

def cleanup_temp_table():
    """Temp tabloyu sil"""
    print_step(6, "Temp Tabloyu Temizleme")
    
    bq_client.delete_table(temp_table, not_found_ok=True)
    print(f"✅ Temp tablo silindi: {temp_table}")

def verify_results():
    """Sonuçları doğrula"""
    print_step(7, "Sonuçları Doğrulama")
    
    query = f"""
    SELECT 
      COUNT(*) as total_rows_after_cleanup,
      COUNT(DISTINCT TO_JSON_STRING(t)) as unique_rows_after_cleanup,
      COUNT(*) - COUNT(DISTINCT TO_JSON_STRING(t)) as remaining_duplicates
    FROM `{table_id}` t
    WHERE order_created_date_tr = "{TARGET_DATE}"
    """
    
    result = bq_client.query(query).result()
    row = list(result)[0]
    
    print(f"Temizleme sonrası toplam satır: {row.total_rows_after_cleanup}")
    print(f"Temizleme sonrası benzersiz satır: {row.unique_rows_after_cleanup}")
    print(f"Kalan çoğalan satır: {row.remaining_duplicates}")
    
    if row.remaining_duplicates == 0:
        print("\n✅ BAŞARILI! Tüm çoğalan kayıtlar temizlendi.")
    else:
        print(f"\n⚠️ DİKKAT: Hala {row.remaining_duplicates} çoğalan kayıt var.")

def main():
    import sys
    
    print(f"\n🔧 4 Kasım 2025 Çoğalan Veri Temizleme İşlemi Başlatılıyor...")
    print(f"Tarih: {TARGET_DATE}")
    print(f"Tablo: {table_id}\n")
    
    # Önce durumu kontrol et
    total, unique, duplicates = check_duplicates()
    
    if duplicates == 0:
        print("\n✅ Çoğalan kayıt bulunamadı. Temizleme gerekmiyor.")
        return
    
    # Eğer --yes parametresi yoksa kullanıcı onayı iste
    auto_confirm = '--yes' in sys.argv or '-y' in sys.argv
    
    if not auto_confirm:
        response = input(f"\n{duplicates} adet çoğalan kayıt bulundu. Temizleme işlemine devam edilsin mi? (evet/hayır): ")
        if response.lower() not in ['evet', 'e', 'yes', 'y']:
            print("❌ İşlem iptal edildi.")
            return
    else:
        print(f"\n{duplicates} adet çoğalan kayıt bulundu. Otomatik onay ile devam ediliyor...")
    
    try:
        # İşlemleri sırayla yap
        create_backup()
        create_clean_data()
        delete_old_data()
        restore_clean_data()
        cleanup_temp_table()
        verify_results()
        
        print(f"\n🎉 İşlem tamamlandı! Yedek tablo: {backup_table}")
        
    except Exception as e:
        print(f"\n❌ HATA: {str(e)}")
        print(f"\n⚠️ Yedek tablodan geri yükleme yapabilirsiniz: {backup_table}")
        raise

if __name__ == "__main__":
    main()
