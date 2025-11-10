from flask import Flask, request, jsonify
import os
import requests
import datetime as dt  # noqa: F401  # kept in case of future use
import math
import time
import gc
import sys  # noqa: F401  # kept in case of future use
import resource
import hashlib
import json
from google.cloud import bigquery

app = Flask(__name__)

# === CONFIG ===
PROJECT_ID = "tazecicekdb"
DATASET = "order_data"
TABLE = "order_items_clean_v3_enriched_partitioned_clustered"
API_URL = "https://apiorders.tazecicek.com/api/order-items/by-period"
API_USER = os.getenv("API_USER")
API_PASS = os.getenv("API_PASSWORD")
BATCH_SIZE = 2000  # RAM-friendly batch size

# Metadata table for tracking last fetch timestamp
METADATA_TABLE = f"{PROJECT_ID}.{DATASET}.fetch_metadata"

# BigQuery client with location specified
bq_client = bigquery.Client(project=PROJECT_ID, location="europe-west3")


# === MEMORY GUARD (prevent OutOfMemory) ===
@app.before_request
def limit_memory_usage():
    """Apply a soft 3 GB limit to avoid memory explosions in container.

    Some restricted runtimes may not allow rlimit; in that case silently skip.
    """
    try:
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        resource.setrlimit(resource.RLIMIT_AS, (3 * 1024 ** 3, hard))
    except Exception:
        pass


# === HELPERS ===
def get_last_fetch_timestamp(date: str) -> dt.datetime:
    """Get the last successful fetch timestamp for a given date."""
    try:
        query = f"""
        SELECT last_fetch_timestamp
        FROM `{METADATA_TABLE}`
        WHERE fetch_date = "{date}"
        ORDER BY last_fetch_timestamp DESC
        LIMIT 1
        """
        result = bq_client.query(query).result()
        row = list(result)
        if row:
            return row[0].last_fetch_timestamp
    except Exception as e:
        # Table might not exist yet, that's okay
        print(f"Warning: Could not get last fetch timestamp: {e}")
    return None

