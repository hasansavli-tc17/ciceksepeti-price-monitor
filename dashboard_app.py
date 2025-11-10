"""
Executive Order Analytics Dashboard - Premium Edition
CEO presentation-ready dashboard with golden ratio design
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from google.cloud import bigquery
from datetime import datetime, timedelta
import numpy as np
from io import BytesIO

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="Sipariş Analitikleri | Yönetim Dashboard'u",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# SIMPLE CSS STYLING
# ============================================
st.markdown("""
<style>
    /* Simple Header */
    .executive-header {
        background: #667eea;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .executive-header h1 {
        color: white;
        font-size: 2.5rem;
        font-weight: 600;
        margin: 0;
    }
    
    .executive-header p {
        color: rgba(255,255,255,0.9);
        font-size: 1.1rem;
        margin-top: 0.5rem;
    }
    
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ============================================
# BIGQUERY CLIENT
# ============================================
@st.cache_resource
def get_bq_client():
    try:
        return bigquery.Client(project="tazecicekdb")
    except Exception as e:
        st.error("❌ Kimlik Doğrulama Hatası")
        st.info("Çalıştır: `gcloud auth application-default login`")
        st.stop()
        raise

@st.cache_data(ttl=300)
def run_query(query):
    client = get_bq_client()
    return client.query(query).to_dataframe()

# Excel export helper
def to_excel(df):
    # Create a copy to avoid modifying original
    df_export = df.copy()
    
    # Remove timezone from datetime columns
    for col in df_export.columns:
        if pd.api.types.is_datetime64_any_dtype(df_export[col]):
            df_export[col] = df_export[col].dt.tz_localize(None)
        elif df_export[col].dtype == 'object':
            # Check if it's a timezone-aware datetime string
            try:
                df_export[col] = pd.to_datetime(df_export[col])
                if df_export[col].dt.tz is not None:
                    df_export[col] = df_export[col].dt.tz_localize(None)
            except:
                pass
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_export.to_excel(writer, index=False, sheet_name='Siparişler')
    return output.getvalue()

# ============================================
# NORMALIZATION
# ============================================
def normalize_turkish(text):
    if pd.isna(text) or text is None:
        return text
    text = str(text).strip()
    fixes = {'Ä°': 'I', 'Ä±': 'i', 'Ã': 'A', 'Ã¼': 'u', 'Ã¶': 'o', 'Ã§': 'c', 'Å': 'S', 'ÄŸ': 'g', '0STANBUL': 'ISTANBUL'}
    for old, new in fixes.items():
        text = text.replace(old, new)
    replacements = {'ğ': 'g', 'Ğ': 'G', 'ü': 'u', 'Ü': 'U', 'ş': 's', 'Ş': 'S', 'ı': 'i', 'İ': 'I', 'ö': 'o', 'Ö': 'O', 'ç': 'c', 'Ç': 'C'}
    for old, new in replacements.items():
        text = text.replace(old, new)
    if 'ISTANBUL' in text.upper() and 'AVRUPA' in text.upper():
        text = 'ISTANBUL-AVRUPA'
    elif 'ISTANBUL' in text.upper() and 'ANADOLU' in text.upper():
        text = 'ISTANBUL-ANADOLU'
    return text.replace('  ', ' ')

# ============================================
# EXECUTIVE HEADER
# ============================================
st.markdown("""
<div class="executive-header">
    <h1>📊 Sipariş Analitikleri Dashboard'u</h1>
    <p>Yönetim Özeti & İş Zekası</p>
</div>
""", unsafe_allow_html=True)

# ============================================
# SIDEBAR - PREMIUM FILTERS
# ============================================
st.sidebar.markdown("## 🎯 Filtreler ve Kontroller")

# Date Presets
date_preset = st.sidebar.selectbox(
    "📅 Zaman Periyodu",
    ["Özel", "Bugün", "Son 7 Gün", "Son 30 Gün", "Son 90 Gün", "Son Yıl", "Tüm Zamanlar"],
    index=2
)

if date_preset == "Bugün":
    date_range = (datetime.now().date(), datetime.now().date())
elif date_preset == "Son 7 Gün":
    date_range = (datetime.now().date() - timedelta(days=7), datetime.now().date())
