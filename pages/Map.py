import streamlit as st
from streamlit_folium import st_folium
from streamlit_geolocation import streamlit_geolocation
import folium

def show_map():
    st.subheader("🗺️ Bản đồ định vị HTML5 chính xác (Laptop/PC)")

    # 🛰️ Lấy vị trí hiện tại của người dùng
    st.info("📍 Vui lòng cho phép trình duyệt truy cập vị trí để hiển thị chính xác bản đồ.")
    location = streamlit_geolocation()

    # Nếu lấy được vị trí
    if location and location["latitude"] and location["longitude"]:
        lat = location["latitude"]
        lon = location["longitude"]
        st.success(f"✅ Đã định vị được vị trí: {lat:.6f}, {lon:.6f}")
    else:
        st.warning("⚠️ Không lấy được vị trí. Hiển thị mặc định TP.HCM.")
        lat, lon = 10.762622, 106.660172  # vị trí mặc định

    # 🗺️ Tạo bản đồ
    m = folium.Map(location=[lat, lon], zoom_start=15)
    folium.Marker([lat, lon], popup="📍 Bạn đang ở đây").add_to(m)

    # Hiển thị bản đồ trên Streamlit
    st_folium(m, width=700, height=500)


# ✅ Gọi hàm để chạy khi chạy file trực tiếp
if __name__ == "__main__":
    show_map()
