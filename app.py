import streamlit as st
import requests
import xml.etree.ElementTree as ET
import math

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="GamePriceTR", layout="wide", page_icon="🎮")

# --- CSS İLE TASARIM İYİLEŞTİRME (OPSİYONEL ŞIKLIK) ---
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ff4b4b;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# --- 1. MERKEZ BANKASI KUR ÇEKME ---
@st.cache_data(ttl=3600)
def get_usd_try_rate():
    try:
        url = "https://www.tcmb.gov.tr/kurlar/today.xml"
        response = requests.get(url)
        root = ET.fromstring(response.content)
        for currency in root.findall('Currency'):
            if currency.get('Kod') == 'USD':
                forex_selling = currency.find('BanknoteSelling').text
                return float(forex_selling)
        return 34.00
    except:
        return 34.00

# --- 2. GELİŞMİŞ OYUN VERİTABANI ---
def get_games_data():
    return [
        {
            "id": 1, "name": "Starfield", "genre": "RPG", 
            "price_usd": 69.99, "price_try_local": 0, "subscription": "Game Pass",
            "image": "https://upload.wikimedia.org/wikipedia/en/6/6d/Starfield_cover_art.jpg",
            "description": "Bethesda'dan uzay temalı açık dünya RPG.",
            "sys_req": "SSD, RTX 2080, 16GB RAM", "is_new": True, "discount": 0
        },
        {
            "id": 2, "name": "EA Sports FC 24", "genre": "Spor",
            "price_usd": 0, "price_try_local": 1200.00, "subscription": "EA Play",
            "image": "https://upload.wikimedia.org/wikipedia/en/b/b3/EA_Sports_FC_24_cover.jpg",
            "description": "Futbol simülasyonu.",
            "sys_req": "GTX 1050 Ti, 8GB RAM", "is_new": False, "discount": 20
        },
        {
            "id": 3, "name": "Cyberpunk 2077", "genre": "Aksiyon/RPG",
            "price_usd": 59.99, "price_try_local": 0, "subscription": "Yok",
            "image": "https://upload.wikimedia.org/wikipedia/en/9/9f/Cyberpunk_2077_box_art.jpg",
            "description": "Distopik gelecek temalı açık dünya.",
            "sys_req": "RTX 3060, 16GB RAM", "is_new": False, "discount": 50
        },
        {
            "id": 4, "name": "Assassin's Creed Mirage", "genre": "Aksiyon",
            "price_usd": 49.99, "price_try_local": 0, "subscription": "Ubisoft+",
            "image": "https://upload.wikimedia.org/wikipedia/en/8/86/Assassin%27s_Creed_Mirage_cover.jpg",
            "description": "Gizlilik odaklı suikastçi oyunu.",
            "sys_req": "GTX 1660, 16GB RAM", "is_new": True, "discount": 0
        },
        {
            "id": 5, "name": "Hollow Knight", "genre": "Platform",
            "price_usd": 14.99, "price_try_local": 149.00, "subscription": "Game Pass",
            "image": "https://upload.wikimedia.org/wikipedia/en/0/04/Hollow_Knight_first_cover_art.webp",
            "description": "Metroidvania türünün en iyisi.",
            "sys_req": "Düşük Sistem Dostu", "is_new": False, "discount": 0
        },
        {
            "id": 6, "name": "Baldur's Gate 3", "genre": "RPG",
            "price_usd": 59.99, "price_try_local": 0, "subscription": "Yok",
            "image": "https://upload.wikimedia.org/wikipedia/en/1/12/Baldur%27s_Gate_3_cover_art.jpg",
            "description": "Sıra tabanlı strateji ve rol yapma.",
            "sys_req": "RTX 2060, 16GB RAM", "is_new": False, "discount": 10
        },
        {
            "id": 7, "name": "Call of Duty: MW3", "genre": "FPS",
            "price_usd": 69.99, "price_try_local": 0, "subscription": "Game Pass",
            "image": "https://upload.wikimedia.org/wikipedia/en/thumb/f/f3/Call_of_Duty_Modern_Warfare_III_%282023%29_cover_art.jpg/220px-Call_of_Duty_Modern_Warfare_III_%282023%29_cover_art.jpg",
            "description": "Hızlı tempolu savaş oyunu.",
            "sys_req": "GTX 1080, 16GB RAM", "is_new": True, "discount": 0
        },
        {
            "id": 8, "name": "GTA V", "genre": "Aksiyon",
            "price_usd": 29.99, "price_try_local": 0, "subscription": "Yok",
            "image": "https://upload.wikimedia.org/wikipedia/en/a/a5/Grand_Theft_Auto_V.png",
            "description": "Los Santos'ta suç dünyası.",
            "sys_req": "GTX 970, 8GB RAM", "is_new": False, "discount": 0
        }
    ]

# --- 3. HESAPLAMA ---
def calculate_price(game, usd_rate):
    if game['price_try_local'] > 0:
        base_price = game['price_try_local']
    else:
        base_price = game['price_usd'] * usd_rate
    
    final_price = base_price * (1 - game['discount'] / 100)
    return base_price, final_price

# --- 4. UYGULAMA MANTIĞI ---

# Session State
if 'selected_game' not in st.session_state:
    st.session_state.selected_game = None
if 'page_number' not in st.session_state:
    st.session_state.page_number = 1

usd_rate = get_usd_try_rate()

def go_to_detail(game):
    st.session_state.selected_game = game

def go_to_home():
    st.session_state.selected_game = None

# --- EKRAN GÖSTERİMİ ---

