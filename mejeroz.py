import streamlit as st
import pandas as pd
import cdsapi
import datetime
from geopy.geocoders import Nominatim

# --- NASTAVENÍ STRÁNKY ---
st.set_page_config(page_title="Solární analytik", layout="wide")
st.title("☀️ Solární data podle města")

# --- KONFIGURACE (TVÉ FUNKČNÍ ÚDAJE) ---
URL = 'https://ads.atmosphere.copernicus.eu/api'
KEY = '2eaa6c36-8f1c-4ee1-ab27-25cecf04a7c5'

# --- BOČNÍ PANEL ---
st.sidebar.header("1. Lokalita")

# Inicializace geolokátoru
geolocator = Nominatim(user_agent="solar_app_cz")

mesto_vstup = st.sidebar.text_input("Zadejte název města:", "Plzeň")
location = geolocator.geocode(mesto_vstup)

if location:
    lat = location.latitude
    lon = location.longitude
    st.sidebar.success(f"Nalezeno: {location.address}")
else:
    st.sidebar.warning("Město nenalezeno, používám výchozí (Plzeň).")
    lat, lon = 49.745, 13.371

# Zobrazení mapy v bočním panelu
mapa_data = pd.DataFrame({'lat': [lat], 'lon': [lon]})
st.sidebar.map(mapa_data, zoom=6)

st.sidebar.divider()
st.sidebar.header("2. Časové období")

today = datetime.date.today()
# Nastavíme konec na minulý měsíc (data za budoucí měsíce neexistují)
last_month = today.replace(day=1) - datetime.timedelta(days=1)
default_start = last_month - datetime.timedelta(days=365)

start_date = st.sidebar.date_input("Od:", default_start)
end_date = st.sidebar.date_input("Do:", last_month)

# --- TLAČÍTKO PRO STAHOVÁNÍ ---
if st.sidebar.button("Stáhnout data z Copernika"):
    try:
        with st.spinner(f"Navazuji spojení pro {mesto_vstup}..."):
            client = cdsapi.Client(url=URL, key=KEY, verify=True)
            
            request = {
                "sky_type": "observed_cloud",
                "location": {"longitude": lon, "latitude": lat},
                "altitude": "310",
                "date": f"{start_date}/{end_date}",
                "time_step": "1month",
                "time_reference": "universal_time",
                "data_format": "csv"
            }
            
            client.retrieve("cams-solar-radiation-timeseries", request).download('vysledek.csv')
            st.sidebar.success("Úspěšně staženo!")
            st.rerun()
            
    except Exception as e:
        st.sidebar.error("CHYBA PŘI STAHOVÁNÍ:")
        st.sidebar.code(str(e))
        
        # Pomocník pro časté chyby
        error_msg = str(e).lower()
        if "401" in error_msg:
            st.sidebar.info("Tip: Zkontrolujte, zda je klíč (KEY) stále platný ve vašem ADS profilu.")
        elif "terms" in error_msg:
            st.sidebar.info("Tip: Musíte jít na web ADS a kliknout na 'Accept Terms' u tohoto datasetu.")
        elif "400" in error_msg:
            st.sidebar.info("Tip: Pravděpodobně jste vybral datum, pro které data ještě nejsou dostupná.")

# --- HLAVNÍ ČÁST (ZOBRAZENÍ) ---
try:
    # Definice sloupců pro CSV bez hlavičky
    cols = ['Období', 'GHI', 'BHI', 'DHI', 'BNI', 'GHI_cl', 'BHI_cl', 'DHI_cl', 'BNI_cl', 'Rel', 'Alb']
    df = pd.read_csv('vysledek.csv', sep=';', comment='#', header=None, names=cols)
    
    st.subheader(f"Analýza osvitu pro místo: {mesto_vstup}")

    c1, c2 = st.columns(2)
    with c1:
        st.write("### Globální osvit (GHI)")
        st.area_chart(data=df, x='Období', y='GHI', color="#FFC300")
    with c2:
        st.write("### Rozptýlený osvit (DHI)")
        st.area_chart(data=df, x='Období', y='DHI', color="#FF5733")

    st.divider()
    m1, m2, m3 = st.columns(3)
    m1.metric("Maximum GHI", f"{df['GHI'].max():.1f} W/m²")
    m2.metric("Průměr GHI", f"{df['GHI'].mean():.1f} W/m²")
    m3.metric("Souřadnice", f"{lat:.2f}, {lon:.2f}")

except Exception:
    st.info("💡 Pro zobrazení grafů vyberte město a klikněte na tlačítko vlevo.")
