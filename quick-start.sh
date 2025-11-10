#!/bin/bash

# 🌸 Multi-Site Çiçek Fiyat Benchmarking - Hızlı Başlangıç Scripti

echo "🌸 Multi-Site Çiçek Fiyat Benchmarking Sistemi"
echo "=============================================="
echo ""

# Renk kodları
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Node.js kontrolü
echo -n "🔍 Node.js kontrolü... "
if command -v node &> /dev/null; then
    NODE_VERSION=$(node -v)
    echo -e "${GREEN}✓${NC} ($NODE_VERSION)"
else
    echo -e "${RED}✗${NC}"
    echo "❌ Node.js bulunamadı. Lütfen yükleyin: https://nodejs.org"
    exit 1
fi

# Python kontrolü
echo -n "🔍 Python kontrolü... "
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓${NC} ($PYTHON_VERSION)"
else
    echo -e "${RED}✗${NC}"
    echo "❌ Python bulunamadı. Lütfen yükleyin: https://python.org"
    exit 1
fi

# npm paketleri kontrolü
echo -n "📦 Node.js bağımlılıkları... "
if [ ! -d "node_modules" ]; then
    echo ""
    echo "   ⚙️  npm install çalıştırılıyor..."
    npm install --silent
    echo -e "   ${GREEN}✓${NC} Yüklendi"
else
    echo -e "${GREEN}✓${NC}"
fi

# Python paketleri kontrolü
echo -n "🐍 Python bağımlılıkları... "
if ! python3 -c "import streamlit" &> /dev/null; then
    echo ""
    echo "   ⚙️  pip install çalıştırılıyor..."
    pip3 install -q -r requirements.txt
    echo -e "   ${GREEN}✓${NC} Yüklendi"
else
    echo -e "${GREEN}✓${NC}"
fi

echo ""
echo "=============================================="
echo "🚀 Sistem Hazır!"
echo "=============================================="
echo ""

