#!/usr/bin/env python3
"""
4 Kasım 2025 verilerini her iki tabloda kontrol eder.
"""
from google.cloud import bigquery

PROJECT_ID = "tazecicekdb"
bq_client = bigquery.Client(project=PROJECT_ID)

tables = [
    "order_items_clean_v3_enriched_partitioned_clustered",
    "order_items_clean_v3_partitioned_v1"
]

print("="*60)
print("4 KASIM 2025 VERİ KONTROLÜ")
print("="*60)

for table_name in tables:
    table_id = f"{PROJECT_ID}.order_data.{table_name}"
    
    print(f"\n📊 Tablo: {table_name}")
    print("-" * 60)
    
    # Tablo bilgilerini kontrol et
    try:
        table = bq_client.get_table(table_id)
        print(f"✅ Tablo bulundu: {table.num_rows:,} toplam satır")
        
        # Sütun isimlerini kontrol et
        date_column = None
        if 'order_created_date_tr' in [col.name for col in table.schema]:
            date_column = 'order_created_date_tr'
        elif 'order_created_date' in [col.name for col in table.schema]:
            date_column = 'order_created_date'
        
        if not date_column:
            print("⚠️ Tarih sütunu bulunamadı!")
            continue
        
        print(f"📅 Tarih sütunu: {date_column}")
        
        # 4 Kasım verilerini kontrol et
        if date_column == 'order_created_date_tr':
            query = f"""
            SELECT 
              order_created_date_tr AS order_date,
              COUNT(*) AS row_count,
              COUNT(DISTINCT order_id) AS unique_orders
            FROM `{table_id}`
            WHERE order_created_date_tr = "2025-11-04"
            GROUP BY order_created_date_tr
            """
        else:
            query = f"""
            SELECT 
              DATE(order_created_date) AS order_date,
              COUNT(*) AS row_count,
              COUNT(DISTINCT order_id) AS unique_orders
            FROM `{table_id}`
            WHERE DATE(order_created_date) = "2025-11-04"
            GROUP BY DATE(order_created_date)
            """
        
        result = bq_client.query(query).result()
        rows = list(result)
        
        if rows:
            for row in rows:
                print(f"✅ 4 Kasım 2025:")
                print(f"   Tarih: {row.order_date}")
                print(f"   Toplam satır: {row.row_count:,}")
                print(f"   Benzersiz sipariş: {row.unique_orders:,}")
        else:
            print("❌ 4 Kasım 2025 için veri bulunamadı!")
            
            # Kasım ayı genel kontrol
            if date_column == 'order_created_date_tr':
                query_nov = f"""
                SELECT 
                  order_created_date_tr AS order_date,
                  COUNT(*) AS row_count
                FROM `{table_id}`
                WHERE EXTRACT(YEAR FROM order_created_date_tr) = 2025
                  AND EXTRACT(MONTH FROM order_created_date_tr) = 11
                GROUP BY order_created_date_tr
                ORDER BY order_created_date_tr DESC
                LIMIT 10
                """
            else:
                query_nov = f"""
                SELECT 
                  DATE(order_created_date) AS order_date,
                  COUNT(*) AS row_count
                FROM `{table_id}`
                WHERE EXTRACT(YEAR FROM DATE(order_created_date)) = 2025
                  AND EXTRACT(MONTH FROM DATE(order_created_date)) = 11
                GROUP BY DATE(order_created_date)
                ORDER BY DATE(order_created_date) DESC
                LIMIT 10
                """
            
            result_nov = bq_client.query(query_nov).result()
            rows_nov = list(result_nov)
            
            if rows_nov:
                print(f"\n📅 Kasım 2025'teki mevcut tarihler:")
                for row in rows_nov:
                    print(f"   {row.order_date}: {row.row_count:,} satır")
            else:
                print("⚠️ Kasım 2025'te hiç veri yok!")
    
    except Exception as e:
        print(f"❌ Hata: {e}")

print("\n" + "="*60)
print("NOT: Eğer enriched tabloda veri varsa ama partitioned_v1'de yoksa,")
print("partitioned_v1 tablosu farklı bir tablo olabilir veya")
print("veri enriched tabloya yazılıyor ama partitioned_v1'e yazılmıyor olabilir.")
print("="*60)



