import streamlit as st
from PIL import Image
import base64
from io import BytesIO
import json
import os
import pyrebase
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

st.title("🔥 Streamlit Firebase Auth 🔥")

menu = ["Sign In", "Sign Up"]
choice = st.selectbox("Menu", menu)

if choice == "Sign Up":
    st.subheader("Create New Account")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type = "password")
    if st.button("Sign Up"):
        if password != confirm_password:
            st.error("❌ Passwords do not match. Please re-enter.")
        elif len(password) < 6:
            st.warning("⚠️ Password should be at least 6 characters long.")
        else:
            try:
                user = auth.create_user_with_email_and_password(email, password)
                st.success("Account created successfully!")
                st.session_state["user"] = email 
                st.switch_page("web.py")
                st.info("Go to Sign In Menu to login")
            except Exception as e:
                st.error(f"Error: {e}")

elif choice == "Sign In":
    st.subheader("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Sign In"):
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            st.success(f"Logged in as {email}")
            st.session_state["user"] = email #Luu trang thai dang nhap
            st.switch_page("web.py")
        except Exception as e:
            st.error(f"Error: {e}")