# DETAY SAYFASI
if st.session_state.selected_game is not None:
    game = st.session_state.selected_game
    
    # Geri Dön Butonu (Üstte şık durması için kolonla ayırdık)
    col_back, col_empty = st.columns([1, 5])
    with col_back:
        st.button("⬅️ Geri Dön", on_click=go_to_home, use_container_width=True)
    
    st.title(f"{game['name']}")
    st.caption(f"Tür: {game['genre']}")
    
    col_main_img, col_details = st.columns([2, 3])
    
    with col_main_img:
        st.image(game['image'], use_container_width=True)
        
        # Fiyat Kartı
        st.markdown("---")
        base, final = calculate_price(game, usd_rate)
        
        st.write("### Fiyat Analizi")
        if game['price_usd'] > 0:
            st.caption(f"Global Fiyat: ${game['price_usd']}")
            
        if game['discount'] > 0:
            st.markdown(f"#### ❌ ~~{base:.2f} TL~~")
            st.success(f"## 🔥 {final:.2f} TL")
            st.caption(f"%{game['discount']} İndirim Fırsatı!")
        else:
            st.markdown(f"## 💰 {final:.2f} TL")
            
        if game['subscription'] != "Yok":
            st.info(f"💡 İpucu: Bu oyuna **{game['subscription']}** aboneliği ile erişebilirsin!")

    with col_details:
        st.subheader("📝 Oyun Hakkında")
        st.write(game['description'])
        
        st.subheader("⚙️ Sistem Gereksinimleri")
        st.code(game['sys_req'], language='text')
        
        st.subheader("📺 Tanıtım Videosu")
        st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ") # Örnek video

# ANA SAYFA (LİSTELEME)
else:
    # Üst Başlık ve Kur Bilgisi
    c1, c2 = st.columns([3, 1])
    with c1:
        st.title("🎮 GamePrice TR")
    with c2:
        st.metric(label="Dolar Kuru", value=f"{usd_rate:.2f} TL")

    # --- ARAMA BÖLÜMÜ ---
    search_query = st.text_input("🔍 Oyun Ara", placeholder="Oyun adı yazın... (Örn: Starfield, FIFA)", help="Oyun adını yazıp Enter'a basın.")
    
    # --- KATEGORİ SEKMELERİ (FİLTRELEME) ---
    tab_all, tab_discount, tab_new, tab_subs = st.tabs(["📋 Tümü", "🔥 İndirimdekiler", "🆕 Yeni Çıkanlar", "💳 Abonelikler"])
    
    # Verileri Çek
    all_games = get_games_data()
    
    # Arama Filtresi (Her sekme için geçerli)
    if search_query:
        all_games = [g for g in all_games if search_query.lower() in g['name'].lower()]

    # Sidebar Filtreleri (Ekstra Filtreler)
    with st.sidebar:
        st.header("Filtreler")
        selected_genres = st.multiselect("Oyun Türü", ["RPG", "Spor", "Aksiyon", "FPS", "Platform"], default=[])
        
    # Tür Filtresi Uygulama
    if selected_genres:
        all_games = [g for g in all_games if g['genre'] in selected_genres]

    # --- OYUNLARI LİSTELEME FONKSİYONU ---
    def show_games_grid(games_list):
        if not games_list:
            st.warning("Aradığınız kriterlere uygun oyun bulunamadı.")
            return

        # Sayfalama
        items_per_page = 4
        total_pages = math.ceil(len(games_list) / items_per_page)
        
        # Sayfa numarası sınır kontrolü
        if st.session_state.page_number > total_pages:
            st.session_state.page_number = 1
            
        current_page = st.session_state.page_number
        start_idx = (current_page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        
        current_view_games = games_list[start_idx:end_idx]
        
        # Grid Yapısı (2 sütunlu)
        cols = st.columns(2)
        for idx, game in enumerate(current_view_games):
            with cols[idx % 2]:
                with st.container(border=True):
                    c_img, c_text = st.columns([1, 2])
                    with c_img:
                        st.image(game['image'], use_container_width=True)
                    with c_text:
                        st.subheader(game['name'])
                        st.caption(f"Tür: {game['genre']}")
                        
                        base, final = calculate_price(game, usd_rate)
                        
                        if game['discount'] > 0:
                            st.write(f"**{final:.0f} TL** _(%{game['discount']} İnd.)_")
                        else:
                            st.write(f"**{final:.0f} TL**")
                        
                        if game['subscription'] != "Yok":
                            st.markdown(f"✅ `{game['subscription']}`")
                        
                        st.button("İncele", key=f"list_btn_{game['id']}", on_click=go_to_detail, args=(game,))
        
        # Sayfa Butonları
        if total_pages > 1:
            st.markdown("---")
            pagination_cols = st.columns(total_pages + 4)
            for p in range(1, total_pages + 1):
                def set_page(page_num):
                    st.session_state.page_number = page_num
                
                if p == current_page:
                    pagination_cols[p].button(f"{p}", key=f"pg_{p}", disabled=True)
                else:
                    pagination_cols[p].button(f"{p}", key=f"pg_{p}", on_click=set_page, args=(p,))

    # --- SEKMELERİN İÇERİĞİ ---
    with tab_all:
        show_games_grid(all_games)
        
    with tab_discount:
        discounted_games = [g for g in all_games if g['discount'] > 0]
        show_games_grid(discounted_games)
        
    with tab_new:
        new_games = [g for g in all_games if g['is_new'] == True]
        show_games_grid(new_games)
        
    with tab_subs:
        sub_games = [g for g in all_games if g['subscription'] != "Yok"]
        show_games_grid(sub_games)
