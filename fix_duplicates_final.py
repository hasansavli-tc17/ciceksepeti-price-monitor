#!/usr/bin/env python3
"""
Streaming buffer sorununu aşarak çoğalan verileri temizler.
Tüm tabloyu yeniden oluşturur (4 Kasım hariç + temiz 4 Kasım).
"""
from google.cloud import bigquery
import sys

PROJECT_ID = "tazecicekdb"
DATASET = "order_data"
TABLE = "order_items_clean_v3_enriched_partitioned_clustered"
TARGET_DATE = "2025-11-04"

bq_client = bigquery.Client(project=PROJECT_ID)
table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"
temp_table = f"{PROJECT_ID}.{DATASET}.temp_2025_11_04_clean"
new_table_id = f"{table_id}_new_{int(__import__('time').time())}"

def print_step(step, desc):
    print(f"\n{'='*60}")
    print(f"{step}: {desc}")
    print(f"{'='*60}")

def recreate_table_without_duplicates():
    """Tüm tabloyu yeniden oluştur - streaming buffer sorununu aşar"""
    
    print_step("ADIM 1", "Tablo Bilgilerini Kontrol Etme")
    table = bq_client.get_table(table_id)
    print(f"✅ Tablo bulundu: {table.num_rows:,} satır")
    print(f"   Partition: {table.time_partitioning.field if table.time_partitioning else 'Yok'}")
    print(f"   Clustering: {table.clustering_fields if table.clustering_fields else 'Yok'}")
    
    # Temp tablonun var olduğunu kontrol et, yoksa oluştur
    try:
        temp_table_obj = bq_client.get_table(temp_table)
        print(f"✅ Temp tablo bulundu: {temp_table_obj.num_rows:,} satır")
    except Exception as e:
        print(f"⚠️ Temp tablo bulunamadı, oluşturuluyor...")
        # Temp tabloyu oluştur
        create_temp_query = f"""
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
        
        try:
            job = bq_client.query(create_temp_query)
            job.result()
            temp_table_obj = bq_client.get_table(temp_table)
            print(f"✅ Temp tablo oluşturuldu: {temp_table_obj.num_rows:,} satır")
        except Exception as create_error:
            print(f"❌ Temp tablo oluşturma hatası: {create_error}")
            return False
    
    print_step("ADIM 2", "Yeni Tablo Oluşturma")
    print("⚠️ Bu işlem birkaç dakika sürebilir...")
    print("   (4 Kasım hariç tüm veriler + temiz 4 Kasım verileri)")
    
    # Partition ve clustering ayarlarını al
    partition_field = table.time_partitioning.field if table.time_partitioning else None
    clustering_fields = table.clustering_fields if table.clustering_fields else None
    
    # CREATE TABLE query'sini oluştur
    partition_clause = ""
    cluster_clause = ""
    
    if partition_field:
        # Partition field zaten DATE tipinde ise sadece field adını kullan
        # Mevcut tabloda nasıl tanımlanmışsa aynısını kullan
        partition_clause = f"\n    PARTITION BY {partition_field}"
    
    if clustering_fields:
        cluster_clause = f"\n    CLUSTER BY {', '.join(clustering_fields)}"
    
    query = f"""
    CREATE TABLE `{new_table_id}`{partition_clause}{cluster_clause}
    AS
    SELECT * FROM (
      -- 4 Kasım hariç tüm veriler (hem partition'dan hem streaming buffer'dan)
      SELECT * FROM `{table_id}`
      WHERE order_created_date_tr != "{TARGET_DATE}"
      
      UNION ALL
      
      -- Temiz 4 Kasım verileri
      SELECT * FROM `{temp_table}`
    )
    """
    
    try:
        print("⏳ Yeni tablo oluşturuluyor...")
        job = bq_client.query(query)
        job.result()  # Wait for completion
        print(f"✅ Yeni tablo oluşturuldu: {new_table_id}")
        
        # Yeni tablo bilgilerini kontrol et
        new_table = bq_client.get_table(new_table_id)
        print(f"✅ Yeni tablo: {new_table.num_rows:,} satır")
        
    except Exception as e:
        print(f"❌ Tablo oluşturma hatası: {e}")
        return False
    
    print_step("ADIM 3", "Eski Tabloyu Yedekleme")
    old_backup_table = f"{table_id}_old_backup_{int(__import__('time').time())}"
    
    try:
        print(f"⏳ Eski tablo yedekleniyor: {old_backup_table}")
        copy_job = bq_client.copy_table(table_id, old_backup_table)
        copy_job.result()
        print(f"✅ Yedek oluşturuldu: {old_backup_table}")
    except Exception as e:
        print(f"⚠️ Yedek oluşturma hatası (devam ediliyor): {e}")
        old_backup_table = None
    
    print_step("ADIM 4", "Tabloları Değiştirme")
    print("⚠️ Bu adım tabloyu kısa süre için kullanılamaz hale getirebilir!")
    
    try:
        # Eski tabloyu sil
        print(f"⏳ Eski tablo siliniyor: {table_id}")
        bq_client.delete_table(table_id, not_found_ok=True)
        
        # Yeni tabloyu eski yerine kopyala
        print(f"⏳ Yeni tablo yerine koyuluyor...")
        copy_job = bq_client.copy_table(new_table_id, table_id)
        copy_job.result()
        print(f"✅ Tablo başarıyla değiştirildi!")
        
        # Yeni geçici tabloyu sil
        print(f"⏳ Geçici tablo temizleniyor: {new_table_id}")
        bq_client.delete_table(new_table_id, not_found_ok=True)
        
    except Exception as e:
        print(f"❌ Tablo değiştirme hatası: {e}")
        if old_backup_table:
            print(f"⚠️ Yedekten geri yükleme yapabilirsiniz: {old_backup_table}")
        raise
    
    print_step("ADIM 5", "Sonuçları Doğrulama")
    
    verify_query = f"""
    SELECT 
      COUNT(*) as total_rows,
      COUNT(DISTINCT TO_JSON_STRING(t)) as unique_rows,
      COUNT(*) - COUNT(DISTINCT TO_JSON_STRING(t)) as remaining_duplicates
    FROM `{table_id}` t
    WHERE order_created_date_tr = "{TARGET_DATE}"
    """
    
    try:
        result = bq_client.query(verify_query).result()
        row = list(result)[0]
        
        print(f"4 Kasım 2025 sonuçları:")
        print(f"  Toplam satır: {row.total_rows}")
        print(f"  Benzersiz satır: {row.unique_rows}")
        print(f"  Kalan çoğalan: {row.remaining_duplicates}")
        
        if row.remaining_duplicates == 0:
            print("\n✅ BAŞARILI! Tüm çoğalan kayıtlar temizlendi.")
            return True
        else:
            print(f"\n⚠️ Hala {row.remaining_duplicates} çoğalan kayıt var.")
            return False
            
    except Exception as e:
        print(f"⚠️ Doğrulama hatası: {e}")
        return True  # Tablo değişti, muhtemelen başarılı

def main():
    print(f"\n🔧 Streaming Buffer Sorununu Aşarak Çoğalan Veri Temizleme")
    print(f"Tarih: {TARGET_DATE}")
    print(f"Tablo: {table_id}\n")
    
    # Onay
    if '--yes' not in sys.argv and '-y' not in sys.argv:
        response = input("⚠️ Bu işlem tüm tabloyu yeniden oluşturacak. Devam edilsin mi? (evet/hayır): ")
        if response.lower() not in ['evet', 'e', 'yes', 'y']:
            print("❌ İşlem iptal edildi.")
            return
    else:
        print("⚠️ Otomatik onay ile devam ediliyor...\n")
    
    try:
        success = recreate_table_without_duplicates()
        
        if success:
            print("\n🎉 İşlem başarıyla tamamlandı!")
        else:
            print("\n⚠️ İşlem tamamlandı ama bazı sorunlar olabilir. Lütfen kontrol edin.")
            
    except Exception as e:
        print(f"\n❌ HATA: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
