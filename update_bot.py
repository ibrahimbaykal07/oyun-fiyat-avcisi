import json
import requests

# Bu fonksiyonlar internetten güncel listeyi çeker.
# Şimdilik örnek olarak manuel listeyi buraya koyuyoruz.
# İleride buraya 'BeautifulSoup' ile site kazıma kodları eklenebilir.

def fetch_data():
    print("🤖 Robot çalıştı! Veriler toplanıyor...")
    
    # ÖRNEK: Gerçek hayatta burası xbox.com'a gidip veri çeker.
    # Biz şimdilik veritabanını kodla güncelliyoruz.
    yeni_veriler = {
        "Game Pass": [
            "call of duty", "black ops 6", "diablo 4", "starfield", "forza", "halo", "minecraft", 
            "lies of p", "palworld", "hellblade", "stalker 2", "indiana jones", "sea of thieves", 
            "doom", "gears 5", "atomic heart", "persona 3", "yakuza", "wo long", "hollow knight"
        ],
        "EA Play Pro": [
            "fc 26", "fc 25", "f1 24", "madden nfl 25", "star wars jedi: survivor", 
            "immortals of aveum", "wild hearts", "dead space remake"
        ],
        "EA Play": [
            "fc 24", "fifa 23", "battlefield 2042", "battlefield v", "battlefield 1", 
            "star wars jedi: fallen order", "sims 4", "titanfall 2", "mass effect legendary", 
            "it takes two", "need for speed unbound", "dead space", "crysis", "apex legends", "skate"
        ],
        "Ubisoft+": [
            "assassin's creed mirage", "assassin's creed valhalla", "shadows", "avatar", "far cry 6", 
            "prince of persia", "the crew motorfest", "rainbow six siege", "skull and bones", 
            "watch dogs legion", "division 2", "ghost recon breakpoint", "anno 1800", "riders republic"
        ]
    }
    
    return yeni_veriler

def save_to_json(data):
    with open('subscriptions.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print("✅ subscriptions.json başarıyla güncellendi!")

if __name__ == "__main__":
    data = fetch_data()
    save_to_json(data)
  
