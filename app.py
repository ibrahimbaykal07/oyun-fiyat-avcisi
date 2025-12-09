import streamlit as st
import requests
import streamlit.components.v1 as components
import math
import re
import xml.etree.ElementTree as ET

# --- 1. AYARLAR ---
st.set_page_config(page_title="Oyun Fiyatı (TR)", page_icon="🇹🇷", layout="centered")
PAGE_SIZE = 12
PLACEHOLDER_IMG = "https://placehold.co/600x900/1a1a1a/FFFFFF/png?text=Gorsel+Yok"
RAWG_API_KEY = "3f8159cbaaac426bac87a770371c941f"

# --- 2. CSS STİLİ (DİKEY GÖRSEL & DÜZEN) ---
st.markdown("""
<style>
    .block-container { padding-top: 1rem; }
    
    /* GÖRSELLERİ DİK (POSTER) ZORLA */
    div[data-testid="stImage"] img { 
        border-radius: 8px; 
        width: 100%; 
        aspect-ratio: 2/3; 
        object-fit: cover; 
    }
    
    .game-title { 
        font-size: 0.9em; 
        font-weight: bold; 
        margin-top: 8px; 
        white-space: nowrap; 
        overflow: hidden; 
        text-overflow: ellipsis; 
        color: #333; 
        text-align: center;
    }
    
    .price-container {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 8px;
        margin: 5px 0;
    }
    
    .game-price { 
        font-size: 1.1em; 
        font-weight: bold; 
        color: #28a745; 
    }
    
    .discount-tag {
        background-color: #dc3545;
        color: white;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.8em;
        font-weight: bold;
    }
    
    .cat-header {
        font-size: 1.5em;
        font-weight: bold;
        margin-top: 20px;
        margin-bottom: 15px;
        border-bottom: 2px solid #eee;
        padding-bottom: 5px;
    }
    
    .kur-kutusu {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
        color: #555;
        margin-bottom: 10px;
        border: 1px solid #ddd;
    }
    
    .stButton button { width: 100%; border-radius: 5px; }
    div[data-testid="column"] button { min-width: 40px; }
</style>
""", unsafe_allow_html=True)

# --- 3. MANUEL LİSTE ---
SUBSCRIPTIONS = {
    "Game Pass": [
        "Call of Duty: Black Ops 6", "Call of Duty: Modern Warfare III", "Diablo IV", "Starfield", 
        "Forza Motorsport", "Forza Horizon 5", "Halo Infinite", "Microsoft Flight Simulator 2024", 
        "Senua's Saga: Hellblade II", "S.T.A.L.K.E.R. 2: Heart of Chornobyl", "Indiana Jones and the Great Circle", 
        "Avowed", "Persona 3 Reload", "Like a Dragon: Infinite Wealth", "Palworld", "Lies of P", "Cocoon", 
        "Hi-Fi RUSH", "Atomic Heart", "Wo Long: Fallen Dynasty", "A Plague Tale: Requiem", "Scorn", "Grounded", 
        "Deathloop", "Ghostwire: Tokyo", "Minecraft", "Sea of Thieves", "Gears 5", "Doom Eternal", 
        "Age of Empires IV", "Back 4 Blood", "Sniper Elite 5", "Monster Hunter Rise", "Assassin's Creed Valhalla", 
        "Far Cry 6", "Watch Dogs 2", "Tom Clancy's Rainbow Six Siege", "FIFA 23", "Battlefield 2042", 
        "Mass Effect Legendary Edition", "It Takes Two", "Need for Speed Unbound", "Star Wars Jedi: Fallen Order", 
        "Titanfall 2", "The Sims 4", "Cities: Skylines II", "Football Manager 2024", "Payday 3", 
        "Warhammer 40,000: Darktide", "Remnant 2", "Hollow Knight", "Stardew Valley", "Vampire Survivors", 
        "Valheim", "Among Us", "No Man's Sky", "Fallout 4", "The Elder Scrolls V: Skyrim Special Edition"
    ],
    "EA Play Pro": [
        "EA SPORTS FC 25", "EA SPORTS FC 26", "Madden NFL 25", "F1 24", "Star Wars Jedi: Survivor", 
        "Immortals of Aveum", "Wild Hearts", "Dead Space (2023)", "PGA Tour", "WRC 23", 
        "It Takes Two", "Mass Effect Legendary Edition", "Need for Speed Unbound", "Battlefield 2042"
    ],
    "EA Play": [
        "EA SPORTS FC 24", "FIFA 23", "F1 23", "Madden NFL 24", "Battlefield 2042", "Battlefield V", 
        "Star Wars Jedi: Fallen Order", "Star Wars Battlefront II", "Mass Effect Legendary Edition", 
        "Titanfall 2", "The Sims 4", "Need for Speed Heat", "It Takes Two", "A Way Out", "Unravel Two", 
        "Dragon Age: Inquisition", "Crysis Remastered", "Dead Space 3", "Skate 3", "Mirror's Edge Catalyst"
    ],
    "Ubisoft+": [
        "Assassin's Creed Shadows", "Star Wars Outlaws", "Avatar: Frontiers of Pandora", "Prince of Persia: The Lost Crown", 
        "Assassin's Creed Mirage", "The Crew Motorfest", "Skull and Bones", "Assassin's Creed Valhalla", "Far Cry 6", 
        "Tom Clancy's Rainbow Six Siege", "Tom Clancy's The Division 2", "Tom Clancy's Ghost Recon Breakpoint", 
        "Watch Dogs: Legion", "Immortals Fenyx Rising", "Riders Republic", "Anno 1800", "For Honor", "The Crew 2"
    ]
}

