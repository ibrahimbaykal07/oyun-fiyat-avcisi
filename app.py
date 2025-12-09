import streamlit as st
import requests
import streamlit.components.v1 as components
from datetime import datetime
import re
import math

# --- 1. AYARLAR ---
st.set_page_config(page_title="Oyun Fiyatı (TR)", page_icon="🇹🇷", layout="centered")
PAGE_SIZE = 12
PLACEHOLDER_IMG = "https://placehold.co/600x300/1a1a1a/FFFFFF/png?text=Gorsel+Yok"
RAWG_API_KEY = "c1e963e178f3416f97f7840a127af77b"

# --- 2. GÖMÜLÜ LOGOLAR ---
ICON_GAMEPASS = "data:image/png;base64,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"
ICON_EA = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iI0ZGODU1NSI+PHBhdGggZD0iTTEyIDJDNi40OCAyIDIgNi40OCAyIDEyczQuNDggMTAgMTAgMTAgMTAtNC40OCAxMC0xMFMxNy41MiAyIDEyIDJ6bTMuNSA3aC0zLjV2Mi41aDN2MS41aC0zVjE2aDN2MS41aC00LjVWOGg0LjV6bS02IDBoLTMuNXY4aDQuNXYtMS41aC0zdi0yLjVoM3YtMS41aC0zVjkuNWgzLjV6Ii8+PC9zdmc+"
ICON_UBI = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iIzAwOTlGRiI+PHBhdGggZD0iTTEyIDJDNi40OCAyIDIgNi40OCAyIDEyczQuNDggMTAgMTAgMTAgMTAtNC40OCAxMC0xMFMxNy41MiAyIDEyIDJ6bTAgMTcuNWMtMy4wMyAwLTUuNS0yLjQ3LTUuNS01LjVTOC45NyA5IDEyIDlzNS41IDIuNDcgNS41IDUuNS0yLjQ3IDUuNS01LjUgNS41em0wLTljLTEuOTMgMC0zLjUgMS41Ny0zLjUgMy41UzEwLjA3IDE1IDEyIDE1czMuNS0xLjU3IDMuNS0zLjUtMS41Ny0zLjUtMy41LTMuNXoiLz48L3N2Zz4="

SUB_LOGOS = {"Game Pass": ICON_GAMEPASS, "EA Play": ICON_EA, "EA Play Pro": ICON_EA, "Ubisoft+": ICON_UBI}
SUB_CLASSES = {"Game Pass": "badge-gamepass", "EA Play Pro": "badge-eapro", "EA Play": "badge-ea", "Ubisoft+": "badge-ubi"}
SUB_BTN_LABELS = {"Game Pass": "🟩 Game Pass", "EA Play": "🟥 EA Play", "EA Play Pro": "🟧 EA Play Pro", "Ubisoft+": "🟦 Ubisoft+"}

try:
    from epicstore_api import EpicGamesStoreAPI
    EPIC_AVAILABLE = True
except ImportError:
    EPIC_AVAILABLE = False

