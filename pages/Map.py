# pages/map_page.py
import streamlit as st
from streamlit_folium import st_folium
import folium

def show_map():
    st.subheader("🗺️ Đây là trang bản đồ")
    m = folium.Map(location=[10.762622, 106.660172], zoom_start=12)
    folium.Marker([10.77, 106.68], popup="Quán ăn ngon").add_to(m)
    st_folium(m, width=700, height=500)
