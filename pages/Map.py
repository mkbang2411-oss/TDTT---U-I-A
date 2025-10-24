import streamlit as st
from streamlit_folium import st_folium
from streamlit_geolocation import streamlit_geolocation
import folium
import pandas as pd
import unicodedata

def remove_accents(text):
    """Bỏ dấu tiếng Việt để tìm kiếm không dấu."""
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn")

def show_map():
    st.subheader("🗺️ Bản đồ định vị & tìm kiếm quán ăn (offline từ Data.csv)")

    # 🛰️ Lấy vị trí hiện tại
    st.info("📍 Cho phép trình duyệt truy cập vị trí để định vị chính xác.")
    location = streamlit_geolocation()

    if location and location["latitude"] and location["longitude"]:
        lat = location["latitude"]
        lon = location["longitude"]
        st.success(f"✅ Vị trí hiện tại: {lat:.6f}, {lon:.6f}")
    else:
        st.warning("⚠️ Không lấy được vị trí, mặc định TP.HCM.")
        lat, lon = 10.762622, 106.660172

    # 📂 Đọc dữ liệu từ file CSV
    try:
        df = pd.read_csv("Data.csv")
        st.success(f"✅ Đã tải {len(df)} địa điểm từ Data.csv")
    except Exception as e:
        st.error(f"🚨 Lỗi đọc file Data.csv: {e}")
        return

    # 🔍 Tìm kiếm địa điểm
    st.divider()
    st.markdown("### 🔍 Tìm kiếm hoặc lọc địa điểm")
    categories = ["Tất cả"] + sorted(df["category"].dropna().unique().tolist())
    selected_cat = st.selectbox("Chọn loại quán:", categories)
    query = st.text_input("Nhập tên hoặc địa chỉ:")

    # 🔧 Lọc dữ liệu (bỏ dấu, không phân biệt hoa thường)
    filtered_df = df.copy()
    if selected_cat != "Tất cả":
        filtered_df = filtered_df[filtered_df["category"] == selected_cat]

    if query:
        q = remove_accents(query.lower().strip())
        mask = filtered_df.apply(
            lambda row: (
                q in remove_accents(str(row["name"]).lower())
                or q in remove_accents(str(row["address"]).lower())
                or q in remove_accents(str(row["category"]).lower())
            ),
            axis=1
        )
        filtered_df = filtered_df[mask]

    st.write(f"📍 Có {len(filtered_df)} địa điểm được hiển thị.")

    # 🗺️ Hiển thị bản đồ Folium
    m = folium.Map(location=[lat, lon], zoom_start=14)

    # 📌 Marker vị trí người dùng
    folium.Marker(
        [lat, lon],
        popup="📍 Vị trí của bạn",
        icon=folium.Icon(color="blue", icon="user")
    ).add_to(m)

    # 📌 Marker quán ăn từ Data.csv
    for _, row in filtered_df.iterrows():
        folium.Marker(
            [row["latitude"], row["longitude"]],
            popup=f"<b>{row['name']}</b><br>{row['address']}<br><i>{row['category']}</i>",
            tooltip=row["name"],
            icon=folium.Icon(color="red", icon="cutlery")
        ).add_to(m)

    st_folium(m, width=700, height=500)


# ✅ Chạy khi mở file
if __name__ == "__main__":
    show_map()
