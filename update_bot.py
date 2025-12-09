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
    # Dipnotları ve parantezleri temizle: "Halo Infinite[2]" -> "Halo Infinite"
    name = re.sub(r'\[.*?\]', '', name)
    name = re.sub(r'\(.*?\)', '', name)
    # Satır sonu boşluklarını temizle
    return name.strip()

def fetch_from_pcgamingwiki(url):
    """PCGamingWiki'den Tabloları Çeker"""
    print(f"   PY: Bağlanılıyor -> {url}")
    games = []
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 'wikitable' sınıfına sahip tüm tabloları bul
        tables = soup.find_all('table', {'class': 'wikitable'})
        
        for table in tables:
            # Tablo başlıklarını kontrol et (Removed/Left tablolarını atla)
            headers = [th.get_text().lower() for th in table.find_all('th')]
            header_text = " ".join(headers)
            
            if "removed" in header_text or "left" in header_text:
                continue # Bu tablo eski oyunlar, atla.
            
            # Satırları gez
            rows = table.find_all('tr')
            for row in rows[1:]:
                cols = row.find_all(['td', 'th'])
                if cols:
                    # Oyun ismi genelde ilk sütundadır
                    raw_name = cols[0].get_text(strip=True)
                    name = clean_name(raw_name)
                    if len(name) > 1:
                        games.append(name)
                        
    except Exception as e:
        print(f"   ⚠️ Hata: {e}")
        
    return list(set(games)) # Tekrarları sil ve döndür

def load_existing_data():
    """Mevcut dosyayı yükle (Veri kaybını önlemek için)"""
    if os.path.exists(FILE_NAME):
        try:
            with open(FILE_NAME, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    
    # Dosya yoksa varsayılan boş şablon
    return {
        "Game Pass": [],
        "EA Play": [],
        "EA Play Pro": [],
        "Ubisoft+": []
    }

def main():
    print("🤖 --- ROBOT BAŞLATILIYOR (V4.0 - ROBUST) ---")
    
    final_data = load_existing_data()
    
    # 1. GAME PASS
    print("\n1️⃣ Game Pass Taranıyor...")
    gp_new = fetch_from_pcgamingwiki("https://www.pcgamingwiki.com/wiki/List_of_PC_Game_Pass_games")
    if len(gp_new) > 100: # En az 100 oyun bulduysa güncelle (Güvenlik Limiti)
        final_data["Game Pass"] = gp_new
        print(f"   ✅ Güncellendi: {len(gp_new)} oyun.")
    else:
        print(f"   ⚠️ Yetersiz veri ({len(gp_new)}), eski liste korunuyor.")

    # 2. UBISOFT+
    print("\n2️⃣ Ubisoft+ Taranıyor...")
    ubi_new = fetch_from_pcgamingwiki("https://www.pcgamingwiki.com/wiki/List_of_Ubisoft%2B_games")
    if len(ubi_new) > 20:
        final_data["Ubisoft+"] = ubi_new
        print(f"   ✅ Güncellendi: {len(ubi_new)} oyun.")
    else:
        print(f"   ⚠️ Yetersiz veri ({len(ubi_new)}), eski liste korunuyor.")

    # 3. EA PLAY (Link değişti, daha temiz liste)
    print("\n3️⃣ EA Play Taranıyor...")
    ea_new = fetch_from_pcgamingwiki("https://www.pcgamingwiki.com/wiki/List_of_EA_Play_games")
    if len(ea_new) > 20:
        # PCGamingWiki'de Play ve Pro genelde karışık veya tek tablodur.
        # Basit çözüm: Hepsini EA Play'e at, Pro listesini manuel koru.
        final_data["EA Play"] = ea_new
        print(f"   ✅ Güncellendi: {len(ea_new)} oyun.")
    
    # 4. EA PLAY PRO (Manuel Koruma / Güncelleme)
    # Pro listesi çok spesifik olduğu için (FC 26 vb.) silinmesini istemiyoruz.
    if "EA Play Pro" not in final_data or len(final_data["EA Play Pro"]) < 5:
        final_data["EA Play Pro"] = ["FC 26", "FC 25", "F1 24", "Madden NFL 25", "Star Wars Jedi: Survivor", "Immortals of Aveum", "Wild Hearts", "Dead Space Remake"]
    
    # --- ZAMAN DAMGASI (GITHUB GÜNCELLESİN DİYE) ---
    final_data["_meta"] = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "Success"
    }
    
    # KAYDET
    with open(FILE_NAME, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=4)
        
    print("\n🎉 İşlem Tamamlandı.")

if __name__ == "__main__":
    main()
