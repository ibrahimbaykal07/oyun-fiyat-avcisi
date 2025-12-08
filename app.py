import streamlit as st
import requests
import xml.etree.ElementTree as ET
import streamlit.components.v1 as components
from datetime import datetime

# --- 1. AYARLAR ---
st.set_page_config(page_title="Oyun Fiyatı (TR)", page_icon="🇹🇷", layout="centered")

# Yedek Resim
PLACEHOLDER_IMG = "https://placehold.co/600x900/1a1a1a/FFFFFF/png?text=Gorsel+Yok"

# Epic Store Kütüphanesi
try:
    from epicstore_api import EpicGamesStoreAPI
    EPIC_AVAILABLE = True
except ImportError:
    EPIC_AVAILABLE = False

# --- CSS STİLİ ---
st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    .kur-kutusu { background-color: #f8f9fa; padding: 8px 15px; border-radius: 8px; font-weight: bold; color: #495057; font-size: 0.9em; text-align: center; border: 1px solid #dee2e6; }
    
    div[data-testid="stImage"] img { border-radius: 8px; aspect-ratio: 2/3; object-fit: cover; }
    
    .vitrin-title { font-size: 0.9em; font-weight: bold; margin-top: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: #333; }
    .vitrin-price { font-size: 1.1em; font-weight: bold; color: #28a745; margin: 2px 0; }
    .vitrin-date { font-size: 0.75em; color: #666; margin-bottom: 5px; font-style: italic; }
    
    .detail-title { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 2.5em; font-weight: 800; margin-bottom: 10px; color: #FFFFFF !important; line-height: 1.2; }
    .desc-box { background-color: transparent; color: #FFFFFF !important; padding: 0; border: none; line-height: 1.6; font-size: 1.05em; margin-bottom: 20px; }
    
    /* ABONELİK KARTI */
    .sub-card {
        display: flex;
        align-items: center;
        background: linear-gradient(90deg, #1c1c1c, #2a2a2a);
        border-left: 5px solid #555;
        padding: 10px 15px;
        border-radius: 0 8px 8px 0;
        margin-top: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        color: white;
        font-family: sans-serif;
    }
    .sub-text { font-weight: bold; font-size: 0.9em; margin-left: 10px; letter-spacing: 0.5px; text-transform: uppercase; }
    
    .req-box { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #e9ecef; font-size: 0.9em; height: 100%; }
    .req-title { font-weight: bold; margin-bottom: 10px; color: #333; font-size: 1.1em; border-bottom: 2px solid #ddd; padding-bottom: 5px; }
    .price-big { font-size: 1.2em; font-weight: bold; color: #28a745; }
    .score-badge { font-size: 0.8em; padding: 4px 8px; border-radius: 4px; color: white; font-weight: bold; margin-right: 5px; display:inline-block;}
    .meta-green { background-color: #6c3; }
    .meta-yellow { background-color: #fc3; color: #333; }
    .meta-red { background-color: #f00; }
    .user-blue { background-color: #1b2838; border: 1px solid #66c0f4; color: #66c0f4; }
    .stButton button { width: 100%; }
</style>
""", unsafe_allow_html=True)

# --- 2. LOGOLAR & RENKLER ---
STORE_LOGOS = {
    "Steam": "https://cdn.simpleicons.org/steam/171a21",
    "Epic Games": "https://cdn.simpleicons.org/epicgames/333333",
    "Ubisoft Connect": "https://cdn.simpleicons.org/ubisoft/0099FF",
    "EA App": "https://cdn.simpleicons.org/ea/FF4747",
    "GOG": "https://cdn.simpleicons.org/gogdotcom/893CE7"
}

# Abonelik Logoları
SUB_LOGOS = {
    "Game Pass": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Xbox_Game_Pass_2020_logo_-_alternative_version_%28colored%29.svg/512px-Xbox_Game_Pass_2020_logo_-_alternative_version_%28colored%29.svg.png",
    "EA Play": "https://cdn.simpleicons.org/ea/FF4747", 
    "EA Play Pro": "https://cdn.simpleicons.org/ea/FF4747", # Pro için de EA logosu kullanıyoruz ama rengi farklı olacak
    "Ubisoft+": "https://cdn.simpleicons.org/ubisoft/0057ff"
}

# Abonelik Renk Kodları (Kartın sol çizgisi için)
SUB_COLORS = {
    "Game Pass": "#107C10",   # Yeşil
    "EA Play": "#FF4747",     # Kırmızı
    "EA Play Pro": "#FFD700", # Altın (Pro Farkı)
    "Ubisoft+": "#0099FF"     # Mavi
}

# --- 3. VERİTABANI (SUBSCRIPTION DATABASE) ---
# Burası oyunların hangi sistemde olduğunu tutar.
# EA Play Pro'ya en yeni oyunları, Normal EA Play'e eskileri ekliyoruz.
SUBSCRIPTIONS = {
    "Game Pass": [
        "call of duty", "black ops 6", "modern warfare iii", "diablo 4", "starfield", 
        "forza horizon 5", "forza motorsport", "halo infinite", "halo: the master chief collection",
        "minecraft", "flight simulator", "lies of p", "palworld", "hellblade", 
        "senua's saga", "stalker 2", "indiana jones", "avowed", "sea of thieves", 
        "doom eternal", "gears 5", "atomic heart", "high on life", "persona 3 reload",
        "yakuza", "like a dragon", "wo long", "hollow knight", "expedition 33", "fable",
        "assassin's creed origins", "assassin's creed odyssey" # Ubisoft oyunları bazen GamePass'te de olur
    ],
    "EA Play Pro": [
        "fc 25", "f1 24", "madden nfl 25", "star wars jedi: survivor", 
        "immortals of aveum", "wild hearts", "dead space remake"
    ],
    "EA Play": [
        "fc 24", "fifa 23", "fifa 22", "battlefield 2042", "battlefield v", "battlefield 1", 
        "battlefield 4", "star wars jedi: fallen order", "star wars battlefront",
        "the sims 4", "titanfall 2", "mass effect legendary edition", "dragon age",
        "need for speed unbound", "need for speed heat", "it takes two", "a way out",
        "mirrors edge", "crysis", "apex legends", "skate", "f1 23"
    ],
    "Ubisoft+": [
        "assassin's creed mirage", "assassin's creed valhalla", "assassin's creed odyssey",
        "assassin's creed origins", "assassin's creed shadows", "avatar: frontiers of pandora",
        "prince of persia: the lost crown", "far cry 6", "far cry 5", "far cry new dawn",
        "the crew motorfest", "the crew 2", "rainbow six siege", "rainbow six extraction",
        "skull and bones", "riders republic", "watch dogs legion", "watch dogs 2",
        "tom clancy's the division 2", "ghost recon breakpoint", "ghost recon wildlands",
        "immortals fenyx rising", "for honor", "anno 1800", "monopoly"
    ]
}

# --- 4. SESSION STATE ---
if 'active_page' not in st.session_state: st.session_state.active_page = 'home'
if 'page_number' not in st.session_state: st.session_state.page_number = 0
if 'selected_cat' not in st.session_state: st.session_state.selected_cat = None
if 'selected_game' not in st.session_state: st.session_state.selected_game = None
if 'search_term' not in st.session_state: st.session_state.search_term = ""
if 'gallery_idx' not in st.session_state: st.session_state.gallery_idx = 0
if 'home_limits' not in st.session_state: st.session_state.home_limits = {"p1": 4, "p2": 4, "p3": 4}

# --- 5. YARDIMCI FONKSİYONLAR ---

def scroll_to_top():
    js = """<script>var body = window.parent.document.querySelector(".main"); body.scrollTop = 0;</script>"""
    components.html(js, height=0)

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

def get_dollar_rate():
    try:
        r = requests.get("https://www.tcmb.gov.tr/kurlar/today.xml", timeout=2)
        root = ET.fromstring(r.content)
        for c in root.findall('Currency'):
            if c.get('Kod') == 'USD': return float(c.find('ForexSelling').text)
    except: return 36.50

def get_game_image(deal):
    sid = deal.get('steamAppID')
    if sid and sid != "0": return f"https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/{sid}/library_600x900.jpg"
    thumb = deal.get('thumb')
    if thumb: return thumb
    return PLACEHOLDER_IMG

def get_meta_color(score):
    if score >= 75: return "meta-green"
    elif score >= 50: return "meta-yellow"
    else: return "meta-red"

def check_subscription(game_name):
    """Oyunun hangi abonelikte olduğunu kontrol eder. PRO önceliklidir."""
    s = game_name.lower()
    
    # 1. Önce EA Play Pro kontrolü (Çünkü Pro, Normalden daha özeldir)
    if any(x in s for x in SUBSCRIPTIONS["EA Play Pro"]):
        return "EA Play Pro", SUB_LOGOS["EA Play Pro"]
        
    # 2. Sonra Diğerleri
    for sub_name, games_list in SUBSCRIPTIONS.items():
        if sub_name == "EA Play Pro": continue # Zaten baktık
        for g in games_list:
            if g in s:
                return sub_name, SUB_LOGOS[sub_name]
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
    d = {"gta": "Grand Theft Auto", "gta 5": "Grand Theft Auto V", "cod": "Call of Duty", "fc 25": "EA SPORTS FC 25", "mc": "Minecraft", "cp": "Cyberpunk 2077"}
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

# --- 6. NAVİGASYON ---
def go_home():
    st.session_state.active_page = 'home'
    st.session_state.page_number = 0
    st.session_state.home_limits = {"p1": 4, "p2": 4, "p3": 4}
    st.rerun()

def go_category(name, sort, sale):
    st.session_state.selected_cat = {"name": name, "sort": sort, "sale": sale}
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

# --- 7. VERİ MOTORU ---
def fetch_vitrin_deals(sort_by, on_sale=0, page=0, page_size=24):
    url = f"https://www.cheapshark.com/api/1.0/deals?storeID=1,25&sortBy={sort_by}&onSale={on_sale}&pageSize={page_size}&pageNumber={page}"
    if sort_by == "Release":
        url = f"https://www.cheapshark.com/api/1.0/deals?storeID=1,25&sortBy=Release&onSale={on_sale}&pageSize={page_size}&pageNumber={page}&desc=1"
    if sort_by == "Metacritic": url += "&upperPrice=60&metacritic=70"
    
    try:
        data = requests.get(url).json()
        results = []
        for d in data:
            s_name = "Steam" if d['storeID'] == "1" else "Epic Games"
            price_tl = int(float(d['salePrice']) * dolar_kuru)
            offer = {"store": s_name, "price": price_tl, "link": f"https://www.cheapshark.com/redirect?dealID={d['dealID']}", "discount": float(d['savings'])}
            results.append({
                "title": d['title'],
                "thumb": get_game_image(d),
                "meta": int(d['metacriticScore']),
                "user": int(d['steamRatingPercent']),
                "dealID": d['dealID'],
                "steamAppID": d.get('steamAppID'),
                "price": price_tl,
                "discount": float(d['savings']),
                "offers": [offer],
                "store": s_name,
                "releaseDate": d.get('releaseDate', 0)
            })
        if sort_by == "Release": results.sort(key=lambda x: x['releaseDate'], reverse=True)
        return results
    except: return []

# ================= ARAYÜZ BAŞLIYOR =================
scroll_to_top()
dolar_kuru = get_dollar_rate()

h1, h2, h3 = st.columns([1.5, 4, 1.5])
with h1:
    if st.button("🏠 Ana Sayfa"): go_home()
with h2:
    c_pop, c_sale, c_new = st.columns(3)
    if c_pop.button("🏆 Popüler"): go_category("En Popüler", "Metacritic", 0)
    if c_sale.button("🔥 İndirim"): go_category("Süper İndirimler", "Savings", 1)
    if c_new.button("✨ Yeni"): go_category("Yeni Çıkanlar", "Release", 0)
with h3:
    st.markdown(f"<div class='kur-kutusu'>💲 {dolar_kuru:.2f} TL</div>", unsafe_allow_html=True)

st.divider()

with st.form(key='global_search'):
    ci, cb = st.columns([4, 1])
    with ci: s_val = st.text_input("Oyun Ara", placeholder="Oyun ismi yazın...", label_visibility="collapsed")
    with cb: s_btn = st.form_submit_button("🔎 Bul")

if s_btn and s_val:
    st.session_state.search_term = s_val
    st.session_state.active_page = 'search'
    st.rerun()

# ================= SAYFA 1: ANA SAYFA =================
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
                        if st.button("İncele", key=f"btn_{g['dealID']}"): go_detail(g)
            st.write("")
        if st.button(f"➕ {title} - Daha Fazla Göster", key=f"more_{limit_key}"):
            increase_home_limit(limit_key)
        st.markdown("---")

# ================= SAYFA 2: KATEGORİ =================
elif st.session_state.active_page == 'category':
    cat = st.session_state.selected_cat
    curr_page = st.session_state.page_number
    st.subheader(f"{cat['name']}")
    games = fetch_vitrin_deals(cat['sort'], on_sale=cat['sale'], page=curr_page, page_size=24)
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
                        if st.button("İncele", key=f"cat_btn_{g['dealID']}"): go_detail(g)
            st.write("")
        st.markdown("---")
        pg_cols = st.columns(7)
        start_p = max(0, curr_page - 3)
        for i in range(7):
            p_num = start_p + i
            with pg_cols[i]:
                b_type = "primary" if p_num == curr_page else "secondary"
                if st.button(f"{p_num + 1}", key=f"pg_{p_num}", type=b_type): set_page_num(p_num)
    else: st.info("Bu sayfada oyun yok.")

# ================= SAYFA 3: DETAY (ABONELİK ÖNCELİKLİ) =================
elif st.session_state.active_page == 'detail':
    game = st.session_state.selected_game
    desc, media_list, req_min, req_rec = get_steam_details_turkish(game.get('steamAppID'))
    c1, c2 = st.columns([1.5, 2.5])
    with c1:
        st.image(game['thumb'], use_container_width=True)
        # --- ABONELİK (RENKLİ & ŞIK) ---
        sub_n, sub_l = check_subscription(game['title'])
        if sub_n:
            border_c = SUB_COLORS.get(sub_n, "#555")
            st.markdown(f"""<div class='sub-card' style='border-left-color: {border_c};'><img src='{sub_l}' height='30'><span class='sub-text'>DAHİL</span></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<h1 class='detail-title'>{game['title']}</h1>", unsafe_allow_html=True)
        mc = get_meta_color(game['meta'])
        st.markdown(f"""<div style="margin-bottom:15px;"><span class='score-badge {mc}'>Metacritic: {game['meta']}</span><span class='score-badge user-blue'>Steam User: %{game['user']}</span></div>""", unsafe_allow_html=True)
        if desc: st.markdown(f"<div class='desc-box'>{desc}</div>", unsafe_allow_html=True)
        st.write("### 🏷️ Mağaza Fiyatları")
        offers = game.get('offers', [])
        if not offers: offers = [{"store": game['store'], "price": game['price'], "link": f"https://www.cheapshark.com/redirect?dealID={game['dealID']}"}]
        for off in offers:
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
        st.subheader("🎬 Medya Galerisi (Fragman & Resim)")
        display_limit = 6
        for i in range(0, min(len(media_list), display_limit), 3):
            cols = st.columns(3)
            for j in range(3):
                idx = i + j
                if idx < len(media_list):
                    item = media_list[idx]
                    with cols[j]:
                        st.image(item['thumb'], use_container_width=True)
                        icon = "▶️ Oynat" if item['type'] == 'video' else "🔍 Büyüt"
                        if st.button(f"{icon}", key=f"gal_{idx}", use_container_width=True):
                            show_gallery_modal(media_list, start_idx=idx)
            st.write("")
    st.write("")
    if req_min != "Bilgi yok." or req_rec != "Bilgi yok.":
        st.subheader("💻 Sistem Gereksinimleri")
        rq1, rq2 = st.columns(2)
        with rq1:
            st.markdown("<div class='req-box'><div class='req-title'>Minimum</div>", unsafe_allow_html=True)
            if req_min: st.markdown(req_min, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with rq2:
            st.markdown("<div class='req-box'><div class='req-title'>Önerilen</div>", unsafe_allow_html=True)
            if req_rec: st.markdown(req_rec, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

# ================= SAYFA 4: ARAMA =================
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
                is_local_tl = False
                final_link = f"https://www.cheapshark.com/redirect?dealID={deal['dealID']}"
                if s_name == "Steam" and deal.get('steamAppID'):
                    price_val, curr = get_steam_turkey_price(deal.get('steamAppID'))
                    if price_val:
                        p_usd = price_val
                        final_link = f"https://store.steampowered.com/app/{deal['steamAppID']}/"
                        if curr == "TRY": is_local_tl = True
                elif s_name == "Epic Games":
                    ep_p, _, ep_l = get_epic_price_local(deal['title'])
                    if ep_p: 
                        p_usd = ep_p
                        is_local_tl = True
                        if ep_l: final_link = ep_l
                price_final = int(p_usd) if is_local_tl else int(p_usd * dolar_kuru)
                grouped[title]["offers"].append({
                    "store": s_name, "price": price_final, "link": final_link
                })
        if grouped:
            st.success(f"✅ {len(grouped)} oyun bulundu.")
            g_list = sorted(grouped.values(), key=lambda x: (x['sort_score'], min(o['price'] for o in x['offers'])))
            for game in g_list:
                with st.container():
                    c1, c2, c3 = st.columns([1.5, 2.5, 3])
                    with c1: st.image(game['thumb'], use_container_width=True)
                    with c2: 
                        st.subheader(game['title'])
                        sub_n, sub_l = check_subscription(game['title'])
                        if sub_n:
                            border_c = SUB_COLORS.get(sub_n, "#555")
                            st.markdown(f"""<div class='sub-card' style='border-left-color: {border_c}; margin-top:0;'><img src='{sub_l}' height='24'><span class='sub-text'>DAHİL</span></div>""", unsafe_allow_html=True)
                        st.write("")
                        if game['meta']>0: 
                            mc=get_meta_color(game['meta'])
                            st.markdown(f"<span class='score-badge {mc}'>Meta: {game['meta']}</span>", unsafe_allow_html=True)
                        if game['user']>0:
                            st.markdown(f"<span class='score-badge user-blue'>Steam: %{game['user']}</span>", unsafe_allow_html=True)
                    with c3:
                        st.write("**Fiyatlar**")
                        s_offers = sorted(game['offers'], key=lambda x: x['price'])
                        for off in s_offers:
                            l_url = STORE_LOGOS.get(off['store'])
                            cc1, cc2, cc3 = st.columns([3, 2, 2])
                            with cc1: 
                                if l_url: st.image(l_url, width=20)
                                else: st.write(off['store'])
                            with cc2: st.markdown(f"<span class='price-big'>{off['price']} TL</span>", unsafe_allow_html=True)
                            with cc3: st.link_button("Git", off['link'])
                            st.divider()
                        if st.button("🔍 Detaylı İncele", key=f"src_dt_{game['title']}"): go_detail(game)
                    st.markdown("---")
        else: st.warning("Sonuç bulunamadı.")
    except Exception as e: st.error(str(e))