# --- 4. SESSION STATE ---
if 'active_page' not in st.session_state: st.session_state.active_page = 'home'
if 'page_number' not in st.session_state: st.session_state.page_number = 0
if 'selected_cat' not in st.session_state: st.session_state.selected_cat = "Popular"
if 'selected_game' not in st.session_state: st.session_state.selected_game = None
if 'search_term' not in st.session_state: st.session_state.search_term = ""

# --- 5. FONKSİYONLAR ---
def scroll_to_top():
    components.html("""<script>window.parent.document.querySelector('.main').scrollTop = 0;</script>""", height=0)

def set_page(page_name):
    st.session_state.active_page = page_name
    st.session_state.page_number = 0
    scroll_to_top()
    st.rerun()

def go_category(cat_key, is_sub=False):
    st.session_state.selected_cat = cat_key
    st.session_state.active_page = 'category'
    st.session_state.page_number = 0
    scroll_to_top()
    st.rerun()

def go_detail(game):
    st.session_state.selected_game = game
    st.session_state.active_page = 'detail'
    scroll_to_top()
    st.rerun()

# --- TCMB KUR ÇEKME ---
@st.cache_data(ttl=3600)
def get_dollar_rate():
    """Merkez Bankası'ndan Dolar Kuru"""
    try:
        r = requests.get("https://www.tcmb.gov.tr/kurlar/today.xml", timeout=3)
        if r.status_code == 200:
            root = ET.fromstring(r.content)
            for c in root.findall('Currency'):
                if c.get('Kod') == 'USD':
                    return float(c.find('ForexSelling').text)
    except: pass
    return 38.50 # Yedek (Eğer TCMB açılmazsa)

# --- VERİ MOTORU ---
@st.cache_data(ttl=3600)
def fetch_steam_data(game_name):
    """Steam'den Resim ve AppID çeker"""
    clean_name = re.sub(r'\(.*?\)', '', game_name).replace(':', '').replace('.', '').strip()
    
    if "fc 26" in clean_name.lower():
        return {"thumb": "https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/2195250/library_600x900.jpg", "appid": "0"}

    try:
        url = f"https://store.steampowered.com/api/storesearch/?term={clean_name}&l=turkish&cc=tr"
        r = requests.get(url, timeout=2)
        if r.status_code == 200:
            data = r.json()
            if data['total'] > 0:
                item = data['items'][0]
                appid = item['id']
                thumb = f"https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/{appid}/library_600x900.jpg"
                return {"thumb": thumb, "appid": appid, "title": item['name']}
    except: pass
    return None

def get_game_details(game_name, sub_name="", dolar_kuru=38.0):
    """Manuel liste için detay ve FİYAT ÇEVİRİSİ"""
    data = {
        "title": game_name,
        "thumb": PLACEHOLDER_IMG,
        "price": "---",
        "store": sub_name,
        "appid": "0",
        "discount": 0
    }
    
    # Resim ve ID için Steam
    steam_res = fetch_steam_data(game_name)
    if steam_res:
        data['title'] = steam_res['title']
        data['thumb'] = steam_res['thumb']
        data['appid'] = steam_res['appid']
    
    # Fiyat için CheapShark (Dolar -> TL)
    try:
        url = f"https://www.cheapshark.com/api/1.0/deals?title={game_name.split(':')[0]}&exact=0&limit=1"
        r = requests.get(url, timeout=2).json()
        if r:
            deal = r[0]
            usd_price = float(deal['salePrice'])
            tl_price = int(usd_price * dolar_kuru)
            data['price'] = f"{tl_price} TL"
            data['discount'] = float(deal['savings'])
    except: pass

    return data

