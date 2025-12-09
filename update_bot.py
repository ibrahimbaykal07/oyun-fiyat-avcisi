import json
import time
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager # KRİTİK EKLENTİ
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- AYARLAR ---
FILE_NAME = "subscriptions.json"

def setup_driver():
    """GitHub Actions Uyumlu Sürücü Ayarları"""
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")
    chrome_options.page_load_strategy = 'eager'
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # OTOMATİK SÜRÜCÜ KURULUMU (HATA ÇÖZÜCÜ)
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def clean_name(name):
    name = re.sub(r'\[.*?\]', '', name)
    name = re.sub(r'\(.*?\)', '', name)
    return name.strip()

def scrape_specific_condition(url, target_col_name, match_string, is_ubisoft=False):
    print(f"   🚀 Bağlanılıyor -> {url}")
    games = []
    driver = None
    
    try:
        driver = setup_driver()
        driver.set_page_load_timeout(60) # Süreyi artırdım
        
        try:
            driver.get(url)
        except:
            print("   ⚠️ Sayfa yükleme zaman aşımı (devam ediliyor)...")
            driver.execute_script("window.stop();")

        # Tabloyu bekle
        try:
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, "wikitable")))
        except:
            print("   ⚠️ Tablo bulunamadı, sayfa yapısı farklı olabilir.")

        tables = driver.find_elements(By.CLASS_NAME, "wikitable")
        print(f"   ℹ️ {len(tables)} tablo taraniyor...")

        for table in tables:
            try:
                # Başlıkları analiz et
                headers = table.find_elements(By.TAG_NAME, "th")
                col_map = {}
                for i, h in enumerate(headers):
                    col_map[i] = h.text.strip().lower()
                
                target_idx = -1
                
                if is_ubisoft:
                    target_idx = 0 
                else:
                    for idx, text in col_map.items():
                        if target_col_name.lower() in text:
                            target_idx = idx
                            break
                
                if target_idx == -1: continue 

                rows = table.find_elements(By.TAG_NAME, "tr")
                for row in rows[1:]:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    
                    # Güvenli hücre okuma
                    # PCGamingWiki'de bazen ilk sütun TH olur, bazen TD.
                    # Satırın tamamından isme ulaşmaya çalışalım.
                    try:
                        # Satırın ilk hücresi (oyun adı)
                        first_cell = row.find_elements(By.XPATH, "./*[1]")[0]
                        name = clean_name(first_cell.text)
                    except: continue

                    if not name: continue

                    if is_ubisoft:
                        games.append(name)
                        continue

                    # Diğerleri için koşul kontrolü
                    # target_idx'e denk gelen hücreyi bulmaya çalış (Offset olabilir)
                    # En garantisi: Satırdaki tüm hücreleri (td+th) alıp index'e bakmak
                    all_cells = row.find_elements(By.XPATH, "./*")
                    
                    if len(all_cells) > target_idx:
                        target_cell = all_cells[target_idx]
                        cell_html = target_cell.get_attribute('innerHTML')
                        
                        # KULLANICININ VERDİĞİ KOD KONTROLÜ
                        if match_string in cell_html:
                            games.append(name)

            except Exception as inner_e:
                # Tek bir tabloda hata olursa diğerine geç
                continue 

    except Exception as e:
        print(f"   ❌ Genel Hata: {e}")
    finally:
        if driver: driver.quit()
        
    unique = sorted(list(set(games)))
    print(f"   ✅ '{target_col_name}' için {len(unique)} oyun bulundu.")
    return unique

def load_existing_data():
    if os.path.exists(FILE_NAME):
        try:
            with open(FILE_NAME, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {"Game Pass": [], "EA Play": [], "EA Play Pro": [], "Ubisoft+": []}

def main():
    print("🤖 --- ROBOT BAŞLATILIYOR (V8 - DRIVER MANAGER) ---")
    
    # Hata olursa eski veriyi korumak için yükle
    final_data = load_existing_data()
    
    # 1. GAME PASS
    print("\n1️⃣ Game Pass...")
    gp = scrape_specific_condition(
        "https://www.pcgamingwiki.com/wiki/List_of_PC_Game_Pass_games", 
        "game pass for pc", 
        "tickcross-true"
    )
    if len(gp) > 10: final_data["Game Pass"] = gp

    # 2. EA PLAY (BASIC)
    print("\n2️⃣ EA Play...")
    ea_play = scrape_specific_condition(
        "https://www.pcgamingwiki.com/wiki/List_of_EA_Play_games", 
        "ea app", 
        "store-origin"
    )
    if len(ea_play) > 5: final_data["EA Play"] = ea_play

    # 3. EA PLAY PRO
    print("\n3️⃣ EA Play Pro...")
    ea_pro = scrape_specific_condition(
        "https://www.pcgamingwiki.com/wiki/List_of_EA_Play_games", 
        "ea play pro", 
        "store-origin"
    )
    # Manuel destek (FC 26 vb. henüz listede yoksa ekle)
    manual_pro = ["FC 26", "FC 25", "F1 24", "Madden NFL 25", "Star Wars Jedi: Survivor"]
    
    if len(ea_pro) > 2:
        final_data["EA Play Pro"] = list(set(ea_pro + manual_pro))
    else:
        # Çekemediysek eskiyi koru + manueli ekle
        existing = final_data.get("EA Play Pro", [])
        final_data["EA Play Pro"] = list(set(existing + manual_pro))

    # 4. UBISOFT+
    print("\n4️⃣ Ubisoft+...")
    ubi = scrape_specific_condition(
        "https://www.pcgamingwiki.com/wiki/List_of_Ubisoft%2B_games", 
        "game", 
        "", 
        is_ubisoft=True
    )
    if len(ubi) > 10: final_data["Ubisoft+"] = ubi

    # Zaman Damgası (GitHub'ı tetiklemek için)
    final_data["_meta"] = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(FILE_NAME, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=4)
        
    print("\n🎉 İşlem Tamamlandı.")

if __name__ == "__main__":
    main()
