import json
import requests
from bs4 import BeautifulSoup
import os
import re

# --- AYARLAR ---
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
FILE_NAME = "subscriptions.json"

def clean_name(name):
    """Oyun ismindeki fazlalıkları temizler"""
    # Örn: "FIFA 23 (2022)" -> "FIFA 23"
    name = re.sub(r'\s*\(.*?\)\s*', '', name)
    return name.strip()

def fetch_pcgw_table(url, table_index=0):
    """PCGamingWiki'den tablo çeken genel fonksiyon"""
    games = []
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT})
        if response.status_code != 200: return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        tables = soup.find_all('table', {'class': 'wikitable'})
        
        if not tables or len(tables) <= table_index: return []
        
        # İstenen tabloyu al
        target_table = tables[table_index]
        rows = target_table.find_all('tr')
        
        for row in rows[1:]: # Başlığı atla
            cols = row.find_all(['td', 'th'])
            if cols:
                # Oyun ismi genelde 1. veya 2. sütundadır
                name = cols[0].get_text(strip=True)
                if name:
                    games.append(clean_name(name))
    except Exception as e:
        print(f"⚠️ Hata ({url}): {e}")
    
    return list(set(games))

def scrape_gamepass():
    print("⏳ Game Pass listesi çekiliyor...")
    url = "https://www.pcgamingwiki.com/wiki/List_of_PC_Game_Pass_games"
    # Genelde ilk tablo aktif oyunlardır
    return fetch_pcgw_table(url, 0)

def scrape_ubisoft():
    print("⏳ Ubisoft+ listesi çekiliyor...")
    url = "https://www.pcgamingwiki.com/wiki/List_of_Ubisoft%2B_games"
    return fetch_pcgw_table(url, 0)

def scrape_ea_play():
    print("⏳ EA Play & Pro listesi çekiliyor...")
    url = "https://www.pcgamingwiki.com/wiki/List_of_EA_Play_games"
    ea_play = []
    ea_pro = []
    
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT})
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Sayfadaki tüm başlıkları ve tabloları sırayla gez
        # PCGamingWiki'de başlık (h2/h3) tablonun hemen üstündedir
        for header in soup.find_all(['h2', 'h3', 'h4']):
            header_text = header.get_text().lower()
            
            # Başlıktan sonraki ilk tabloyu bul
            next_node = header.find_next_sibling()
            while next_node and next_node.name != 'table':
                next_node = next_node.find_next_sibling()
            
            if next_node and next_node.name == 'table':
                rows = next_node.find_all('tr')
                temp_games = []
                for row in rows[1:]:
                    cols = row.find_all(['td', 'th'])
                    if cols:
                        temp_games.append(clean_name(cols[0].get_text(strip=True)))
                
                # Listelere dağıt
                if "pro" in header_text:
                    ea_pro.extend(temp_games)
                elif "play" in header_text and "pro" not in header_text:
                    ea_play.extend(temp_games)
                    
    except Exception as e:
        print(f"⚠️ EA Hatası: {e}")

    return list(set(ea_play)), list(set(ea_pro))

def load_existing_data():
    """Eski veriyi yükle (Yedek)"""
    if os.path.exists(FILE_NAME):
        try:
            with open(FILE_NAME, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {"Game Pass": [], "EA Play": [], "EA Play Pro": [], "Ubisoft+": []}

def main():
    print("🤖 Robot Başlatılıyor (PCGamingWiki Modu)...")
    
    # 1. Eski veriyi hafızaya al (Güvenlik)
    old_data = load_existing_data()
    final_data = old_data.copy()
    
    # 2. Game Pass Çek
    gp = scrape_gamepass()
    if gp: 
        final_data["Game Pass"] = gp
        print(f"✅ Game Pass: {len(gp)} oyun")
    else:
        print("⚠️ Game Pass çekilemedi, eski liste korunuyor.")

    # 3. Ubisoft+ Çek
    ubi = scrape_ubisoft()
    if ubi:
        final_data["Ubisoft+"] = ubi
        print(f"✅ Ubisoft+: {len(ubi)} oyun")
    else:
        print("⚠️ Ubisoft+ çekilemedi, eski liste korunuyor.")

    # 4. EA Play & Pro Çek
    ea_std, ea_pro = scrape_ea_play()
    if ea_std:
        final_data["EA Play"] = ea_std
        print(f"✅ EA Play: {len(ea_std)} oyun")
    if ea_pro:
        final_data["EA Play Pro"] = ea_pro
        print(f"✅ EA Play Pro: {len(ea_pro)} oyun")
    
    # 5. Kaydet
    with open(FILE_NAME, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=4)
        
    print("🎉 İşlem Tamam! subscriptions.json güncellendi.")

if __name__ == "__main__":
    main()
