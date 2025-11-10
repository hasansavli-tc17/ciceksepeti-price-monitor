# Streamlit Dashboard Deployment Rehberi

## 📊 Dashboard Özellikleri

- ✅ BigQuery'den gerçek zamanlı veri çekme
- ✅ İnteraktif filtreler (tarih, şehir, ödeme yöntemi)
- ✅ 10+ farklı grafik ve metrik
- ✅ Responsive tasarım
- ✅ Cloud Run'a deploy edilebilir

## 🚀 Hızlı Başlangıç (Local)

### 1. Paketleri Yükle
```bash
pip install -r dashboard_requirements.txt
```

### 2. Google Cloud Authentication
```bash
gcloud auth application-default login
```

### 3. Dashboard'u Çalıştır
```bash
streamlit run dashboard_app.py
```

Tarayıcıda otomatik açılacak: http://localhost:8501

## ☁️ Cloud Run'a Deploy

### 1. Deploy
```bash
gcloud run deploy order-items-dashboard \
  --source . \
  --dockerfile dashboard_Dockerfile \
  --region europe-west3 \
  --project tazecicekdb \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=1 \
  --timeout=300 \
  --port=8080
```

### 2. Erişim
Deploy sonrası verilen URL'den erişebilirsin.

## 📋 Özellikler

### Filtreler (Sidebar)
- **Tarih Aralığı**: İstediğin tarih aralığını seç
- **Şehir**: Belirli şehirleri filtrele
- **Ödeme Yöntemi**: Ödeme yöntemlerine göre filtrele

### Metrikler
- Toplam Sipariş Sayısı
- Toplam Ürün Adedi
- Toplam Gelir
- Ortalama Sipariş Değeri
- Aktif Gün Sayısı

### Grafikler
1. **Günlük Sipariş Trendi**: Son 90 günlük sipariş sayısı
2. **Günlük Gelir Trendi**: Son 90 günlük gelir trendi
3. **Şehir Dağılımı**: Top 15 şehir
4. **Ödeme Yöntemleri**: Pie chart
5. **Teslimat Durumları**: Bar chart
6. **Gün İçi Saat Dağılımı**: 24 saatlik dağılım

### Tablolar
- **Top Ürünler**: En çok satan 50 ürün
- **Vendor Performansı**: Vendor bazlı metrikler

## 🔧 Özelleştirme

### Grafik Ekleme
`dashboard_app.py` dosyasında yeni grafikler ekleyebilirsin:

```python
st.subheader("Yeni Grafik")
query = """
SELECT ...
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE {where_clause}
"""
df = run_query(query)
fig = px.bar(df, x='...', y='...')
st.plotly_chart(fig, use_container_width=True)
```

### Filtre Ekleme
Sidebar'a yeni filtre ekle:

```python
new_filter = st.sidebar.selectbox(
    "Yeni Filtre",
    options=[...]
)
```

## 💰 Maliyet

- **BigQuery**: Query başına ücret (ilk 1TB/ay ücretsiz)
- **Cloud Run**: Kullanım bazlı (minimal maliyet)
- **Cache**: 5 dakika cache ile gereksiz query'leri önler

## 🔒 Güvenlik

- Dashboard public olabilir (sadece okuma)
- BigQuery'de IAM permissions kontrol et
- İstersen authentication ekleyebiliriz

## 📱 Mobil Uyumlu

Dashboard responsive tasarıma sahip, mobilde de çalışır.

## 🐛 Sorun Giderme

### "Permission denied" hatası
```bash
gcloud auth application-default login
gcloud projects add-iam-policy-binding tazecicekdb \
  --member=user:YOUR_EMAIL \
  --role=roles/bigquery.user
```

### Dashboard yavaş yükleniyor
- Cache süresini artır (`@st.cache_data(ttl=600)`)
- Filtreleri daralt
- Limit ekle (zaten ekli)

### Veri görünmüyor
- BigQuery permissions kontrol et
- WHERE clause'u kontrol et
- Tablo adını doğrula

## 📞 İletişim

Sorun olursa veya yeni özellik eklemek istersen söyle!