elif date_preset == "Son 30 Gün":
    date_range = (datetime.now().date() - timedelta(days=30), datetime.now().date())
elif date_preset == "Son 90 Gün":
    date_range = (datetime.now().date() - timedelta(days=90), datetime.now().date())
elif date_preset == "Son Yıl":
    date_range = (datetime.now().date() - timedelta(days=365), datetime.now().date())
elif date_preset == "Tüm Zamanlar":
    date_range = (datetime(2020, 1, 1).date(), datetime.now().date())
else:
    date_range = st.sidebar.date_input(
        "Özel Tarih Aralığı",
        value=(datetime.now() - timedelta(days=30), datetime.now()),
        max_value=datetime.now()
    )

# City Filter
cities_query = """
SELECT DISTINCT city
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE city IS NOT NULL
ORDER BY city
"""
cities_df = run_query(cities_query)
cities_df['city_normalized'] = cities_df['city'].apply(normalize_turkish)
selected_cities = st.sidebar.multiselect("🏙️ Şehirler", options=cities_df['city_normalized'].tolist(), default=[])
selected_cities_original = cities_df[cities_df['city_normalized'].isin(selected_cities)]['city'].tolist() if selected_cities else []

# Payment Method
payment_query = """
SELECT DISTINCT payment_method
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE payment_method IS NOT NULL
ORDER BY payment_method
"""
payment_df = run_query(payment_query)
selected_payment = st.sidebar.multiselect("💳 Ödeme Yöntemleri", options=payment_df['payment_method'].tolist(), default=[])

# Comparison Mode
st.sidebar.markdown("---")
compare_mode = st.sidebar.checkbox("📊 Karşılaştırma Modu", value=False)
compare_period = None
if compare_mode:
    compare_period = st.sidebar.selectbox("Karşılaştır", ["Önceki Dönem", "Önceki Yıl", "Önceki Ay"])

# Refresh
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Veriyi Yenile"):
    st.cache_data.clear()
    st.rerun()

# ============================================
# BUILD WHERE CLAUSE
# ============================================
where_conditions = []
if date_range[0] and date_range[1]:
    where_conditions.append(f"order_created_date_tr BETWEEN '{date_range[0]}' AND '{date_range[1]}'")
if selected_cities_original:
    cities_str = "', '".join(selected_cities_original)
    where_conditions.append(f"city IN ('{cities_str}')")
if selected_payment:
    payment_str = "', '".join(selected_payment)
    where_conditions.append(f"payment_method IN ('{payment_str}')")
where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

# ============================================
# EXECUTIVE SUMMARY - KEY METRICS
# ============================================
st.markdown("### 📈 Yönetim Özeti")

metrics_query = f"""
SELECT
  COUNT(DISTINCT order_id) AS total_orders,
  COUNT(*) AS total_items,
  SUM(order_amount) AS total_revenue,
  AVG(order_amount) AS avg_order_value,
  COUNT(DISTINCT DATE(order_created_date_tr)) AS active_days,
  COUNT(DISTINCT city) AS unique_cities,
  COUNT(DISTINCT vendor_id) AS unique_vendors
FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
WHERE {where_clause}
  AND order_created_date_tr IS NOT NULL
"""

metrics_df = run_query(metrics_query)

# Calculate growth if comparison mode
growth_orders = None
growth_revenue = None
if compare_mode and compare_period:
    if compare_period == "Önceki Dönem":
        days_diff = (date_range[1] - date_range[0]).days
        compare_start = date_range[0] - timedelta(days=days_diff + 1)
        compare_end = date_range[0] - timedelta(days=1)
    elif compare_period == "Önceki Yıl":
        compare_start = date_range[0] - timedelta(days=365)
        compare_end = date_range[1] - timedelta(days=365)
    else:
        compare_start = date_range[0] - timedelta(days=30)
        compare_end = date_range[1] - timedelta(days=30)
    
    compare_where = where_clause.replace(
        f"order_created_date_tr BETWEEN '{date_range[0]}' AND '{date_range[1]}'",
        f"order_created_date_tr BETWEEN '{compare_start}' AND '{compare_end}'"
    )
    compare_query = f"""
    SELECT
      COUNT(DISTINCT order_id) AS total_orders,
      SUM(order_amount) AS total_revenue
    FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
    WHERE {compare_where}
      AND order_created_date_tr IS NOT NULL
    """
    compare_df = run_query(compare_query)
    if compare_df['total_orders'].iloc[0] > 0:
        growth_orders = ((metrics_df['total_orders'].iloc[0] - compare_df['total_orders'].iloc[0]) / compare_df['total_orders'].iloc[0]) * 100
        growth_revenue = ((metrics_df['total_revenue'].iloc[0] - compare_df['total_revenue'].iloc[0]) / compare_df['total_revenue'].iloc[0]) * 100

