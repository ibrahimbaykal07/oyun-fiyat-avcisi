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
    # Dipnotları temizle
    name = re.sub(r'\[.*?\]', '', name)
    name = re.sub(r'\(.*?\)', '', name)
    return name.strip()

def scrape_pcgw_fast(url, target_col_name):
    """
    Hızlı ve Agresif Tarama (Requests + BS4)
    """
    print(f"   🚀 Bağlanılıyor -> {url}")
    games = []
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Tüm tabloları bul
        tables = soup.find_all('table', {'class': 'wikitable'})
        print(f"   ℹ️ {len(tables)} tablo bulundu.")
        
        for table in tables:
            # Sütun başlıklarını bul
            headers = [th.get_text(strip=True).lower() for th in table.find_all('th')]
            
            # Hedef sütun kaçıncı sırada?
            target_idx = -1
            for i, h in enumerate(headers):
                if target_col_name.lower() in h:
                    target_idx = i
                    break
            
            if target_idx == -1: 
                continue # Bu tabloda aradığımız sütun yok, geç.

            # Satırları gez
            rows = table.find_all('tr')
            for row in rows[1:]:
                cols = row.find_all(['td', 'th'])
                
                # Oyun ismi genelde ilk hücredir
                if not cols: continue
                
                # Sütun sayısı tutuyor mu?
                # Not: Bazen TH kullanıldığı için index kayabilir, ama genelde 
                # wiki tablolarında tüm hücreler TD veya TH olarak sıralıdır.
                # Ancak 'Game' sütunu TH ise, cells listesinde o da vardır.
                
                # Basit kontrol: Satırdaki toplam hücre sayısı hedeften büyük olmalı
                if len(cols) <= target_idx: continue
                
                # Hedef hücreye bak (Yeşil mi?)
                target_cell = cols[target_idx]
                classes = target_cell.get('class', [])
                style = target_cell.get('style', '')
                text = target_cell.get_text(strip=True).lower()
                
                is_active = False
                if 'table-yes' in classes: is_active = True
                elif 'background' in str(style) and ('#90ff90' in str(style) or 'lightgreen' in str(style)): is_active = True
                elif text == 'available': is_active = True
                
                if is_active:
                    name = clean_name(cols[0].get_text(strip=True))
                    if len(name) > 1:
                        games.append(name)

    except Exception as e:
        print(f"   ❌ Hata: {e}")
        
    unique = sorted(list(set(games)))
    print(f"   ✅ Toplanan: {len(unique)}")
    return unique

def scrape_ubisoft_fast():
    # Ubisoft için özel basit fonksiyon (Sadece isimleri al)
    print("   🚀 Ubisoft+ Taranıyor...")
    games = []
    try:
        url = "https://www.pcgamingwiki.com/wiki/List_of_Ubisoft%2B_games"
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        tables = soup.find_all('table', {'class': 'wikitable'})
        
        for table in tables:
            for row in table.find_all('tr')[1:]:
                cols = row.find_all(['td', 'th'])
                if cols:
                    name = clean_name(cols[0].get_text(strip=True))
                    if len(name) > 1: games.append(name)
    except: pass
    print(f"   ✅ Toplanan: {len(games)}")
    return list(set(games))

def load_existing_data():
    if os.path.exists(FILE_NAME):
        try:
            with open(FILE_NAME, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {"Game Pass": [], "EA Play": [], "EA Play Pro": [], "Ubisoft+": []}

def main():
    print("🤖 --- ROBOT BAŞLATILIYOR (V59 - FAST & FURIOUS) ---")
    
    # 1. Verileri Çek
    print("\n1️⃣ Game Pass...")
    gp = scrape_pcgw_fast("https://www.pcgamingwiki.com/wiki/List_of_PC_Game_Pass_games", "Game Pass for PC")
    
    # KONTROL NOKTASI: Eğer Game Pass boşsa işlemi durdur (HATA VER)
    if len(gp) < 50:
        raise Exception(f"❌ HATA: Game Pass listesi çekilemedi! Sadece {len(gp)} oyun bulundu.")

    print("\n2️⃣ EA Play (Basic)...")
    ea_play = scrape_pcgw_fast("https://www.pcgamingwiki.com/wiki/List_of_EA_Play_games", "EA App")
    
    print("\n3️⃣ EA Play Pro...")
    ea_pro = scrape_pcgw_fast("https://www.pcgamingwiki.com/wiki/List_of_EA_Play_games", "EA Play Pro")
    
    # Manuel Pro Destek
    manual_pro = ["FC 26", "FC 25", "F1 24", "Madden NFL 25", "Star Wars Jedi: Survivor"]
    ea_pro = list(set(ea_pro + manual_pro))

    print("\n4️⃣ Ubisoft+...")
    ubi = scrape_ubisoft_fast()

    # Hepsini Birleştir
    final_data = {
        "Game Pass": gp,
        "EA Play": ea_play,
        "EA Play Pro": ea_pro,
        "Ubisoft+": ubi,
        "_meta": {
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    }
    
    # Kaydet
    with open(FILE_NAME, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=4)
        
    print("\n🎉 BAŞARILI! Dosya yazıldı.")

if __name__ == "__main__":
    main()
