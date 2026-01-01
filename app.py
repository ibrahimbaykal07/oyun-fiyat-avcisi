import streamlit as st
import pandas as pd
import requests

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="Oyun Fiyat Karşılaştırma",
    page_icon="🔍",
    layout="wide"
)

# --- BAŞLIK ---
st.title("🔍 Dijital Oyun Fiyat Arama Motoru")
st.markdown("İstediğiniz oyunun adını yazın, **Steam, Epic, GOG, Ubisoft ve EA** fiyatlarını TL karşılığıyla karşılaştırın.")
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
        return 35.0 # Varsayılan güvenlik kuru

@st.cache_data(ttl=86400)
def get_stores():
    """Mağaza ID'lerini ve isimlerini (Logo vb) çeker."""
    # Hangi ID'nin hangi mağaza olduğunu bilmemiz lazım (Store 1 = Steam, Store 25 = Epic vb.)
    try:
        url = "https://www.cheapshark.com/api/1.0/stores"
        response = requests.get(url)
        stores = response.json()
        store_map = {store['storeID']: store['storeName'] for store in stores}
        # Logoları da alabiliriz ama şimdilik isimler yeterli
        return store_map
    except:
        return {}

def search_game_deals(game_name, usd_rate, store_map):
    """Oyun ismine göre arama yapar ve mağaza fiyatlarını getirir."""
    # 1. Adım: Oyunu ismen arat
    search_url = f"https://www.cheapshark.com/api/1.0/games?title={game_name}"
    try:
        response = requests.get(search_url)
        games = response.json()
        
        if not games:
            return None

        results = []
        
        # İlk 5 sonucu getir (Çok fazla sonuç çıkmaması için)
        for game in games[:5]:
            game_id = game['gameID']
            title = game['external']
            thumb = game['thumb']
            
            # 2. Adım: Oyunun detaylarına (mağaza fiyatlarına) git
            details_url = f"https://www.cheapshark.com/api/1.0/games?id={game_id}"
            details_resp = requests.get(details_url)
            details = details_resp.json()
            
            deals = details.get('deals', [])
            
            store_prices = []
            
            # İstenen Mağazaları Filtrele (Steam, Epic, GOG, Origin/EA, Uplay/Ubisoft, MS Store)
            # CheapShark Store ID'leri: Steam=1, GOG=7, Origin=8, Uplay=13, Epic=25
            target_stores = ['Steam', 'Epic Games Store', 'GOG', 'Origin', 'Uplay', 'Microsoft Store']
            
            for deal in deals:
                store_id = deal['storeID']
                store_name = store_map.get(store_id, "Bilinmiyor")
                
                # Sadece hedeflediğimiz popüler mağazaları göster
                if store_name in target_stores:
                    price_usd = float(deal['price'])
                    price_tl = price_usd * usd_rate
                    
                    store_prices.append({
                        "store": store_name,
                        "price_usd": price_usd,
                        "price_tl": price_tl,
                        # Link oluşturma (CheapShark yönlendirme linki)
                        "link": f"https://www.cheapshark.com/redirect?dealID={deal['dealID']}"
                    })
            
            if store_prices:
                results.append({
                    "title": title,
                    "image": thumb,
                    "prices": store_prices
                })
                
        return results

    except Exception as e:
        st.error(f"Arama sırasında hata oluştu: {e}")
        return None

# --- ARAYÜZ VE AKIŞ ---

# 1. Gerekli verileri hazırla
usd_rate = get_usd_rate()
store_mapping = get_stores()

# 2. Arama Çubuğu
search_query = st.text_input("Oyun Adı Girin:", placeholder="Örn: Cyberpunk, FIFA, GTA V...")

if search_query:
    with st.spinner(f"'{search_query}' için mağazalar taranıyor..."):
        found_games = search_game_deals(search_query, usd_rate, store_mapping)
        
    if found_games:
        st.success(f"{len(found_games)} oyun bulundu. Güncel Kur: 1$ = {usd_rate:.2f} TL")
        
        for game in found_games:
            # Her oyun için bir kutu (Container)
            with st.container(border=True):
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    st.image(game['image'], width=150)
                
                with col2:
                    st.subheader(game['title'])
                    
                    # Fiyatları Yan Yana Göster
                    price_cols = st.columns(len(game['prices']))
                    
                    for idx, price_info in enumerate(game['prices']):
                        with price_cols[idx]:
                            # Mağaza Logosu yerine İsmi ve Fiyatı
                            st.markdown(f"**{price_info['store']}**")
                            st.markdown(f"<h3 style='color:#4CAF50'>{price_info['price_tl']:.0f} ₺</h3>", unsafe_allow_html=True)
                            st.caption(f"({price_info['price_usd']} $)")
                            
                            # Satın Al Butonu
                            st.link_button("Mağazaya Git", price_info['link'])
    else:
        st.warning("Aradığınız oyun bulunamadı veya şu an indirimli listelerde yok.")

else:
    # Arama yapılmadıysa boş durmasın, bilgi verelim
    st.info("👆 Yukarıdaki arama çubuğuna oyun adını yazıp Enter'a basın.")
    
    st.markdown("""
    ### Hangi Mağazalar Var?
    Bu arama motoru aşağıdaki platformları tarar:
    * ✅ **Steam**
    * ✅ **Epic Games Store**
    * ✅ **GOG**
    * ✅ **Ubisoft Connect**
    * ✅ **EA (Origin)**
    """)
