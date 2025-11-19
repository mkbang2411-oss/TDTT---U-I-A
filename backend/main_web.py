from flask import Flask, jsonify, request, send_from_directory
from chatbot_component_v2 import get_chatbot_html
import pandas as pd
from datetime import datetime
import os, json
from food_planner_v2 import generate_food_plan, get_food_planner_html
from music_player_component import get_music_player_html

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
    
    # Inject cả 2 vào trước </body>
    html_content = html_content.replace("</body>", f"{chatbot_html}\n{food_planner_html}\n{music_player_html}</body>")
    
    return html_content

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
    app.run(debug=True)
