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
    """Hızlandırılmış Sürücü"""
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    # Resimleri ve gereksizleri engelle
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")
    chrome_options.page_load_strategy = 'eager' # HTML gelir gelmez başla
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def clean_name(name):
    name = re.sub(r'\[.*?\]', '', name)
    name = re.sub(r'\(.*?\)', '', name)
    return name.strip()

def scrape_with_timeout(url, target_col_name, match_string, is_ubisoft=False):
    print(f"   🚀 Bağlanılıyor -> {url}")
    games = []
    driver = None
    
    try:
        driver = setup_driver()
        # KRİTİK AYAR: 20 saniyede açılmazsa durdur ve devam et
        driver.set_page_load_timeout(20)
        
        try:
            driver.get(url)
        except:
            print("   ⚠️ Zaman aşımı! Yükleme durduruluyor ve okumaya geçiliyor...")
            driver.execute_script("window.stop();")

        # Tabloyu bekle (Max 5 sn)
        try:
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "wikitable")))
        except:
            pass # Bekleme, varsa al yoksa devam et

        tables = driver.find_elements(By.CLASS_NAME, "wikitable")
        print(f"   ℹ️ {len(tables)} tablo taraniyor...")

        for table in tables:
            try:
                # Başlıkları al
                headers = table.find_elements(By.TAG_NAME, "th")
                col_map = {}
                for i, h in enumerate(headers):
                    col_map[i] = h.text.strip().lower()
                
                # Hedef sütunu bul
                target_idx = -1
                
                if is_ubisoft:
                    target_idx = 0 
                else:
                    for idx, text in col_map.items():
                        if target_col_name.lower() in text:
                            target_idx = idx
                            break
                
                if target_idx == -1: continue 

                # Satırları gez
                rows = table.find_elements(By.TAG_NAME, "tr")
                for row in rows[1:]:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    
                    try:
                        # Oyun ismi
                        first_cell = row.find_elements(By.XPATH, "./*[1]")[0]
                        name = clean_name(first_cell.text)
                    except: continue

                    if not name: continue

                    if is_ubisoft:
                        games.append(name)
                        continue

                    # Koşul kontrolü
                    all_cells = row.find_elements(By.XPATH, "./*")
                    if len(all_cells) > target_idx:
                        target_cell = all_cells[target_idx]
                        cell_html = target_cell.get_attribute('innerHTML')
                        
                        # Kullanıcının verdiği class/kod kontrolü
                        if match_string in cell_html:
                            games.append(name)

            except: continue 

    except Exception as e:
        print(f"   ❌ Hata: {e}")
    finally:
        if driver: driver.quit()
        
    unique = sorted(list(set(games)))
    print(f"   ✅ '{target_col_name}' -> {len(unique)} oyun.")
    return unique

def load_existing_data():
    if os.path.exists(FILE_NAME):
        try:
            with open(FILE_NAME, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {"Game Pass": [], "EA Play": [], "EA Play Pro": [], "Ubisoft+": []}

def main():
    print("🤖 --- ROBOT BAŞLATILIYOR (V10 - ANTI-FREEZE) ---")
    final_data = load_existing_data()
    
    # 1. GAME PASS
    print("\n1️⃣ Game Pass...")
    gp = scrape_with_timeout(
        "https://www.pcgamingwiki.com/wiki/List_of_PC_Game_Pass_games", 
        "game pass for pc", "tickcross-true"
    )
    if len(gp) > 10: final_data["Game Pass"] = gp

    # 2. EA PLAY
    print("\n2️⃣ EA Play...")
    ea_play = scrape_with_timeout(
        "https://www.pcgamingwiki.com/wiki/List_of_EA_Play_games", 
        "ea app", "store-origin"
    )
    if len(ea_play) > 5: final_data["EA Play"] = ea_play

    # 3. EA PLAY PRO
    print("\n3️⃣ EA Play Pro...")
    ea_pro = scrape_with_timeout(
        "https://www.pcgamingwiki.com/wiki/List_of_EA_Play_games", 
        "ea play pro", "store-origin"
    )
    manual_pro = ["FC 26", "FC 25", "F1 24", "Madden NFL 25", "Star Wars Jedi: Survivor"]
    if len(ea_pro) > 2:
        final_data["EA Play Pro"] = list(set(ea_pro + manual_pro))
    else:
        # Hata olursa eskiyi koru + manuel
        existing = final_data.get("EA Play Pro", [])
        final_data["EA Play Pro"] = list(set(existing + manual_pro))

    # 4. UBISOFT+
    print("\n4️⃣ Ubisoft+...")
    ubi = scrape_with_timeout(
        "https://www.pcgamingwiki.com/wiki/List_of_Ubisoft%2B_games", 
        "game", "", is_ubisoft=True
    )
    if len(ubi) > 10: final_data["Ubisoft+"] = ubi

    # Zaman Damgası
    final_data["_meta"] = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(FILE_NAME, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=4)
        
    print("\n🎉 İşlem Tamamlandı.")

if __name__ == "__main__":
    main()
