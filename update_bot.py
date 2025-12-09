import json
import requests
from bs4 import BeautifulSoup
import os
import re
from datetime import datetime

# --- AYARLAR ---
# Gerçek bir tarayıcı gibi görünmek için detaylı User-Agent
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://google.com"
}
FILE_NAME = "subscriptions.json"

def clean_name(name):
    """Oyun ismindeki gereksiz karakterleri temizler"""
    name = re.sub(r'\[.*?\]', '', name) # [not 1] gibi şeyleri sil
    name = re.sub(r'\(.*?\)', '', name) # (2022) gibi şeyleri sil
    return name.strip()

def fetch_pcgw_table(url, table_keywords=[]):
    """
    PCGamingWiki'den akıllı tablo çekici.
    Tablo başlıklarında 'keywords' arar, bulursa o tabloyu çeker.
    """
    print(f"   PY: Bağlanılıyor -> {url}")
    games = []
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            print(f"   ❌ Hata Kodu: {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        tables = soup.find_all('table', {'class': 'wikitable'})
        
        print(f"   ℹ️ Sayfada {len(tables)} adet tablo bulundu.")
        
        target_table = None
        
        # Eğer özel anahtar kelime verilmediyse (Game Pass gibi) ilk tabloyu al
        if not table_keywords:
            if tables: target_table = tables[0]
        else:
            # Anahtar kelimeye göre doğru tabloyu bul (Örn: 'Ubisoft+ Classics' vs 'Premium')
            # PCGW'de tablolar genelde bir H2 veya H3 başlığının altındadır.
            # Bu biraz karmaşık olabilir, o yüzden basitçe ilk büyük tabloyu alalım şimdilik.
            # Gelişmiş versiyonda tablo içeriğine bakabiliriz.
            if tables: target_table = tables[0]

        if target_table:
            rows = target_table.find_all('tr')
            print(f"   ℹ️ Tabloda {len(rows)} satır var.")
            for row in rows[1:]: # Başlığı atla
                cols = row.find_all(['td', 'th'])
                if cols:
                    # Oyun ismi genelde 1. veya 2. sütundadır (Wiki yapısına göre değişir)
                    # Game Pass listesinde 1. sütun (index 0) oyun ismidir.
                    name_col = cols[0].get_text(strip=True)
                    if name_col:
                        clean = clean_name(name_col)
                        if len(clean) > 1: games.append(clean)
        else:
            print("   ❌ Hedef tablo bulunamadı.")

    except Exception as e:
        print(f"   ⚠️ Kritik Hata: {e}")
    
    unique_games = sorted(list(set(games)))
    print(f"   ✅ Çekilen Oyun Sayısı: {len(unique_games)}")
    return unique_games

def load_existing_data():
    if os.path.exists(FILE_NAME):
        try:
            with open(FILE_NAME, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {"Game Pass": [], "EA Play": [], "EA Play Pro": [], "Ubisoft+": []}

def main():
    print("🤖 --- ROBOT BAŞLATILIYOR (V2.1 - TIMESTAMP) ---")
    
    # 1. Eski veriyi yükle (Yedek)
    final_data = load_existing_data()
    
    # 2. Game Pass
    print("\n1️⃣ Game Pass Taranıyor...")
    gp_games = fetch_pcgw_table("https://www.pcgamingwiki.com/wiki/List_of_PC_Game_Pass_games")
    if gp_games: final_data["Game Pass"] = gp_games

    # 3. Ubisoft+
    print("\n2️⃣ Ubisoft+ Taranıyor...")
    ubi_games = fetch_pcgw_table("https://www.pcgamingwiki.com/wiki/List_of_Ubisoft%2B_games")
    if ubi_games: final_data["Ubisoft+"] = ubi_games

    # 4. EA Play (Pro ve Normal ayrımı PCGW'de tek tabloda zor olabilir, şimdilik basit çekelim)
    print("\n3️⃣ EA Play Taranıyor...")
    ea_games = fetch_pcgw_table("https://www.pcgamingwiki.com/wiki/List_of_EA_Play_games")
    if ea_games: 
        # EA listesi karışık gelirse diye mevcut listeyi koruyarak üstüne ekleyelim veya filtreleyelim
        # Şimdilik direkt EA Play'e atıyoruz, Pro ayrımı manuel kalabilir.
        final_data["EA Play"] = ea_games

    # --- ÖNEMLİ: GÜNCELLEME ZAMANINI EKLE ---
    # Bu sayede dosya içeriği her zaman değişmiş olur ve GitHub commit atar.
    final_data["_meta"] = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "Success"
    }
    
    # 5. Kaydet
    with open(FILE_NAME, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=4)
        
    print(f"\n🎉 Dosya yazıldı! Son Güncelleme: {final_data['_meta']['last_updated']}")

if __name__ == "__main__":
    main()
