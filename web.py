import streamlit as st
from PIL import Image
import base64
from io import BytesIO
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