@st.cache_data(ttl=3600)
def fetch_dynamic_deals(category, dolar_kuru):
    """Vitrin için CheapShark Verisi (TL ÇEVRİLMİŞ)"""
    sort_map = {"Popular": "Metacritic", "Sale": "Savings", "New": "Release"}
    sort_type = sort_map.get(category, "Metacritic")
    
    try:
        url = f"https://www.cheapshark.com/api/1.0/deals?storeID=1&sortBy={sort_type}&pageSize=12&pageNumber=0"
        if category == "New": url += "&desc=1"
        if category == "Popular": url += "&metacritic=75"
        
        data = requests.get(url, timeout=3).json()
        results = []
        
        for d in data:
            s_data = fetch_steam_data(d['title'])
            
            final_title = d['title']
            final_thumb = d.get('thumb', PLACEHOLDER_IMG)
            final_appid = d.get('steamAppID', '0')
            
            # Resim Düzeltme
            if s_data:
                final_title = s_data['title']
                final_thumb = s_data['thumb']
                final_appid = s_data['appid']
            
            # FİYAT ÇEVİRİSİ (USD -> TL)
            price_usd = float(d['salePrice'])
            price_tl = int(price_usd * dolar_kuru)
            
            results.append({
                "title": final_title,
                "thumb": final_thumb,
                "price": f"{price_tl} TL",
                "appid": final_appid,
                "discount": float(d['savings']),
                "store": "Steam Store"
            })
        return results
    except: return []

# ================= ARAYÜZ =================
scroll_to_top()
kur = get_dollar_rate()

# 1. ÜST NAVİGASYON
c1, c2 = st.columns([1, 4])
with c1:
    if st.button("🏠 Ana Sayfa"): set_page('home')
with c2:
    # 3'lü Vitrin Butonları
    c_vitrin = st.columns(3)
    if c_vitrin[0].button("🏆 Popüler"): go_category("Popular")
    if c_vitrin[1].button("🔥 İndirim"): go_category("Sale")
    if c_vitrin[2].button("✨ Yeni"): go_category("New")
    
    st.write("") 
    
    # 4'lü Abonelik Butonları
    c_sub = st.columns(4)
    if c_sub[0].button("Game Pass"): go_category("Game Pass", True)
    if c_sub[1].button("EA Play"): go_category("EA Play", True)
    if c_sub[2].button("EA Pro"): go_category("EA Play Pro", True)
    if c_sub[3].button("Ubisoft+"): go_category("Ubisoft+", True)

# Kur Bilgisi
st.markdown(f"<div class='kur-kutusu'>💲 Güncel Kur: 1 USD = {kur:.2f} TL</div>", unsafe_allow_html=True)
st.divider()

# 2. ARAMA
with st.form("search_form"):
    c1, c2 = st.columns([5, 1])
    query = c1.text_input("Oyun Ara", placeholder="Oyun adı...", label_visibility="collapsed")
    if c2.form_submit_button("Ara") and query:
        st.session_state.search_term = query
        set_page('search')

# --- SAYFA: ANA SAYFA ---
if st.session_state.active_page == 'home':
    
    # 1. POPÜLER
    st.markdown("<div class='cat-header'>🏆 En Popüler Başyapıtlar</div>", unsafe_allow_html=True)
    pop_games = fetch_dynamic_deals("Popular", kur)
    if pop_games:
        cols = st.columns(4)
        for i, g in enumerate(pop_games[:4]):
            with cols[i]:
                st.image(g['thumb'])
                st.markdown(f"<div class='game-title'>{g['title']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='price-container'><span class='game-price'>{g['price']}</span></div>", unsafe_allow_html=True)
                if st.button("İncele", key=f"home_pop_{i}"): go_detail(g)

    # 2. İNDİRİM
    st.markdown("<div class='cat-header'>🔥 Süper İndirimler</div>", unsafe_allow_html=True)
    sale_games = fetch_dynamic_deals("Sale", kur)
    if sale_games:
        cols = st.columns(4)
        for i, g in enumerate(sale_games[:4]):
            with cols[i]:
                st.image(g['thumb'])
                st.markdown(f"<div class='game-title'>{g['title']}</div>", unsafe_allow_html=True)
                disc_html = f"<span class='discount-tag'>-%{int(g['discount'])}</span>"
                st.markdown(f"<div class='price-container'><span class='game-price'>{g['price']}</span>{disc_html}</div>", unsafe_allow_html=True)
                if st.button("İncele", key=f"home_sale_{i}"): go_detail(g)

    # 3. YENİ
    st.markdown("<div class='cat-header'>✨ Yeni Çıkanlar</div>", unsafe_allow_html=True)
    new_games = fetch_dynamic_deals("New", kur)
    if new_games:
        cols = st.columns(4)
        for i, g in enumerate(new_games[:4]):
            with cols[i]:
                st.image(g['thumb'])
                st.markdown(f"<div class='game-title'>{g['title']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='price-container'><span class='game-price'>{g['price']}</span></div>", unsafe_allow_html=True)
                if st.button("İncele", key=f"home_new_{i}"): go_detail(g)

