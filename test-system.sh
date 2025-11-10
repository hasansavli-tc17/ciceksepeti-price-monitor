#!/bin/bash

# 🧪 Sistem Test Scripti - Tüm bileşenleri test eder

echo "🧪 Multi-Site Sistem Test Başlıyor..."
echo "======================================"
echo ""

# Renk kodları
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

TESTS_PASSED=0
TESTS_FAILED=0

# Test fonksiyonu
run_test() {
    local test_name=$1
    local test_command=$2
    
    echo -n "  ⏳ $test_name... "
    
    if eval "$test_command" > /tmp/test_output.log 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        echo "     Error: $(head -1 /tmp/test_output.log)"
        ((TESTS_FAILED++))
        return 1
    fi
}

# 1. Prerequisite testleri
echo -e "${BLUE}[1/6] Prerequisite Tests${NC}"
echo "------------------------"
run_test "Node.js yüklü" "command -v node"
run_test "Python3 yüklü" "command -v python3"
run_test "npm yüklü" "command -v npm"
run_test "pip3 yüklü" "command -v pip3"
echo ""

# 2. Bağımlılık testleri
echo -e "${BLUE}[2/6] Dependency Tests${NC}"
echo "----------------------"
run_test "node_modules mevcut" "test -d node_modules"
run_test "Puppeteer yüklü" "test -d node_modules/puppeteer"
run_test "Python paketleri" "python3 -c 'import streamlit, plotly, pandas'"
echo ""

# 3. Konfigürasyon testleri
echo -e "${BLUE}[3/6] Configuration Tests${NC}"
echo "-------------------------"
run_test "sites-config.json mevcut" "test -f sites-config.json"
run_test "sites-config.json valid JSON" "python3 -c 'import json; json.load(open(\"sites-config.json\"))'"
run_test "package.json mevcut" "test -f package.json"
run_test "requirements.txt mevcut" "test -f requirements.txt"
echo ""

# 4. Script testleri
echo -e "${BLUE}[4/6] Script Tests${NC}"
echo "------------------"
run_test "scraper.js mevcut" "test -f scraper.js"
run_test "multi-site-scraper.js mevcut" "test -f multi-site-scraper.js"
run_test "multi-site-price-monitor.js mevcut" "test -f multi-site-price-monitor.js"
run_test "benchmarking_dashboard.py mevcut" "test -f benchmarking_dashboard.py"
run_test "bigquery_sync.py mevcut" "test -f bigquery_sync.py"
run_test "quick-start.sh executable" "test -x quick-start.sh"
echo ""

# 5. Syntax testleri
echo -e "${BLUE}[5/6] Syntax Tests${NC}"
echo "------------------"
run_test "scraper.js syntax" "node --check scraper.js"
run_test "multi-site-scraper.js syntax" "node --check multi-site-scraper.js"
run_test "multi-site-price-monitor.js syntax" "node --check multi-site-price-monitor.js"
run_test "benchmarking_dashboard.py syntax" "python3 -m py_compile benchmarking_dashboard.py"
run_test "bigquery_sync.py syntax" "python3 -m py_compile bigquery_sync.py"
echo ""

# 6. Functional test (opsiyonel)
echo -e "${BLUE}[6/6] Functional Tests (Optional)${NC}"
echo "-----------------------------------"

read -p "🔍 Gerçek tarama testi yapmak ister misiniz? (y/n): " do_scrape_test
if [ "$do_scrape_test" = "y" ] || [ "$do_scrape_test" = "Y" ]; then
    echo ""
    echo "  ⏳ Test taraması çalışıyor (30 saniye)..."
    
    if timeout 45 node scraper.js > /tmp/scraper_test.json 2>&1; then
        # JSON çıktısını kontrol et
        if python3 -c "import json, sys; data=json.load(open('/tmp/scraper_test.json')); sys.exit(0 if 'products' in data else 1)" 2>/dev/null; then
            product_count=$(python3 -c "import json; print(len(json.load(open('/tmp/scraper_test.json'))['products']))" 2>/dev/null)
            echo -e "  ${GREEN}✓ Scraper çalışıyor ($product_count ürün)${NC}"
            ((TESTS_PASSED++))
        else
            echo -e "  ${RED}✗ Scraper çıktısı geçersiz${NC}"
            ((TESTS_FAILED++))
        fi
    else
        echo -e "  ${RED}✗ Scraper timeout veya hata${NC}"
        ((TESTS_FAILED++))
    fi
else
    echo -e "  ${YELLOW}⊘ Atlandı${NC}"
fi

echo ""

# Sonuçlar
echo "======================================"
echo -e "${BLUE}Test Sonuçları${NC}"
echo "======================================"
echo ""

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
SUCCESS_RATE=$(python3 -c "print(f'{($TESTS_PASSED/$TOTAL_TESTS*100):.1f}')" 2>/dev/null || echo "0")

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "  ${GREEN}✓ Tüm testler başarılı!${NC}"
    echo ""
    echo "  📊 Toplam: $TOTAL_TESTS test"
    echo "  ✓ Başarılı: $TESTS_PASSED"
    echo "  ✗ Başarısız: $TESTS_FAILED"
    echo "  📈 Başarı Oranı: ${SUCCESS_RATE}%"
    echo ""
    echo -e "  ${GREEN}🎉 Sistem hazır! quick-start.sh ile başlayabilirsiniz.${NC}"
    exit 0
else
    echo -e "  ${YELLOW}⚠ Bazı testler başarısız${NC}"
    echo ""
    echo "  📊 Toplam: $TOTAL_TESTS test"
    echo "  ✓ Başarılı: $TESTS_PASSED"
    echo "  ✗ Başarısız: $TESTS_FAILED"
    echo "  📈 Başarı Oranı: ${SUCCESS_RATE}%"
    echo ""
    echo -e "  ${YELLOW}🔧 Lütfen başarısız testleri kontrol edin:${NC}"
    echo ""
    
    if [ ! -d "node_modules" ]; then
        echo "     • npm install çalıştırın"
    fi
    
    if ! python3 -c 'import streamlit' 2>/dev/null; then
        echo "     • pip3 install -r requirements.txt çalıştırın"
    fi
    
    exit 1
fi