# Menü
while true; do
    echo "Ne yapmak istersiniz?"
    echo ""
    echo "  1) 🔍 Test Taraması (Tek site - hızlı)"
    echo "  2) 🌐 Full Tarama (Tüm siteler - 5-6 dakika)"
    echo "  3) 💰 Fiyat Takibi (Slack bildirimi ile)"
    echo "  4) 📊 Dashboard'u Aç"
    echo "  5) 🗄️  BigQuery Sync"
    echo "  6) 📋 Sistem Durumu"
    echo "  7) 🔧 Site Ayarlarını Düzenle"
    echo "  0) ❌ Çıkış"
    echo ""
    read -p "Seçiminiz (0-7): " choice
    echo ""

    case $choice in
        1)
            echo "🔍 Test taraması başlıyor (sadece ÇiçekSepeti)..."
            echo ""
            node scraper.js
            echo ""
            echo -e "${GREEN}✓${NC} Tamamlandı!"
            echo ""
            ;;
        2)
            echo "🌐 Tüm siteler taranıyor (bu 5-6 dakika sürebilir)..."
            echo ""
            node multi-site-scraper.js
            echo ""
            echo -e "${GREEN}✓${NC} Tamamlandı!"
            echo ""
            ;;
        3)
            if [ -z "$SLACK_WEBHOOK_URL" ]; then
                echo -e "${YELLOW}⚠️  SLACK_WEBHOOK_URL environment variable tanımlı değil${NC}"
                read -p "Slack Webhook URL'i girin (boş bırakırsanız bildirim olmaz): " webhook
                if [ ! -z "$webhook" ]; then
                    export SLACK_WEBHOOK_URL="$webhook"
                fi
            fi
            echo "💰 Fiyat takibi başlıyor..."
            echo ""
            node multi-site-price-monitor.js
            echo ""
            echo -e "${GREEN}✓${NC} Tamamlandı!"
            echo ""
            ;;
        4)
            echo "📊 Dashboard açılıyor..."
            echo ""
            if [ ! -f "benchmark_report.json" ]; then
                echo -e "${YELLOW}⚠️  Henüz veri yok. Önce tarama yapılıyor...${NC}"
                echo ""
                node multi-site-scraper.js > /tmp/scraper_output.json 2>&1
                node -e "
                    const data = JSON.parse(require('fs').readFileSync('/tmp/scraper_output.json', 'utf8'));
                    const report = {
                        date: new Date().toISOString(),
                        summary: {
                            total_sites: 1,
                            successful_sites: 1,
                            total_products: data.products ? data.products.length : 0
                        },
                        price_analysis: { by_site: {}, by_category: {} }
                    };
                    require('fs').writeFileSync('benchmark_report.json', JSON.stringify(report));
                    console.log('Report created');
                "
            fi
            echo "🌐 Dashboard: http://localhost:8501"
            echo ""
            echo -e "${YELLOW}📝 Not: Dashboard'u kapatmak için Ctrl+C${NC}"
            echo ""
            streamlit run benchmarking_dashboard.py
            echo ""
            ;;
        5)
            if [ -z "$GCP_PROJECT_ID" ]; then
                echo -e "${YELLOW}⚠️  GCP_PROJECT_ID environment variable tanımlı değil${NC}"
                read -p "Google Cloud Project ID girin: " project_id
                if [ -z "$project_id" ]; then
                    echo -e "${RED}❌ Project ID gerekli${NC}"
                    echo ""
                    continue
                fi
                export GCP_PROJECT_ID="$project_id"
            fi
            
            echo "🗄️  BigQuery'ye senkronize ediliyor..."
            echo ""
            python3 bigquery_sync.py
            echo ""
            echo -e "${GREEN}✓${NC} Tamamlandı!"
            echo ""
            ;;
        6)
            echo "📋 Sistem Durumu"
            echo "================"
            echo ""
            
            # Dosya kontrolleri
            echo "📁 Veri Dosyaları:"
            if [ -f "sites-config.json" ]; then
                site_count=$(python3 -c "import json; print(len(json.load(open('sites-config.json'))['sites']))" 2>/dev/null || echo "?")
                echo -e "  • sites-config.json: ${GREEN}✓${NC} ($site_count site)"
            else
                echo -e "  • sites-config.json: ${RED}✗${NC}"
            fi
            
            if [ -f "multi_site_price_history.json" ]; then
                last_update=$(python3 -c "import json; print(json.load(open('multi_site_price_history.json')).get('last_update', 'N/A'))" 2>/dev/null || echo "N/A")
                echo -e "  • price_history.json: ${GREEN}✓${NC} (Son: $last_update)"
            else
                echo -e "  • price_history.json: ${YELLOW}⚠${NC} (Henüz veri yok)"
            fi
            
            if [ -f "benchmark_report.json" ]; then
                report_date=$(python3 -c "import json; print(json.load(open('benchmark_report.json')).get('date', 'N/A'))" 2>/dev/null || echo "N/A")
                echo -e "  • benchmark_report.json: ${GREEN}✓${NC} (Tarih: $report_date)"
            else
                echo -e "  • benchmark_report.json: ${YELLOW}⚠${NC} (Henüz rapor yok)"
            fi
            
            echo ""
            echo "🔧 Environment Variables:"
            [ ! -z "$SLACK_WEBHOOK_URL" ] && echo -e "  • SLACK_WEBHOOK_URL: ${GREEN}✓${NC}" || echo -e "  • SLACK_WEBHOOK_URL: ${YELLOW}⚠${NC} (Tanımlı değil)"
            [ ! -z "$GCP_PROJECT_ID" ] && echo -e "  • GCP_PROJECT_ID: ${GREEN}✓${NC}" || echo -e "  • GCP_PROJECT_ID: ${YELLOW}⚠${NC} (Tanımlı değil)"
            [ ! -z "$GOOGLE_APPLICATION_CREDENTIALS" ] && echo -e "  • GOOGLE_APPLICATION_CREDENTIALS: ${GREEN}✓${NC}" || echo -e "  • GOOGLE_APPLICATION_CREDENTIALS: ${YELLOW}⚠${NC} (Tanımlı değil)"
            
            echo ""
            ;;
        7)
            echo "🔧 Site ayarlarını düzenlemek için:"
            echo ""
            echo "  nano sites-config.json"
            echo ""
            echo "veya"
            echo ""
            echo "  code sites-config.json"
            echo ""
            read -p "Şimdi açmak ister misiniz? (y/n): " open_editor
            if [ "$open_editor" = "y" ] || [ "$open_editor" = "Y" ]; then
                if command -v code &> /dev/null; then
                    code sites-config.json
                elif command -v nano &> /dev/null; then
                    nano sites-config.json
                else
                    echo "❌ Editor bulunamadı"
                fi
            fi
            echo ""
            ;;
        0)
            echo "👋 Görüşmek üzere!"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Geçersiz seçim${NC}"
            echo ""
            ;;
    esac
done

