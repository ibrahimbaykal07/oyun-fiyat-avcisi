import streamlit as st
import requests
import streamlit.components.v1 as components
from datetime import datetime
import re
import math # BU EKSİKTİ, EKLENDİ

# --- 1. AYARLAR ---
st.set_page_config(page_title="Oyun Fiyatı (TR)", page_icon="🇹🇷", layout="centered")
PAGE_SIZE = 12
PLACEHOLDER_IMG = "https://placehold.co/600x900/1a1a1a/FFFFFF/png?text=Gorsel+Yok"
RAWG_API_KEY = "3f8159cbaaac426bac87a770371c941f"

# --- 2. CSS STİLİ (DİKEY GÖRSEL & TEMİZ ARAYÜZ) ---
st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    
    /* GÖRSELLERİ DİK (POSTER) YAP */
    div[data-testid="stImage"] img { 
        border-radius: 8px; 
        width: 100%; 
        aspect-ratio: 2/3; 
        object-fit: cover; 
    }
    
    .vitrin-title { 
        font-size: 0.95em; 
        font-weight: bold; 
        margin-top: 5px; 
        white-space: nowrap; 
        overflow: hidden; 
        text-overflow: ellipsis; 
        color: #333; 
    }
    .vitrin-price { 
        font-size: 1.1em; 
        font-weight: bold; 
        color: #28a745; 
        margin: 2px 0; 
    }
    .discount-tag {
        background-color: #d00;
        color: white;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.8em;
        font-weight: bold;
    }
    
    .detail-title { font-family: sans-serif; font-size: 2.5em; font-weight: 800; margin-bottom: 10px; color: #FFFFFF !important; line-height: 1.2; text-shadow: 0 0 10px rgba(0,0,0,0.5); }
    .desc-box { background-color: transparent; color: #FFFFFF !important; padding: 0; border: none; line-height: 1.6; font-size: 1.05em; margin-bottom: 20px; }
    
    .badge-container { display: inline-block; padding: 6px 12px; border-radius: 6px; font-family: sans-serif; font-weight: 800; font-size: 0.85em; letter-spacing: 0.5px; text-transform: uppercase; margin-top: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.2); }
    .badge-gamepass { background-color: #107C10; color: white; border: 1px solid #0e6f0e; }
    .badge-eapro { background: linear-gradient(135deg, #ff8c00, #ff0080); color: white; border: 1px solid #e67e00; }
    .badge-ea { background-color: #FF4747; color: white; border: 1px solid #e03e3e; }
    .badge-ubi { background-color: #0099FF; color: white; border: 1px solid #0088e0; }
    
    .price-big { font-size: 1.2em; font-weight: bold; color: #28a745; }
    .score-badge { font-size: 0.8em; padding: 4px 8px; border-radius: 4px; color: white; font-weight: bold; margin-right: 5px; display:inline-block;}
    .meta-green { background-color: #6c3; }
    .meta-yellow { background-color: #fc3; color: #333; }
    .meta-red { background-color: #f00; }
    .user-blue { background-color: #1b2838; border: 1px solid #66c0f4; color: #66c0f4; }
    
    .stButton button { width: 100%; }
    div[data-testid="column"] button { min-width: 40px; }
</style>
""", unsafe_allow_html=True)

# --- 3. MANUEL LİSTE ---
SUBSCRIPTIONS = {
    "Game Pass": [
        "Call of Duty: Black Ops 6", "Modern Warfare III", "Diablo IV", "Starfield", "Forza Motorsport", "Forza Horizon 5", 
        "Halo Infinite", "Microsoft Flight Simulator 2024", "Senua's Saga: Hellblade II", "S.T.A.L.K.E.R. 2", "Indiana Jones", 
        "Avowed", "Persona 3 Reload", "Like a Dragon: Infinite Wealth", "Palworld", "Lies of P", "Cocoon", "Sea of Stars", 
        "Hi-Fi RUSH", "Atomic Heart", "Wo Long", "A Plague Tale: Requiem", "Scorn", "Grounded", "High On Life", "Deathloop", 
        "Ghostwire: Tokyo", "Minecraft", "Sea of Thieves", "Gears 5", "Doom Eternal", "Halo MCC", "Age of Empires IV", 
        "Psychonauts 2", "Back 4 Blood", "Sniper Elite 5", "Monster Hunter Rise", "Assassin's Creed Valhalla", 
        "Assassin's Creed Odyssey", "Far Cry 6", "Watch Dogs 2", "Rainbow Six Siege", "FIFA 23", "Battlefield 2042", 
        "Mass Effect Legendary", "It Takes Two", "Need for Speed Unbound", "Jedi Fallen Order", "Titanfall 2", "The Sims 4", 
        "Cities Skylines II", "Football Manager 2024", "Payday 3", "Darktide", "Remnant 2", "Hollow Knight", "Stardew Valley", 
        "Vampire Survivors", "Valheim", "Among Us", "No Man's Sky", "Fallout 4", "Skyrim", "Control", "Dishonored 2", 
        "Yakuza: Like a Dragon", "Persona 5 Royal", "Tunic", "Dead Cells", "Slay the Spire", "Celeste", "Undertale"
    ],
    "EA Play Pro": [
        "EA SPORTS FC 25", "EA SPORTS FC 26", "Madden NFL 25", "F1 24", "Star Wars Jedi: Survivor", "Immortals of Aveum", 
        "Wild Hearts", "Dead Space Remake", "Tales of Kenzera", "PGA Tour", "WRC 23", "Lost in Random", "Knockout City",
        "It Takes Two", "Mass Effect Legendary", "Need for Speed Unbound", "Battlefield 2042"
    ],
    "EA Play": [
        "EA SPORTS FC 24", "FIFA 23", "F1 23", "Madden NFL 24", "Battlefield 2042", "Battlefield V", "Jedi Fallen Order", 
        "Battlefront II", "Mass Effect Legendary", "Titanfall 2", "The Sims 4", "Need for Speed Heat", "It Takes Two", 
        "A Way Out", "Unravel Two", "Dragon Age Inquisition", "Crysis Remastered", "Dead Space 3", "Skate 3", "Mirror's Edge"
    ],
    "Ubisoft+": [
        "Assassin's Creed Shadows", "Star Wars Outlaws", "Avatar: Frontiers of Pandora", "Prince of Persia: The Lost Crown", 
        "Assassin's Creed Mirage", "The Crew Motorfest", "Skull and Bones", "Assassin's Creed Valhalla", "Far Cry 6", 
        "Rainbow Six Siege", "The Division 2", "Ghost Recon Breakpoint", "Watch Dogs Legion", "Immortals Fenyx Rising", 
        "Riders Republic", "Anno 1800", "For Honor", "The Crew 2", "Trackmania", "South Park", "Rayman Legends", "Splinter Cell"
    ]
}

# --- 4. YARDIMCI FONKSİYONLAR ---
def scroll_to_top():
    components.html("""<script>window.parent.document.querySelector('.main').scrollTop = 0;</script>""", height=0)

def set_page_num(num):
    st.session_state.page_number = num
    scroll_to_top()
    st.rerun()

def go_category(name, is_sub=False):
    st.session_state.selected_cat = {"name": name, "is_sub": is_sub}
    st.session_state.active_page = 'category'
    st.session_state.page_number = 0
    scroll_to_top()
    st.rerun()

def go_detail(game_data):
    st.session_state.selected_game = game_data
    st.session_state.active_page = 'detail'
    scroll_to_top()
    st.rerun()

def go_home():
    st.session_state.active_page = 'home'
    scroll_to_top()
    st.rerun()

def increase_home_limit(key):
    st.session_state.home_limits[key] += 4
    st.rerun()

def check_subscription(game_name):
    s = game_name.lower().strip()
    if "fc 26" in s: return "EA Play Pro", "badge-eapro"
    
    for g in SUBSCRIPTIONS.get("EA Play Pro", []):
        if g.lower() in s: return "EA Play Pro", "badge-eapro"
    for sub_name, games_list in SUBSCRIPTIONS.items():
        if sub_name == "EA Play Pro": continue
        for g in games_list:
            if g.lower() in s:
                cls = "badge-gamepass" if sub_name == "Game Pass" else "badge-ea" if sub_name == "EA Play" else "badge-ubi"
                return sub_name, cls
    return None, None

def get_meta_color(score):
    if score is None: score = 0
    if score >= 75: return "meta-green"
    elif score >= 50: return "meta-yellow"
    else: return "meta-red"

# --- 5. VERİ MOTORU ---
# Steam TR Verisi (Dikey Görsel + Native Price)
@st.cache_data(ttl=3600)
def get_steam_data_tr(game_name):
    clean_name = re.sub(r'\(.*?\)', '', game_name).replace(':', '').replace('.', '').strip()
    
    if "fc 26" in clean_name.lower():
        return {
            "price": "Çıkmadı",
            "thumb": "https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/2195250/library_600x900.jpg",
            "steamAppID": "0"
        }

    try:
        url = f"https://store.steampowered.com/api/storesearch/?term={clean_name}&l=turkish&cc=tr"
        r = requests.get(url, timeout=3)
        if r.status_code == 200:
            data = r.json()
            if data['total'] > 0:
                item = data['items'][0]
                app_id = item['id']
                img_poster = f"https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/{app_id}/library_600x900.jpg"
                
                price_text = "Fiyat Yok"
                if 'price' in item:
                    raw_val = item['price']['final'] / 100
                    price_text = f"${raw_val:.2f}" 
                else:
                    price_text = "Ücretsiz"
                
                return {
                    "price": price_text,
                    "thumb": img_poster,
                    "steamAppID": app_id,
                    "dealID": f"steam_{app_id}"
                }
    except: pass
    return None

# RAWG Görsel (Yedek)
@st.cache_data(ttl=3600)
def fetch_rawg_data(game_name):
    clean_name = re.sub(r'\(.*?\)', '', game_name)
    search_queries = [clean_name, clean_name.split(':')[0]]
    
    for query in search_queries:
        if len(query) < 2: continue
        try:
            url = f"https://api.rawg.io/api/games?key={RAWG_API_KEY}&search={query}&page_size=1"
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                data = r.json()
                if data['results']:
                    res = data['results'][0]
                    if res.get('background_image'):
                        return {"image": res.get('background_image'), "meta": res.get('metacritic', 0)}
        except: pass
    return None

# CheapShark (Yedek)
def fetch_vitrin_deals(sort_by, on_sale=0, page=0, page_size=24):
    url = f"https://www.cheapshark.com/api/1.0/deals?storeID=1,25&sortBy={sort_by}&onSale={on_sale}&pageSize={page_size}&pageNumber={page}"
    if sort_by == "Release": url += "&desc=1"
    try:
        data = requests.get(url).json()
        res = []
        for d in data:
            price_display = f"${d['salePrice']}"
            steam_data = get_steam_data_tr(d['title'])
            final_thumb = d.get('thumb')
            
            if steam_data: 
                price_display = steam_data['price']
                final_thumb = steam_data['thumb']

            res.append({
                "title": d['title'], "thumb": final_thumb,
                "meta": int(d['metacriticScore']), "user": int(d['steamRatingPercent']),
                "dealID": d['dealID'], "steamAppID": d.get('steamAppID'),
                "price": price_display, "discount": float(d['savings']),
                "offers": [{"store": "Mağaza", "price": price_display, "link": f"https://www.cheapshark.com/redirect?dealID={d['dealID']}"}]
            })
        if sort_by == "Release": res.sort(key=lambda x: x.get('releaseDate', 0), reverse=True)
        return res
    except: return []

def fetch_sub_games(sub_name, page=0, page_size=12):
    game_names = SUBSCRIPTIONS.get(sub_name, [])
    start = page * page_size
    end = start + page_size
    batch = game_names[start:end]
    results = []
    
    for i, name in enumerate(batch):
        game_obj = {
            "title": name,
            "thumb": PLACEHOLDER_IMG,
            "meta": 0, "user": 0,
            "dealID": f"sub_{sub_name}_{start + i}",
            "steamAppID": "0",
            "price": "---", "discount": 0.0, "store": sub_name, "offers": []
        }
        
        steam_data = get_steam_data_tr(name)
        if steam_data:
            game_obj.update({
                "thumb": steam_data['thumb'],
                "price": steam_data['price'],
                "steamAppID": steam_data['steamAppID'],
                "offers": [{"store": "Steam (TR)", "price": steam_data['price'], "link": f"https://store.steampowered.com/app/{steam_data['steamAppID']}"}]
            })
        
        if game_obj["thumb"] == PLACEHOLDER_IMG:
            rawg = fetch_rawg_data(name)
            if rawg and rawg['image']: game_obj["thumb"] = rawg['image']
            
        results.append(game_obj)
    return results

def get_steam_details_turkish(steam_id):
    if not steam_id or str(steam_id) == "0": return (None, [], None, None)
    try:
        url = f"http://store.steampowered.com/api/appdetails?appids={steam_id}&cc=tr&l=turkish"
        data = requests.get(url, timeout=3).json()
        if str(steam_id) in data and data[str(steam_id)]['success']:
            d = data[str(steam_id)]['data']
            screens = []
            if 'screenshots' in d:
                for s in d['screenshots']:
                    screens.append({"url": s['path_full']})
            return d.get('short_description'), screens, d.get('pc_requirements', {}).get('minimum'), d.get('pc_requirements', {}).get('recommended')
    except: pass
    return (None, [], None, None)

# --- 6. SESSION STATE ---
if 'active_page' not in st.session_state: st.session_state.active_page = 'home'
if 'page_number' not in st.session_state: st.session_state.page_number = 0
if 'selected_cat' not in st.session_state: st.session_state.selected_cat = None
if 'selected_game' not in st.session_state: st.session_state.selected_game = None
if 'search_term' not in st.session_state: st.session_state.search_term = ""
if 'home_limits' not in st.session_state: st.session_state.home_limits = {"p1": 4, "p2": 4, "p3": 4}

# ================= ARAYÜZ =================
scroll_to_top()

h1, h2 = st.columns([1.5, 4])
with h1:
    if st.button("🏠 Ana Sayfa"): go_home()
with h2:
    s1, s2, s3, s4 = st.columns(4)
    if s1.button("Game Pass"): go_category("Game Pass", True)
    if s2.button("EA Play"): go_category("EA Play", True)
    if s3.button("EA Play Pro"): go_category("EA Play Pro", True)
    if s4.button("Ubisoft+"): go_category("Ubisoft+", True)

st.divider()

# ARAMA
with st.form(key='global_search'):
    ci, cb = st.columns([4, 1])
    with ci: s_val = st.text_input("Oyun Ara (Steam TR)", placeholder="Call of Duty, GTA V...", label_visibility="collapsed")
    with cb: s_btn = st.form_submit_button("🔎 Bul")

if s_btn and s_val:
    st.session_state.search_term = s_val
    st.session_state.active_page = 'search'
    st.rerun()

# SAYFA: ANA SAYFA
if st.session_state.active_page == 'home':
    cats_config = [("🏆 En Popüler", "Metacritic", 0, "p1"), ("🔥 İndirimler", "Savings", 1, "p2"), ("✨ Yeni Çıkanlar", "Release", 0, "p3")]
    for title, sort_key, sale_flag, limit_key in cats_config:
        st.subheader(title)
        games = fetch_vitrin_deals(sort_key, on_sale=sale_flag, page_size=st.session_state.home_limits[limit_key])
        for i in range(0, len(games), 4):
            cols = st.columns(4)
            for j in range(4):
                if i+j < len(games):
                    g = games[i+j]
                    with cols[j]:
                        st.image(g['thumb'], use_container_width=True)
                        st.markdown(f"<div class='vitrin-title'>{g['title']}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='vitrin-price'>{g['price']}</div>", unsafe_allow_html=True)
                        if g['discount'] > 0: 
                            st.markdown(f"<span class='discount-tag'>-{int(g['discount'])}%</span>", unsafe_allow_html=True)
                        if st.button("İncele", key=f"h_{limit_key}_{i}_{j}"): go_detail(g)
            st.write("")
        if st.button(f"➕ {title} - Daha Fazla", key=f"m_{limit_key}"): increase_home_limit(limit_key)
        st.markdown("---")

# SAYFA: KATEGORİ
elif st.session_state.active_page == 'category':
    cat = st.session_state.selected_cat
    curr_page = st.session_state.page_number
    st.subheader(f"{cat['name']} Listesi")
    
    if cat.get('is_sub'):
        games = fetch_sub_games(cat['name'], page=curr_page, page_size=PAGE_SIZE)
        total_items = len(SUBSCRIPTIONS.get(cat['name'], []))
        total_pages = math.ceil(total_items / PAGE_SIZE)
    else:
        games = fetch_vitrin_deals(cat['sort'], on_sale=cat['sale'], page=curr_page, page_size=24)
        total_pages = 10
    
    if games:
        for i in range(0, len(games), 4):
            cols = st.columns(4)
            for j in range(4):
                if i+j < len(games):
                    g = games[i+j]
                    with cols[j]:
                        st.image(g['thumb'], use_container_width=True)
                        st.markdown(f"<div class='vitrin-title'>{g['title']}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='vitrin-price'>{g['price']}</div>", unsafe_allow_html=True)
                        if st.button("İncele", key=f"c_{curr_page}_{i}_{j}"): go_detail(g)
            st.write("")
        
        cols = st.columns(min(total_pages, 10))
        for p in range(min(total_pages, 10)):
            with cols[p]:
                if st.button(str(p+1), key=f"pg_{p}", type="primary" if p==curr_page else "secondary"): set_page_num(p)
    else: st.info("Bu sayfada oyun yok.")

# SAYFA: DETAY
elif st.session_state.active_page == 'detail':
    game = st.session_state.selected_game
    desc, media_list, req_min, req_rec = get_steam_details_turkish(game.get('steamAppID'))
    
    c1, c2 = st.columns([1.5, 2.5])
    with c1:
        st.image(game['thumb'], use_container_width=True)
        sub_n, sub_cls = check_subscription(game['title'])
        if sub_n:
            st.markdown(f"<span class='badge-container {sub_cls}'>{sub_n} DAHİL</span>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<h1 class='detail-title'>{game['title']}</h1>", unsafe_allow_html=True)
        mc = get_meta_color(game.get('meta', 0))
        st.markdown(f"""<span class='score-badge {mc}'>Metacritic: {game.get('meta', 0)}</span>""", unsafe_allow_html=True)
        if desc: st.markdown(f"<div class='desc-box'>{desc}</div>", unsafe_allow_html=True)
        
        st.write("### 🏷️ Market Fiyatı")
        for off in game.get('offers', []):
            st.write(f"**{off.get('store', 'Mağaza')}**: {off['price']}")
            st.link_button("Satın Al", off['link'], type="primary")
            st.divider()
            
    if media_list:
        st.subheader("📸 Ekran Görüntüleri")
        cols = st.columns(3)
        for i, m in enumerate(media_list[:3]):
            with cols[i]: st.image(m['url'], use_container_width=True)

# SAYFA: ARAMA
elif st.session_state.active_page == 'search':
    term = st.session_state.search_term
    st.info(f"🔎 '{term}' aranıyor...")
    
    steam_res = get_steam_data_tr(term)
    
    grouped = {}
    if steam_res:
        grouped[steam_res['steamAppID']] = {
            "title": term.title(),
            "thumb": steam_res['thumb'],
            "meta": 0, "user": 0, "dealID": steam_res['dealID'],
            "steamAppID": steam_res['steamAppID'],
            "price": steam_res['price'],
            "offers": [{"store": "Steam (TR)", "price": steam_res['price'], "link": f"https://store.steampowered.com/app/{steam_res['steamAppID']}"}]
        }

    if grouped:
        st.success(f"✅ Sonuç bulundu.")
        for i, (k, game) in enumerate(grouped.items()):
            with st.container():
                c1, c2, c3 = st.columns([1.5, 2.5, 3])
                with c1: st.image(game['thumb'], use_container_width=True)
                with c2: 
                    st.subheader(game['title'])
                    sub_n, sub_cls = check_subscription(game['title'])
                    if sub_n: st.markdown(f"<span class='badge-container {sub_cls}'>{sub_n} DAHİL</span>", unsafe_allow_html=True)
                with c3:
                    st.write(f"**{game['price']}**")
                    if st.button("İncele", key=f"s_{i}"): go_detail(game)
                st.markdown("---")
    else: st.warning("Sonuç bulunamadı.")
