import streamlit as st
from PIL import Image
import base64
from io import BytesIO
import locale 
import json
from streamlit_cookies_manager import EncryptedCookieManager

#---TRANSLATION-----Start--------------------------------------------------------
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
#----------END-------------------------------------------------------------------


# Mở ảnh
img = Image.open(r"Picture\Food\UIA.png")
buffer = BytesIO()
img.save(buffer, format="PNG")
img_str = base64.b64encode(buffer.getvalue()).decode()
# st.image(img, use_column_width=True)
# st.set_page_config(layout="wide", initial_sidebar_state="collapsed")
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
    /*Account*/
    .account-link{
        position: absolute;
        top: 100px;
        left: 150px;
        z-index:2;
    }
    /*Style account*/
    a[data-testid="stPageLink"]{
        color: #BC2A21 !important;
        font-weight: bold !important;
        font-size: 32px !important;
        text-decoration: none !important;
    }
    a[data-testid="stPageLink"]:hover{
        color: #ffcc00 !important;
        text-decoration: underline !important;
    }
    </style>
""", unsafe_allow_html=True)


st.markdown(f"""
<div class="rectangle">
    <img src="data:image/png;base64,{img_str}" alt="UIA logo" style = "height: 1000px !important;">
    <div class= "account-link">
""", unsafe_allow_html=True)
st.page_link("pages/Account.py", label="Account")

# Account
st.markdown("""
    </div>
</div>
""", unsafe_allow_html=True)

