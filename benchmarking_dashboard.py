#!/usr/bin/env python3
"""
Multi-Site Çiçek Fiyat Benchmarking Dashboard
Streamlit tabanlı interaktif dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import datetime, timedelta
import os

# Sayfa ayarları
st.set_page_config(
    page_title="Çiçek Fiyat Benchmarking",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Stil
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FF69B4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1rem;
    }
    .site-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #FF69B4;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Veri yükleme fonksiyonları
@st.cache_data(ttl=300)
def load_benchmark_report():
    """Benchmarking raporunu yükle"""
    try:
        with open('benchmark_report.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

@st.cache_data(ttl=300)
def load_price_history():
    """Fiyat geçmişini yükle"""
    try:
        with open('multi_site_price_history.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

@st.cache_data(ttl=300)
def load_sites_config():
    """Site ayarlarını yükle"""
    try:
        with open('sites-config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def format_price(price):
    """Fiyat formatla"""
    try:
        return f"{float(price):,.2f}₺"
    except:
        return "N/A"

def create_site_comparison_chart(report):
    """Site karşılaştırma grafiği"""
    data = []
    for site_name, site_data in report['price_analysis']['by_site'].items():
        data.append({
            'Site': site_name,
            'Ortalama': float(site_data['avg_price']),
            'Minimum': float(site_data['min_price']),
            'Maksimum': float(site_data['max_price']),
            'Ürün Sayısı': site_data['product_count']
        })
    
    df = pd.DataFrame(data)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Ortalama Fiyat',
        x=df['Site'],
        y=df['Ortalama'],
        marker_color='#FF69B4',
        text=df['Ortalama'].apply(lambda x: f"{x:.2f}₺"),
        textposition='outside'
    ))
    
    fig.add_trace(go.Bar(
        name='Minimum Fiyat',
        x=df['Site'],
        y=df['Minimum'],
        marker_color='#90EE90',
        text=df['Minimum'].apply(lambda x: f"{x:.2f}₺"),
        textposition='outside'
    ))
    
    fig.add_trace(go.Bar(
        name='Maksimum Fiyat',
        x=df['Site'],
        y=df['Maksimum'],
        marker_color='#FFB6C1',
        text=df['Maksimum'].apply(lambda x: f"{x:.2f}₺"),
        textposition='outside'
    ))
    
    fig.update_layout(
        title='Site Bazında Fiyat Karşılaştırması',
        xaxis_title='Site',
        yaxis_title='Fiyat (₺)',
        barmode='group',
        height=500,
        showlegend=True
    )
    
    return fig

def create_category_comparison_chart(report):
    """Kategori karşılaştırma grafiği"""
    data = []
    for category, cat_data in report['price_analysis']['by_category'].items():
        data.append({
            'Kategori': category,
            'Ortalama Fiyat': float(cat_data['avg_price']),
            'Ürün Sayısı': cat_data['count']
        })
    
    df = pd.DataFrame(data).sort_values('Ortalama Fiyat', ascending=False)
    
    fig = px.bar(
        df,
        x='Kategori',
        y='Ortalama Fiyat',
        color='Ortalama Fiyat',
        color_continuous_scale='Purples',
        text='Ortalama Fiyat',
        title='Çiçek Kategorilerine Göre Ortalama Fiyatlar'
    )
    
    fig.update_traces(texttemplate='%{text:.2f}₺', textposition='outside')
    fig.update_layout(height=500, showlegend=False)
    
    return fig

def create_category_by_site_heatmap(report):
    """Kategori ve site bazında heatmap"""
    categories = list(report['price_analysis']['by_category'].keys())
    sites = list(report['price_analysis']['by_site'].keys())
    
    # Matris oluştur
    matrix = []
    for category in categories:
        row = []
        cat_data = report['price_analysis']['by_category'][category]
        for site in sites:
            if site in cat_data['prices_by_site']:
                row.append(float(cat_data['prices_by_site'][site]['avg']))
            else:
                row.append(0)
        matrix.append(row)
    
    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=sites,
        y=categories,
        colorscale='RdYlGn_r',
        text=[[f"{val:.2f}₺" if val > 0 else "N/A" for val in row] for row in matrix],
        texttemplate='%{text}',
        textfont={"size": 10},
        colorbar=dict(title="Fiyat (₺)")
    ))
    
    fig.update_layout(
        title='Site ve Kategori Bazında Fiyat Haritası',
        xaxis_title='Site',
        yaxis_title='Kategori',
        height=600
    )
    
    return fig

def create_product_count_pie(report):
    """Ürün dağılım grafiği"""
    data = []
    for site_name, site_data in report['price_analysis']['by_site'].items():
        data.append({
            'Site': site_name,
            'Ürün Sayısı': site_data['product_count']
        })
    
    df = pd.DataFrame(data)
    
    fig = px.pie(
        df,
        values='Ürün Sayısı',
        names='Site',
        title='Sitelere Göre Ürün Dağılımı',
        color_discrete_sequence=px.colors.sequential.RdBu
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=400)
    
    return fig

# Ana sayfa
def main():
    st.markdown('<div class="main-header">🌸 Çiçek Fiyat Benchmarking Dashboard</div>', unsafe_allow_html=True)
    
    # Veri yükle
    report = load_benchmark_report()
    history = load_price_history()
    config = load_sites_config()
    
    if not report:
        st.error("❌ Benchmarking raporu bulunamadı. Lütfen önce 'node multi-site-price-monitor.js' çalıştırın.")
        return
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Ayarlar")
        
        if history:
            st.success(f"✅ Son Güncelleme:\n{datetime.fromisoformat(history['last_update']).strftime('%d/%m/%Y %H:%M')}")
        
        st.markdown("---")
        
        # Site filtreleme
        all_sites = list(report['price_analysis']['by_site'].keys())
        selected_sites = st.multiselect(
            "Siteler",
            all_sites,
            default=all_sites
        )
        
        # Kategori filtreleme
        all_categories = list(report['price_analysis']['by_category'].keys())
        selected_categories = st.multiselect(
            "Kategoriler",
            all_categories,
            default=all_categories
        )
        
        st.markdown("---")
        
        if st.button("🔄 Verileri Yenile", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        st.caption("📊 Canlı verilerle güncellenir")
    
    # Özet metrikler
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🏪 Taranan Site",
            value=report['summary']['successful_sites']
        )
    
    with col2:
        st.metric(
            label="📦 Toplam Ürün",
            value=report['summary']['total_products']
        )
    
    with col3:
        all_prices = []
        for site_data in report['price_analysis']['by_site'].values():
            all_prices.append(float(site_data['avg_price']))
        avg_all = sum(all_prices) / len(all_prices) if all_prices else 0
        st.metric(
            label="💰 Genel Ortalama",
            value=f"{avg_all:.2f}₺"
        )
    
    with col4:
        st.metric(
            label="🎯 Kategori",
            value=len(report['price_analysis']['by_category'])
        )
    
    st.markdown("---")
    
    # Tab'lar
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Site Karşılaştırma", "🎨 Kategori Analizi", "🔥 Heatmap", "📋 Detaylı Tablo"])
    
    with tab1:
        st.plotly_chart(create_site_comparison_chart(report), use_container_width=True)
        st.plotly_chart(create_product_count_pie(report), use_container_width=True)
        
        # Site detayları
        st.subheader("📊 Site Detayları")
        for site_name, site_data in report['price_analysis']['by_site'].items():
            if site_name in selected_sites:
                with st.expander(f"🏪 {site_name}"):
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Ürün Sayısı", site_data['product_count'])
                    col2.metric("Ortalama", format_price(site_data['avg_price']))
                    col3.metric("Minimum", format_price(site_data['min_price']))
                    col4.metric("Maksimum", format_price(site_data['max_price']))
    
    with tab2:
        st.plotly_chart(create_category_comparison_chart(report), use_container_width=True)
        
        # Kategori detayları
        st.subheader("🎨 Kategori Detayları")
        for category, cat_data in report['price_analysis']['by_category'].items():
            if category in selected_categories:
                with st.expander(f"🌸 {category}"):
                    col1, col2 = st.columns(2)
                    col1.metric("Toplam Ürün", cat_data['count'])
                    col2.metric("Ortalama Fiyat", format_price(cat_data['avg_price']))
                    
                    st.markdown("**Site Bazında Fiyatlar:**")
                    site_prices = []
                    for site, price_data in cat_data['prices_by_site'].items():
                        site_prices.append({
                            'Site': site,
                            'Ürün Sayısı': price_data['count'],
                            'Ortalama Fiyat': format_price(price_data['avg'])
                        })
                    st.dataframe(pd.DataFrame(site_prices), use_container_width=True, hide_index=True)
    
    with tab3:
        st.plotly_chart(create_category_by_site_heatmap(report), use_container_width=True)
        
        st.info("💡 **İpucu:** Koyu renkler daha yüksek fiyatları gösterir. Beyaz alanlar o sitede o kategoride ürün olmadığını gösterir.")
    
    with tab4:
        st.subheader("📋 Tüm Ürünler")
        
        if history and history.get('sites'):
            all_products = []
            for site_id, site_data in history['sites'].items():
                for product_id, product in site_data['products'].items():
                    all_products.append({
                        'Site': site_data['name'],
                        'Ürün Adı': product['name'],
                        'Kategori': product.get('category', 'N/A'),
                        'Fiyat': float(product['price']),
                        'URL': product.get('url', '')
                    })
            
            df = pd.DataFrame(all_products)
            
            # Filtreleme
            if selected_sites:
                df = df[df['Site'].isin(selected_sites)]
            if selected_categories:
                df = df[df['Kategori'].isin(selected_categories)]
            
            # Sıralama seçeneği
            sort_by = st.selectbox("Sırala:", ['Fiyat (Düşükten Yükseğe)', 'Fiyat (Yüksekten Düşüğe)', 'Site', 'Kategori'])
            
            if sort_by == 'Fiyat (Düşükten Yükseğe)':
                df = df.sort_values('Fiyat', ascending=True)
            elif sort_by == 'Fiyat (Yüksekten Düşüğe)':
                df = df.sort_values('Fiyat', ascending=False)
            elif sort_by == 'Site':
                df = df.sort_values('Site')
            elif sort_by == 'Kategori':
                df = df.sort_values('Kategori')
            
            # Fiyat formatla
            df['Fiyat'] = df['Fiyat'].apply(lambda x: f"{x:,.2f}₺")
            
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "URL": st.column_config.LinkColumn("URL", display_text="🔗 Link")
                }
            )
            
            # İstatistikler
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            col1.metric("Gösterilen Ürün", len(df))
            prices = [float(p.replace('₺', '').replace(',', '')) for p in df['Fiyat']]
            if prices:
                col2.metric("En Düşük", f"{min(prices):.2f}₺")
                col3.metric("En Yüksek", f"{max(prices):.2f}₺")

if __name__ == "__main__":
    main()

