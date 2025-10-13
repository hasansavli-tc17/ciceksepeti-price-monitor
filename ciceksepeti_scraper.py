#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json
import re

def scrape_ciceksepeti():
    url = "https://www.ciceksepeti.com/d/cicek-buketleri"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Script taglerinde JSON data ara
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                print(json.dumps(data, indent=2, ensure_ascii=False)[:500])
            except:
                pass
        
        # HTML yapısını kaydet
        with open('/tmp/ciceksepeti_page.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("\nSayfa kaydedildi: /tmp/ciceksepeti_page.html")
        
    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    scrape_ciceksepeti()
