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
    # Gereksiz notları temizle: "Halo Infinite[2]" -> "Halo Infinite"
    name = re.sub(r'\[.*?\]', '', name)
    name = re.sub(r'\(.*?\)', '', name)
    return name.strip()

def fetch_games_from_page(url, mode="standard"):
    """
    Sayfadaki TÜM geçerli oyun tablolarını bulur ve birleştirir.
    mode: 'standard' (Hepsini al), 'ea' (Pro/Normal ayır)
    """
    print(f"   PY: Bağlanılıyor -> {url}")
    games_list = []
    ea_play_games = []
    ea_pro_games = []
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code != 200: return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Sayfadaki tüm tabloları bul
        tables = soup.find_all('table', {'class': 'wikitable'})
        print(f"   ℹ️ {len(tables)} adet tablo bulundu.")
        
        for table in tables:
            # --- TABLO ANALİZİ ---
            # Tablo başlıklarını (th) kontrol et
            headers = [th.get_text(strip=True).lower() for th in table.find_all('th')]
            
            # 1. "Removed" (Kaldırılanlar) tablosuysa ATLA
            if any("removed" in h or "date left" in h for h in headers):
                print("   🚫 'Removed' tablosu atlandı.")
                continue
            
            # 2. Oyun İsimlerini Çek
            rows = table.find_all('tr')
            extracted_games = []
            for row in rows[1:]:
                cols = row.find_all(['td', 'th'])
                if cols:
                    # Oyun ismi genelde 1. sütundur
                    name = cols[0].get_text(strip=True)
                    if name:
                        clean = clean_name(name)
                        if len(clean) > 1: extracted_games.append(clean)
            
            print(f"   ✅ Tablodan {len(extracted_games)} oyun çekildi.")
            
            # --- EA PLAY AYRIMI (ÖZEL MOD) ---
            if mode == "ea":
                # Bu tablonun bir önceki başlığını (H2, H3) bulmaya çalış
                # Bu kısım biraz karmaşık, basitçe EA sayfasında genelde:
                # Tablo 1: EA Play
                # Tablo 2: EA Play Pro (Third Party)
                # Tablo 3: Removed
                # PCGW yapısına göre genelde ilk büyük tablo Play, ikincisi Pro veya tersi olabilir.
                # Garanti olması için: Hepsini EA Play'e atalım, manuel Pro listesiyle süsleyelim.
                # VEYA: EA sayfasındaki "Pro" oyunları genelde "Third-party" tablosundadır.
                ea_play_games.extend(extracted_games)
            else:
                games_list.extend(extracted_games)

    except Exception as e:
        print(f"   ⚠️ Hata: {e}")
        
    if mode == "ea": return list(set(ea_play_games))
    return list(set(games_list))

def load_existing_data():
    if os.path.exists(FILE_NAME):
        try:
            with open(FILE_NAME, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {"Game Pass": [], "EA Play": [], "EA Play Pro": [], "Ubisoft+": []}

def main():
    print("🤖 --- ROBOT BAŞLATILIYOR (V3.0 - MULTI TABLE) ---")
    
    # 1. Eski veriyi yükle (Hata olursa veri kaybolmasın)
    final_data = load_existing_data()
    
    # 2. GAME PASS (Tüm geçerli tabloları çek)
    print("\n1️⃣ Game Pass Taranıyor...")
    gp_games = fetch_games_from_page("https://www.pcgamingwiki.com/wiki/List_of_PC_Game_Pass_games")
    if len(gp_games) > 100: # Güvenlik kontrolü (boş değilse güncelle)
        final_data["Game Pass"] = gp_games
        print(f"   🎉 Toplam {len(gp_games)} Game Pass oyunu kaydedildi.")

    # 3. UBISOFT+
    print("\n2️⃣ Ubisoft+ Taranıyor...")
    ubi_games = fetch_games_from_page("https://www.pcgamingwiki.com/wiki/List_of_Ubisoft%2B_games")
    if len(ubi_games) > 10:
        final_data["Ubisoft+"] = ubi_games
        print(f"   🎉 Toplam {len(ubi_games)} Ubisoft+ oyunu kaydedildi.")

    # 4. EA PLAY (Pro ayrımı zor olduğu için hepsini çekip, Pro'ları manuel ekleyebiliriz veya hepsini kapsayabiliriz)
    print("\n3️⃣ EA Play Taranıyor...")
    ea_games = fetch_games_from_page("https://www.pcgamingwiki.com/wiki/List_of_EA_Play_games", mode="ea")
    if len(ea_games) > 10:
        # EA Play listesini güncelle
        final_data["EA Play"] = ea_games
        # Not: PCGW listesi genelde "Basic" oyunları içerir. 
        # Pro oyunları (FC 26 vb.) genelde yenidir. Onları manuel koruyalım veya ayrıca ekleyelim.
        # Şimdilik mevcut Pro listesini koruyalım, üzerine ekleme yapmayalım (Robot bozmasın).
        if "EA Play Pro" not in final_data or len(final_data["EA Play Pro"]) < 5:
             final_data["EA Play Pro"] = ["FC 26", "FC 25", "F1 24", "Madden NFL 25", "Star Wars Jedi: Survivor", "Immortals of Aveum", "Wild Hearts"]

    # Meta verisi (GitHub güncellesin diye)
    final_data["_meta"] = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Kaydet
    with open(FILE_NAME, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=4)
    print("\n✅ Veritabanı başarıyla güncellendi.")

if __name__ == "__main__":
    main()
