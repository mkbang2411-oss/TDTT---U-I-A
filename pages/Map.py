# map_view.py
import streamlit as st
from streamlit_folium import st_folium
from streamlit_geolocation import streamlit_geolocation
import folium
import pandas as pd
import os

# Nếu bạn có file crawl_places.py
try:
    from crawl_places import get_places, save_places_to_csv
except Exception:
    def get_places(query, lat, lon):
        st.warning("Không thể gọi get_places(): chưa import được crawl_places.py")
        return []
    def save_places_to_csv(places):
        return pd.DataFrame()

# --- Cấu hình ---
CSV_FILE = "Data.csv"
DEFAULT_CENTER = (10.762622, 106.660172)

st.set_page_config(page_title="Bản đồ quán ăn", layout="wide")
st.title("🗺️ Bản đồ quán ăn — Xem & Thu thập dữ liệu")

# --- Sidebar ---
with st.sidebar:
    st.header("🔎 Tìm quán")
    query = st.text_input("Nhập từ khóa (ví dụ: phở, trà sữa...)", "quán cà phê")
    st.write("📡 Lấy vị trí (HTML5 Geolocation)")
    location = streamlit_geolocation()

    if location and location.get("latitude") and location.get("longitude"):
        lat = location["latitude"]
        lon = location["longitude"]
        st.success(f"Vị trí hiện tại: {lat:.6f}, {lon:.6f}")
    else:
        st.warning("Không lấy được GPS — dùng vị trí mặc định (TP.HCM).")
        lat, lon = DEFAULT_CENTER

    if st.button("🔎 Tìm quanh đây và lưu vào Data.csv"):
        with st.spinner(f"Đang tìm '{query}' quanh {lat:.6f}, {lon:.6f} ..."):
            places = get_places(query, lat, lon)
            new_df = save_places_to_csv(places)
        if isinstance(new_df, pd.DataFrame) and not new_df.empty:
            st.success(f"Đã lưu {len(new_df)} quán mới vào {CSV_FILE}")
        else:
            st.info("Không có dữ liệu mới hoặc chưa import được crawl_places.py.")

# --- Đọc dữ liệu ---
if os.path.exists(CSV_FILE):
    try:
        df = pd.read_csv(CSV_FILE)
    except Exception as e:
        st.error(f"Lỗi đọc {CSV_FILE}: {e}")
        df = pd.DataFrame(columns=["ten_quan", "dia_chi", "so_dien_thoai", "rating", "gio_mo_cua", "lat", "lon"])
else:
    df = pd.DataFrame(columns=["ten_quan", "dia_chi", "so_dien_thoai", "rating", "gio_mo_cua", "lat", "lon"])

# --- Tạo bản đồ ---
map_center = [lat, lon]
m = folium.Map(location=map_center, zoom_start=15, tiles="OpenStreetMap", control_scale=True)

# Marker vị trí người dùng
folium.Marker(
    location=map_center,
    popup="📍 Bạn đang ở đây",
    tooltip="Bạn đang ở đây",
    icon=folium.Icon(color="blue", icon="user", prefix="fa")
).add_to(m)

# Thêm markers cho từng quán
for _, row in df.iterrows():
    try:
        rlat, rlon = float(row["lat"]), float(row["lon"])
    except Exception:
        continue

    popup_html = f"""
    <div>
        <b>{row.get('ten_quan', '')}</b><br>
        {row.get('dia_chi', '')}<br>
        ⭐ {row.get('rating', '')}
    </div>
    """

    # Dùng popup để lưu ID của quán (truy xuất lại sau)
    folium.Marker(
        [rlat, rlon],
        popup=popup_html,
        tooltip=row.get("ten_quan", ""),
        icon=folium.Icon(color="red", icon="cutlery", prefix="fa")
    ).add_to(m)

# --- Chia layout ---
col1, col2 = st.columns([1.2, 2.8])

with col2:
    map_data = st_folium(m, width=1100, height=750)

with col1:
    st.subheader("📋 Thông tin quán ăn")
    selected_row = None

    # Nếu người dùng bấm vào marker
    if map_data and map_data.get("last_object_clicked"):
        click = map_data["last_object_clicked"]
        click_lat, click_lon = click["lat"], click["lng"]

        # Tìm quán gần nhất so với tọa độ click
        df["distance"] = ((df["lat"] - click_lat)**2 + (df["lon"] - click_lon)**2)
        selected_row = df.loc[df["distance"].idxmin()]
    else:
        st.info("👉 Bấm vào một quán trên bản đồ để xem chi tiết.")

    if selected_row is not None:
        st.image("https://upload.wikimedia.org/wikipedia/commons/6/6b/Food_placeholder.png", use_container_width=True)
        st.markdown(f"**🏠 Địa chỉ:** {selected_row.get('dia_chi', 'Không rõ')}")
        st.markdown(f"**📞 SĐT:** {selected_row.get('so_dien_thoai', 'Không có')}")
        st.markdown(f"**⭐ Đánh giá:** {selected_row.get('rating', 'Chưa có')}")
        st.markdown(f"**⏰ Giờ mở cửa:** {selected_row.get('gio_mo_cua', 'Không rõ')}")

# --- Dưới cùng: bảng dữ liệu ---
with st.expander("📑 Danh sách quán trong Data.csv"):
    st.write(f"Tổng số quán: {len(df)}")
    if not df.empty:
        st.dataframe(
            df[["ten_quan", "dia_chi", "so_dien_thoai", "rating", "gio_mo_cua"]].fillna(""),
            width="stretch",
            hide_index=True
        )
