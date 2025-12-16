import streamlit as st
import requests
import xml.etree.ElementTree as ET
import math

# --- AYARLAR ---
st.set_page_config(page_title="Oyun Fiyat & Abonelik Takip", layout="wide")

# --- 1. MERKEZ BANKASI KUR ÇEKME ---
@st.cache_data(ttl=3600)  # Kuru 1 saat hafızada tutar, sürekli istek atmaz
def get_usd_try_rate():
    try:
        url = "https://www.tcmb.gov.tr/kurlar/today.xml"
        response = requests.get(url)
        root = ET.fromstring(response.content)
        for currency in root.findall('Currency'):
            if currency.get('Kod') == 'USD':
                forex_selling = currency.find('BanknoteSelling').text
                return float(forex_selling)
        return 34.00  # Bulamazsa varsayılan
    except:
        return 34.00  # Hata olursa varsayılan

# --- 2. OYUN VERİLERİ (Manuel Veritabanı) ---
def get_games_data():
    return [
        {
            "id": 1,
            "name": "Starfield",
            "price_usd": 69.99,
            "price_try_local": 0,
            "subscription": "Game Pass",
            "image": "https://upload.wikimedia.org/wikipedia/en/6/6d/Starfield_cover_art.jpg",
            "description": "Bethesda Game Studios'tan yıldızlararası bir RPG.",
            "sys_req": "SSD Zorunlu, RTX 2080 veya eşdeğeri, 16GB RAM",
            "is_new": True,
            "discount": 0
        },
        {
            "id": 2,
            "name": "EA Sports FC 24",
            "price_usd": 0,
            "price_try_local": 1200.00,
            "subscription": "EA Play",
            "image": "https://upload.wikimedia.org/wikipedia/en/b/b3/EA_Sports_FC_24_cover.jpg",
            "description": "Dünyanın en popüler futbol oyunu.",
            "sys_req": "GTX 1050 Ti, 8GB RAM, 50GB HDD",
            "is_new": False,
            "discount": 20
        },
        {
            "id": 3,
            "name": "Cyberpunk 2077",
            "price_usd": 59.99,
            "price_try_local": 0,
            "subscription": "Yok",
            "image": "https://upload.wikimedia.org/wikipedia/en/9/9f/Cyberpunk_2077_box_art.jpg",
            "description": "Gelecekte geçen açık dünya aksiyon oyunu.",
            "sys_req": "RTX 3060, 16GB RAM, SSD",
            "is_new": False,
            "discount": 50
        },
        {
            "id": 4,
            "name": "Assassin's Creed Mirage",
            "price_usd": 49.99,
            "price_try_local": 0,
            "subscription": "Ubisoft+",
            "image": "https://upload.wikimedia.org/wikipedia/en/8/86/Assassin%27s_Creed_Mirage_cover.jpg",
            "description": "Bağdat sokaklarında geçen suikastçilik deneyimi.",
            "sys_req": "GTX 1660, 16GB RAM",
            "is_new": True,
            "discount": 0
        },
        {
            "id": 5,
            "name": "Hollow Knight",
            "price_usd": 14.99,
            "price_try_local": 149.00,
            "subscription": "Game Pass",
            "image": "https://upload.wikimedia.org/wikipedia/en/0/04/Hollow_Knight_first_cover_art.webp",
            "description": "Zorlu ve atmosferik bir platform oyunu.",
            "sys_req": "4GB RAM, Standart Ekran Kartı",
            "is_new": False,
            "discount": 0
        },
        {
            "id": 6,
            "name": "Baldur's Gate 3",
            "price_usd": 59.99,
            "price_try_local": 0,
            "subscription": "Yok",
            "image": "https://upload.wikimedia.org/wikipedia/en/1/12/Baldur%27s_Gate_3_cover_art.jpg",
            "description": "D&D evreninde geçen, yılın oyunu ödüllü RPG.",
            "sys_req": "RTX 2060 Super, 16GB RAM, SSD",
            "is_new": False,
            "discount": 10
        },
        {
            "id": 7,
            "name": "Forza Horizon 5",
            "price_usd": 59.99,
            "price_try_local": 0,
            "subscription": "Game Pass",
            "image": "https://upload.wikimedia.org/wikipedia/en/8/86/Forza_Horizon_5_cover_art.jpg",
            "description": "Meksika'da geçen açık dünya yarış festivali.",
            "sys_req": "GTX 1070, 16GB RAM",
            "is_new": False,
            "discount": 0
        },
        {
            "id": 8,
            "name": "Red Dead Redemption 2",
            "price_usd": 59.99,
            "price_try_local": 0,
            "subscription": "Yok",
            "image": "https://upload.wikimedia.org/wikipedia/en/4/44/Red_Dead_Redemption_II.jpg",
            "description": "Vahşi batıda geçen epik bir hikaye.",
            "sys_req": "GTX 1060, 12GB RAM, 150GB HDD",
            "is_new": False,
            "discount": 60
        }
    ]