def update_last_fetch_timestamp(date: str, timestamp: dt.datetime):
    """Update the last successful fetch timestamp for a given date."""
    try:
        # Create table if not exists
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS `{METADATA_TABLE}` (
            fetch_date DATE,
            last_fetch_timestamp TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
        )
        """
        bq_client.query(create_table_query).result()
        
        # Insert or update
        upsert_query = f"""
        MERGE `{METADATA_TABLE}` AS target
        USING (
            SELECT "{date}" AS fetch_date, 
                   TIMESTAMP("{timestamp.isoformat()}") AS last_fetch_timestamp
        ) AS source
        ON target.fetch_date = source.fetch_date
        WHEN MATCHED THEN
            UPDATE SET 
                last_fetch_timestamp = source.last_fetch_timestamp,
                updated_at = CURRENT_TIMESTAMP()
        WHEN NOT MATCHED THEN
            INSERT (fetch_date, last_fetch_timestamp, updated_at)
            VALUES (source.fetch_date, source.last_fetch_timestamp, CURRENT_TIMESTAMP())
        """
        bq_client.query(upsert_query).result()
    except Exception as e:
        print(f"Warning: Could not update last fetch timestamp: {e}")

def normalize_row(row: dict) -> dict:
    """Simplify Turkish characters, convert additional_products list to string, and map column names."""
    clean = {}
    for k, v in row.items():
        key = (
            k.replace("ğ", "g")
            .replace("ü", "u")
            .replace("ş", "s")
            .replace("ı", "i")
            .replace("ö", "o")
            .replace("ç", "c")
        )
        # Map order_created_date to order_created_date_tr for enriched table
        if key == "order_created_date":
            key = "order_created_date_tr"
            # Convert datetime string to date format (YYYY-MM-DD) if needed
            if isinstance(v, str) and "T" in v:
                v = v.split("T")[0]  # Extract date part only
        
        # Convert delivery dates from TIMESTAMP to DATE (YYYY-MM-DD only)
        if key in ["order_delivery_date", "requested_delivery_date"]:
            if isinstance(v, str) and "T" in v:
                v = v.split("T")[0]  # Extract date part only
        
        if key == "additional_products" and isinstance(v, list):
            clean[key] = ", ".join(map(str, v))
        else:
            clean[key] = v
    return clean


def get_row_hash_key(row: dict) -> str:
    """
    Create a hash based on business key fields only (not timestamps).
    This ensures same order item gets same hash even if timestamps differ.
    
    NOTE: order_code is NOT included in hash because it's added later.
    Including it would cause duplicates when backfilling old data.
    """
    # Fields that define a unique order item (business key)
    # Exclude timestamps and other auto-generated fields
    # Exclude order_code (it's derived from order_id, adding it causes duplicate issues)
    hash_fields = [
        'order_id',
        'product_code_1',
        'user_id',
        'city',
        'district',
        'neighborhood',
        'delivery_location_type',
        'vendor_id',
        'rider_id',
        'additional_products',
        'product_name',
        'order_created_date_tr',
        # Add other core fields but NOT timestamps or order_code
    ]
    
    hash_dict = {}
    for field in hash_fields:
        if field in row:
            hash_dict[field] = row[field]
    
    # Create deterministic hash
    hash_json = json.dumps(hash_dict, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(hash_json.encode('utf-8')).hexdigest()


def insert_to_bigquery(rows: list) -> dict:
    """Insert data into BigQuery in batches. Uses MERGE to prevent exact duplicate rows."""
    if not rows:
        return {"inserted_rows": 0, "status": "empty"}

    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"
    total_inserted = 0
    skipped_duplicates = 0

    # First, remove exact duplicates from the input data
    # This prevents inserting the same row multiple times in one batch
    # Use business key hash (order_id + product + user, etc.) not full row
    seen_hashes = set()
    unique_rows = []
    for row in rows:
        normalized = normalize_row(row)
        # Use business key hash instead of full row hash
        # This ignores timestamps that may differ between API calls
        row_hash = get_row_hash_key(normalized)
        if row_hash not in seen_hashes:
            seen_hashes.add(row_hash)
            unique_rows.append(normalized)
        else:
            skipped_duplicates += 1
    
    if not unique_rows:
        return {
            "inserted_rows": 0,
            "skipped_duplicates": skipped_duplicates,
            "status": "all_duplicates",
        }

    # Check for existing data for the date range to avoid re-inserting
    # Extract dates from the data (use order_delivery_date as partition field)
    delivery_dates_in_batch = set()
    for row in unique_rows:
        if "order_delivery_date" in row and row["order_delivery_date"]:
            delivery_dates_in_batch.add(row["order_delivery_date"])
    
    # If we have dates, check if data already exists in BigQuery
    # Important: Parse BigQuery JSON and normalize it to match our format
    existing_hashes = set()
    if delivery_dates_in_batch:
        try:
            # Use order_delivery_date (partition field) for optimal query performance
            date_filter = " OR ".join([f"order_delivery_date = '{d}'" for d in delivery_dates_in_batch])
            # Optimize: Use clustering and partitioning for faster queries
            # Also add timeout configuration
            job_config = bigquery.QueryJobConfig(
                use_query_cache=True,
                maximum_bytes_billed=100 * 1024 * 1024  # 100 MB limit
            )
            query = f"""
            SELECT DISTINCT TO_JSON_STRING(t) as row_json
            FROM `{table_id}` t
            WHERE {date_filter}
            """
            print(f"🔍 Checking existing data for delivery dates: {', '.join(delivery_dates_in_batch)}")
            result = bq_client.query(query, job_config=job_config).result()
            row_count = 0
            for row in result:
                row_count += 1
                # Parse BigQuery JSON, normalize it, then hash using business key
                # This ensures same order item gets same hash even if timestamps differ
                try:
                    bq_row_dict = json.loads(row.row_json)
                    normalized_bq_row = normalize_row(bq_row_dict)
                    # Use business key hash instead of full row hash
                    row_hash = get_row_hash_key(normalized_bq_row)
                    existing_hashes.add(row_hash)
                except (json.JSONDecodeError, Exception) as e:
                    # If parsing fails, skip this row (don't add to existing_hashes)
                    print(f"⚠️ Warning: Could not parse row from BigQuery: {e}")
            print(f"✅ Found {row_count:,} existing rows in BigQuery ({len(existing_hashes):,} unique hashes)")
        except Exception as e:
            # If query fails, proceed with insert (might be permissions or schema issue)
            print(f"⚠️ Warning: Could not check existing data: {e}")
            print(f"   Type: {type(e).__name__}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            print(f"   ⚠️ Proceeding without duplicate check - duplicates may be inserted!")

    # Filter out rows that already exist in BigQuery
    new_rows = []
    duplicate_examples = []  # For debugging
    
    for row in unique_rows:
        # Use business key hash (same method as BigQuery comparison above)
        row_hash = get_row_hash_key(row)
        if row_hash not in existing_hashes:
            new_rows.append(row)
        else:
            skipped_duplicates += 1
            # Log first few duplicates for debugging
            if len(duplicate_examples) < 3:
                duplicate_examples.append({
                    "order_id": row.get("order_id"),
                    "hash": row_hash[:16],
                    "sample": str(row)[:100]
                })
    
    # Debug logging
    if skipped_duplicates > 0:
        print(f"⚠️ Duplicate prevention: {skipped_duplicates} duplicate rows filtered out")
        if duplicate_examples:
            print(f"   Sample duplicates: {duplicate_examples}")

    if not new_rows:
        return {
            "inserted_rows": 0,
            "skipped_duplicates": skipped_duplicates,
            "status": "all_existing",
        }

    # Insert remaining unique rows
    for i in range(0, len(new_rows), BATCH_SIZE):
        batch = new_rows[i : i + BATCH_SIZE]
        
        # Insert directly - BigQuery will handle schema mismatches
        errors = bq_client.insert_rows_json(table_id, batch)
        
        if errors:
            # Check if errors are just duplicates (safe to skip)
            # or actual schema/data issues (should raise)
            has_critical_error = False
            for error in errors:
                error_msg = str(error.get("errors", [{}])[0].get("message", "")).lower()
                # Skip duplicate errors but raise on other issues
                if "duplicate" not in error_msg and "already exists" not in error_msg:
                    has_critical_error = True
                    break
            
            if has_critical_error:
                raise Exception(f"Batch {i // BATCH_SIZE + 1} failed: {errors[:2]}")
            else:
                # Duplicate errors - count skipped rows
                skipped_duplicates += len([e for e in errors if e.get("errors")])
        else:
            total_inserted += len(batch)

        batch.clear()
        gc.collect()
        time.sleep(0.5)

    # Visibility check
    try:
        result = bq_client.query(f"SELECT COUNT(*) AS c FROM `{table_id}`").result()
        visible_count = list(result)[0].c
    except Exception:
        visible_count = 0

    return {
        "inserted_rows": total_inserted,
        "skipped_duplicates": skipped_duplicates,
        "status": "success",
        "verified_visible_rows": visible_count,
    }


# === ROUTES ===
@app.route("/")
def index():
    return jsonify(
        {
            "message": "Order Items Ingest v3 (memory-safe, optimized) is running",
            "endpoints": ["/fetch?date=YYYY-MM or YYYY-MM-DD"],
        }
    )


@app.route("/fetch")
def fetch():
    """
    Fetch order data from API and insert to BigQuery.
    
    Query parameters:
    - date: Optional. Date in YYYY-MM-DD format. If not provided:
      - mode=morning: Fetches today's data from 00:00 to 08:00 (for 08:05 scheduled job)
      - mode=incremental: Uses today's date (for 5-min interval jobs from 08:10 onwards)
    - days_back: Optional. Number of days back to fetch (e.g., days_back=1 fetches yesterday)
    - mode: Optional. 'morning' (for 08:05 job, 00:00-08:00) or 'incremental' (for 5-min intervals)
    - start_hour: Optional. Start hour for morning mode (default: 0)
    - end_hour: Optional. End hour for morning mode (default: 8)
    """
    date = request.args.get("date")
    days_back = request.args.get("days_back")
    mode = request.args.get("mode", "incremental")  # 'morning' or 'incremental'
    start_hour = int(request.args.get("start_hour", 0))  # Default: 00:00
    end_hour = int(request.args.get("end_hour", 8))  # Default: 08:00
    
    # If no date provided, determine based on mode or days_back
    if not date:
        now = dt.datetime.now(dt.timezone(dt.timedelta(hours=3)))  # Europe/Istanbul = UTC+3
        
        # If days_back specified, calculate date
        if days_back:
            target_date = now - dt.timedelta(days=int(days_back))
            date = target_date.strftime("%Y-%m-%d")
        elif mode == "morning":
            # For 08:05 scheduled job: fetch today's data from 00:00 to 08:00
            date = now.strftime("%Y-%m-%d")
        else:
            # For incremental updates (every 5 min from 08:10): fetch today's data
            date = now.strftime("%Y-%m-%d")
    
    # For incremental mode, try to get last fetch timestamp to optimize API call
    last_timestamp = None
    if mode == "incremental" and len(date) == 10:  # Only for Day format
        last_timestamp = get_last_fetch_timestamp(date)
        if last_timestamp:
            # Convert to Istanbul timezone if needed
            if last_timestamp.tzinfo is None:
                last_timestamp = last_timestamp.replace(tzinfo=dt.timezone(dt.timedelta(hours=3)))
            print(f"Incremental mode: Last fetch was at {last_timestamp}")
    
    # Determine payload based on date format
    # API only supports: {"yearMonth": "2025-08"} or {"day": "2025-10-23"}
    # No timestamp filtering available, so we fetch full day/month
    # Duplicate prevention handles filtering on our side
    payload = {"yearMonth": date} if len(date) == 7 else {"day": date}

    try:
        r = requests.post(
            API_URL, auth=(API_USER, API_PASS), json=payload, timeout=180
        )
        if r.status_code != 200:
            return (
                jsonify({"error": f"API error: {r.status_code}", "body": r.text}),
                r.status_code,
            )

        data = r.json()
        original_data_count = len(data) if isinstance(data, list) else 0
        
        # Filter data for morning mode (00:00 to 08:00 today)
        if mode == "morning" and isinstance(data, list):
            # Recalculate now for filtering
            now_for_filter = dt.datetime.now(dt.timezone(dt.timedelta(hours=3)))  # Europe/Istanbul = UTC+3
            today_date = now_for_filter.date()
            
            # Define time range: today 00:00 to 08:00
            start_time = now_for_filter.replace(hour=start_hour, minute=0, second=0, microsecond=0)
            end_time = now_for_filter.replace(hour=end_hour, minute=0, second=0, microsecond=0)
            
            filtered_data = []
            for row in data:
                # Try to extract timestamp from various possible fields
                timestamp_str = None
                for field in ['order_created_date', 'order_creation_timestamp', 'created_at', 'timestamp', 'date']:
                    if field in row and row[field]:
                        timestamp_str = row[field]
                        break
                
                if timestamp_str:
                    try:
                        # Parse timestamp (could be ISO format or date string)
                        if isinstance(timestamp_str, str):
                            if 'T' in timestamp_str:
                                row_time = dt.datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            else:
                                # Date only, assume midnight
                                row_time = dt.datetime.fromisoformat(timestamp_str + 'T00:00:00+03:00')
                        else:
                            continue
                        
                        # Convert to Istanbul timezone if needed
                        if row_time.tzinfo is None:
                            row_time = row_time.replace(tzinfo=dt.timezone(dt.timedelta(hours=3)))
                        
                        # Filter: keep only today 00:00 to 07:59 range
                        row_date = row_time.date()
                        
                        if row_date == today_date:
                            # Today: keep only 00:00-08:00 (before end_hour, inclusive)
                            if start_hour <= row_time.hour < end_hour:
                                filtered_data.append(row)
                    except (ValueError, TypeError):
                        # If timestamp parsing fails, include the row (safe fallback)
                        # But only if it's today's date
                        if 'order_created_date_tr' in row or 'order_created_date' in row:
                            row_date_str = row.get('order_created_date_tr') or row.get('order_created_date')
                            if row_date_str and str(row_date_str) == today_date.strftime("%Y-%m-%d"):
                                filtered_data.append(row)
                else:
                    # If no timestamp found, check date field
                    row_date_str = row.get('order_created_date_tr') or row.get('order_created_date')
                    if row_date_str and str(row_date_str) == today_date.strftime("%Y-%m-%d"):
                        # Include all rows for today if no timestamp (safe fallback)
                        filtered_data.append(row)
            
            data = filtered_data
            print(f"Morning mode: Filtered {original_data_count} rows to {len(data)} rows (00:00-{end_hour:02d}:00 range, inclusive)")
        
        result = insert_to_bigquery(data)
        
        # Update last fetch timestamp for incremental mode
        if mode == "incremental" and len(date) == 10 and result.get("status") == "success":
            current_timestamp = dt.datetime.now(dt.timezone(dt.timedelta(hours=3)))
            update_last_fetch_timestamp(date, current_timestamp)
        
        response_data = {
            "status": "ok", 
            "mode": mode,
            "date": date,
            "row_count": len(data), 
            "bq_status": result
        }
        
        if mode == "morning":
            response_data["note"] = f"Morning fetch: Coverage from {start_hour:02d}:00 to {end_hour:02d}:00 today"
        elif mode == "incremental" and last_timestamp:
            response_data["last_fetch"] = last_timestamp.isoformat()
            response_data["note"] = "Incremental fetch: Only new data since last fetch will be inserted (duplicate prevention)"
        
        return jsonify(response_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# === MAIN ===
if __name__ == "__main__":
    print("✅ Flask app starting on port 8080")
    app.run(host="0.0.0.0", port=8080)


