#!/usr/bin/env python3
from google.cloud import bigquery
import time

PROJECT_ID = 'tazecicekdb'
DATASET = 'order_data'
TABLE = 'order_items_clean_v3_enriched_partitioned_clustered'
TARGET_DATE = '2025-11-05'

bq_client = bigquery.Client(project=PROJECT_ID, location='europe-west3')
table_id = f'{PROJECT_ID}.{DATASET}.{TABLE}'

print(f'🧹 {TARGET_DATE} duplicate temizleme başlatılıyor...')

# 1. Durum kontrolü
print('📊 Mevcut durum kontrol ediliyor...')
check_query = f'''
SELECT 
  COUNT(*) as total_rows,
  COUNT(DISTINCT TO_JSON_STRING(t)) as unique_rows,
  COUNT(*) - COUNT(DISTINCT TO_JSON_STRING(t)) as exact_duplicates
FROM `{table_id}` t
WHERE order_created_date_tr = "{TARGET_DATE}"
'''
result = bq_client.query(check_query).result()
row = list(result)[0]
print(f'  Toplam satır: {row.total_rows:,}')
print(f'  Unique satır: {row.unique_rows:,}')
print(f'  Duplicates: {row.exact_duplicates:,}')

if row.exact_duplicates == 0:
    print('✅ Duplicate yok, temizleme gerekmiyor.')
    exit(0)

# 2. Temiz veri oluştur
temp_table = f'{PROJECT_ID}.{DATASET}.temp_clean_{TARGET_DATE.replace("-", "")}_{int(time.time())}'
print(f'\n⏳ Temiz veri oluşturuluyor: {temp_table}')
clean_query = f'''
CREATE OR REPLACE TABLE `{temp_table}`
PARTITION BY order_created_date_tr
CLUSTER BY order_id
AS
SELECT * EXCEPT(row_num)
FROM (
  SELECT *,
    ROW_NUMBER() OVER (
      PARTITION BY TO_JSON_STRING(t)
      ORDER BY COALESCE(order_creation_timestamp, CURRENT_TIMESTAMP()) DESC
    ) as row_num
  FROM `{table_id}` t
  WHERE order_created_date_tr = "{TARGET_DATE}"
)
WHERE row_num = 1
'''
bq_client.query(clean_query).result()
print('✅ Temiz veri oluşturuldu')

# 3. Yeni tablo oluştur (diğer günler + temiz hedef gün)
table = bq_client.get_table(table_id)
partition_field = table.time_partitioning.field if table.time_partitioning else None
cluster_fields = table.clustering_fields if table.clustering_fields else []

new_table_id = f'{table_id}_new_{int(time.time())}'
print(f'\n⏳ Yeni tablo oluşturuluyor: {new_table_id}')

partition_clause = f'PARTITION BY {partition_field}' if partition_field else ''
cluster_clause = f'CLUSTER BY {", ".join(cluster_fields)}' if cluster_fields else ''

new_table_query = f'''
CREATE TABLE `{new_table_id}`
{partition_clause}
{cluster_clause}
AS
SELECT * FROM (
  SELECT * FROM `{table_id}` WHERE order_created_date_tr != "{TARGET_DATE}"
  UNION ALL
  SELECT * FROM `{temp_table}`
)
'''
bq_client.query(new_table_query).result()
print('✅ Yeni tablo oluşturuldu')

# 4. Yedek, sil, kopyala
backup_table = f'{table_id}_backup_{TARGET_DATE.replace("-", "")}_{int(time.time())}'
print(f'\n⏳ Yedekleme: {backup_table}')
bq_client.copy_table(table_id, backup_table).result()
print('✅ Yedek oluşturuldu')

print('⏳ Eski tablo siliniyor...')
bq_client.delete_table(table_id, not_found_ok=True)
print('✅ Eski tablo silindi')

print('⏳ Yeni tablo kopyalanıyor...')
bq_client.copy_table(new_table_id, table_id).result()
print('✅ Yeni tablo kopyalandı')

# 5. Temizlik
print('\n🗑️  Geçici tablolar siliniyor...')
bq_client.delete_table(new_table_id, not_found_ok=True)
bq_client.delete_table(temp_table, not_found_ok=True)
print('✅ Geçici tablolar silindi')

# 6. Final kontrol
print('\n📊 Final durum:')
result2 = bq_client.query(check_query).result()
row2 = list(result2)[0]
print(f'  Toplam satır: {row2.total_rows:,}')
print(f'  Unique satır: {row2.unique_rows:,}')
print(f'  Duplicates: {row2.exact_duplicates:,}')

if row2.exact_duplicates == 0:
    print('\n✅✅✅ Temizleme başarılı! ✅✅✅')
else:
    print(f'\n⚠️ Hâlâ {row2.exact_duplicates:,} duplicate var!')