# --- 3. YARDIMCI HESAPLAMA ---
def calculate_price(game, usd_rate):
    if game['price_try_local'] > 0:
        base_price = game['price_try_local']
    else:
        base_price = game['price_usd'] * usd_rate
    
    final_price = base_price * (1 - game['discount'] / 100)
    return base_price, final_price

# --- 4. ARAYÜZ MANTIĞI ---

# Session State (Sayfa geçişleri için)
if 'selected_game' not in st.session_state:
    st.session_state.selected_game = None
if 'page_number' not in st.session_state:
    st.session_state.page_number = 1

usd_rate = get_usd_try_rate()

# Fonksiyonlar
def go_to_detail(game):
    st.session_state.selected_game = game

def go_to_home():
    st.session_state.selected_game = None

# --- EKRAN GÖSTERİMİ ---

# DETAY SAYFASI
if st.session_state.selected_game is not None:
    game = st.session_state.selected_game
    st.button("⬅️ Listeye Geri Dön", on_click=go_to_home)
    
    st.title(game['name'])
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.image(game['image'], use_container_width=True)
        base, final = calculate_price(game, usd_rate)
        st.markdown("### Fiyat")
        
        if game['discount'] > 0:
            st.write(f"~~{base:.2f} TL~~")
            st.success(f"🔥 {final:.2f} TL")
        else:
            st.info(f"💰 {final:.2f} TL")
            
        if game['subscription'] != "Yok":
            st.warning(f"Bu oyun **{game['subscription']}** sisteminde var!")
    
    with c2:
        st.subheader("Oyun Açıklaması")
        st.write(game['description'])
        st.divider()
        st.subheader("Sistem Gereksinimleri")
        st.code(game['sys_req'])
        st.divider()
        st.info(f"Dolar Kuru Hesabı: 1 USD = {usd_rate} TL üzerinden yapılmıştır.")

# ANA SAYFA
else:
    st.title("🎮 Oyun Fiyat & Abonelik Listesi")
    st.write(f"Güncel Dolar Kuru: **{usd_rate} TL**")
    
    # Filtreleme
    st.sidebar.header("Filtrele")
    subs_filter = st.sidebar.multiselect("Abonelik", ["Game Pass", "EA Play", "Ubisoft+", "Yok"], default=["Game Pass", "EA Play", "Ubisoft+", "Yok"])
    
    all_games = get_games_data()
    filtered_games = [g for g in all_games if g['subscription'] in subs_filter]
    
    # Sayfalama
    items_per_page = 4
    total_pages = math.ceil(len(filtered_games) / items_per_page)
    current_page = st.session_state.page_number
    
    start_idx = (current_page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    current_games = filtered_games[start_idx:end_idx]
    
    # Grid Yapısı
    cols = st.columns(2)
    for idx, game in enumerate(current_games):
        with cols[idx % 2]:
            with st.container(border=True):
                c_img, c_info = st.columns([1, 2])
                with c_img:
                    st.image(game['image'], use_container_width=True)
                with c_info:
                    st.subheader(game['name'])
                    if game['subscription'] != "Yok":
                        st.caption(f"✅ {game['subscription']}")
                    
                    base, final = calculate_price(game, usd_rate)
                    st.write(f"**{final:.0f} TL**")
                    st.button("İncele", key=f"btn_{game['id']}", on_click=go_to_detail, args=(game,))
    
    # Sayfa Butonları
    st.divider()
    page_cols = st.columns(total_pages + 2)
    for i in range(1, total_pages + 1):
        def set_page(p):
            st.session_state.page_number = p
        
        if i == current_page:
            page_cols[i].button(f"{i}", key=f"p{i}", disabled=True)
        else:
            page_cols[i].button(f"{i}", key=f"p{i}", on_click=set_page, args=(i,))
