from flask import Flask, jsonify, request, send_from_directory
from chatbot_component_v2 import get_chatbot_html
import pandas as pd
from datetime import datetime
import os, json
from food_planner_v2 import generate_food_plan, get_food_planner_html
from music_player_component import get_music_player_html
from language_toggle_component import get_language_toggle_html 

app = Flask(__name__, static_folder="../frontend", static_url_path="/")

# ============================
# 🔑 GEMINI API KEY
# ============================
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
        GEMINI_API_KEY = config.get("GEMINI_API_KEY", "")
else:
    GEMINI_API_KEY = ""
    print("⚠️ Không tìm thấy file config.json, chatbot có thể không hoạt động!")

# ============================
# 📁 FILE PATH
# ============================
BASE_DIR = os.path.dirname(__file__)
CSV_FILE = os.path.join(BASE_DIR, "Data_with_flavor.csv")
REVIEWS_FILE = os.path.join(BASE_DIR, "reviews.json")

WEB_FILE = os.path.join(BASE_DIR,"../frontend/main_web.html")
INDEX_FILE = os.path.join(BASE_DIR, "../frontend/index.html")
ACCOUNT_FILE = os.path.join(BASE_DIR, "../frontend/Account.html")  # ✅ THÊM

LANGUAGES_FILE = os.path.join(BASE_DIR, "languages.json") 

# ============================
# 🌐 API: SERVE FILE NGÔN NGỮ
# ============================
@app.route("/languages.json")
def get_languages():
    """
    API để serve file languages.json
    Nếu không có file, trả về bản dịch mặc định
    """
    if os.path.exists(LANGUAGES_FILE):
        try:
            with open(LANGUAGES_FILE, "r", encoding="utf-8") as f:
                return jsonify(json.load(f))
        except Exception as e:
            print(f"❌ Lỗi đọc languages.json: {e}")
            return jsonify(get_default_translations())
    else:
        print("⚠️ Không tìm thấy languages.json, sử dụng bản dịch mặc định")
        return jsonify(get_default_translations())

def get_default_translations():
    """Bản dịch mặc định nếu không có file languages.json"""
    return {
        "vi": {
            "title": "Khám Phá Ẩm Thực Sài Gòn",
            "greeting": "Xin chào! Chào mừng bạn đến với hệ thống tìm kiếm quán ăn",
            "instruction": "Chọn ngôn ngữ ở góc trên bên phải",
            "search_placeholder": "Tìm kiếm quán ăn...",
            "location": "Vị trí",
            "rating": "Đánh giá",
            "price": "Giá",
            "opening_hours": "Giờ mở cửa",
            "reviews": "Nhận xét",
            "description": "Mô tả",
            "close": "Đóng",
            "submit": "Gửi",
            "cancel": "Hủy"
        },
        "en": {
            "title": "Explore Saigon Cuisine",
            "greeting": "Hello! Welcome to our restaurant search system",
            "instruction": "Select language at top right corner",
            "search_placeholder": "Search restaurants...",
            "location": "Location",
            "rating": "Rating",
            "price": "Price",
            "opening_hours": "Opening Hours",
            "reviews": "Reviews",
            "description": "Description",
            "close": "Close",
            "submit": "Submit",
            "cancel": "Cancel"
        }
    }

# ============================
# 🍴 API: LẤY DANH SÁCH QUÁN
# ============================
@app.route("/api/places", methods=["GET"])
def get_places_data():
    if not os.path.exists(CSV_FILE):
        return jsonify([])

    df = pd.read_csv(CSV_FILE)
    df = df.where(pd.notnull(df), None)

    query = request.args.get("query", "").lower()
    if query:
        df = df[df["ten_quan"].str.lower().str.contains(query, na=False) |
                df["dia_chi"].str.lower().str.contains(query, na=False)]

    data = json.loads(df.to_json(orient="records", force_ascii=False))
    return jsonify(data)

