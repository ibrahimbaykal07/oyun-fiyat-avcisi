import streamlit as st
import pandas as pd
import requests

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="Steam TR Fiyat Analiz",
    page_icon="🎮",
    layout="wide"
)

# --- BAŞLIK VE STİL ---
st.title("🎮 Steam Türkiye (MENA) Anlık Fiyat Analizi")
st.markdown("""
Bu site **Steam Türkiye** mağazasındaki (MENA-USD) indirimleri anlık olarak çeker 
ve güncel kur üzerinden **TL karşılığını** hesaplar. 
*Ayrıca Epic Games fiyatlarını kontrol etmeniz için kısayol sunar.*
""")
st.divider()

# --- FONKSİYONLAR (Önbellekli) ---

@st.cache_data(ttl=3600) # Kuru 1 saat hafızada tut
def get_usd_rate():
    """Güncel Dolar kurunu çeker."""
    try:
        url = "https://open.er-api.com/v6/latest/USD"
        response = requests.get(url, timeout=5)
        data = response.json()
        return data["rates"]["TRY"]
    except:
        return 35.0 # Hata olursa varsayılan güvenli kur

@st.cache_data(ttl=1800) # Oyunları 30 dakika hafızada tut
def get_steam_data():
    """Steam'in öne çıkan indirimlerini çeker."""
    # cc=tr: Türkiye bölgesi
    # l=turkish: Türkçe dil
    url = "https://store.steampowered.com/api/featuredcategories?cc=tr&l=turkish"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        # Steam API'den gelen karmaşık veriyi düzeltiyoruz
        games_list = []
        
        # 'Specials' (Özel İndirimler) ve 'Top Sellers' (Çok Satanlar) bölümlerini tarayalım
        categories_to_check = ['specials', 'top_sellers', 'new_releases']
        
        processed_ids = set() # Aynı oyunu iki kere eklememek için
        
        for category in categories_to_check:
            if category in data:
                items = data[category].get('items', [])
                for game in items:
                    game_id = game.get('id')
                    
                    # Eğer oyun daha önce listeye eklenmediyse ve fiyat bilgisi varsa
                    if game_id not in processed_ids and 'final_price' in game:
                        
                        # Steam fiyatı 0 ise (Ücretsiz oyun) atla veya ekle
                        if game['final_price'] == 0:
                            continue

                        processed_ids.add(game_id)
                        
                        # Fiyatlar 'cent' cinsinden gelir (1000 = 10.00$)
                        price_usd = game['final_price'] / 100
                        original_usd = game.get('original_price', game['final_price']) / 100
                        discount = game.get('discount_percent', 0)
                        
                        games_list.append({
                            "title": game['name'],
                            "image": game['large_capsule_image'],
                            "price_usd": price_usd,
                            "original_usd": original_usd,
                            "discount": discount,
                            "steam_url": f"https://store.steampowered.com/app/{game_id}",
                            "epic_url": f"https://store.epicgames.com/tr/browse?q={game['name'].replace(' ', '%20')}&sortBy=price&sortDir=ASC"
                        })
        
        return games_list
    except Exception as e:
        st.error(f"Veri çekme hatası: {e}")
        return []

# --- ANA AKIŞ ---

# 1. Verileri Hazırla
usd_rate = get_usd_rate()
st.info(f"💵 **Referans Dolar Kuru:** {usd_rate:.2f} TL (Anlık Kur)")

with st.spinner('Steam sunucularından veriler alınıyor...'):
    games = get_steam_data()

# 2. Ekrana Bas
if games:
    # Mobilde tek, bilgisayarda 4 sütun olsun
    cols = st.columns([1, 1, 1, 1])
    
    for i, game in enumerate(games):
        col = cols[i % 4]
        
        with col:
            # TL Hesaplama
            price_tl = game['price_usd'] * usd_rate
            original_tl = game['original_usd'] * usd_rate
            
            # Görsel
            st.image(game['image'], use_container_width=True)
            
            # Başlık (Çok uzunsa kısalt)
            title = game['title']
            if len(title) > 25:
                title = title[:22] + "..."
            st.write(f"**{title}**")
            
            # Fiyat Bilgisi
            if game['discount'] > 0:
                st.markdown(f"""
                <span style='color:#d9534f; font-weight:bold'>%{game['discount']} İndirim</span><br>
                <span style='text-decoration: line-through; color:gray'>{original_tl:.0f} ₺</span> -> 
                <span style='color:#5cb85c; font-size:1.2em; font-weight:bold'>{price_tl:.0f} ₺</span>
                <br><span style='font-size:0.8em; color:gray'>({game['price_usd']}$)</span>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <span style='color:#5cb85c; font-size:1.2em; font-weight:bold'>{price_tl:.0f} ₺</span>
                <br><span style='font-size:0.8em; color:gray'>({game['price_usd']}$)</span>
                """, unsafe_allow_html=True)
            
            # Butonlar
            st.link_button("Steam", game['steam_url'])
            st.link_button("Epic Games'te Ara", game['epic_url'])
            
            st.divider()

else:
    st.warning("Steam bağlantısında geçici bir sorun var veya şu an öne çıkan indirim yok.")
