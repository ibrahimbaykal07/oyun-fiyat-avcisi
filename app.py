import streamlit as st
import requests
import streamlit.components.v1 as components
import math
import re

# --- 1. AYARLAR ---
st.set_page_config(page_title="Oyun Fiyatı (TR)", page_icon="🇹🇷", layout="centered")
PAGE_SIZE = 12
PLACEHOLDER_IMG = "https://placehold.co/600x900/1a1a1a/FFFFFF/png?text=Gorsel+Yok"

# --- 2. CSS STİLİ (DİKEY GÖRSEL & DÜZEN) ---
st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    
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
    
    .game-price { 
        font-size: 1.1em; 
        font-weight: bold; 
        color: #28a745; 
        margin: 2px 0; 
        text-align: center;
    }

    .cat-header {
        font-size: 1.5em;
        font-weight: bold;
        margin-top: 30px;
        margin-bottom: 15px;
        border-bottom: 2px solid #eee;
        padding-bottom: 5px;
    }
    
    .stButton button { width: 100%; border-radius: 5px; }
    div[data-testid="column"] button { min-width: 40px; }
</style>
""", unsafe_allow_html=True)

# --- 3. MANUEL ABONELİK LİSTELERİ ---
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
if 'selected_cat' not in st.session_state: st.session_state.selected_cat = "Game Pass"
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

def go_detail(game):
    st.session_state.selected_game = game
    st.session_state.active_page = 'detail'
    scroll_to_top()
    st.rerun()

# --- VERİ MOTORU (STEAM TR - DİKEY & ORİJİNAL FİYAT) ---
@st.cache_data(ttl=3600)
def fetch_steam_data(game_name):
    """Steam TR'den Veri Çeker"""
    clean_name = re.sub(r'\(.*?\)', '', game_name).replace(':', '').replace('.', '').strip()
    
    # FC 26 Manuel
    if "fc 26" in clean_name.lower():
        return {"price": "Henüz Çıkmadı", "thumb": "https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/2195250/library_600x900.jpg", "appid": "0"}

    try:
        url = f"https://store.steampowered.com/api/storesearch/?term={clean_name}&l=turkish&cc=tr"
        r = requests.get(url, timeout=2)
        if r.status_code == 200:
            data = r.json()
            if data['total'] > 0:
                item = data['items'][0]
                appid = item['id']
                thumb = f"https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/{appid}/library_600x900.jpg"
                
                price_text = "Ücretsiz"
                if 'price' in item:
                    val = item['price']['final'] / 100
                    # Steam API para birimi sembolü vermez, varsayılan $ ekliyoruz (TR artık USD)
                    # Ancak eski oyunlar TL olabilir, API sadece rakam verir.
                    # Basitlik için $ varsayıyoruz.
                    price_text = f"${val:.2f}"
                
                return {"price": price_text, "thumb": thumb, "appid": appid, "title": item['name']}
    except: pass
    return None

def get_game_details(game_name, sub_name=""):
    """Manuel liste için detay hazırlayıcı"""
    data = {
        "title": game_name,
        "thumb": PLACEHOLDER_IMG,
        "price": "---",
        "store": sub_name,
        "appid": "0",
        "desc": "Açıklama bulunamadı."
    }
    
    steam_res = fetch_steam_data(game_name)
    if steam_res:
        data['title'] = steam_res['title'] # Gerçek isimi al
        data['thumb'] = steam_res['thumb']
        data['price'] = steam_res['price']
        data['appid'] = steam_res['appid']
    
    return data

@st.cache_data(ttl=3600)
def fetch_dynamic_deals(category):
    """
    CheapShark'tan (Metacritic/Deal/New) listeyi alıp
    Steam TR fiyatlarıyla eşleştirir.
    """
    sort_map = {"Popular": "Metacritic", "Sale": "Savings", "New": "Release"}
    sort_type = sort_map.get(category, "Metacritic")
    
    try:
        url = f"https://www.cheapshark.com/api/1.0/deals?storeID=1&sortBy={sort_type}&pageSize=8&pageNumber=0"
        if category == "New": url += "&desc=1" # Yeniden eskiye
        if category == "Popular": url += "&metacritic=75"
        
        data = requests.get(url, timeout=3).json()
        results = []
        
        for d in data:
            # Önce Steam TR'den gerçek veriyi çek
            s_data = fetch_steam_data(d['title'])
            
            final_title = d['title']
            final_thumb = d.get('thumb', PLACEHOLDER_IMG) # CheapShark'ın yatay resmi (Yedek)
            final_price = f"${d['salePrice']}" # Global Fiyat (Yedek)
            final_appid = d.get('steamAppID', '0')
            
            if s_data:
                final_title = s_data['title']
                final_thumb = s_data['thumb'] # Dikey Poster!
                final_price = s_data['price'] # TR Fiyatı
                final_appid = s_data['appid']
            
            results.append({
                "title": final_title,
                "thumb": final_thumb,
                "price": final_price,
                "appid": final_appid,
                "store": "Steam Store"
            })
        return results
    except: return []

