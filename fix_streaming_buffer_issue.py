#!/usr/bin/env python3
"""
Streaming buffer sorununu çözmek için alternatif yöntem.
Streaming buffer'daki verileri de dahil ederek, 4 Kasım verilerini yeniden yazıyor.
"""
from google.cloud import bigquery
import time

PROJECT_ID = "tazecicekdb"
DATASET = "order_data"
TABLE = "order_items_clean_v3_enriched_partitioned_clustered"
TARGET_DATE = "2025-11-04"

bq_client = bigquery.Client(project=PROJECT_ID)
table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"
temp_table = f"{PROJECT_ID}.{DATASET}.temp_2025_11_04_clean"

def check_streaming_buffer():
    """Streaming buffer'daki satır sayısını kontrol et"""
    print("\n📊 Streaming buffer kontrol ediliyor...")
    
    # Streaming buffer'daki verileri kontrol et (yeni eklenenler)
    query = f"""
    SELECT COUNT(*) as streaming_count
    FROM `{table_id}`
    WHERE order_created_date_tr = "{TARGET_DATE}"
    AND _PARTITIONTIME IS NULL
    """
    
    try:
        result = bq_client.query(query).result()
        row = list(result)[0]
        return row.streaming_count
    except Exception as e:
        print(f"⚠️ Streaming buffer kontrolü başarısız: {e}")
        return 0

def wait_for_streaming_buffer(max_wait_minutes=30):
    """Streaming buffer'ın temizlenmesini bekle"""
    print(f"\n⏳ Streaming buffer kontrol ediliyor...")
    
    for i in range(max_wait_minutes):
        streaming_count = check_streaming_buffer()
        
        if streaming_count == 0:
            print("✅ Streaming buffer temizlendi!")
            return True
        
        print(f"   Bekleniyor... ({i+1}/{max_wait_minutes} dakika) - Streaming buffer'da {streaming_count} satır var")
        time.sleep(60)  # 1 dakika bekle
    
    print(f"⚠️ {max_wait_minutes} dakika sonra hala streaming buffer var")
    return False

def fix_with_merge():
    """MERGE kullanarak çoğalan verileri temizle"""
    print("\n🔄 MERGE yöntemi ile temizleme deneniyor...")
    
    # MERGE kullanarak: Eğer kayıt varsa güncelle, yoksa ekle
    # Ama bu yöntem de streaming buffer'da çalışmayabilir
    query = f"""
    MERGE `{table_id}` AS target
    USING `{temp_table}` AS source
    ON FALSE  -- Her kayıt benzersiz olduğu için ON condition yok
    WHEN NOT MATCHED BY SOURCE 
      AND target.order_created_date_tr = "{TARGET_DATE}"
    THEN DELETE
    WHEN NOT MATCHED BY TARGET
    THEN INSERT ROW
    """
    
    try:
        job = bq_client.query(query)
        job.result()
        print("✅ MERGE başarılı!")
        return True
    except Exception as e:
        print(f"❌ MERGE başarısız: {e}")
        return False

def fix_with_table_recreation():
    """Tüm tabloyu yeniden oluştur (4 Kasım hariç + temiz 4 Kasım)"""
    print("\n🔄 Tablo yeniden oluşturuluyor (streaming buffer sorunu için)...")
    print("⚠️ Bu işlem büyük tablolarda uzun sürebilir!")
    
    # Önce tablo bilgilerini al
    table = bq_client.get_table(table_id)
    print(f"📋 Tablo boyutu: {table.num_rows:,} satır")
    print(f"📋 Partition: {table.time_partitioning.field if table.time_partitioning else 'Yok'}")
    
    # Yeni tablo oluştur: 4 Kasım hariç + temiz 4 Kasım
    new_table_id = f"{table_id}_new"
    
    query = f"""
    CREATE TABLE `{new_table_id}`
    PARTITION BY DATE(order_created_date_tr)
    CLUSTER BY order_id
    AS
    SELECT * FROM (
      -- 4 Kasım hariç tüm veriler
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
        job.result()
        print(f"✅ Yeni tablo oluşturuldu: {new_table_id}")
        
        # Eski tabloyu sil ve yenisini yerine koy
        print("🔄 Tablolar değiştiriliyor...")
        
        # Eski tabloyu yedekle
        old_table_id = f"{table_id}_old"
        bq_client.copy_table(table_id, old_table_id)
        print(f"✅ Eski tablo yedeklendi: {old_table_id}")
        
        # Yeni tabloyu eski yerine koy
        bq_client.delete_table(table_id, not_found_ok=True)
        bq_client.copy_table(new_table_id, table_id)
        print(f"✅ Yeni tablo yerine koyuldu")
        
        # Geçici tabloları temizle
        bq_client.delete_table(new_table_id, not_found_ok=True)
        
        return True
        
    except Exception as e:
        print(f"❌ Tablo yeniden oluşturma başarısız: {e}")
        return False

def main():
    import sys
    
    print(f"\n🔧 Streaming Buffer Sorunu Çözümü")
    print(f"Tarih: {TARGET_DATE}\n")
    
    # Streaming buffer kontrolü
    streaming_count = check_streaming_buffer()
    
    if streaming_count > 0:
        print(f"⚠️ Streaming buffer'da {streaming_count} satır var")
        print("\nSeçenekler:")
        print("1. Streaming buffer'ın temizlenmesini bekle (önerilen)")
        print("2. Tablo yeniden oluşturma yöntemi (riskli, uzun sürebilir)")
        
        if '--wait' in sys.argv:
            print("\n⏳ Streaming buffer'ın temizlenmesi bekleniyor...")
            if wait_for_streaming_buffer():
                # Bekleme başarılı, normal DELETE yapılabilir
                from fix_duplicates_2025_11_04 import delete_old_data, restore_clean_data
                delete_old_data()
                return
        elif '--recreate' in sys.argv:
            # Tablo yeniden oluştur
            if fix_with_table_recreation():
                print("✅ Başarılı!")
                return
        else:
            print("\n💡 Kullanım:")
            print("   python fix_streaming_buffer_issue.py --wait     # 30 dakika bekle")
            print("   python fix_streaming_buffer_issue.py --recreate # Tabloyu yeniden oluştur")
            print("\n⚠️ En güvenli yöntem: 30 dakika bekleyip delete_duplicates_manual.sql'i çalıştırın")
            return
    
    # Streaming buffer yoksa normal DELETE çalışabilir
    print("✅ Streaming buffer yok, normal DELETE yapılabilir")
    from fix_duplicates_2025_11_04 import delete_old_data
    delete_old_data()

if __name__ == "__main__":
    main()