# --- SAYFA: KATEGORİ ---
elif st.session_state.active_page == 'category':
    cat_name = st.session_state.selected_cat
    is_sub = cat_name in SUBSCRIPTIONS
    st.markdown(f"<div class='cat-header'>{cat_name} Listesi</div>", unsafe_allow_html=True)
    
    curr_page = st.session_state.page_number
    
    if is_sub:
        full_list = SUBSCRIPTIONS.get(cat_name, [])
        total_games = len(full_list)
        total_pages = math.ceil(total_games / PAGE_SIZE)
        start_idx = curr_page * PAGE_SIZE
        end_idx = start_idx + PAGE_SIZE
        
        current_batch_names = full_list[start_idx:end_idx]
        current_batch = [get_game_details(name, cat_name, kur) for name in current_batch_names]
    else:
        # Dinamik Liste (Zaten 12 tane çekiyoruz)
        current_batch = fetch_dynamic_deals(cat_name, kur)
        total_pages = 1 
    
    if not current_batch:
        st.info("Bu kategoride oyun bulunamadı.")
    else:
        # 4'lü Grid
        for i in range(0, len(current_batch), 4):
            cols = st.columns(4)
            for j in range(4):
                if i+j < len(current_batch):
                    g = current_batch[i+j]
                    with cols[j]:
                        st.image(g['thumb'])
                        st.markdown(f"<div class='game-title'>{g['title']}</div>", unsafe_allow_html=True)
                        
                        disc_val = g.get('discount', 0)
                        disc_html = f"<span class='discount-tag'>-%{int(disc_val)}</span>" if disc_val > 0 else ""
                        st.markdown(f"<div class='price-container'><span class='game-price'>{g['price']}</span>{disc_html}</div>", unsafe_allow_html=True)
                        
                        if st.button("İncele", key=f"cat_btn_{curr_page}_{i}_{j}"): go_detail(g)
            st.write("")

        # Sayfalama
        if total_pages > 1:
            st.markdown("---")
            p_cols = st.columns(min(total_pages, 10))
            for p in range(min(total_pages, 10)):
                btn_type = "primary" if p == curr_page else "secondary"
                if p_cols[p].button(str(p+1), key=f"page_btn_{p}", type=btn_type):
                    st.session_state.page_number = p
                    st.rerun()

# --- SAYFA: DETAY ---
elif st.session_state.active_page == 'detail':
    g = st.session_state.selected_game
    
    desc = "Açıklama bulunamadı."
    if g['appid'] != "0":
        try:
            url = f"http://store.steampowered.com/api/appdetails?appids={g['appid']}&cc=tr&l=turkish"
            data = requests.get(url, timeout=2).json()
            if str(g['appid']) in data and data[str(g['appid'])]['success']:
                desc = data[str(g['appid'])]['data']['short_description']
        except: pass

    c1, c2 = st.columns([1.5, 2.5])
    with c1:
        st.image(g['thumb'])
        st.info(f"Kaynak: **{g['store']}**")
    
    with c2:
        st.markdown(f"<h1 style='margin-top:0;'>{g['title']}</h1>", unsafe_allow_html=True)
        st.markdown(desc, unsafe_allow_html=True)
        st.write("")
        st.subheader("Market Fiyatı")
        
        disc_val = g.get('discount', 0)
        disc_str = f" (-%{int(disc_val)})" if disc_val > 0 else ""
        
        st.markdown(f"<div class='game-price' style='font-size:2em; text-align:left;'>{g['price']}{disc_str}</div>", unsafe_allow_html=True)
        if g['appid'] != "0":
            st.link_button("Steam Mağazasına Git", f"https://store.steampowered.com/app/{g['appid']}")

# --- SAYFA: ARAMA ---
elif st.session_state.active_page == 'search':
    term = st.session_state.search_term
    st.info(f"🔎 '{term}' aranıyor...")
    
    res = get_game_details(term, "Arama Sonucu", kur)
    
    if res['appid'] != "0" or res['price'] != "---":
        with st.container():
            c1, c2 = st.columns([1, 3])
            with c1: st.image(res['thumb'])
            with c2:
                st.subheader(res['title'])
                st.markdown(f"<div class='game-price' style='text-align:left;'>{res['price']}</div>", unsafe_allow_html=True)
                if st.button("İncele", key="search_res_btn"): go_detail(res)
    else:
        st.warning("Oyun bulunamadı.")