# --- 3. CSS STİLİ ---
st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    .kur-kutusu { background-color: #f8f9fa; padding: 8px 15px; border-radius: 8px; font-weight: bold; color: #495057; font-size: 0.9em; text-align: center; border: 1px solid #dee2e6; }
    div[data-testid="stImage"] img { border-radius: 8px; aspect-ratio: 16/9; object-fit: cover; }
    .vitrin-title { font-size: 0.9em; font-weight: bold; margin-top: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: #333; }
    .vitrin-price { font-size: 1.1em; font-weight: bold; color: #28a745; margin: 2px 0; }
    .vitrin-date { font-size: 0.75em; color: #666; margin-bottom: 5px; font-style: italic; }
    .detail-title { font-family: sans-serif; font-size: 2.5em; font-weight: 800; margin-bottom: 10px; color: #FFFFFF !important; line-height: 1.2; text-shadow: 0 0 10px rgba(0,0,0,0.5); }
    .desc-box { background-color: transparent; color: #FFFFFF !important; padding: 0; border: none; line-height: 1.6; font-size: 1.05em; margin-bottom: 20px; }
    .badge-container { display: inline-block; padding: 6px 12px; border-radius: 6px; font-family: sans-serif; font-weight: 800; font-size: 0.85em; letter-spacing: 0.5px; text-transform: uppercase; margin-top: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.2); }
    .badge-gamepass { background-color: #107C10; color: white; border: 1px solid #0e6f0e; }
    .badge-eapro { background: linear-gradient(135deg, #ff8c00, #ff0080); color: white; border: 1px solid #e67e00; }
    .badge-ea { background-color: #FF4747; color: white; border: 1px solid #e03e3e; }
    .badge-ubi { background-color: #0099FF; color: white; border: 1px solid #0088e0; }
    .sub-card { display: flex; align-items: center; background: linear-gradient(90deg, #1c1c1c, #2a2a2a); border-left: 5px solid #555; padding: 10px 15px; border-radius: 0 8px 8px 0; margin-top: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); color: white; font-family: sans-serif; width: fit-content; }
    .sub-icon { width: 24px; height: 24px; margin-right: 10px; }
    .sub-text { font-weight: bold; font-size: 0.9em; letter-spacing: 0.5px; text-transform: uppercase; }
    .req-box { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #e9ecef; font-size: 0.9em; height: 100%; }
    .req-title { font-weight: bold; margin-bottom: 10px; color: #333; font-size: 1.1em; border-bottom: 2px solid #ddd; padding-bottom: 5px; }
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

# --- 4. MANUEL LİSTE ---
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

STORE_LOGOS = {"Steam": "https://cdn.simpleicons.org/steam/171a21", "Epic Games": "https://cdn.simpleicons.org/epicgames/333333", "Ubisoft Connect": "https://cdn.simpleicons.org/ubisoft/0099FF", "EA App": "https://cdn.simpleicons.org/ea/FF4747", "GOG": "https://cdn.simpleicons.org/gogdotcom/893CE7"}

# --- 5. SESSION STATE ---
if 'active_page' not in st.session_state: st.session_state.active_page = 'home'
if 'page_number' not in st.session_state: st.session_state.page_number = 0
if 'selected_cat' not in st.session_state: st.session_state.selected_cat = None
if 'selected_game' not in st.session_state: st.session_state.selected_game = None
if 'search_term' not in st.session_state: st.session_state.search_term = ""
if 'gallery_idx' not in st.session_state: st.session_state.gallery_idx = 0
if 'home_limits' not in st.session_state: st.session_state.home_limits = {"p1": 4, "p2": 4, "p3": 4}

# --- 6. YARDIMCI FONKSİYONLAR ---
def scroll_to_top():
    components.html("""<script>window.parent.document.querySelector('.main').scrollTop = 0;</script>""", height=0)

@st.dialog("🎬 Medya Galerisi", width="large")
def show_gallery_modal(media_list, start_idx=0):
    idx = st.slider("Medya Gezgini", 0, len(media_list)-1, start_idx, label_visibility="collapsed")
    current_item = media_list[idx]
    st.write("")
    if current_item['type'] == 'video':
        st.video(current_item['url'], autoplay=True)
        st.caption(f"🎥 {current_item.get('name', 'Fragman')}")
    else:
        st.markdown("""<style>div[data-testid="stImage"] img { aspect-ratio: auto !important; }</style>""", unsafe_allow_html=True)
        st.image(current_item['url'], use_container_width=True)
        st.caption(f"📷 Görsel {idx + 1} / {len(media_list)}")
    st.markdown(f"<div style='text-align:center; color:#888; font-size:0.8em;'>Diğer medyaya geçmek için yukarıdaki kaydırıcıyı kullanın.</div>", unsafe_allow_html=True)

# --- ÇOKLU KAYNAKLI GÖRSEL AVCISI (STEAM + RAWG) ---
@st.cache_data(ttl=3600)
def fetch_best_image(game_name):
    """
    Oyun görseli bulmak için Steam -> RAWG sıralamasını kullanır.
    FC 26 gibi olmayan oyunlar için manuel görsel atar.
    """
    
    # 1. Manuel Düzeltmeler (Henüz Görseli Olmayanlar)
    name_lower = game_name.lower()
    if "fc 26" in name_lower: return "https://cdn.akamai.steamstatic.com/steam/apps/2195250/header.jpg" # FC 25 görseli (Geçici)
    if "madden nfl 26" in name_lower: return "https://cdn.akamai.steamstatic.com/steam/apps/2582560/header.jpg" # Madden 25
    if "f1 25" in name_lower: return "https://cdn.akamai.steamstatic.com/steam/apps/2488620/header.jpg" # F1 24
    
    # İsim Temizleme (Noktalama, Yıl vb.)
    clean_name = re.sub(r'\(.*?\)', '', game_name).replace(':', '').replace('.', '')
    
    # 2. STEAM ARAMA (En Kaliteli Görsel)
    try:
        steam_url = f"https://store.steampowered.com/api/storesearch/?term={clean_name}&l=turkish&cc=tr"
        r = requests.get(steam_url, timeout=2)
        if r.status_code == 200:
            data = r.json()
            if data['total'] > 0:
                item = data['items'][0]
                # Steam Header Görseli (Yüksek Kalite)
                return f"https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/{item['id']}/header.jpg"
    except: pass

    # 3. RAWG ARAMA (Yedek)
    try:
        rawg_url = f"https://api.rawg.io/api/games?key={RAWG_API_KEY}&search={clean_name}&page_size=1"
        r = requests.get(rawg_url, timeout=2)
        if r.status_code == 200:
            data = r.json()
            if data['results']:
                return data['results'][0].get('background_image')
    except: pass

    return PLACEHOLDER_IMG

def get_dollar_rate():
    try:
        r = requests.get("https://www.tcmb.gov.tr/kurlar/today.xml", timeout=2)
        from xml.etree import ElementTree as ET
        root = ET.fromstring(r.content)
        for c in root.findall('Currency'):
            if c.get('Kod') == 'USD': return float(c.find('ForexSelling').text)
    except: return 36.50

def get_game_image(deal):
    sid = deal.get('steamAppID')
    if sid and sid != "0": return f"https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/{sid}/library_600x900.jpg"
    thumb = deal.get('thumb')
    if thumb and ("capsule" in thumb or "header" in thumb): return thumb
    return PLACEHOLDER_IMG

def get_meta_color(score):
    if score is None: score = 0
    if score >= 75: return "meta-green"
    elif score >= 50: return "meta-yellow"
    else: return "meta-red"

def check_subscription(game_name):
    s = game_name.lower().strip()
    if "fc 26" in s or "fc26" in s: return "EA Play Pro", SUB_CLASSES["EA Play Pro"]
    for g in SUBSCRIPTIONS.get("EA Play Pro", []):
        if g.lower() in s: return "EA Play Pro", SUB_CLASSES["EA Play Pro"]
    for sub_name, games_list in SUBSCRIPTIONS.items():
        if sub_name == "EA Play Pro": continue
        for g in games_list:
            if g.lower() in s: return sub_name, SUB_CLASSES[sub_name]
    return None, None

def get_steam_turkey_price(sid):
    try:
        r = requests.get(f"http://store.steampowered.com/api/appdetails?appids={sid}&cc=tr", timeout=2).json()
        if r[str(sid)]['success']:
            d = r[str(sid)]['data']
            if 'price_overview' in d: return d['price_overview']['final'] / 100, d['price_overview']['currency']
    except: pass
    return None, None

def get_epic_price_local(game_name):
    if not EPIC_AVAILABLE: return None, None, None
    try:
        api = EpicGamesStoreAPI()
        games = api.fetch_store_games(keywords=game_name, market="TR", country="TR", count=1)
        elements = games.get('data', {}).get('Catalog', {}).get('searchStore', {}).get('elements', [])
        if elements:
            game = elements[0]
            if game_name.lower() in game['title'].lower() or game['title'].lower() in game_name.lower():
                return game['price']['totalPrice']['discountPrice'] / 100, None, f"https://store.epicgames.com/tr/p/{game['productSlug']}"
    except: pass
    return None, None, None

def get_steam_details_turkish(steam_id):
    empty_return = (None, [], None, None)
    if not steam_id or str(steam_id) == "0": return empty_return
    try:
        url = f"http://store.steampowered.com/api/appdetails?appids={steam_id}&cc=tr&l=turkish"
        data = requests.get(url, timeout=3).json()
        if str(steam_id) in data and data[str(steam_id)]['success']:
            game_data = data[str(steam_id)]['data']
            desc = game_data.get('short_description', 'Açıklama bulunamadı.')
            media_list = []
            if 'movies' in game_data:
                for m in game_data['movies']:
                    mp4_url = m.get('mp4', {}).get('max')
                    if mp4_url:
                        media_list.append({"type": "video", "url": mp4_url, "thumb": m.get('thumbnail'), "name": m.get('name', 'Fragman')})
                        if len(media_list) >= 2: break
            if 'screenshots' in game_data:
                for s in game_data['screenshots']:
                    media_list.append({"type": "image", "url": s['path_full'], "thumb": s['path_thumbnail']})
            req_min = "Bilgi yok."
            req_rec = "Bilgi yok."
            if 'pc_requirements' in game_data and isinstance(game_data['pc_requirements'], dict):
                req_min = game_data['pc_requirements'].get('minimum', 'Belirtilmemiş.')
                req_rec = game_data['pc_requirements'].get('recommended', 'Belirtilmemiş.')
            return desc, media_list, req_min, req_rec
    except: pass
    return empty_return

def autocorrect_name(term):
    d = {"gta": "Grand Theft Auto", "gta 5": "Grand Theft Auto V", "cod": "Call of Duty", "fc 25": "EA SPORTS FC 25", "fc 26": "EA SPORTS FC 26", "mc": "Minecraft", "cp": "Cyberpunk 2077"}
    return d.get(term.lower().strip(), term)

def clean_game_title(title):
    remove_words = ["standard edition", " edition", " base game", " launch"]
    cleaned = title.lower()
    for word in remove_words: cleaned = cleaned.replace(word, "")
    return cleaned.strip()

def calculate_sort_score(game_title, search_term):
    title_lower = game_title.lower()
    search_lower = search_term.lower()
    if title_lower == search_lower: return 0
    if not any(x in title_lower for x in ["dlc", "pack", "soundtrack", "expansion", "bundle", "season pass", "coin", "credit"]): return 1
    if any(x in title_lower for x in ["edition", "deluxe", "gold", "ultimate", "goty"]): return 2
    return 3

def timestamp_to_date(ts):
    if not ts: return ""
    try: return datetime.fromtimestamp(ts).strftime('%d.%m.%Y')
    except: return ""

# --- 7. NAVİGASYON ---
def go_home():
    st.session_state.active_page = 'home'
    st.session_state.page_number = 0
    st.session_state.home_limits = {"p1": 4, "p2": 4, "p3": 4}
    scroll_to_top()
    st.rerun()

def go_category(name, sort, sale, is_sub=False):
    st.session_state.selected_cat = {"name": name, "sort": sort, "sale": sale, "is_sub": is_sub}
    st.session_state.active_page = 'category'
    st.session_state.page_number = 0
    scroll_to_top()
    st.rerun()

def go_detail(game_data):
    st.session_state.selected_game = game_data
    st.session_state.active_page = 'detail'
    scroll_to_top()
    st.rerun()

def set_page_num(num):
    st.session_state.page_number = num
    scroll_to_top()
    st.rerun()

def increase_home_limit(key):
    st.session_state.home_limits[key] += 4
    st.rerun()

# --- 8. VERİ MOTORU ---
def fetch_vitrin_deals(sort_by, on_sale=0, page=0, page_size=24):
    url = f"https://www.cheapshark.com/api/1.0/deals?storeID=1,25&sortBy={sort_by}&onSale={on_sale}&pageSize={page_size}&pageNumber={page}"
    if sort_by == "Release": url += "&desc=1"
    if sort_by == "Metacritic": url += "&upperPrice=60&metacritic=70"
    try:
        data = requests.get(url).json()
        results = []
        for d in data:
            s_name = "Steam" if d['storeID'] == "1" else "Epic Games"
            price_tl = int(float(d['salePrice']) * dolar_kuru)
            offer = {"store": s_name, "price": price_tl, "link": f"https://www.cheapshark.com/redirect?dealID={d['dealID']}", "discount": float(d['savings'])}
            results.append({
                "title": d['title'], "thumb": get_game_image(d),
                "meta": int(d['metacriticScore']), "user": int(d['steamRatingPercent']),
                "dealID": d['dealID'], "steamAppID": d.get('steamAppID'),
                "price": price_tl, "discount": float(d['savings']),
                "offers": [offer], "store": s_name, "releaseDate": d.get('releaseDate', 0)
            })
        if sort_by == "Release": results.sort(key=lambda x: x['releaseDate'], reverse=True)
        return results
    except: return []

# --- GÜÇLENDİRİLMİŞ LİSTE ÇEKİCİ ---
def fetch_sub_games(sub_name, page=0, page_size=12):
    game_names = SUBSCRIPTIONS.get(sub_name, [])
    start = page * page_size
    end = start + page_size
    batch = game_names[start:end]
    results = []
    
    for i, name in enumerate(batch):
        # Varsayılan Obje (Garantili)
        game_obj = {
            "title": name,
            "thumb": PLACEHOLDER_IMG,
            "meta": 0, "user": 0,
            "dealID": f"sub_{sub_name}_{start + i}", # ÇAKIŞMA ÖNLEYİCİ ID
            "steamAppID": "0",
            "price": "---", "discount": 0.0, "store": sub_name, "offers": []
        }
        
        # 1. GÖRSEL ARA (Steam > RAWG)
        best_img = fetch_best_image(name)
        if best_img: game_obj["thumb"] = best_img
        
        # 2. FİYAT (CheapShark)
        if game_obj["thumb"] == PLACEHOLDER_IMG:
            try:
                search_name = name.split(':')[0]
                url = f"https://www.cheapshark.com/api/1.0/deals?title={search_name}&exact=0&limit=1"
                r = requests.get(url, timeout=1.0)
                if r.status_code == 200:
                    d = r.json()
                    if d:
                        item = d[0]
                        game_obj["thumb"] = get_game_image(item)
                        game_obj["dealID"] = item['dealID']
            except: pass
            
        results.append(game_obj)
    return results

# ================= ARAYÜZ BAŞLIYOR =================
scroll_to_top()
dolar_kuru = get_dollar_rate()

h1, h2, h3 = st.columns([1.5, 4, 1.5])
with h1:
    if st.button("🏠 Ana Sayfa"): go_home()
with h2:
    c1, c2, c3 = st.columns(3)
    if c1.button("🏆 Popüler"): go_category("En Popüler", "Metacritic", 0)
    if c2.button("🔥 İndirim"): go_category("Süper İndirimler", "Savings", 1)
    if c3.button("✨ Yeni"): go_category("Yeni Çıkanlar", "Release", 0)
    
    st.write("")
    s1, s2, s3, s4 = st.columns(4)
    if s1.button("Game Pass"): go_category("Game Pass", None, None, True)
    if s2.button("EA Play"): go_category("EA Play", None, None, True)
    if s3.button("EA Play Pro"): go_category("EA Play Pro", None, None, True)
    if s4.button("Ubisoft+"): go_category("Ubisoft+", None, None, True)

with h3:
    st.markdown(f"<div class='kur-kutusu'>💲 {dolar_kuru:.2f} TL</div>", unsafe_allow_html=True)

st.divider()

with st.form(key='global_search'):
    ci, cb = st.columns([4, 1])
    with ci: s_val = st.text_input("Oyun Ara", placeholder="FC 26, GTA V...", label_visibility="collapsed")
    with cb: s_btn = st.form_submit_button("🔎 Bul")

if s_btn and s_val:
    st.session_state.search_term = s_val
    st.session_state.active_page = 'search'
    st.rerun()

# SAYFA: ANA SAYFA
if st.session_state.active_page == 'home':
    cats_config = [("🏆 En Popüler Başyapıtlar", "Metacritic", 0, "p1"), ("🔥 Şuan İndirimde", "Savings", 1, "p2"), ("✨ Yeni Çıkanlar", "Release", 0, "p3")]
    for title, sort_key, sale_flag, limit_key in cats_config:
        st.subheader(title)
        current_limit = st.session_state.home_limits[limit_key]
        games = fetch_vitrin_deals(sort_key, on_sale=sale_flag, page_size=current_limit)
        for i in range(0, len(games), 4):
            cols = st.columns(4)
            for j in range(4):
                if i+j < len(games):
                    g = games[i+j]
                    with cols[j]:
                        st.image(g['thumb'], use_container_width=True)
                        st.markdown(f"<div class='vitrin-title'>{g['title']}</div>", unsafe_allow_html=True)
                        if sort_key == "Release" and g['releaseDate'] > 0:
                            st.markdown(f"<div class='vitrin-date'>📅 {timestamp_to_date(g['releaseDate'])}</div>", unsafe_allow_html=True)
                        c_p, c_d = st.columns([2, 1])
                        c_p.markdown(f"<div class='vitrin-price'>{g['price']} TL</div>", unsafe_allow_html=True)
                        if g['discount'] > 0: c_d.markdown(f"<span style='background:#d00;color:white;font-size:0.8em;padding:2px;border-radius:3px;'>-%{g['discount']}</span>", unsafe_allow_html=True)
                        # BENZERSİZ KEY
                        if st.button("İncele", key=f"home_btn_{limit_key}_{i}_{j}"): go_detail(g)
            st.write("")
        if st.button(f"➕ {title} - Daha Fazla Göster", key=f"more_{limit_key}"): increase_home_limit(limit_key)
        st.markdown("---")

# SAYFA: KATEGORİ
elif st.session_state.active_page == 'category':
    cat = st.session_state.selected_cat
    curr_page = st.session_state.page_number
    st.subheader(f"{cat['name']}")
    
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
                        st.markdown(f"<div class='vitrin-price'>{g['price']} TL</div>", unsafe_allow_html=True)
                        # BENZERSİZ KEY
                        if st.button("İncele", key=f"cat_btn_{curr_page}_{i}_{j}"): go_detail(g)
            st.write("")
        st.markdown("---")
        if total_pages > 1:
            cols = st.columns(min(total_pages, 10))
            for p in range(total_pages):
                if p < 10:
                    with cols[p]:
                        b_type = "primary" if p == curr_page else "secondary"
                        if st.button(str(p+1), key=f"pg_{p}", type=b_type): set_page_num(p)
    else: st.info("Bu sayfada oyun yok.")

# SAYFA: DETAY
elif st.session_state.active_page == 'detail':
    game = st.session_state.selected_game
    if game['thumb'] == PLACEHOLDER_IMG:
        img_url = fetch_best_image(game['title'])
        if img_url: game['thumb'] = img_url

    desc, media_list, req_min, req_rec = get_steam_details_turkish(game.get('steamAppID'))
    c1, c2 = st.columns([1.5, 2.5])
    with c1:
        st.image(game['thumb'], use_container_width=True)
        sub_n, sub_cls = check_subscription(game['title'])
        if sub_n:
            st.markdown(f"<span class='badge-container {sub_cls}'>{sub_n} DAHİL</span>", unsafe_allow_html=True)
            if st.button(f"Tüm {sub_n} Listesi", key="sub_link"): go_category(sub_n, None, None, True)
    with c2:
        st.markdown(f"<h1 class='detail-title'>{game['title']}</h1>", unsafe_allow_html=True)
        mc = get_meta_color(game.get('meta', 0))
        st.markdown(f"""<div style="margin-bottom:15px;"><span class='score-badge {mc}'>Metacritic: {game.get('meta', 0)}</span><span class='score-badge user-blue'>Steam User: %{game.get('user', 0)}</span></div>""", unsafe_allow_html=True)
        if desc: st.markdown(f"<div class='desc-box'>{desc}</div>", unsafe_allow_html=True)
        st.write("### 🏷️ Mağaza Fiyatları")
        offers = game.get('offers', [])
        if not offers: offers = [{"store": game.get('store', 'Bilinmiyor'), "price": game.get('price', '---'), "link": "#"}]
        for i, off in enumerate(offers):
            logo = STORE_LOGOS.get(off['store'])
            cl1, cl2, cl3 = st.columns([3, 2, 2])
            with cl1:
                if logo: st.markdown(f"<div style='display:flex;align-items:center;'><img src='{logo}' width='24' style='margin-right:8px;'><b>{off['store']}</b></div>", unsafe_allow_html=True)
                else: st.write(f"**{off['store']}**")
            with cl2: st.markdown(f"<span class='price-big'>{off['price']} TL</span>", unsafe_allow_html=True)
            with cl3: st.link_button("Satın Al", off['link'], type="primary")
            st.divider()
    st.markdown("---")
    if media_list:
        st.subheader("🎬 Medya Galerisi")
        for i in range(0, min(len(media_list), 6), 3):
            cols = st.columns(3)
            for j in range(3):
                idx = i + j
                if idx < len(media_list):
                    item = media_list[idx]
                    with cols[j]:
                        st.image(item['thumb'], use_container_width=True)
                        icon = "▶️ Oynat" if item['type'] == 'video' else "🔍 Büyüt"
                        if st.button(f"{icon}", key=f"gal_{idx}", use_container_width=True): show_gallery_modal(media_list, start_idx=idx)
            st.write("")
    if req_min != "Bilgi yok.":
        st.write("")
        st.subheader("💻 Sistem Gereksinimleri")
        rq1, rq2 = st.columns(2)
        with rq1:
            st.markdown("<div class='req-box'><div class='req-title'>Minimum</div>", unsafe_allow_html=True)
            st.markdown(req_min, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with rq2:
            st.markdown("<div class='req-box'><div class='req-title'>Önerilen</div>", unsafe_allow_html=True)
            if req_rec: st.markdown(req_rec, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

# SAYFA: ARAMA
elif st.session_state.active_page == 'search':
    term = st.session_state.search_term
    st.info(f"🔎 '{term}' aranıyor...")
    corrected = autocorrect_name(term)
    url = f"https://www.cheapshark.com/api/1.0/deals?title={corrected}&exact=0&limit=60"
    try:
        deals = requests.get(url).json()
        grouped = {}
        s_map = { "1": "Steam", "25": "Epic Games", "7": "GOG", "8": "EA App", "13": "Ubisoft Connect" }
        for deal in deals:
            if deal['storeID'] in s_map:
                title = clean_game_title(deal['title'])
                if title not in grouped:
                    sort_score = calculate_sort_score(title, corrected)
                    grouped[title] = {
                        "title": deal['title'],
                        "thumb": get_game_image(deal),
                        "meta": int(deal['metacriticScore']),
                        "user": int(deal['steamRatingPercent']),
                        "offers": [],
                        "steamAppID": deal.get('steamAppID'),
                        "sort_score": sort_score
                    }
                if deal.get('steamAppID') and not grouped[title].get('steamAppID'):
                    grouped[title]['steamAppID'] = deal.get('steamAppID')
                    grouped[title]['thumb'] = get_game_image(deal)
                s_name = s_map[deal['storeID']]
                p_usd = float(deal['salePrice'])
                final_link = f"https://www.cheapshark.com/redirect?dealID={deal['dealID']}"
                if s_name == "Steam" and deal.get('steamAppID'):
                    price_val, curr = get_steam_turkey_price(deal.get('steamAppID'))
                    if price_val: p_usd = price_val
                elif s_name == "Epic Games":
                    ep_p, _, ep_l = get_epic_price_local(deal['title'])
                    if ep_p: p_usd = ep_p
                price_final = int(p_usd) if s_name in ["Steam", "Epic Games"] else int(p_usd * dolar_kuru)
                grouped[title]["offers"].append({"store": s_name, "price": price_final, "link": final_link})
        
        if not grouped:
            for sub, games in SUBSCRIPTIONS.items():
                for g_name in games:
                    if term.lower() in g_name.lower():
                        img_url = fetch_best_image(g_name)
                        thumb = img_url if img_url else PLACEHOLDER_IMG
                        grouped[g_name.title()] = {
                            "title": g_name.title(), "thumb": thumb,
                            "meta": 0, "user": 0, "sort_score": 0, "offers": [], "steamAppID": "0"
                        }

        if grouped:
            st.success(f"✅ {len(grouped)} oyun bulundu.")
            g_list = sorted(grouped.values(), key=lambda x: (x['sort_score'], min([o['price'] for o in x['offers']] if x['offers'] else [99999])))
            for i, game in enumerate(g_list):
                with st.container():
                    c1, c2, c3 = st.columns([1.5, 2.5, 3])
                    with c1: st.image(game['thumb'], use_container_width=True)
                    with c2: 
                        st.subheader(game['title'])
                        sub_n, sub_cls = check_subscription(game['title'])
                        if sub_n:
                            st.markdown(f"<span class='badge-container {sub_cls}'>{sub_n} DAHİL</span>", unsafe_allow_html=True)
                            if st.button(f"Listeye Git ({sub_n})", key=f"src_sub_{game['title']}_{i}"): go_category(sub_n, None, None, True)
                        st.write("")
                        if game['meta']>0: 
                            mc=get_meta_color(game['meta'])
                            st.markdown(f"<span class='score-badge {mc}'>Meta: {game['meta']}</span>", unsafe_allow_html=True)
                    with c3:
                        st.write("**Fiyatlar**")
                        s_offers = sorted(game['offers'], key=lambda x: x['price'])
                        if s_offers:
                            for off in s_offers:
                                l_url = STORE_LOGOS.get(off['store'])
                                cc1, cc2, cc3 = st.columns([3, 2, 2])
                                with cc1: 
                                    if l_url: st.image(l_url, width=20)
                                    else: st.write(off['store'])
                                with cc2: st.markdown(f"<span class='price-big'>{off['price']} TL</span>", unsafe_allow_html=True)
                                with cc3: st.link_button("Git", off['link'])
                                st.divider()
                        else: st.caption("Henüz mağaza fiyatı yok.")
                        
                        # BENZERSİZ KEY
                        if st.button("🔍 Detaylı İncele", key=f"src_dt_{game['title']}_{i}"): go_detail(game)
                    st.markdown("---")
        else: st.warning("Sonuç bulunamadı.")
    except Exception as e: st.error(str(e))
