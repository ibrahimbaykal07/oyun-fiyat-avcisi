import streamlit as st
import requests
from epicstore_api import EpicGamesStoreAPI

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Pro Oyun Fiyat Avcısı", page_icon="🚀", layout="wide")

# CSS İyileştirmesi
st.markdown("""
<style>
    .big-font { font-size:20px !important; font-weight: bold; }
    .price-box { background-color: #f0f2f6; padding: 10px; border-radius: 10px; border: 1px solid #ddd; }
    .epic-price { color: #0078f2; font-size: 24px; font-weight: bold; }
    .steam-price { color: #1b2838; font-size: 24px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("🚀 Gerçek Zamanlı Steam & Epic Fiyat Karşılaştırma")
st.write("Bu modül, **Epic Games Store** ve **Steam** sunucularına doğrudan bağlanır.")
st.divider()

# --- FONKSİYONLAR ---

@st.cache_data(ttl=3600)
def get_usd_rate():
    """Dolar kurunu al"""
    try:
        r = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5).json()
        return r["rates"]["TRY"]
    except:
        return 35.0

def search_epic_price(game_name):
    """Epic Games Store'dan doğrudan TL fiyatı çeker"""
    try:
        api = EpicGamesStoreAPI()
        # Oyunu arat
        games = api.fetch_store_games(
            keywords=game_name,
            sort_dir="DESC",
            sort_by="relevancy",
            count=1
        )
        
        elements = games.get('data', {}).get('Catalog', {}).get('searchStore', {}).get('elements', [])
        
        if elements:
            game_data = elements[0]
            title = game_data.get('title')
            
            # Fiyat verisine ulaşmak biraz karmaşık (JSON içinde gömülü)
            price_info = game_data.get('price', {}).get('totalPrice', {})
            original_price = price_info.get('originalPrice', 0) / 100 # Kuruş hesabı
            discount_price = price_info.get('discountPrice', 0) / 100
            currency = price_info.get('currencyCode')
            
            # Resim bulma
            image = None
            for img in game_data.get('keyImages', []):
                if img.get('type') == 'OfferImageWide':
                    image = img.get('url')
                    break
            if not image and game_data.get('keyImages'):
                image = game_data['keyImages'][0]['url']

            # Ürün linki (Slug üzerinden)
            product_slug = game_data.get('productSlug')
            # Bazen slug boş olabilir, catalogNs kullanırız
            if not product_slug:
                product_slug = game_data.get('urlSlug')
                
            link = f"https://store.epicgames.com/tr/p/{product_slug}" if product_slug else "https://store.epicgames.com/tr/"

            return {
                "source": "Epic Games",
                "title": title,
                "price": discount_price,
                "original_price": original_price,
                "currency": currency, # Genelde TRY gelir
                "image": image,
                "link": link
            }
        return None
    except Exception as e:
        print(f"Epic Hatası: {e}")
        return None

def search_steam_price(game_name, usd_rate):
    """CheapShark üzerinden Steam fiyatı ve görseli"""
    try:
        url = f"https://www.cheapshark.com/api/1.0/games?title={game_name}"
        resp = requests.get(url).json()
        
        if resp:
            # En alakalı sonucu al
            game_id = resp[0]['gameID']
            thumb = resp[0]['thumb']
            
            # Detayları çek
            details = requests.get(f"https://www.cheapshark.com/api/1.0/games?id={game_id}").json()
            steam_deal = None
            
            # Sadece Steam (Store ID 1) olanı bul
            for deal in details.get('deals', []):
                if deal['storeID'] == "1":
                    steam_deal = deal
                    break
            
            if steam_deal:
                price_usd = float(steam_deal['price'])
                price_tl = price_usd * usd_rate
                return {
                    "source": "Steam",
                    "price_tl": price_tl,
                    "price_usd": price_usd,
                    "link": f"https://store.steampowered.com/app/{details['info'].get('steamAppID')}",
                    "image": f"https://cdn.cloudflare.steamstatic.com/steam/apps/{details['info'].get('steamAppID')}/header.jpg"
                }
        return None
    except:
        return None

# --- ARAYÜZ ---

game_query = st.text_input("Oyun Adı Girin:", placeholder="Örn: FC 24, Cyberpunk 2077...")
if st.button("Fiyatları Getir") or game_query:
    
    if game_query:
        usd_rate = get_usd_rate()
        
        col1, col2 = st.columns(2)
        
        with st.spinner('Epic Games ve Steam taranıyor...'):
            # İki fonksiyonu da çalıştır
            epic_data = search_epic_price(game_query)
            steam_data = search_steam_price(game_query, usd_rate)
        
        # --- GÖRÜNTÜLEME ---
        
        if epic_data or steam_data:
            # Ortak bir başlık veya resim kullanalım (Epic resmi daha kalitelidir genelde)
            main_image = epic_data['image'] if epic_data else steam_data['image']
            game_title = epic_data['title'] if epic_data else game_query
            
            st.image(main_image, use_container_width=True)
            st.header(f"Sonuçlar: {game_title}")
            
            # Fiyatları Yan Yana Kıyasla
            c1, c2 = st.columns(2)
            
            # SOL KUTU: EPIC GAMES
            with c1:
                st.markdown('<div class="price-box">', unsafe_allow_html=True)
                st.image("https://upload.wikimedia.org/wikipedia/commons/3/31/Epic_Games_logo.svg", width=50)
                st.subheader("Epic Games Store")
                if epic_data:
                    fiyat = epic_data['price']
                    if fiyat == 0:
                        st.markdown(f"<span class='epic-price'>ÜCRETSİZ</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<span class='epic-price'>{fiyat:.2f} ₺</span>", unsafe_allow_html=True)
                    
                    if epic_data['original_price'] > fiyat:
                        st.caption(f"Normalde: {epic_data['original_price']:.2f} ₺")
                        
                    st.link_button("Epic'ten Al", epic_data['link'])
                else:
                    st.warning("Epic'te bulunamadı.")
                st.markdown('</div>', unsafe_allow_html=True)

            # SAĞ KUTU: STEAM
            with c2:
                st.markdown('<div class="price-box">', unsafe_allow_html=True)
                st.image("https://upload.wikimedia.org/wikipedia/commons/8/83/Steam_icon_logo.svg", width=50)
                st.subheader("Steam (TR)")
                if steam_data:
                    st.markdown(f"<span class='steam-price'>{steam_data['price_tl']:.2f} ₺</span>", unsafe_allow_html=True)
                    st.caption(f"({steam_data['price_usd']} USD x {usd_rate:.2f})")
                    st.link_button("Steam'den Al", steam_data['link'])
                else:
                    st.warning("Steam'de bulunamadı.")
                st.markdown('</div>', unsafe_allow_html=True)
                
            # Kazananı Belirle
            st.divider()
            if epic_data and steam_data:
                fark = abs(epic_data['price'] - steam_data['price_tl'])
                if epic_data['price'] < steam_data['price_tl']:
                    st.success(f"🎉 **Epic Games** şu an **{fark:.2f} TL** daha ucuz!")
                elif steam_data['price_tl'] < epic_data['price']:
                    st.success(f"🎉 **Steam** şu an **{fark:.2f} TL** daha ucuz!")
                else:
                    st.info("İki platformda da fiyatlar yaklaşık aynı.")
                    
        else:
            st.error("Oyun hiçbir mağazada bulunamadı. İsmi doğru yazdığınızdan emin olun.")
