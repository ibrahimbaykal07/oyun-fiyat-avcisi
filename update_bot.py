import json
import requests
from bs4 import BeautifulSoup
import os
import re
from datetime import datetime

# --- AYARLAR ---
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
FILE_NAME = "subscriptions.json"

def clean_name(name):
    """Oyun ismindeki [1], (2022) gibi fazlalıkları temizler"""
    name = re.sub(r'\[.*?\]', '', name)
    name = re.sub(r'\(.*?\)', '', name)
    return name.strip()

def is_cell_green(cell):
    """Bir hücrenin (td) 'Yeşil Tik' içerip içermediğini kontrol eder"""
    if not cell: return False
    # PCGamingWiki'de yeşil hücreler 'table-yes' sınıfına sahiptir
    classes = cell.get('class', [])
    if any("table-yes" in c for c in classes):
        return True
    # Bazen yazı olarak "Available" yazar
    if "available" in cell.get_text().lower():
        return True
    return False

def get_column_index(headers, keyword):
    """Tablo başlıkları arasında aranan kelimenin kaçıncı sırada olduğunu bulur"""
    for i, h in enumerate(headers):
        if keyword.lower() in h.get_text(strip=True).lower():
            return i
    return -1

def scrape_pcgw_gamepass():
    print("⏳ Game Pass taranıyor...")
    url = "https://www.pcgamingwiki.com/wiki/List_of_PC_Game_Pass_games"
    games = []
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'wikitable'}) # İlk büyük tablo
        
        if table:
            # Başlıkları analiz et
            headers = table.find_all('th')
            name_idx = 0 # Genelde ilk sütun isimdir
            # "Game Pass for PC" sütununu bul
            check_idx = get_column_index(headers, "Game Pass for PC")
            
            if check_idx == -1: 
                print("   ⚠️ 'Game Pass for PC' sütunu bulunamadı, varsayılan 3. sütun deneniyor.")
                check_idx = 3 # Yedek tahmin
            
            # Satırları gez
            rows = table.find_all('tr')[1:]
            for row in rows:
                cols = row.find_all(['td', 'th'])
                if len(cols) > check_idx:
                    # İlgili kutucuk yeşil mi?
                    if is_cell_green(cols[check_idx]):
                        game_name = cols[name_idx].get_text(strip=True)
                        games.append(clean_name(game_name))
                        
    except Exception as e:
        print(f"   ❌ Hata: {e}")
        
    print(f"   ✅ {len(games)} oyun bulundu.")
    return list(set(games))

def scrape_pcgw_ea():
    print("⏳ EA Play & Pro taranıyor...")
    url = "https://www.pcgamingwiki.com/wiki/List_of_EA_Play_games"
    ea_play = []
    ea_pro = []
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'wikitable'})
        
        if table:
            headers = table.find_all('th')
            name_idx = 0
            
            # Sütunları bul
            play_idx = get_column_index(headers, "EA App") # Normal EA Play
            pro_idx = get_column_index(headers, "EA Play Pro") # Pro
            
            rows = table.find_all('tr')[1:]
            for row in rows:
                cols = row.find_all(['td', 'th'])
                if len(cols) > max(play_idx, pro_idx):
                    game_name = clean_name(cols[name_idx].get_text(strip=True))
                    
                    # Normal EA Play Kontrolü
                    if play_idx != -1 and is_cell_green(cols[play_idx]):
                        ea_play.append(game_name)
                        
                    # Pro Kontrolü
                    if pro_idx != -1 and is_cell_green(cols[pro_idx]):
                        ea_pro.append(game_name)
                        
    except Exception as e:
        print(f"   ❌ Hata: {e}")
        
    print(f"   ✅ Play: {len(ea_play)} | Pro: {len(ea_pro)}")
    return list(set(ea_play)), list(set(ea_pro))

def scrape_pcgw_ubisoft():
    print("⏳ Ubisoft+ taranıyor...")
    url = "https://www.pcgamingwiki.com/wiki/List_of_Ubisoft%2B_games"
    games = []
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'wikitable'})
        
        if table:
            rows = table.find_all('tr')[1:]
            for row in rows:
                cols = row.find_all(['td', 'th'])
                if cols:
                    # Ubisoft sayfasında sadece oyun ismi yeterli
                    game_name = cols[0].get_text(strip=True)
                    games.append(clean_name(game_name))
    except Exception as e:
        print(f"   ❌ Hata: {e}")
        
    print(f"   ✅ {len(games)} oyun bulundu.")
    return list(set(games))

def load_existing_data():
    if os.path.exists(FILE_NAME):
        try:
            with open(FILE_NAME, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {"Game Pass": [], "EA Play": [], "EA Play Pro": [], "Ubisoft+": []}

def main():
    print("🤖 --- ROBOT BAŞLATILIYOR (V5 - YEŞİL TİK MODU) ---")
    
    final_data = load_existing_data()
    
    # 1. Game Pass
    gp_new = scrape_pcgw_gamepass()
    if len(gp_new) > 50: final_data["Game Pass"] = gp_new
    
    # 2. EA Play & Pro
    ea_new, pro_new = scrape_pcgw_ea()
    if len(ea_new) > 10: final_data["EA Play"] = ea_new
    if len(pro_new) > 5: final_data["EA Play Pro"] = pro_new
    
    # 3. Ubisoft+
    ubi_new = scrape_pcgw_ubisoft()
    if len(ubi_new) > 10: final_data["Ubisoft+"] = ubi_new
    
    # Zaman Damgası
    final_data["_meta"] = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Kaydet
    with open(FILE_NAME, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=4)
        
    print("\n🎉 Veritabanı başarıyla güncellendi.")

if __name__ == "__main__":
    main()
