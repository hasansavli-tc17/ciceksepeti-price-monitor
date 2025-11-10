#!/usr/bin/env python3
"""
BigQuery Entegrasyonu
Multi-site fiyat verilerini BigQuery'ye senkronize eder
"""

import json
import os
from datetime import datetime
from google.cloud import bigquery
from google.oauth2 import service_account

# BigQuery ayarları
PROJECT_ID = os.getenv('GCP_PROJECT_ID', 'tazecicek-project')
DATASET_ID = 'flower_pricing'
PRODUCTS_TABLE = 'products'
PRICE_HISTORY_TABLE = 'price_history'
BENCHMARKS_TABLE = 'benchmarks'

def get_bigquery_client():
    """BigQuery client oluştur"""
    # Service account key dosyası varsa kullan
    key_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if key_path and os.path.exists(key_path):
        credentials = service_account.Credentials.from_service_account_file(key_path)
        return bigquery.Client(credentials=credentials, project=PROJECT_ID)
    else:
        # Default credentials kullan
        return bigquery.Client(project=PROJECT_ID)

def create_dataset_and_tables(client):
    """Dataset ve tabloları oluştur"""
    
    # Dataset oluştur
    dataset_id = f"{PROJECT_ID}.{DATASET_ID}"
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = "europe-west3"  # Frankfurt
    
    try:
        dataset = client.create_dataset(dataset, exists_ok=True)
        print(f"✅ Dataset oluşturuldu: {dataset_id}")
    except Exception as e:
        print(f"⚠️  Dataset hatası: {e}")
    
    # Products tablosu
    products_schema = [
        bigquery.SchemaField("product_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("site_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("site_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("product_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("category", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("url", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("first_seen", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("last_seen", "TIMESTAMP", mode="REQUIRED"),
    ]
    
    products_table_id = f"{dataset_id}.{PRODUCTS_TABLE}"
    products_table = bigquery.Table(products_table_id, schema=products_schema)
    
    try:
        products_table = client.create_table(products_table, exists_ok=True)
        print(f"✅ Tablo oluşturuldu: {PRODUCTS_TABLE}")
    except Exception as e:
        print(f"⚠️  Tablo hatası: {e}")
    
    # Price History tablosu
    price_history_schema = [
        bigquery.SchemaField("product_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("site_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("price", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
    ]
    
    price_history_table_id = f"{dataset_id}.{PRICE_HISTORY_TABLE}"
    price_history_table = bigquery.Table(price_history_table_id, schema=price_history_schema)
    
    # Partitioning by date
    price_history_table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="date",
    )
    
    try:
        price_history_table = client.create_table(price_history_table, exists_ok=True)
        print(f"✅ Tablo oluşturuldu: {PRICE_HISTORY_TABLE}")
    except Exception as e:
        print(f"⚠️  Tablo hatası: {e}")
    
    # Benchmarks tablosu
    benchmarks_schema = [
        bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("site_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("site_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("product_count", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("avg_price", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("min_price", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("max_price", "FLOAT", mode="REQUIRED"),
    ]
    
    benchmarks_table_id = f"{dataset_id}.{BENCHMARKS_TABLE}"
    benchmarks_table = bigquery.Table(benchmarks_table_id, schema=benchmarks_schema)
    
    # Partitioning by date
    benchmarks_table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="date",
    )
    
    try:
        benchmarks_table = client.create_table(benchmarks_table, exists_ok=True)
        print(f"✅ Tablo oluşturuldu: {BENCHMARKS_TABLE}")
    except Exception as e:
        print(f"⚠️  Tablo hatası: {e}")

def sync_to_bigquery():
    """Fiyat verilerini BigQuery'ye senkronize et"""
    
    print("🔄 BigQuery senkronizasyonu başlıyor...")
    
    # Verileri yükle
    try:
        with open('multi_site_price_history.json', 'r', encoding='utf-8') as f:
            price_data = json.load(f)
    except FileNotFoundError:
        print("❌ Fiyat geçmişi dosyası bulunamadı")
        return
    
    try:
        with open('benchmark_report.json', 'r', encoding='utf-8') as f:
            benchmark_data = json.load(f)
    except FileNotFoundError:
        print("⚠️  Benchmark raporu bulunamadı")
        benchmark_data = None
    
    # BigQuery client
    client = get_bigquery_client()
    
    # Dataset ve tabloları oluştur
    create_dataset_and_tables(client)
    
    dataset_id = f"{PROJECT_ID}.{DATASET_ID}"
    
    # Ürünleri ve fiyat geçmişini kaydet
    now = datetime.utcnow()
    date_str = now.date().isoformat()
    
    products_rows = []
    price_history_rows = []
    
    for site_id, site_data in price_data.get('sites', {}).items():
        for product_id, product in site_data['products'].items():
            # Ürün kaydı
            products_rows.append({
                "product_id": product_id,
                "site_id": site_id,
                "site_name": site_data['name'],
                "product_name": product['name'],
                "category": product.get('category', 'Unknown'),
                "url": product.get('url', ''),
                "first_seen": product.get('timestamp', now.isoformat()),
                "last_seen": product.get('timestamp', now.isoformat()),
            })
            
            # Fiyat geçmişi kaydı
            price_history_rows.append({
                "product_id": product_id,
                "site_id": site_id,
                "price": float(product['price']),
                "timestamp": product.get('timestamp', now.isoformat()),
                "date": date_str,
            })
    
    # Ürünleri kaydet (upsert)
    if products_rows:
        # Products tablosuna merge query kullan
        merge_query = f"""
        MERGE `{dataset_id}.{PRODUCTS_TABLE}` T
        USING UNNEST(@products) S
        ON T.product_id = S.product_id
        WHEN MATCHED THEN
          UPDATE SET 
            product_name = S.product_name,
            category = S.category,
            url = S.url,
            last_seen = S.last_seen
        WHEN NOT MATCHED THEN
          INSERT (product_id, site_id, site_name, product_name, category, url, first_seen, last_seen)
          VALUES (S.product_id, S.site_id, S.site_name, S.product_name, S.category, S.url, S.first_seen, S.last_seen)
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ArrayQueryParameter("products", "STRUCT", products_rows)
            ]
        )
        
        try:
            query_job = client.query(merge_query, job_config=job_config)
            query_job.result()
            print(f"✅ {len(products_rows)} ürün kaydedildi/güncellendi")
        except Exception as e:
            print(f"⚠️  Ürün kaydetme hatası: {e}")
            # Fallback: insert only
            try:
                table_id = f"{dataset_id}.{PRODUCTS_TABLE}"
                errors = client.insert_rows_json(table_id, products_rows)
                if errors:
                    print(f"⚠️  Insert hataları: {errors}")
                else:
                    print(f"✅ {len(products_rows)} ürün eklendi")
            except Exception as e2:
                print(f"❌ Insert hatası: {e2}")
    
    # Fiyat geçmişini kaydet
    if price_history_rows:
        table_id = f"{dataset_id}.{PRICE_HISTORY_TABLE}"
        errors = client.insert_rows_json(table_id, price_history_rows)
        if errors:
            print(f"⚠️  Fiyat geçmişi hataları: {errors}")
        else:
            print(f"✅ {len(price_history_rows)} fiyat kaydı eklendi")
    
    # Benchmark verilerini kaydet
    if benchmark_data:
        benchmark_rows = []
        for site_name, site_stats in benchmark_data['price_analysis']['by_site'].items():
            # Site ID'yi bul
            site_id = site_name.lower().replace(' ', '_').replace('ç', 'c').replace('ş', 's').replace('ğ', 'g').replace('ü', 'u').replace('ö', 'o').replace('ı', 'i')
            
            benchmark_rows.append({
                "date": date_str,
                "timestamp": benchmark_data['date'],
                "site_id": site_id,
                "site_name": site_name,
                "product_count": site_stats['product_count'],
                "avg_price": float(site_stats['avg_price']),
                "min_price": float(site_stats['min_price']),
                "max_price": float(site_stats['max_price']),
            })
        
        if benchmark_rows:
            table_id = f"{dataset_id}.{BENCHMARKS_TABLE}"
            errors = client.insert_rows_json(table_id, benchmark_rows)
            if errors:
                print(f"⚠️  Benchmark hataları: {errors}")
            else:
                print(f"✅ {len(benchmark_rows)} benchmark kaydı eklendi")
    
    print("🎉 BigQuery senkronizasyonu tamamlandı!")

if __name__ == "__main__":
    sync_to_bigquery()

