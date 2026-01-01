import streamlit as st
import pandas as pd
import requests

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="Oyun Fiyat Avcısı",
    page_icon="🔥",
    layout="wide"
)

# --- CSS İLE GÖRÜNÜMÜ İYİLEŞTİRME ---
st.markdown("""
<style>
    .stButton button {
        width: 100%;
        border-radius: 10px;
        font-weight: bold;
    }
    .price-tag {
        font-size: 24px;
        font-weight: bold;
        color: #2e7d32;
    }
    .store-name {
        font-size: 18px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# --- BAŞLIK ---
st.title("🔥 Dev Oyun Fiyat Karşılaştırma")
st.markdown("Oyunun adını yazın, **Steam, Epic, Xbox** ve diğer mağazalardaki fiyatları dev resimlerle görün.")
st.divider()

# --- FONKSİYONLAR ---

@st.cache_data(ttl=3600)
def get_usd_rate():
    """Güncel Dolar kurunu çeker."""
    try:
        url = "https://open.er-api.com/v6/latest/USD"
        response = requests.get(url, timeout=5)
        data = response.json()
        return data["rates"]["TRY"]
    except:
        return 35.0 

@st.cache_data(ttl=86400)
def get_stores():
    """Mağaza bilgilerini çeker."""
    try:
        url = "https://www.cheapshark.com/api/1.0/stores"
        response = requests.get(url)
        stores = response.json()
        return {store['storeID']: store['storeName'] for store in stores}
    except:
        return {}

def search_game_deals(game_name, usd_rate, store_map):
    """Oyun ismine göre arama yapar."""
    # CheapShark üzerinden arama
    search_url = f"https://www.cheapshark.com/api/1.0/games?title={game_name}"
    try:
        response = requests.get(search_url)
        games = response.json()
        
        if not games:
            return None

        results = []
        
        # İlk 10 sonucu getir
        for game in games[:10]:
            game_id = game['gameID']
            title = game['external']
            thumb = game['thumb'] # Küçük resim yerine detaydan büyüğünü almaya çalışacağız
            
            # Detayları çek
            details_url = f"https://www.cheapshark.com/api/1.0/games?id={game_id}"
            details_resp = requests.get(details_url)
            details = details_resp.json()
            
            # En iyi görüntü kalitesi için görseli değiştirmeyi deneyelim
            # CheapShark bazen küçük resim verir, Steam ID varsa Steam görselini alırız
            image_url = thumb
            if 'info' in details and 'steamAppID' in details['info']:
                steam_id = details['info']['steamAppID']
                if steam_id:
                    image_url = f"https://cdn.cloudflare.steamstatic.com/steam/apps/{steam_id}/header.jpg"

            deals = details.get('deals', [])
            store_prices = []
            
            # Hedef Mağazalar
            target_stores = ['Steam', 'Epic Games Store', 'Microsoft Store', 'GOG', 'Origin', 'Uplay']
            
            for deal in deals:
                store_id = deal['storeID']
                store_name = store_map.get(store_id, "Diğer")
                
                if store_name in target_stores:
                    price_usd = float(deal['price'])
                    price_tl = price_usd * usd_rate
                    
                    store_prices.append({
                        "store": store_name,
                        "price_tl": price_tl,
                        "price_usd": price_usd,
                        # Epic linklerini manuel düzeltme (API bazen bozuk link verir)
                        "link": f"https://www.cheapshark.com/redirect?dealID={deal['dealID']}"
                    })
            
            # Eğer hiç fiyat bulamadıysa bile oyunu listeye ekle (manuel link vermek için)
            results.append({
                "title": title,
                "image": image_url,
                "prices": store_prices
            })
                
        return results

    except Exception as e:
        st.error(f"Hata: {e}")
        return None

# --- ARAYÜZ ---

usd_rate = get_usd_rate()
store_mapping = get_stores()

search_query = st.text_input("Hangi oyunu arıyorsunuz?", placeholder="Örn: FIFA 24, God of War, Red Dead Redemption 2...")

if search_query:
    with st.spinner(f"'{search_query}' için tüm mağazalar taranıyor..."):
        found_games = search_game_deals(search_query, usd_rate, store_mapping)
        
    if found_games:
        st.success(f"Güncel Kur: 1$ = {usd_rate:.2f} TL (Fiyatlar tahmini çeviridir)")
        
        for game in found_games:
            # KONTEYNER TASARIMI
            with st.container(border=True):
                # Sütun Oranlarını Değiştirdim: [1.5, 2.5] -> Resim Alanı Genişletildi
                col_img, col_info = st.columns([1.5, 2.5])
                
                with col_img:
                    # use_container_width=True resmi sütuna sığacak kadar büyütür
                    if game['image']:
                        st.image(game['image'], use_container_width=True)
                    else:
                        st.write("Resim Yok")
                
                with col_info:
                    st.header(game['title'])
                    
                    if game['prices']:
                        # Fiyatları listele
                        for price in game['prices']:
                            c1, c2, c3 = st.columns([2, 2, 2])
                            with c1:
                                st.markdown(f"<span class='store-name'>{price['store']}</span>", unsafe_allow_html=True)
                            with c2:
                                st.markdown(f"<span class='price-tag'>{price['price_tl']:.0f} ₺</span>", unsafe_allow_html=True)
                                st.caption(f"({price['price_usd']} $)")
                            with c3:
                                st.link_button("Mağazaya Git 🔗", price['link'])
                            st.divider()
                    else:
                        st.warning("Bu oyun için CheapShark veritabanında anlık fiyat bilgisi yok.")
                        # Fiyat yoksa bile manuel arama butonları koyalım
                        e_col1, e_col2 = st.columns(2)
                        with e_col1:
                             st.link_button("Steam'de Ara", f"https://store.steampowered.com/search/?term={game['title']}")
                        with e_col2:
                             st.link_button("Epic Games'te Ara", f"https://store.epicgames.com/tr/browse?q={game['title']}&sortBy=relevancy")

    else:
        st.warning("Oyun bulunamadı. Tam adını yazmayı deneyin.")
else:
    st.info("Arama yapmak için yukarıya oyun adını yazıp Enter'a basın.")