# Golden Ratio Layout: 1.618 columns
col1, col2, col3, col4 = st.columns([1.618, 1, 1.618, 1])

with col1:
    delta = f"{growth_orders:+.1f}%" if growth_orders is not None else None
    st.metric(
        "📦 Toplam Sipariş",
        f"{metrics_df['total_orders'].iloc[0]:,}",
        delta=delta,
        delta_color="normal"
    )

with col2:
    st.metric("🛍️ Toplam Ürün", f"{metrics_df['total_items'].iloc[0]:,}")

with col3:
    delta = f"{growth_revenue:+.1f}%" if growth_revenue is not None else None
    st.metric(
        "💰 Toplam Gelir",
        f"₺{metrics_df['total_revenue'].iloc[0]:,.0f}",
        delta=delta,
        delta_color="normal"
    )

with col4:
    st.metric("💵 Ortalama Sipariş Değeri", f"₺{metrics_df['avg_order_value'].iloc[0]:,.2f}")

# Second row with golden ratio
col5, col6, col7 = st.columns([1.618, 1, 1.618])

with col5:
    st.metric("📅 Aktif Günler", f"{metrics_df['active_days'].iloc[0]}")

with col6:
    st.metric("🏙️ Şehir Sayısı", f"{metrics_df['unique_cities'].iloc[0]}")

with col7:
    st.metric("🏪 Vendor Sayısı", f"{metrics_df['unique_vendors'].iloc[0]}")

st.markdown("---")

# ============================================
# PREMIUM TREND VISUALIZATION
# ============================================
col1, col2 = st.columns([1.618, 1])  # Golden ratio

