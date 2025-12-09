import json
import time
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
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    # Resimleri yükleme (Hız için)
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")
    # Sayfa yüklenmesini bekleme stratejisi (Hız için)
    chrome_options.page_load_strategy = 'eager'
    
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    return webdriver.Chrome(options=chrome_options)

def clean_name(name):
    """Oyun ismini temizler"""
    name = re.sub(r'\[.*?\]', '', name)
    name = re.sub(r'\(.*?\)', '', name)
    return name.strip()

def scrape_specific_condition(url, target_col_name, match_string, is_ubisoft=False):
    """
    Belirtilen sütunda, belirtilen HTML kodunu (match_string) arar.
    """
    print(f"   🚀 Bağlanılıyor -> {url}")
    driver = setup_driver()
    games = []
    
    try:
        # 1. Sayfayı Aç
        driver.set_page_load_timeout(45)
        try:
            driver.get(url)
        except:
            print("   ⚠️ Sayfa yüklenmesi uzun sürdü, işleme devam ediliyor...")
            driver.execute_script("window.stop();")

        # 2. Tabloyu Bekle
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "wikitable")))
        except:
            print("   ⚠️ Tablo hemen bulunamadı, yine de deneniyor.")

        tables = driver.find_elements(By.CLASS_NAME, "wikitable")
        print(f"   ℹ️ {len(tables)} tablo taraniyor...")

        for table in tables:
            try:
                # Başlıkları analiz et
                headers = table.find_elements(By.TAG_NAME, "th")
                col_map = {}
                for i, h in enumerate(headers):
                    col_map[i] = h.text.strip().lower()
                
                # Hedef sütun indeksini bul
                target_idx = -1
                name_idx = 0 # Genelde 0, ama bazen değişebilir
                
                # Ubisoft için özel durum: Direkt ilk sütunu alacağız
                if is_ubisoft:
                    target_idx = 0 
                else:
                    for idx, text in col_map.items():
                        if target_col_name.lower() in text:
                            target_idx = idx
                            break
                
                if target_idx == -1: continue # Bu tabloda aranan sütun yok

                # Satırları gez
                rows = table.find_elements(By.TAG_NAME, "tr")
                for row in rows[1:]: # Başlığı atla
                    cells = row.find_elements(By.TAG_NAME, "td")
                    
                    # Hücre sayısı yeterli mi?
                    check_idx = target_idx
                    # Bazen th ile başlar satır, o zaman kaydırma gerekebilir.
                    # Garanti yöntem: Satırın HTML'ini alıp analiz etmek yerine hücreye gitmek.
                    
                    if len(cells) > 0:
                        # Oyun İsmi (Genelde ilk hücre, bazen th olabilir)
                        try:
                            # İlk eleman (th veya td) oyun ismidir
                            name_el = row.find_elements(By.XPATH, "./*[1]")[0]
                            name = clean_name(name_el.text)
                        except: continue

                        if not name: continue

                        # Ubisoft ise direkt ekle
                        if is_ubisoft:
                            games.append(name)
                            continue

                        # Diğerleri için koşul kontrolü
                        # Eğer target_idx hücrelerde varsa
                        # NOT: 'th' olduğu için 'cells' listesi 1 eksik olabilir. 
                        # Genelde 1. sütun TH, diğerleri TD'dir. Yani cells[target_idx - 1] olabilir.
                        # PCGamingWiki yapısı: Oyun Adı (th/td) | Dev | Pub | Date | System | [Sütunlar...]
                        
                        # Basit ve sağlam yöntem: Satırın HTML'ini çekip bakmak yerine,
                        # Hedef sütuna denk gelen hücrenin HTML'ine bakalım.
                        
                        # Hücreyi bulmaya çalışalım (Index kayması olabilir, dikkat)
                        # Genelde Oyun ismi TH ise, cells listesi 0'dan başlar ve o 2. sütundur.
                        # target_idx 5 ise, cells[4] olabilir.
                        
                        # Daha güvenli yöntem: Row içindeki tüm hücreleri alıp (th+td) indexe bakmak
                        all_cells = row.find_elements(By.XPATH, "./*")
                        if len(all_cells) > target_idx:
                            target_cell = all_cells[target_idx]
                            cell_html = target_cell.get_attribute('innerHTML')
                            
                            # KULLANICININ VERDİĞİ KRİTİK KOD KONTROLÜ
                            if match_string in cell_html:
                                games.append(name)

            except Exception as e:
                continue 

    except Exception as e:
        print(f"   ❌ Hata: {e}")
    finally:
        driver.quit()
        
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
    print("🤖 --- ROBOT BAŞLATILIYOR (V7 - CLASS DETECTIVE) ---")
    start_time = time.time()
    
    final_data = load_existing_data()
    
    # 1. GAME PASS
    # Kriter: "Game Pass for PC" sütununda "tickcross-true" sınıfı var mı?
    print("\n1️⃣ Game Pass...")
    gp = scrape_specific_condition(
        "https://www.pcgamingwiki.com/wiki/List_of_PC_Game_Pass_games", 
        "game pass for pc", 
        "tickcross-true"
    )
    if len(gp) > 50: final_data["Game Pass"] = gp

    # 2. EA PLAY (BASIC)
    # Kriter: "EA App" sütununda "store-origin" sınıfı var mı?
    print("\n2️⃣ EA Play...")
    ea_play = scrape_specific_condition(
        "https://www.pcgamingwiki.com/wiki/List_of_EA_Play_games", 
        "ea app", 
        "store-origin"
    )
    if len(ea_play) > 10: final_data["EA Play"] = ea_play

    # 3. EA PLAY PRO
    # Kriter: "EA Play Pro" sütununda "store-origin" sınıfı var mı?
    print("\n3️⃣ EA Play Pro...")
    ea_pro = scrape_specific_condition(
        "https://www.pcgamingwiki.com/wiki/List_of_EA_Play_games", 
        "ea play pro", 
        "store-origin"
    )
    # Manuel destek (FC 26 vb. henüz listede yoksa)
    manual_pro = ["FC 26", "FC 25", "F1 24", "Madden NFL 25", "Star Wars Jedi: Survivor"]
    if len(ea_pro) > 5:
        final_data["EA Play Pro"] = list(set(ea_pro + manual_pro))
    else:
        # Eğer çekemezse eskisine manuel ekle
        final_data["EA Play Pro"] = list(set(final_data.get("EA Play Pro", []) + manual_pro))

    # 4. UBISOFT+
    # Kriter: Tüm oyunları al (is_ubisoft=True)
    print("\n4️⃣ Ubisoft+...")
    ubi = scrape_specific_condition(
        "https://www.pcgamingwiki.com/wiki/List_of_Ubisoft%2B_games", 
        "game", 
        "", # String aramıyoruz, hepsini alıyoruz
        is_ubisoft=True
    )
    if len(ubi) > 10: final_data["Ubisoft+"] = ubi

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
