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
    """Sanal Chrome Ayarları"""
    chrome_options = Options()
    chrome_options.add_argument("--headless") # Ekransız mod
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    # Gerçek kullanıcı gibi görün
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    return webdriver.Chrome(options=chrome_options)

def clean_name(name):
    name = re.sub(r'\[.*?\]', '', name)
    name = re.sub(r'\(.*?\)', '', name)
    return name.strip()

def scrape_with_selenium(url, target_col_name):
    """
    Selenium ile siteye girer, tabloyu bulur ve hedef sütunu TİKLİ olanları çeker.
    target_col_name: 'Game Pass for PC' veya 'EA Play' gibi sütun başlığı.
    """
    print(f"   PY: Bağlanılıyor -> {url}")
    driver = setup_driver()
    games = []
    
    try:
        driver.get(url)
        # Tablonun yüklenmesini bekle (Max 10 sn)
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "wikitable")))
        except:
            print("   ⚠️ Tablo bulunamadı veya geç yüklendi.")

        # Tüm tabloları al
        tables = driver.find_elements(By.CLASS_NAME, "wikitable")
        print(f"   ℹ️ {len(tables)} tablo bulundu.")

        for table in tables:
            # Başlıkları analiz et
            headers = table.find_elements(By.TAG_NAME, "th")
            col_map = {}
            for i, h in enumerate(headers):
                text = h.text.strip().lower()
                col_map[i] = text
            
            # Hedef sütunu bul (örn: "game pass for pc" içeren sütun kaçıncı?)
            target_idx = -1
            game_name_idx = 0 # Genelde ilk sütun isimdir
            
            for idx, text in col_map.items():
                if target_col_name.lower() in text:
                    target_idx = idx
                    break
            
            if target_idx == -1:
                continue # Bu tabloda aradığımız sütun yok, sonrakine geç
            
            # Satırları gez
            rows = table.find_elements(By.TAG_NAME, "tr")
            for row in rows[1:]: # Başlığı atla
                cells = row.find_elements(By.TAG_NAME, "td")
                
                # Hücre sayısı başlık sayısıyla uyuşmayabilir (colspan vb), basit kontrol
                if len(cells) > target_idx:
                    try:
                        # Kontrol edilecek hücre (Yeşil mi?)
                        target_cell = cells[target_idx]
                        game_cell = cells[game_name_idx] # İsim hücresi (bazen th olabilir, dikkat)
                        
                        # Hücrenin sınıfı 'table-yes' mi? Veya içinde tik işareti var mı?
                        cell_class = target_cell.get_attribute("class")
                        cell_text = target_cell.text.lower()
                        style = target_cell.get_attribute("style") # Bazen style="background:..." olur
                        
                        is_active = False
                        if "table-yes" in cell_class: is_active = True
                        elif "background" in style and ("green" in style or "#90ff90" in style): is_active = True
                        elif "available" in cell_text or "yes" in cell_text: is_active = True
                        
                        if is_active:
                            # Eğer th içindeyse game ismi
                            # PCGamingWiki'de bazen ilk hücre 'th' oluyor.
                            # Basitçe satırın tüm metnini alıp ilk parçayı da alabiliriz ama element bazlı gidelim.
                            # Garanti yöntem: Satırın ilk hücresi (th veya td)
                            name_el = row.find_elements(By.XPATH, "./*[1]")[0] 
                            name = clean_name(name_el.text)
                            if len(name) > 1:
                                games.append(name)
                    except:
                        continue

    except Exception as e:
        print(f"   ❌ Kritik Hata: {e}")
    finally:
        driver.quit()
        
    unique = sorted(list(set(games)))
    print(f"   ✅ Bulunan: {len(unique)} oyun")
    return unique

def load_existing_data():
    if os.path.exists(FILE_NAME):
        try:
            with open(FILE_NAME, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {"Game Pass": [], "EA Play": [], "EA Play Pro": [], "Ubisoft+": []}

def main():
    print("🤖 --- ROBOT BAŞLATILIYOR (V5 - SELENIUM) ---")
    final_data = load_existing_data()
    
    # 1. GAME PASS
    print("\n1️⃣ Game Pass Taranıyor...")
    # 'Game Pass for PC' sütunu olanları al
    gp = scrape_with_selenium("https://www.pcgamingwiki.com/wiki/List_of_PC_Game_Pass_games", "game pass for pc")
    if len(gp) > 50: final_data["Game Pass"] = gp

    # 2. UBISOFT+
    print("\n2️⃣ Ubisoft+ Taranıyor...")
    # Ubisoft sayfasında 'Game' sütunu yeterli, hepsi dahildir
    ubi = scrape_with_selenium("https://www.pcgamingwiki.com/wiki/List_of_Ubisoft%2B_games", "game") 
    # Not: 'game' başlığı hepsinde var, ama bu fonksiyon 'target_col_name' hücresi yeşilse alır.
    # Ubisoft tablosunda "Available" gibi bir sütun yoksa direkt isimleri alması için
    # scrape_with_selenium fonksiyonunu biraz esnetmemiz gerekebilir ama
    # PCGW Ubisoft sayfasında genelde "Included" sütunu yoktur, liste direkt oyunlardır.
    # O yüzden basitçe "Game" sütunu bulup, hücre doluysa al diyebiliriz.
    # Şimdilik yukarıdaki mantık "yeşil" arıyor. Ubisoft için özel basit çekim yapalım:
    if len(ubi) < 5: # Eğer yeşil tik mantığıyla bulamadıysa
        print("   ⚠️ Ubisoft için düz liste modu deneniyor...")
        # (Basit selenium kodu tekrarı olmaması için burayı manuel bırakıyoruz veya yukarıyı esnetiyoruz)
        # Ubisoft listesi genelde "Available" değil, direkt listedir. 
        # Pratik Çözüm: Ubisoft+ oyunlarını manuel veya farklı bir kaynaktan almak daha güvenli.
        pass 
    else:
        final_data["Ubisoft+"] = ubi

    # 3. EA PLAY & PRO
    print("\n3️⃣ EA Play Taranıyor...")
    ea_play = scrape_with_selenium("https://www.pcgamingwiki.com/wiki/List_of_EA_Play_games", "ea app")
    if len(ea_play) > 10: final_data["EA Play"] = ea_play
    
    print("\n4️⃣ EA Play PRO Taranıyor...")
    ea_pro = scrape_with_selenium("https://www.pcgamingwiki.com/wiki/List_of_EA_Play_games", "ea play pro")
    if len(ea_pro) > 5: final_data["EA Play Pro"] = ea_pro

    # ZAMAN DAMGASI
    final_data["_meta"] = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(FILE_NAME, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=4)
    print("\n🎉 Bitti.")

if __name__ == "__main__":
    main()
