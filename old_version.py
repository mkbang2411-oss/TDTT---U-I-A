import streamlit as st
import base64
from pathlib import Path
from pages.Map import show_map

import locale 
import json
from streamlit_cookies_manager import EncryptedCookieManager
# from pages.Favorite import show_favorite
# from pages.BestFood import show_bestfood
# from pages.Account import show_account
# from pages.Language import show_language
st.set_page_config(layout="wide", initial_sidebar_state="collapsed")

#---Kpang--
cookies = EncryptedCookieManager(prefix="multilang_", password="secret_key_123")

if not cookies.ready():
    st.warning("🔄 Đang tải cookies... vui lòng refresh trang sau vài giây.")
    st.stop()

def load_translations(file_path="languages.json"):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

translations = load_translations()

browser_lang = locale.getdefaultlocale()[0] 
if "lang" not in cookies:
    if browser_lang and "vi" in browser_lang.lower():
        cookies["lang"] = "vi"
    else:
        cookies["lang"] = "en"

current_lang = cookies["lang"]


#-----KPang
# CSS custom
st.markdown("""
<style>
.lang-button {
    position: fixed;
    top: 480px;
    right: 15px;
    z-index: 9999;
    background-color: white;
    border: 1px solid #ddd;
    border-radius: 50%;
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 1px 4px rgba(0,0,0,0.2);
    cursor: pointer;
    font-size: 18px;
    transition: all 0.2s ease;
}
.lang-button:hover {
    background-color: #f5f5f5;
    transform: scale(1.05);
}

/* Ẩn menu thừa của streamlit */
div[data-testid="stSelectbox"] > label {
    display: none !important;
}

/* Dropdown nhỏ gọn */
div[data-testid="stSelectbox"] {
    position: fixed !important;
    top: 480px !important;
    right: 60px !important;
    width: 120px !important;
    z-index: 10000 !important;
    background-color: white !important;
    border-radius: 8px !important;
    font-size: 10px !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.15) !important;
}
</style>
""", unsafe_allow_html=True)

lang_icon = st.empty()
with lang_icon.container():
    st.markdown('<div class="lang-button" id="langBtn">🌐</div>', unsafe_allow_html=True)

selected_lang = st.selectbox(
    "🌐",
    ["en", "vi"],
    index=0 if current_lang == "en" else 1,
    format_func=lambda x: "en English" if x == "en" else "🇻🇳 Vietnamese",
    label_visibility="collapsed",
    key="lang_selector"
)

st.markdown("</div></div>", unsafe_allow_html=True)

# Nếu đổi → lưu lại cookie và reload
if selected_lang != current_lang:
    cookies["lang"] = selected_lang
    cookies.save()
    st.rerun()


lang_data = translations[selected_lang]
#----------

# HÀM HỖ TRỢ DỊCH
def t(key):
    """Hàm trả về bản dịch tương ứng"""
    return translations[current_lang].get(key, key)
#----------






# Ẩn sidebar hoàn toàn bằng CSS
st.markdown("""
    <style>
    /* Ẩn toàn bộ sidebar và vùng chứa của nó */
    [data-testid="stSidebar"], 
    [data-testid="stSidebarNav"], 
    section[data-testid="stSidebar"] > div:first-child {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        height: 0 !important;
    }

    /* Ẩn luôn nút thu gọn/mở rộng sidebar */
    [data-testid="collapsedControl"] {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        height: 0 !important;
    }

    /* Mở rộng phần nội dung chính ra toàn màn hình */
    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        margin: 0 auto !important;
        max-width: 100% !important;
    }
    </style>
""", unsafe_allow_html=True)

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
    font-size: 1.3em;
    color: #BC2A15 !important ;
    margin: 0 40px;
    font-weight: bold;
    cursor: pointer;
    transition: color 0.3s ease;
    letter-spacing: 2px;
    text-decoration: none !important;
}}

.nav-link:hover {{
    color: white !important;
}}

.active {{
    color: white;
    font-weight: bold;
    text-decoration: none ;
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

nav_items = ["Home", "Map","Account"]
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
    st.subheader(lang_data["subheader"])
elif page == "Map":
    show_map()
# elif page == "Favorite":
#      show_favorite()
# elif page == "Best Food":
#      show_bestfood()
# elif page == "Account":
#      show_account()