# ================= ARAYÜZ =================
scroll_to_top()

# 1. ÜST MENÜ
c1, c2 = st.columns([1, 4])
with c1:
    if st.button("🏠 Ana Sayfa"): set_page('home')
with c2:
    cols = st.columns(4)
    if cols[0].button("Game Pass"): 
        st.session_state.selected_cat = "Game Pass"
        set_page('category')
    if cols[1].button("EA Play"): 
        st.session_state.selected_cat = "EA Play"
        set_page('category')
    if cols[2].button("EA Play Pro"): 
        st.session_state.selected_cat = "EA Play Pro"
        set_page('category')
    if cols[3].button("Ubisoft+"): 
        st.session_state.selected_cat = "Ubisoft+"
        set_page('category')

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
    
    # 1. POPÜLER OYUNLAR
    st.markdown("<div class='cat-header'>🏆 En Popüler Başyapıtlar</div>", unsafe_allow_html=True)
    pop_games = fetch_dynamic_deals("Popular")
    if pop_games:
        cols = st.columns(4)
        for i, g in enumerate(pop_games[:4]):
            with cols[i]:
                st.image(g['thumb'])
                st.markdown(f"<div class='game-title'>{g['title']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='game-price'>{g['price']}</div>", unsafe_allow_html=True)
                if st.button("İncele", key=f"pop_{i}"): go_detail(g)

    # 2. İNDİRİMDEKİLER
    st.markdown("<div class='cat-header'>🔥 Süper İndirimler</div>", unsafe_allow_html=True)
    sale_games = fetch_dynamic_deals("Sale")
    if sale_games:
        cols = st.columns(4)
        for i, g in enumerate(sale_games[:4]):
            with cols[i]:
                st.image(g['thumb'])
                st.markdown(f"<div class='game-title'>{g['title']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='game-price'>{g['price']}</div>", unsafe_allow_html=True)
                if st.button("İncele", key=f"sale_{i}"): go_detail(g)

    # 3. YENİ ÇIKANLAR
    st.markdown("<div class='cat-header'>✨ Yeni Çıkanlar</div>", unsafe_allow_html=True)
    new_games = fetch_dynamic_deals("New")
    if new_games:
        cols = st.columns(4)
        for i, g in enumerate(new_games[:4]):
            with cols[i]:
                st.image(g['thumb'])
                st.markdown(f"<div class='game-title'>{g['title']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='game-price'>{g['price']}</div>", unsafe_allow_html=True)
                if st.button("İncele", key=f"new_{i}"): go_detail(g)

# --- SAYFA: KATEGORİ ---
elif st.session_state.active_page == 'category':
    cat_name = st.session_state.selected_cat
    st.markdown(f"<div class='cat-header'>{cat_name} Kütüphanesi</div>", unsafe_allow_html=True)
    
    full_list = SUBSCRIPTIONS.get(cat_name, [])
    
    # Sayfalama
    total_games = len(full_list)
    total_pages = math.ceil(total_games / PAGE_SIZE)
    curr_page = st.session_state.page_number
    
    start_idx = curr_page * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    current_batch = full_list[start_idx:end_idx]
    
    if not current_batch:
        st.info("Bu kategoride oyun bulunamadı.")
    else:
        cols = st.columns(4)
        for i, game_name in enumerate(current_batch):
            col = cols[i % 4]
            with col:
                g = get_game_details(game_name, cat_name)
                st.image(g['thumb'])
                st.markdown(f"<div class='game-title'>{g['title']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='game-price'>{g['price']}</div>", unsafe_allow_html=True)
                if st.button("İncele", key=f"cat_{curr_page}_{i}"): go_detail(g)
                st.write("")

        # Sayfa Butonları
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
        st.markdown(f"<div class='game-price' style='font-size:2em; text-align:left;'>{g['price']}</div>", unsafe_allow_html=True)
        if g['appid'] != "0":
            st.link_button("Steam Mağazasına Git", f"https://store.steampowered.com/app/{g['appid']}")

# --- SAYFA: ARAMA ---
elif st.session_state.active_page == 'search':
    term = st.session_state.search_term
    st.info(f"🔎 '{term}' aranıyor...")
    
    res = get_game_details(term, "Arama Sonucu")
    
    if res['appid'] != "0":
        with st.container():
            c1, c2 = st.columns([1, 3])
            with c1: st.image(res['thumb'])
            with c2:
                st.subheader(res['title'])
                st.markdown(f"<div class='game-price' style='text-align:left;'>{res['price']}</div>", unsafe_allow_html=True)
                if st.button("İncele", key="search_res_btn"): go_detail(res)
    else:
        st.warning("Oyun bulunamadı veya Steam'de yok.")
