# 📅 Schedule Kullanım Kılavuzu

## Mantık

Sistem iki farklı modda çalışır:

### 1. **Sabah 08:05 - Morning (Sabah Verileri)**
- **Ne zaman**: Her gün sabah 08:05 (Türkiye saati)
- **Ne yapar**: Bugün 00:00 - 08:00 arası verileri çeker (gece ve sabah saatlerindeki verileri)
- **Endpoint**: `/fetch?mode=morning`
- **Mantık**: Gece saatlerinde schedule çalışmıyor, 08:05'te sabah verilerini çeker

### 2. **Her 5 Dakika - Incremental (Artımlı)**
- **Ne zaman**: 08:10'dan itibaren 23:59'a kadar her 5 dakikada bir
- **Ne yapar**: Bugünün sadece yeni gelen verilerini çeker (08:00-23:59:59 arası)
- **Endpoint**: `/fetch?mode=incremental` veya sadece `/fetch`

## Cloud Scheduler Ayarları

### Sabah 08:05 Morning Job

```bash
# Cloud Scheduler komutu (Cloud Console'dan veya gcloud CLI ile)
gcloud scheduler jobs create http order-fetch-morning \
  --schedule="5 8 * * *" \
  --time-zone="Europe/Istanbul" \
  --uri="https://YOUR-SERVICE-URL/fetch?mode=morning" \
  --http-method=GET \
  --headers="Authorization=Bearer $(gcloud auth print-access-token)"
```

**Cron format**: `5 8 * * *` = Her gün saat 08:05

### Her 5 Dakika Incremental Job (08:10 - 23:55)

```bash
# Cloud Scheduler komutu - Ana incremental job
gcloud scheduler jobs create http order-fetch-incremental \
  --schedule="10,15,20,25,30,35,40,45,50,55 8-23 * * *" \
  --time-zone="Europe/Istanbul" \
  --uri="https://YOUR-SERVICE-URL/fetch?mode=incremental" \
  --http-method=GET \
  --headers="Authorization=Bearer $(gcloud auth print-access-token)"
```

**Cron format**: `10,15,20,25,30,35,40,45,50,55 8-23 * * *` = Saat 8-23 arası, 10, 15, 20, ..., 55 dakikalarda (08:10, 08:15, ..., 23:55)

### Son Incremental Job (23:59)

```bash
# Cloud Scheduler komutu - Günün son verilerini çekmek için
gcloud scheduler jobs create http order-fetch-incremental-last \
  --schedule="59 23 * * *" \
  --time-zone="Europe/Istanbul" \
  --uri="https://YOUR-SERVICE-URL/fetch?mode=incremental" \
  --http-method=GET \
  --headers="Authorization=Bearer $(gcloud auth print-access-token)"
```

**Cron format**: `59 23 * * *` = Her gün 23:59'da (günün son verilerini çekmek için)

## Örnek Çalışma Senaryosu

### Gün: 2025-11-05

**08:05** (Sabah):
- Endpoint: `/fetch?mode=morning`
- Çekilen veri: **2025-11-05 00:00 - 08:00** arası veriler
- Sebep: Gece saatlerinde schedule çalışmadığı için sabah verilerini almak

**08:10** (5 dakika sonra):
- Endpoint: `/fetch?mode=incremental`
- Çekilen veri: **2025-11-05** tarihinin 08:00-08:10 arası verileri

**08:15, 08:20, ... 23:55** (her 5 dakikada):
- Aynı şekilde bugünün yeni verileri çekilir (08:00-23:59:59 arası)

**23:59** (Günün sonu):
- Son incremental job çalışır
- 23:55-23:59:59 arası verileri çeker

**00:00 - 08:04** (Gece):
- Schedule çalışmaz (boş)

**Ertesi gün 08:05**:
- Yine bugünün 00:00-08:00 arası verileri çekilir
- Ve döngü devam eder...

## Manuel Test

### Morning Test:
```bash
curl "http://localhost:8080/fetch?mode=morning"
```

### Incremental Test:
```bash
curl "http://localhost:8080/fetch?mode=incremental"
# veya
curl "http://localhost:8080/fetch"
```

### Belirli Bir Tarih:
```bash
curl "http://localhost:8080/fetch?date=2025-11-04"
```

## API Response Örneği

```json
{
  "status": "ok",
  "mode": "incremental",
  "date": "2025-11-05",
  "row_count": 1523,
  "bq_status": {
    "inserted_rows": 1500,
    "skipped_duplicates": 23,
    "status": "success",
    "verified_visible_rows": 2240918
  }
}
```

## Önemli Notlar

⚠️ **Duplicate Prevention**: 
- Sistem otomatik olarak çoğalan verileri önler
- Aynı veri tekrar çekilse bile sadece yeni olanlar eklenir

⚠️ **Incremental Mode**:
- Her 5 dakikada bugünün verisini çeker
- API'den gelen veriler otomatik olarak filtrelenir
- BigQuery'de zaten varsa eklenmez

⚠️ **Morning Mode**:
- Bugün 00:00 - 08:00 arası verileri çeker
- Gece saatlerinde schedule çalışmadığı için sabah bu gap'i kapatır
- Duplicate prevention sayesinde zaten çekilmiş veriler tekrar eklenmez

## Sorun Giderme

### "Saat 08:05'te çalışmıyor"
- Cloud Scheduler job'ının timezone'ının `Europe/Istanbul` olduğundan emin olun
- Log'ları kontrol edin: `gcloud logging read "resource.type=cloud_scheduler_job"`

### "Her 5 dakikada çalışmıyor"
- Cron formatını kontrol edin: `10,15,20,25,30,35,40,45,50,55 8-23 * * *,59 23 * * *`
- Cloud Scheduler limit'lerini kontrol edin (max 1 job per minute)
- 23:59'daki son job günün son verilerini (23:55-23:59:59) çeker

### "Veri tekrar ekleniyor"
- `insert_to_bigquery` fonksiyonu otomatik duplicate check yapar
- Eğer hala sorun varsa, `main.py`'deki duplicate prevention mantığını kontrol edin