with col1:
    st.markdown("### 📈 Gelir & Sipariş Trendleri")
    daily_query = f"""
    SELECT
      order_created_date_tr AS date,
      COUNT(DISTINCT order_id) AS unique_orders,
      SUM(order_amount) AS total_revenue,
      AVG(order_amount) AS avg_order_value
    FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
    WHERE {where_clause}
      AND order_created_date_tr IS NOT NULL
    GROUP BY date
    ORDER BY date DESC
    LIMIT 90
    """
    daily_df = run_query(daily_query).sort_values('date')
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Orders line
    fig.add_trace(
        go.Scatter(
            x=daily_df['date'],
            y=daily_df['unique_orders'],
            name='Siparişler',
            line=dict(color='#667eea', width=2),
            hovertemplate='%{x|%Y-%m-%d}<br>Sipariş: %{y:,}<extra></extra>'
        ),
        secondary_y=False
    )
    
    # Revenue line
    fig.add_trace(
        go.Scatter(
            x=daily_df['date'],
            y=daily_df['total_revenue'],
            name='Gelir (₺)',
            line=dict(color='#27ae60', width=2),
            hovertemplate='%{x|%Y-%m-%d}<br>Gelir: ₺%{y:,.0f}<extra></extra>'
        ),
        secondary_y=True
    )
    
    fig.update_xaxes(title_text="Tarih")
    fig.update_yaxes(title_text="Sipariş", secondary_y=False)
    fig.update_yaxes(title_text="Gelir (₺)", secondary_y=True)
    
    fig.update_layout(
        height=450,
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

with col2:
    st.markdown("### 🎯 Temel İçgörüler")
    
    # Calculate insights
    if len(daily_df) > 1:
        recent_avg = daily_df.tail(7)['unique_orders'].mean()
        previous_avg = daily_df.iloc[-14:-7]['unique_orders'].mean() if len(daily_df) >= 14 else recent_avg
        
        if recent_avg > previous_avg * 1.1:
            insight = "📈 Son 7 günde güçlü yükseliş trendi"
            color = "green"
        elif recent_avg < previous_avg * 0.9:
            insight = "📉 Son günlerde düşüş gözlemlendi"
            color = "orange"
        else:
            insight = "➡️ İstikrarlı performans"
            color = "blue"
        
        st.markdown(f"""
        <div class="insight-box">
            <h4 style="color: {color}; margin-bottom: 0.5rem;">{insight}</h4>
            <p style="margin: 0; color: #666;">Ortalama: {recent_avg:.0f} sipariş/gün</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Revenue insight
    total_rev = metrics_df['total_revenue'].iloc[0]
    avg_daily = total_rev / metrics_df['active_days'].iloc[0] if metrics_df['active_days'].iloc[0] > 0 else 0
    
    st.markdown(f"""
    <div class="insight-box">
        <h4 style="color: #667eea; margin-bottom: 0.5rem;">💰 Gelir Performansı</h4>
        <p style="margin: 0; color: #666;">Günlük Ortalama: ₺{avg_daily:,.0f}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Growth insight
    if growth_orders:
        st.markdown(f"""
        <div class="insight-box">
            <h4 style="color: {'green' if growth_orders > 0 else 'red'}; margin-bottom: 0.5rem;">📊 Büyüme Analizi</h4>
            <p style="margin: 0; color: #666;">Sipariş: {growth_orders:+.1f}%</p>
            <p style="margin: 0; color: #666;">Gelir: {growth_revenue:+.1f}%</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ============================================
# HEATMAP & DISTRIBUTION
# ============================================
col1, col2 = st.columns([1.618, 1])

with col1:
    st.markdown("### 🔥 Haftalık & Saatlik Dağılım")
    heatmap_query = f"""
    SELECT
      EXTRACT(DAYOFWEEK FROM order_created_date_tr) AS day_of_week,
      EXTRACT(HOUR FROM order_creation_timestamp) AS hour,
      COUNT(DISTINCT order_id) AS unique_orders
    FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
    WHERE {where_clause}
      AND order_created_date_tr IS NOT NULL
      AND order_creation_timestamp IS NOT NULL
    GROUP BY day_of_week, hour
    ORDER BY day_of_week, hour
    """
    heatmap_df = run_query(heatmap_query)
    
    if not heatmap_df.empty:
        pivot_df = heatmap_df.pivot(index='day_of_week', columns='hour', values='unique_orders').fillna(0)
        days = ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz']
        pivot_df.index = [days[int(i)-1] for i in pivot_df.index if int(i) <= 7]
        
        fig = px.imshow(
            pivot_df,
            labels=dict(x="Saat", y="Gün", color="Sipariş"),
            color_continuous_scale='YlOrRd',
            aspect="auto"
        )
        fig.update_layout(
            height=450,
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

with col2:
    st.markdown("### 🏙️ En İyi Şehirler")
    city_query = f"""
    SELECT
      city,
      COUNT(DISTINCT order_id) AS unique_orders,
      SUM(order_amount) AS total_revenue
    FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
    WHERE {where_clause}
      AND city IS NOT NULL
    GROUP BY city
    ORDER BY unique_orders DESC
    LIMIT 10
    """
    city_df = run_query(city_query)
    city_df['city_display'] = city_df['city'].apply(normalize_turkish)
    city_df = city_df.groupby('city_display').agg({
        'unique_orders': 'sum',
        'total_revenue': 'sum'
    }).reset_index().sort_values('unique_orders', ascending=False).head(10)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=city_df['unique_orders'],
        y=city_df['city_display'],
        orientation='h',
        marker=dict(color='#667eea'),
        text=city_df['unique_orders'],
        texttemplate='%{text:,}',
        textposition='outside',
        hovertemplate='%{y}<br>Sipariş: %{x:,}<br>Gelir: ₺%{customdata:,.0f}<extra></extra>',
        customdata=city_df['total_revenue']
    ))
    fig.update_layout(
        height=450,
        xaxis_title="Sipariş",
        yaxis_title="",
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=0, r=0, t=0, b=0)
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# ============================================
# DISTRIBUTION CHARTS
# ============================================
col1, col2 = st.columns([1.618, 1])

with col1:
    st.markdown("### 💳 Ödeme Yöntemleri")
    payment_query = f"""
    SELECT
      payment_method,
      COUNT(DISTINCT order_id) AS unique_orders,
      SUM(order_amount) AS total_revenue
    FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
    WHERE {where_clause}
      AND payment_method IS NOT NULL
    GROUP BY payment_method
    ORDER BY unique_orders DESC
    """
    payment_df = run_query(payment_query)
    payment_df['payment_method'] = payment_df['payment_method'].apply(normalize_turkish)
    
    fig = px.pie(
        payment_df,
        values='unique_orders',
        names='payment_method',
        hole=0.5
    )
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        marker=dict(line=dict(color='#FFFFFF', width=2))
    )
    fig.update_layout(
        height=450,
        showlegend=True,
        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05)
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

with col2:
    st.markdown("### 📊 Teslimat Durumu")
    delivery_query = f"""
    SELECT
      delivery_status,
      COUNT(DISTINCT order_id) AS unique_orders
    FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
    WHERE {where_clause}
      AND delivery_status IS NOT NULL
    GROUP BY delivery_status
    ORDER BY unique_orders DESC
    """
    delivery_df = run_query(delivery_query)
    delivery_df['delivery_status'] = delivery_df['delivery_status'].apply(normalize_turkish)
    
    fig = px.bar(
        delivery_df,
        x='delivery_status',
        y='unique_orders',
        color='unique_orders',
        color_continuous_scale='Greens',
        text='unique_orders'
    )
    fig.update_traces(
        texttemplate='%{text:,}',
        textposition='outside',
        marker=dict(line=dict(color='rgba(0,0,0,0.2)', width=1))
    )
    fig.update_layout(
        height=450,
        xaxis_title="Durum",
        yaxis_title="Sipariş",
        xaxis_tickangle=-45,
        plot_bgcolor='white',
        paper_bgcolor='white',
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# ============================================
# DETAILED TABLES
# ============================================
st.markdown("---")
st.markdown("### 📋 Detaylı Analiz")

tab1, tab2, tab3 = st.tabs(["📦 Sipariş Listesi", "🏆 En İyi Ürünler", "🏪 Vendor Performansı"])

with tab1:
    st.markdown("#### 📊 Detaylı Sipariş Listesi")
    
    # Limit selector
    limit_options = [100, 500, 1000, 5000, 10000]
    selected_limit = st.selectbox("Gösterilecek Kayıt Sayısı", limit_options, index=2)
    
    orders_query = f"""
    SELECT
      order_id,
      order_created_date_tr AS tarih,
      city AS sehir,
      payment_method AS odeme_yontemi,
      delivery_status AS teslimat_durumu,
      vendor_id,
      product_name AS urun_adi,
      product_code_1 AS urun_kodu,
      order_amount AS siparis_tutari,
      order_creation_timestamp AS siparis_zamani
    FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
    WHERE {where_clause}
      AND order_created_date_tr IS NOT NULL
    ORDER BY order_created_date_tr DESC, order_id
    LIMIT {selected_limit}
    """
    
    orders_df = run_query(orders_query)
    
    if not orders_df.empty:
        # Create a copy for Excel (keep numeric values)
        orders_df_excel = orders_df.copy()
        
        # Remove timezone from datetime columns for Excel
        for col in ['tarih', 'siparis_zamani']:
            if col in orders_df_excel.columns:
                if pd.api.types.is_datetime64_any_dtype(orders_df_excel[col]):
                    orders_df_excel[col] = orders_df_excel[col].dt.tz_localize(None)
                else:
                    try:
                        orders_df_excel[col] = pd.to_datetime(orders_df_excel[col])
                        if orders_df_excel[col].dt.tz is not None:
                            orders_df_excel[col] = orders_df_excel[col].dt.tz_localize(None)
                    except:
                        pass
        
        # Normalize Turkish characters for both
        for col in ['sehir', 'odeme_yontemi', 'teslimat_durumu', 'urun_adi']:
            if col in orders_df.columns:
                orders_df[col] = orders_df[col].apply(normalize_turkish)
                orders_df_excel[col] = orders_df_excel[col].apply(normalize_turkish)
        
        # Format currency for display only
        orders_df_display = orders_df.copy()
        if 'siparis_tutari' in orders_df_display.columns:
            orders_df_display['siparis_tutari'] = orders_df_display['siparis_tutari'].apply(lambda x: f"₺{x:,.2f}" if pd.notna(x) else "")
        
        # Format datetime for display
        if 'siparis_zamani' in orders_df_display.columns:
            orders_df_display['siparis_zamani'] = pd.to_datetime(orders_df_display['siparis_zamani']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Rename columns for display
        display_columns = {
            'order_id': 'Sipariş ID',
            'tarih': 'Tarih',
            'sehir': 'Şehir',
            'odeme_yontemi': 'Ödeme Yöntemi',
            'teslimat_durumu': 'Teslimat Durumu',
            'vendor_id': 'Vendor ID',
            'urun_adi': 'Ürün Adı',
            'urun_kodu': 'Ürün Kodu',
            'siparis_tutari': 'Sipariş Tutarı',
            'siparis_zamani': 'Sipariş Zamanı'
        }
        orders_df_display = orders_df_display.rename(columns=display_columns)
        orders_df_excel = orders_df_excel.rename(columns=display_columns)
        
        # Export button
        col1, col2 = st.columns([1, 4])
        with col1:
            excel_data = to_excel(orders_df_excel)
            st.download_button(
                label="📥 Excel'e İndir",
                data=excel_data,
                file_name=f"siparisler_{date_range[0]}_to_{date_range[1]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        with col2:
            st.info(f"📊 **{len(orders_df)}** sipariş gösteriliyor. Excel'e indirmek için yukarıdaki butonu kullanın.")
        
        # Display dataframe
        st.dataframe(orders_df_display, use_container_width=True, height=400)
    else:
        st.warning("Seçilen filtreler için sipariş bulunamadı.")

with tab2:
    products_query = f"""
    SELECT
      product_name,
      product_code_1,
      COUNT(DISTINCT order_id) AS unique_orders,
      COUNT(*) AS total_items_sold,
      SUM(order_amount) AS total_revenue,
      AVG(order_amount) AS avg_price
    FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
    WHERE {where_clause}
      AND product_name IS NOT NULL
    GROUP BY product_name, product_code_1
    ORDER BY unique_orders DESC
    LIMIT 50
    """
    products_df = run_query(products_query)
    products_df['product_name'] = products_df['product_name'].apply(normalize_turkish)
    products_df.columns = ['Ürün', 'Kod', 'Sipariş', 'Satılan Adet', 'Gelir', 'Ortalama Fiyat']
    products_df['Gelir'] = products_df['Gelir'].apply(lambda x: f"₺{x:,.2f}")
    products_df['Ortalama Fiyat'] = products_df['Ortalama Fiyat'].apply(lambda x: f"₺{x:,.2f}")
    st.dataframe(products_df, use_container_width=True, height=400)

with tab3:
    vendor_query = f"""
    SELECT
      vendor_id,
      COUNT(DISTINCT order_id) AS unique_orders,
      COUNT(*) AS total_items,
      SUM(order_amount) AS total_revenue,
      AVG(order_amount) AS avg_order_value
    FROM `tazecicekdb.order_data.order_items_clean_v3_enriched_partitioned_clustered`
    WHERE {where_clause}
      AND vendor_id IS NOT NULL
    GROUP BY vendor_id
    ORDER BY unique_orders DESC
    LIMIT 50
    """
    vendor_df = run_query(vendor_query)
    vendor_df.columns = ['Vendor ID', 'Sipariş', 'Ürün', 'Gelir', 'Ortalama Sipariş']
    vendor_df['Gelir'] = vendor_df['Gelir'].apply(lambda x: f"₺{x:,.2f}")
    vendor_df['Ortalama Sipariş'] = vendor_df['Ortalama Sipariş'].apply(lambda x: f"₺{x:,.2f}")
    st.dataframe(vendor_df, use_container_width=True, height=400)

# ============================================
# FOOTER
# ============================================
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"**Son Güncelleme:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
with col2:
    st.markdown("*BigQuery'den gerçek zamanlı veri*")
with col3:
    st.markdown("**Yönetim Dashboard'u v2.0**")
