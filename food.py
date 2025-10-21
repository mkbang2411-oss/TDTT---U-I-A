import streamlit as st
import base64
from pathlib import Path
from pages.Map import show_map
# from pages.Favorite import show_favorite
# from pages.BestFood import show_bestfood
# from pages.Account import show_account
# from pages.Language import show_language
st.set_page_config(layout="wide", initial_sidebar_state="collapsed")

# --- HÀM ĐỌC ẢNH ---
def img_to_base64(image_path):
    try:
        img_bytes = Path(image_path).read_bytes()
        encoded = base64.b64encode(img_bytes).decode()
        return f"data:image/png;base64,{encoded}"
    except FileNotFoundError:
        st.error(f"Không tìm thấy file ảnh tại: {image_path}")
        return "https://placehold.co/120x120/BC2A15/white?text=Error"

# --- STATE QUẢN LÝ TRANG ---
if "page" not in st.session_state:
    st.session_state.page = "Home"

def navigate(page):
    st.session_state.page = page

# --- HEADER ---
logo_food_trai = "Picture/Food/food.png"
base64_logo_food_trai = img_to_base64(logo_food_trai)

# --- CSS ĐẸP + NAVBAR GỘN CHỮ VÀNG ---
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Anton&family=Cinzel:wght@400;700&display=swap');

/* --- Banner --- */
.header-banner {{
    background-color: #BC2A15;
    padding: 10px 0;
    text-align: center;
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    color: white;
}}
.header-text {{
    font-family: 'Anton', sans-serif;
    font-size: 5em;
    color: #EFD293;
    text-shadow: 5px 5px 0 #D17051;
    letter-spacing: 5px;
    margin: 0 auto;
}}
.header-image {{
    width: 170px;
    height: auto;
    margin: 0 20px;
}}

/* --- NAVBAR --- */
.nav-bar {{
    background-color: #EFD293;
    padding: 20px 0;
    text-align: center;
    border-bottom: 2px solid #EFD293;
}}

.nav-link {{
    font-family: 'Cinzel', serif;
    font-size: 1.1em;
    color: #BC2A15 !important ;
    margin: 0 40px;
    font-weight: bold;
    cursor: pointer;
    transition: color 0.3s ease;
    letter-spacing: 2px;
}}

.nav-link:hover {{
    color: white !important;
}}

.active {{
    color: white;
    font-weight: bold;
    text-decoration: none;
}}
</style>

<div class="header-banner">
    <img src="{base64_logo_food_trai}" class="header-image">
    <div class="header-text">UIA FOOD</div>
    <img src="{base64_logo_food_trai}" class="header-image">
</div>
""", unsafe_allow_html=True)

# --- THANH NAV HTML ---
current_page = st.session_state.page

nav_items = ["Home", "Map", "Favorite", "Best Food", "Account", "Language"]
nav_html = '<div class="nav-bar">'
for item in nav_items:
    active_class = "active" if current_page == item else ""
    # Dùng href trỏ tới query param page
    nav_html += f"<a class='nav-link {active_class}' href='?page={item}'>{item}</a>"
nav_html += "</div>"

st.markdown(nav_html, unsafe_allow_html=True)

# --- CẬP NHẬT PAGE DỰA TRÊN URL ---
query_params = st.query_params
if "page" in query_params:
    page = query_params["page"]
    if page != st.session_state.page:
        st.session_state.page = page
else:
    page = st.session_state.page
    st.query_params["page"]=page

# --- HIỂN THỊ NỘI DUNG ---
st.write("---")
page = st.session_state.page
if page == "Home":
    st.subheader("🍜 Đây là trang Home")
elif page == "Map":
    show_map()
# elif page == "Favorite":
#      show_favorite()
# elif page == "Best Food":
#      show_bestfood()
# elif page == "Account":
#      show_account()
# elif page == "Language":
#      show_language()
