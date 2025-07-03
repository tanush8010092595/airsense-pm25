
import streamlit as st
import pandas as pd
import joblib
import pydeck as pdk
import plotly.express as px
from datetime import datetime
from geopy.geocoders import Nominatim

# Load model and data
model = joblib.load("aod_to_pm25_model.pkl")
data = pd.read_csv("sample_pm25_data.csv")
data["datetime"] = pd.to_datetime(data["datetime"])

# Title
st.set_page_config(page_title="AirSense - PM2.5 Monitoring", layout="wide")
st.title("🌍 AirSense: Satellite-Based PM2.5 Monitoring")

# Sidebar inputs
st.sidebar.header("🔎 Select Parameters")
input_mode = st.sidebar.radio("Select Location Mode", ["📍 City Name", "🗺️ Click Map"])

if input_mode == "📍 City Name":
    location_input = st.sidebar.text_input("Enter City or Location", "Delhi")
    geolocator = Nominatim(user_agent="airsense-app")
    location = geolocator.geocode(location_input)
    if location:
        lat, lon = location.latitude, location.longitude
    else:
        st.error("❌ Location not found. Please enter a valid city.")
        lat, lon = None, None
else:
    lat = st.sidebar.number_input("Latitude", value=28.61, format="%.6f")
    lon = st.sidebar.number_input("Longitude", value=77.21, format="%.6f")

# Select date and mode
selected_date = st.sidebar.date_input("📅 Select Date", datetime(2025, 6, 1))
view_mode = st.sidebar.radio("View Mode", ["📊 Historical", "🤖 Predict from AOD"])

if lat is not None and lon is not None:
    if view_mode == "📊 Historical":
        filtered = data[(data["datetime"].dt.date == selected_date) &
                        (data["latitude"].between(lat - 1, lat + 1)) &
                        (data["longitude"].between(lon - 1, lon + 1))]

        st.subheader(f"📍 PM2.5 near selected location on {selected_date}")
        if not filtered.empty:
            st.plotly_chart(px.line(filtered, x="datetime", y="PM2.5", title="PM2.5 Trend"), use_container_width=True)
            st.pydeck_chart(pdk.Deck(
                map_style="mapbox://styles/mapbox/light-v9",
                initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=4),
                layers=[pdk.Layer(
                    "ScatterplotLayer",
                    data=filtered,
                    get_position='[longitude, latitude]',
                    get_color='[200, 30, 0, 160]',
                    get_radius=20000,
                )]
            ))
        else:
            st.warning("⚠️ No historical data found for that location and date.")
    else:
        input_aod = st.sidebar.number_input("🌫️ Enter AOD value", min_value=0.0, max_value=5.0, step=0.01, value=1.0)
        predicted_pm25 = model.predict([[input_aod]])[0]
        st.subheader("🤖 PM2.5 Prediction")
        st.metric("Predicted PM2.5", f"{predicted_pm25:.2f} µg/m³", help="Based on AOD input")
        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))
else:
    st.info("Enter a valid city or coordinates to continue.")