# ============================
# 💾 REVIEW NGƯỜI DÙNG
# ============================
def load_user_reviews():
    if not os.path.exists(REVIEWS_FILE):
        print("⚠️ Không tìm thấy reviews.json!")
        return {}
    with open(REVIEWS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            print("⚠️ reviews.json bị lỗi định dạng JSON.")
            return {}

def save_user_reviews(data):
    with open(REVIEWS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ============================
# ⭐ API: LẤY REVIEW GOOGLE + USER
# ============================
@app.route("/api/reviews/<place_id>")
def get_reviews(place_id):
    all_reviews = load_user_reviews()
    value = all_reviews.get(place_id)

    if isinstance(value, list):
        return jsonify({"google": value, "user": []})
    elif isinstance(value, dict):
        return jsonify(value)
    else:
        return jsonify({"google": [], "user": []})


# ============================
# 🍽️ API: TẠO FOOD PLAN (ENHANCED)
# ============================
@app.route("/api/food-plan", methods=["GET"])
def get_food_plan():
    try:
        # Lấy parameters
        user_lat = float(request.args.get("lat", 10.7769))
        user_lon = float(request.args.get("lon", 106.7009))
        theme = request.args.get("theme", None)
        tastes_str = request.args.get("tastes", "")
        start_time = request.args.get("start_time", "07:00")
        end_time = request.args.get("end_time", "21:00")
        
        radius_km_str = request.args.get("radius_km")
        radius_km = float(radius_km_str) if radius_km_str else None

        # Parse tastes
        user_tastes = [t.strip() for t in tastes_str.split(",") if t.strip()] if tastes_str else None
        
        print(f"🍽️ Tạo food plan: lat={user_lat}, lon={user_lon}, theme={theme}, tastes={user_tastes}")
        
        # Generate plan với các tham số mới
        plan = generate_food_plan(
            user_lat, user_lon, 
            csv_file=CSV_FILE,
            theme=theme,
            user_tastes=user_tastes,
            start_time=start_time,
            end_time=end_time,
            radius_km=radius_km
        )
        
        return jsonify(plan)
        
    except Exception as e:
        print(f"❌ Lỗi tạo food plan: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ============================
# 🌐 ROUTE FRONTEND
# ============================
@app.route("/")
def serve_index():
    """Serve trang chính với chatbot + food planner tích hợp"""
    # Đọc file HTML gốc
    with open(WEB_FILE, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Lấy chatbot HTML
    chatbot_html = get_chatbot_html(GEMINI_API_KEY)
    
    # Lấy food planner HTML
    food_planner_html = get_food_planner_html()

    music_player_html = get_music_player_html()

    language_toggle_html = get_language_toggle_html()
    
    # Inject vào div#insert-chatbot-and-map thay vì </body>
    insert_point = '<div id="insert-chatbot-and-map">'
    if insert_point in html_content:
        html_content = html_content.replace(
            insert_point,
            f'{insert_point}\n{chatbot_html}\n{food_planner_html}\n{music_player_html}\n{language_toggle_html}'
        )
    else:
        # Fallback: inject trước </body> nếu không tìm thấy
        html_content = html_content.replace("</body>", f"{chatbot_html}\n{food_planner_html}\n{music_player_html}\n{language_toggle_html}</body>")
    
    return html_content

@app.route("/account")
@app.route("/Account.html")
def serve_account():
    """Serve trang account với language toggle"""
    try:
        with open("../frontend/Account.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        if not os.path.exists(ACCOUNT_FILE):
            print(f"❌ Không tìm thấy Account.html tại: {ACCOUNT_FILE}")
            return "Account page not found", 404
        
        # Thêm language toggle vào trang account
        language_toggle_html = get_language_toggle_html()
        # Tìm vị trí inject tốt nhất (sau <body> tag)
        if '<body>' in html_content:
            html_content = html_content.replace(
                '<body>',
                f'<body>\n{language_toggle_html}\n',
                1  # Chỉ replace lần đầu tiên
            )
        else:
            # Fallback: inject trước </body>
            html_content = html_content.replace("</body>", f"{language_toggle_html}</body>")
        
        print("✅ Language toggle injected vào Account.html")
        return html_content
    except FileNotFoundError:
        return "Account page not found", 404

@app.route("/<path:path>")
def serve_static_files(path):
    return send_from_directory("../frontend", path)

# ============================
# 🚀 CHẠY SERVER
# ============================
if __name__ == "__main__":
    print(f"📂 Đang chạy Flask tại: {os.path.abspath(BASE_DIR)}")
    print(f"📄 File CSV: {os.path.exists(CSV_FILE)}")
    print(f"📄 File reviews.json: {os.path.exists(REVIEWS_FILE)}")
    print(f"🤖 Chatbot đã được tích hợp!")
    print(f"🍽️ Food Planner đã được tích hợp!")
    print(f"🎵 Music player đã được tích hợp!")
    print(f"📄 Languages File: {'✅ Found' if os.path.exists(LANGUAGES_FILE) else '⚠️ Not Found (using defaults)'}")
    print("=" * 60)
    print("🎉 COMPONENTS LOADED:")
    print("   ✅ Chatbot Component")
    print("   ✅ Food Planner Component")
    print("   ✅ Music Player Component")
    print("   ✅ Language Toggle Component")
    print("=" * 60)
    print("🌐 API ENDPOINTS:")
    print("   • GET  /                    → Main page")
    print("   • GET  /account             → Account page")
    print("   • GET  /api/places          → Get restaurant list")
    print("   • GET  /api/reviews/<id>    → Get reviews")
    print("   • GET  /api/food-plan       → Generate food plan")
    print("   • GET  /languages.json      → Get translations")
    print("=" * 60)
    print("🔥 Server running at: http://localhost:5000")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=False)  # ← Tắt debug
