import streamlit as st
from PIL import Image
import base64
from io import BytesIO
import json
import os
import pyrebase
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
    top: 280px;
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
    top: 280px !important;
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
    </style>
""", unsafe_allow_html=True)

#---------
firebase_config = {
    "apiKey": "AIzaSyCcg5huFKHyU2KU9phub_e8M_9HweZ_6MA",
    "authDomain": "account-food.firebaseapp.com",
    "databaseURL": "https://account-food-default-rtdb.firebaseio.com/",  # bắt buộc
    "projectId": "account-food",
    "storageBucket": "account-food.appspot.com",  # sửa từ firebasestorage.app
    "messagingSenderId": "754910654148",
    "appId": "1:754910654148:web:a1a31fa24154a6c93ae391",
    "measurementId": "G-916KQ5DBWJ"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

#---------SIGN IN/ SIGN UP------
# --- TITLE ---
st.markdown(
    f"""
    <h1 style='text-align: center; color: black;'>
         {t("title")} 
    </h1>
    """,
    unsafe_allow_html=True
)


# --- CĂN GIỮA ---
form_container = st.container()
with form_container:

    # Tạo 3 cột, cột giữa chứa form
    col_left, col_center, col_right = st.columns([1, 2, 1])

    # Giới hạn độ rộng input bằng CSS vẫn ổn (chỉ giữ phần này nếu muốn)
    st.markdown(
        """
        <style>
        /* Toàn bộ phần form ở giữa màn hình */
        div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"] {
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            text-align: center !important;
            width: 100%;
            margin-top: 10px !important;
        }
        div[data-testid="stTextInput"] {
            width: 350px !important;
            margin: 0 auto !important;
            text-align: center !important;
        }

        /* Giới hạn độ rộng input */
        div[data-testid="stTextInput"] {
            width: 350px !important;
        }

        /* Giới hạn nút bấm */
        button[kind="secondary"], button[kind="primary"] {
            width: 150px !important;
            align-self: center !important;
        }

        /* Đảm bảo form không dính lề */
        section.main > div {
            display: flex !important;
            justify-content: center !important;
        }

        /* Tùy chọn: căn giữa luôn theo chiều dọc nếu muốn */
        section.main > div[data-testid="stVerticalBlock"] {
            min-height: 80vh !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    with col_center:
        menu = [t("SI"), t("SU")]
        choice = st.radio(
            "",
            [t("SI"), t("SU")],
            horizontal=True,  # cho nằm ngang
            key="auth_menu_radio"
        )
    
        if choice == t("SU"):
            st.subheader(t("CNA"))
            email = st.text_input("Email")
            password = st.text_input(t("Pass"), type="password")
            confirm_password = st.text_input(t("ConP"), type = "password")
            if st.button(t("SU")):
                if password != confirm_password:
                    st.error(t("NotM"))
                elif len(password) < 6:
                    st.warning(t("RuleP"))
                else:
                    try:
                        user = auth.create_user_with_email_and_password(email, password)
                        st.success(t("SucA"))
                        st.session_state[t("U")] = email 
                        st.switch_page("web.py")
                        st.info(t("GoSI"))
                    except Exception as e:
                        error_str = str(e)
                        if "INVALID_EMAIL" in error_str:
                            st.error(t("error_invalid_email"))
                        elif "EMAIL_EXISTS" in error_str:
                            st.error(t("error_email_exists"))
                        elif "INVALID_PASSWORD" in error_str:
                            st.error(t("error_wrong_password"))
                        else:
                            st.error(t("error_generic"))

        elif choice == t("SI"):
            st.subheader(t("LI"))
            email = st.text_input("Email")
            password = st.text_input(t("Pass"), type="password")
            if st.button(t("SI")):
                try:
                    user = auth.sign_in_with_email_and_password(email, password)
                    st.success(f"{t('logged_in_as')} {email}")
                    st.session_state[t("U")] = email #Luu trang thai dang nhap
                    st.switch_page("web.py")
                except Exception as e:
                        error_str = str(e)
                        if "INVALID_EMAIL" in error_str:
                            st.error(t("error_invalid_email"))
                        elif "EMAIL_EXISTS" in error_str:
                            st.error(t("error_email_exists"))
                        elif "INVALID_PASSWORD" in error_str:
                            st.error(t("error_wrong_password"))
                        else:
                            st.error(t("error_generic"))
