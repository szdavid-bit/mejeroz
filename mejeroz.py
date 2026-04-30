import streamlit as st
import pandas as pd
import cdsapi
import datetime
from geopy.geocoders import Nominatim

# --- NASTAVENÍ STRÁNKY ---
st.set_page_config(page_title="Solární analytik", layout="wide")
st.title("☀️ Solární data podle města")

# --- BOČNÍ PANEL ---
st.sidebar.header("1. Vyhledat lokalitu")

# Inicializace geolokátoru
geolocator = Nominatim(user_agent="solar_app_cz")

mesto_vstup = st.sidebar.text_input("Zadejte název města (např. Brno):", "Plzeň")
location = geolocator.geocode(mesto_vstup)

if location:
    lat = location.latitude
    lon = location.longitude
    st.sidebar.success(f"Nalezeno: {location.address}")
else:
    st.sidebar.error("Město nenalezeno, používám výchozí (Plzeň).")
    lat, lon = 49.745, 13.371

# Zobrazení souřadnic a mapy
st.sidebar.write(f"GPS: {lat:.3f}, {lon:.3f}")
mapa_data = pd.DataFrame({'lat': [lat], 'lon': [lon]})
st.sidebar.map(mapa_data, zoom=6)

st.sidebar.divider()
st.sidebar.header("2. Časové období")

URL = 'https://copernicus.eu'
KEY = '2eaa6c36-8f1c-4ee1-ab27-25cecf04a7c5'

today = datetime.date.today()
default_start = today - datetime.timedelta(days=365)
start_date = st.sidebar.date_input("Od:", default_start)
end_date = st.sidebar.date_input("Do:", today)

if st.sidebar.button("Stáhnout data"):
    try:
        with st.spinner(f"Stahuji data pro {mesto_vstup}..."):
            client = cdsapi.Client(url=URL, key=KEY)
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
            st.sidebar.success("Data stažena!")
            st.rerun()
    except Exception as e:
        st.sidebar.error(f"Chyba: {e}")

# --- HLAVNÍ ČÁST (ZOBRAZENÍ) ---
try:
    názvy_sloupců = ['Období', 'GHI', 'BHI', 'DHI', 'BNI', 'GHI_cl', 'BHI_cl', 'DHI_cl', 'BNI_cl', 'Reliab', 'Albedo']
    df = pd.read_csv('vysledek.csv', sep=';', comment='#', header=None, names=názvy_sloupců)
    
    st.subheader(f"Statistiky osvitu: {mesto_vstup}")

    col1, col2 = st.columns(2)
    with col1:
        st.write("### Globální osvit (GHI)")
        st.area_chart(data=df, x='Období', y='GHI', color="#FFC300")
    with col2:
        st.write("### Rozptýlený osvit (DHI)")
        st.area_chart(data=df, x='Období', y='DHI', color="#FF5733")

    st.divider()
    m1, m2, m3 = st.columns(3)
    m1.metric("Maximum", f"{df['GHI'].max():.1f} W/m²")
    m2.metric("Průměr", f"{df['GHI'].mean():.1f} W/m²")
    m3.metric("Lokalita", mesto_vstup)

except Exception as e:
    st.info("Zadejte město a klikněte na tlačítko.")
