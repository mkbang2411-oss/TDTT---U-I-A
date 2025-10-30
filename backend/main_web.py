from flask import Flask, jsonify, request, send_from_directory
from chatbot_component_v2 import get_chatbot_html
import pandas as pd
import os, json

app = Flask(__name__, static_folder="../frontend", static_url_path="/")

# ============================
# 🔑 GEMINI API KEY
# ============================
GEMINI_API_KEY = "AIzaSyApgc9Zzduf1d7LdXUvsZriymK4RvBHOjc"

# ============================
# 📁 FILE PATH
# ============================
BASE_DIR = os.path.dirname(__file__)
CSV_FILE = os.path.join(BASE_DIR, "Data.csv")
REVIEWS_FILE = os.path.join(BASE_DIR, "reviews.json")

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
    """Trả review Google + người dùng cho 1 quán"""
    all_reviews = load_user_reviews()

    # Nếu key trong JSON là danh sách reviews (list)
    if place_id in all_reviews:
        value = all_reviews[place_id]
        if isinstance(value, list):
            # 👉 Giả định đây là các review Google đã lấy sẵn
            return jsonify({"google": value, "user": []})
        else:
            # Nếu đã ở dạng {"google": [], "user": []}
            return jsonify(value)

    # Không có review
    return jsonify({"google": [], "user": []})


# ============================
# ✏️ API: THÊM REVIEW NGƯỜI DÙNG
# ============================
@app.route("/api/reviews/<place_id>", methods=["POST"])
def add_review(place_id):
    data = request.json
    if not data or not data.get("ten") or not data.get("comment"):
        return jsonify({"success": False, "message": "Thiếu thông tin"}), 400

    all_reviews = load_user_reviews()
    if place_id not in all_reviews:
        all_reviews[place_id] = {"google": [], "user": []}

    new_review = {
        "ten": data.get("ten"),
        "rating": int(data.get("rating", 0)),
        "comment": data.get("comment")
    }

    all_reviews[place_id]["user"].append(new_review)
    save_user_reviews(all_reviews)
    return jsonify({"success": True, "message": "✅ Đã thêm đánh giá!"})

# ============================
# 🌐 ROUTE FRONTEND
# ============================
@app.route("/")
def serve_index():
    """Serve trang chính với chatbot tích hợp"""
    # Đọc file HTML gốc
    with open("../frontend/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Lấy chatbot HTML
    chatbot_html = get_chatbot_html(GEMINI_API_KEY)
    
    # Inject chatbot vào trước thẻ </body>
    html_content = html_content.replace("</body>", f"{chatbot_html}</body>")
    
    return html_content

@app.route("/<path:path>")
def serve_static_files(path):
    return send_from_directory("../frontend", path)

# ============================
# 🚀 CHẠY SERVER
# ============================
if __name__ == "__main__":
    print(f"📂 Đang chạy Flask tại: {os.path.abspath(BASE_DIR)}")
    print(f"📄 File reviews.json: {os.path.exists(REVIEWS_FILE)}")
    print(f"🤖 Chatbot đã được tích hợp!")
    app.run(debug=True)