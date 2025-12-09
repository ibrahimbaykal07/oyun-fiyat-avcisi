import json
import time
import os
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- AYARLAR ---
FILE_NAME = "subscriptions.json"

def setup_driver():
    """Hızlandırılmış Chrome Ayarları"""
    chrome_options = Options()
    chrome_options.add_argument("--headless") # Ekransız mod
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions") # Eklentileri kapat
    chrome_options.add_argument("--blink-settings=imagesEnabled=false") # RESİMLERİ YÜKLEME (HIZ İÇİN)
    chrome_options.page_load_strategy = 'eager' # Tüm sayfanın bitmesini bekleme, HTML gelince başla
    
    # Gerçek kullanıcı gibi görün
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    return webdriver.Chrome(options=chrome_options)

def clean_name(name):
    name = re.sub(r'\[.*?\]', '', name)
    name = re.sub(r'\(.*?\)', '', name)
    return name.strip()

def scrape_with_selenium(url, target_col_name):
    """Güvenli ve Hızlı Scraping"""
    print(f"   🚀 Bağlanılıyor -> {url}")
    driver = setup_driver()
    games = []
    
    try:
        # Sayfaya git (Timeout 20 saniye)
        driver.set_page_load_timeout(30)
        try:
            driver.get(url)
        except:
            print("   ⚠️ Sayfa yüklenmesi uzun sürdü, işleme devam ediliyor...")
            driver.execute_script("window.stop();") # Yüklemeyi durdur ve devam et

        # Tabloyu bekle (Max 5 saniye)
        try:
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "wikitable")))
        except:
            print("   ⚠️ Tablo hemen bulunamadı.")

        tables = driver.find_elements(By.CLASS_NAME, "wikitable")
        print(f"   ℹ️ {len(tables)} tablo bulundu.")

        for table in tables:
            try:
                # Başlıkları analiz et
                headers = table.find_elements(By.TAG_NAME, "th")
                col_map = {}
                for i, h in enumerate(headers):
                    col_map[i] = h.text.strip().lower()
                
                # Hedef sütunu bul
                target_idx = -1
                name_idx = 0 
                
                for idx, text in col_map.items():
                    if target_col_name.lower() in text:
                        target_idx = idx
                        break
                
                if target_idx == -1: continue 

                # Satırları gez
                rows = table.find_elements(By.TAG_NAME, "tr")
                for row in rows[1:]:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) > target_idx:
                        target_cell = cells[target_idx]
                        
                        # Hücre rengi veya içeriği kontrolü
                        # PCGamingWiki'de yeşil tik için class="table-yes" kullanılır
                        cell_html = target_cell.get_attribute('outerHTML').lower()
                        is_active = "table-yes" in cell_html or "background" in cell_html or "available" in target_cell.text.lower()
                        
                        if is_active:
                            # İsim bazen th bazen td olabilir, ilk elemanı al
                            name_el = row.find_elements(By.XPATH, "./*[1]")[0]
                            name = clean_name(name_el.text)
                            if len(name) > 1:
                                games.append(name)
            except:
                continue # Tablo bozuksa sonrakine geç

    except Exception as e:
        print(f"   ❌ Hata: {e}")
    finally:
        driver.quit() # Tarayıcıyı kesinlikle kapat
        
    unique = sorted(list(set(games)))
    print(f"   ✅ Toplanan: {len(unique)}")
    return unique

def load_existing_data():
    if os.path.exists(FILE_NAME):
        try:
            with open(FILE_NAME, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {"Game Pass": [], "EA Play": [], "EA Play Pro": [], "Ubisoft+": []}

def main():
    print("🤖 --- ROBOT BAŞLATILIYOR (V6 - TURBO MODE) ---")
    start_time = time.time()
    
    final_data = load_existing_data()
    
    # 1. Game Pass
    print("\n1️⃣ Game Pass...")
    gp = scrape_with_selenium("https://www.pcgamingwiki.com/wiki/List_of_PC_Game_Pass_games", "game pass for pc")
    if len(gp) > 50: final_data["Game Pass"] = gp

    # 2. Ubisoft+
    print("\n2️⃣ Ubisoft+...")
    # Ubisoft için sadece oyun ismini almak yeterli, "game" sütunu her zaman vardır
    ubi = scrape_with_selenium("https://www.pcgamingwiki.com/wiki/List_of_Ubisoft%2B_games", "game")
    if len(ubi) > 10: final_data["Ubisoft+"] = ubi

    # 3. EA Play & Pro
    print("\n3️⃣ EA Play...")
    ea_play = scrape_with_selenium("https://www.pcgamingwiki.com/wiki/List_of_EA_Play_games", "ea app")
    if len(ea_play) > 10: final_data["EA Play"] = ea_play
    
    print("\n4️⃣ EA Play Pro...")
    ea_pro = scrape_with_selenium("https://www.pcgamingwiki.com/wiki/List_of_EA_Play_games", "ea play pro")
    # Pro listesine manuel olarak yeni oyunları da ekleyelim (Garanti olsun)
    manual_pro = ["FC 26", "FC 25", "F1 24", "Madden NFL 25", "Star Wars Jedi: Survivor", "Immortals of Aveum"]
    if len(ea_pro) > 5:
        final_data["EA Play Pro"] = list(set(ea_pro + manual_pro))
    else:
        final_data["EA Play Pro"] = list(set(final_data.get("EA Play Pro", []) + manual_pro))

    # Zaman Damgası
    final_data["_meta"] = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(FILE_NAME, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=4)
        
    duration = time.time() - start_time
    print(f"\n🎉 İşlem {duration:.2f} saniyede tamamlandı.")

if __name__ == "__main__":
    main()
