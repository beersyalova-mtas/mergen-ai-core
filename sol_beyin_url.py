import requests
from bs4 import BeautifulSoup
import re

def siber_url_ozetle(url):
    try:
        # 🌐 SİBER SIZMA: Siteye kullanıcı gibi (User-Agent) bağlanıyoruz
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            return None, f"Siber Hata: Siteye erişim engellendi (Kod: {response.status_code})"

        # ✂️ SİBER NEŞTER: HTML içindeki çöpleri (reklam, script, stil) temizliyoruz
        soup = BeautifulSoup(response.text, 'html.parser')
        for script_or_style in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script_or_style.decompose()

        # Ana metni çek ve temizle
        metin = soup.get_text()
        satirlar = (line.strip() for line in metin.splitlines())
        parcalar = (phrase.strip() for line in satirlar for phrase in line.split("  "))
        temiz_metin = '\n'.join(chunk for chunk in parcalar if chunk)

        # 🧠 SİBER ÖZET: İlk 1000 karakteri (ana fikri) Mergen'e pasla
        ozet_metin = temiz_metin[:1000] + "..." if len(temiz_metin) > 1000 else temiz_metin
        
        return ozet_metin, "Başarılı"

    except Exception as e:
        return None, f"Siber Bağlantı Koptu: {str(e)}"