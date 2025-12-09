import json
import time
import re
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- AYARLAR ---
FILE_NAME = "subscriptions.json"

def setup_driver():
    """Stabil Sürücü Ayarları"""
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--blink-settings=imagesEnabled=false") # Hız için
    
    # User Agent (Bot gibi görünmemek için)
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def clean_name(name):
    # Dipnotları temizle: "Halo Infinite[2]" -> "Halo Infinite"
    name = re.sub(r'\[.*?\]', '', name)
    name = re.sub(r'\(.*?\)', '', name)
    return name.strip()

def scrape_universal(url, target_col_name, check_green=True):
    """
    Evrensel Tablo Okuyucu (TH ve TD fark etmeksizin okur)
    check_green: True ise hedef sütunda yeşil tik arar. False ise tüm listeyi alır (Ubisoft gibi).
    """
    print(f"   🚀 Bağlanılıyor -> {url}")
    driver = setup_driver()
    games = []
    
    try:
        driver.get(url)
        # Tablonun tamamen yüklenmesi için bekle
        try:
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, "wikitable")))
        except:
            print("   ⚠️ Tablo geç yüklendi veya bulunamadı.")

        tables = driver.find_elements(By.CLASS_NAME, "wikitable")
        print(f"   ℹ️ {len(tables)} tablo taraniyor...")

        for table in tables:
            try:
                # 1. Başlıkları analiz et ve hedef sütunu bul
                headers = table.find_elements(By.TAG_NAME, "th")
                col_map = {}
                for i, h in enumerate(headers):
                    col_map[i] = h.text.strip().lower()
                
                target_idx = -1
                name_idx = 0 # Oyun ismi genelde ilk sütundur
                
                # Eğer yeşil tik kontrolü yapılacaksa sütunu bul
                if check_green:
                    for idx, text in col_map.items():
                        if target_col_name.lower() in text:
                            target_idx = idx
                            break
                    if target_idx == -1: continue # Bu tabloda aradığımız sütun yok, atla
                
                # 2. Satırları gez
                rows = table.find_elements(By.TAG_NAME, "tr")
                for row in rows[1:]: # Başlığı atla
                    # --- KRİTİK DÜZELTME ---
                    # Sadece 'td' değil, 'th' de olabilir (Oyun isimleri bazen başlıktır)
                    # Bu yüzden xpath ./* kullanarak tüm çocukları sırasıyla alıyoruz
                    cells = row.find_elements(By.XPATH, "./*")
                    
                    if not cells: continue
                    
                    # Oyun İsmi (İlk Hücre)
                    try:
                        raw_name = cells[0].text
                        game_name = clean_name(raw_name)
                    except: continue

                    if len(game_name) < 2: continue

                    # 3. Kontrol Mantığı
                    if not check_green:
                        # Ubisoft gibi düz listeler: Direkt ekle
                        games.append(game_name)
                    else:
                        # Game Pass / EA gibi onaylı listeler
                        if len(cells) > target_idx:
                            cell = cells[target_idx]
                            html_content = cell.get_attribute('outerHTML').lower()
                            text_content = cell.text.lower()
                            
                            # Yeşil Tik Kontrolü (Genişletilmiş)
                            is_active = False
                            if "tickcross-true" in html_content: is_active = True
                            elif "table-yes" in html_content: is_active = True
                            elif "store-origin" in html_content: is_active = True # EA için
                            elif "background" in html_content and ("green" in html_content or "#90ff90" in html_content): is_active = True
                            elif "available" in text_content: is_active = True
                            
                            if is_active:
                                games.append(game_name)

            except Exception as e:
                continue # Tablo bozuksa sonrakine geç

    except Exception as e:
        print(f"   ❌ Hata: {e}")
    finally:
        driver.quit()
        
    unique = sorted(list(set(games)))
    print(f"   ✅ Toplanan: {len(unique)} oyun")
    return unique

def load_existing_data():
    if os.path.exists(FILE_NAME):
        try:
            with open(FILE_NAME, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {"Game Pass": [], "EA Play": [], "EA Play Pro": [], "Ubisoft+": []}

def main():
    print("🤖 --- ROBOT BAŞLATILIYOR (V11 - DEEP SCAN) ---")
    final_data = load_existing_data()
    
    # 1. GAME PASS
    print("\n1️⃣ Game Pass...")
    gp = scrape_universal(
        "https://www.pcgamingwiki.com/wiki/List_of_PC_Game_Pass_games", 
        "game pass for pc", 
        check_green=True
    )
    if len(gp) > 100: final_data["Game Pass"] = gp

    # 2. UBISOFT+ (Düz Liste Modu)
    print("\n2️⃣ Ubisoft+...")
    # Ubisoft sayfasında sütun kontrolü yapmadan tabloyu süpür
    ubi = scrape_universal(
        "https://www.pcgamingwiki.com/wiki/List_of_Ubisoft%2B_games", 
        "", 
        check_green=False 
    )
    if len(ubi) > 10: final_data["Ubisoft+"] = ubi

    # 3. EA PLAY (Basic)
    print("\n3️⃣ EA Play...")
    ea_play = scrape_universal(
        "https://www.pcgamingwiki.com/wiki/List_of_EA_Play_games", 
        "ea app", 
        check_green=True
    )
    if len(ea_play) > 10: final_data["EA Play"] = ea_play
    
    # 4. EA PLAY PRO
    print("\n4️⃣ EA Play Pro...")
    ea_pro = scrape_universal(
        "https://www.pcgamingwiki.com/wiki/List_of_EA_Play_games", 
        "ea play pro", 
        check_green=True
    )
    
    # Pro listesi bazen az çekilebilir, manuel destek ekleyelim
    manual_pro = ["FC 26", "FC 25", "F1 24", "Madden NFL 25", "Star Wars Jedi: Survivor"]
    combined_pro = list(set(ea_pro + manual_pro))
    
    if len(combined_pro) > 5:
        final_data["EA Play Pro"] = combined_pro

    # ZAMAN DAMGASI
    final_data["_meta"] = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(FILE_NAME, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=4)
        
    print("\n🎉 İşlem Tamamlandı.")

if __name__ == "__main__":
    main()
