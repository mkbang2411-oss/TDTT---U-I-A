from flask import Flask, jsonify, request, send_from_directory
from chatbot_component_v2 import get_chatbot_html
import pandas as pd
from datetime import datetime
import os, json
from food_planner_v2 import generate_food_plan, get_food_planner_html
from music_player_component import get_music_player_html
from language_toggle_component import get_language_toggle_html, get_language_script_only

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
ACCOUNT_FILE = os.path.join(BASE_DIR, "../frontend/Account.html")

LANGUAGES_FILE = os.path.join(BASE_DIR, "languages.json") 

# ============================
# ✨ TỰ ĐỘNG INJECT LANGUAGE TOGGLE VÀO MỌI HTML
# ============================
def inject_language_toggle(html_content):
    """
    Tự động inject Language Toggle vào bất kỳ HTML nào
    ✅ XÓA SẠCH CODE CŨ trước khi inject
    """
    import re
    
    print("\n🔍 Checking for old language code...")
    
    # ============================
    # 🗑️ XÓA CODE CŨ
    # ============================
    
    # 1️⃣ Xóa localStorage.setItem("selectedLanguage", ...)
    patterns_to_remove = [
        r'localStorage\.setItem\s*\(\s*["\']selectedLanguage["\']\s*,.*?\);?',
        r'localStorage\.getItem\s*\(\s*["\']selectedLanguage["\']\s*\)',
        r'const\s+savedLang\s*=\s*localStorage\.getItem\(["\']selectedLanguage["\']\).*?;',
        r'let\s+savedLang\s*=\s*localStorage\.getItem\(["\']selectedLanguage["\']\).*?;',
        r'var\s+savedLang\s*=\s*localStorage\.getItem\(["\']selectedLanguage["\']\).*?;',
    ]
    
    for pattern in patterns_to_remove:
        matches = re.findall(pattern, html_content, re.DOTALL)
        if matches:
            print(f"   🗑️ Found old code: {pattern[:50]}...")
            html_content = re.sub(pattern, '', html_content)
    
    # 2️⃣ Xóa function syncToggleWithLanguage() HOÀN TOÀN
    sync_function_pattern = r'function\s+syncToggleWithLanguage\s*\(\s*\)\s*\{[^}]*\}'
    if re.search(sync_function_pattern, html_content):
        print("   🗑️ Removing function syncToggleWithLanguage()")
        html_content = re.sub(sync_function_pattern, '', html_content, flags=re.DOTALL)
    
    # 3️⃣ Xóa các dòng gọi syncToggleWithLanguage()
    sync_call_pattern = r'syncToggleWithLanguage\s*\(\s*\)\s*;?'
    if re.search(sync_call_pattern, html_content):
        print("   🗑️ Removing calls to syncToggleWithLanguage()")
        html_content = re.sub(sync_call_pattern, '', html_content)
    
    # 4️⃣ Xóa old checkbox với id="language-toggle"
    old_checkbox_pattern = r'<input[^>]*id\s*=\s*["\']language-toggle["\'][^>]*>'
    if re.search(old_checkbox_pattern, html_content):
        print("   🗑️ Removing old language-toggle checkbox")
        html_content = re.sub(old_checkbox_pattern, '', html_content)
    
    # 5️⃣ Xóa function changeLanguage() cũ (nếu có)
    change_lang_pattern = r'function\s+changeLanguage\s*\([^)]*\)\s*\{[^}]*localStorage\.setItem\(["\']selectedLanguage["\'][^}]*\}'
    if re.search(change_lang_pattern, html_content, re.DOTALL):
        print("   🗑️ Removing old changeLanguage() function")
        html_content = re.sub(change_lang_pattern, '', html_content, flags=re.DOTALL)
    
    # 6️⃣ Xóa event listener cho toggle cũ
    toggle_listener_pattern = r'document\.getElementById\(["\']language-toggle["\']\)\.addEventListener\([^)]*\)[^;]*;'
    if re.search(toggle_listener_pattern, html_content):
        print("   🗑️ Removing old toggle event listener")
        html_content = re.sub(toggle_listener_pattern, '', html_content)
    
    # 7️⃣ 🔥 XÓA CODE LẤY NGÔN NGỮ TỪ TRÌNH DUYỆT (CRITICAL!)
    browser_lang_patterns = [
        r'navigator\.language',
        r'navigator\.languages\[0\]',
        r'window\.navigator\.language',
        r'const\s+browserLang\s*=\s*navigator\.language[^;]*;',
        r'let\s+browserLang\s*=\s*navigator\.language[^;]*;',
        r'var\s+browserLang\s*=\s*navigator\.language[^;]*;',
        # Pattern phức tạp: const lang = navigator.language.split('-')[0];
        r'(const|let|var)\s+\w+\s*=\s*navigator\.language\.split\([^)]*\)\[0\]\s*;',
    ]
    
    for pattern in browser_lang_patterns:
        if re.search(pattern, html_content):
            print(f"   🔥 CRITICAL: Found browser language detection! Removing...")
            html_content = re.sub(pattern, '', html_content)
    
    # 8️⃣ Tìm và cảnh báo nếu có code set language từ navigator
    if 'navigator.language' in html_content or 'navigator.languages' in html_content:
        print("   ⚠️⚠️⚠️ WARNING: Still found navigator.language in HTML!")
        print("   ⚠️⚠️⚠️ This may cause auto-switching to browser language!")
        print("   ⚠️⚠️⚠️ Please manually remove it from the HTML file!")
    
    # ============================
    # ✅ INJECT CODE MỚI
    # ============================
    
    has_toggle_container = 'language-toggle-container' in html_content
    is_main_web = 'main_web' in html_content.lower() or 'id="map"' in html_content
    
    if is_main_web:
        # ✅ MAIN_WEB.HTML: Inject FULL component (có nút toggle)
        if has_toggle_container:
            print("   ℹ️ Language toggle already exists, skipping inject")
            return html_content
        
        from language_toggle_component import get_language_toggle_html
        language_toggle_html = get_language_toggle_html()
        
        if '<body>' in html_content:
            html_content = html_content.replace(
                '<body>',
                f'<body>\n{language_toggle_html}\n',
                1
            )
            print("   ✅ Language toggle injected (main_web.html)")
        elif '</body>' in html_content:
            html_content = html_content.replace(
                '</body>',
                f'{language_toggle_html}\n</body>',
                1
            )
            print("   ✅ Language toggle injected (fallback)")
    
    else:
        # ✅ CÁC TRANG KHÁC: Chỉ inject SCRIPT (không có nút)
        if has_toggle_container:
            print("   🗑️ Removing language toggle container from secondary page")
            # Xóa toàn bộ div#language-toggle-container
            pattern = r'<div id="language-toggle-container">.*?</div>\s*<style>.*?</style>\s*<script>.*?</script>\s*<!-- .*? -->'
            html_content = re.sub(pattern, '', html_content, flags=re.DOTALL)
        
        from language_toggle_component import get_language_script_only
        script_only = get_language_script_only()
        
        if '</body>' in html_content:
            html_content = html_content.replace(
                '</body>',
                f'{script_only}\n</body>',
                1
            )
            print("   ✅ Language script injected (secondary page - no UI)")
    
    return html_content

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
    print("\n📄 Serving: main_web.html")
    
    with open(WEB_FILE, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # ✅ Inject Language Toggle TRƯỚC (ở đầu <body>)
    html_content = inject_language_toggle(html_content)

    # Lấy chatbot HTML
    chatbot_html = get_chatbot_html(GEMINI_API_KEY)
    
    # Lấy food planner HTML
    food_planner_html = get_food_planner_html()

    music_player_html = get_music_player_html()
    
    # Inject vào div#insert-chatbot-and-map
    insert_point = '<div id="insert-chatbot-and-map">'
    if insert_point in html_content:
        html_content = html_content.replace(
            insert_point,
            f'{insert_point}\n{chatbot_html}\n{food_planner_html}\n{music_player_html}'
        )
    else:
        # Fallback: inject trước </body> nếu không tìm thấy
        html_content = html_content.replace("</body>", f"{chatbot_html}\n{food_planner_html}\n{music_player_html}</body>")
    
    return html_content

@app.route("/account")
@app.route("/Account.html")
def serve_account():
    """Serve trang account với language toggle"""
    print("\n📄 Serving: Account.html")
    
    try:
        # ✅ KIỂM TRA FILE TỒN TẠI TRƯỚC
        if not os.path.exists(ACCOUNT_FILE):
            print(f"❌ Không tìm thấy Account.html tại: {ACCOUNT_FILE}")
            return "Account page not found", 404
        
        # ✅ SAU ĐÓ MỚI MỞ FILE
        with open(ACCOUNT_FILE, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        # ✅ Inject Language Toggle
        html_content = inject_language_toggle(html_content)

        return html_content
        
    except FileNotFoundError:
        return "Account page not found", 404

# ============================
# ✨ SERVE CÁC FILE HTML TRONG user_management/templates
# ============================
@app.route("/accounts/<path:filename>")
def serve_user_management_html(filename):
    """
    Tự động serve và inject language toggle vào tất cả HTML trong user_management
    Ví dụ: /accounts/login/, /accounts/signup/, etc.
    """
    print(f"\n📄 Serving: user_management/templates/{filename}")
    
    # Đường dẫn đến file
    template_path = os.path.join(BASE_DIR, "user_management", "templates", filename)
    
    # Nếu không có extension, thử thêm .html
    if not os.path.exists(template_path) and not filename.endswith('.html'):
        template_path = os.path.join(BASE_DIR, "user_management", "templates", f"{filename}.html")
    
    if not os.path.exists(template_path):
        return "Page not found", 404
    
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        # ✅ Tự động inject Language Toggle nếu là file HTML
        if template_path.endswith('.html'):
            html_content = inject_language_toggle(html_content)
        
        return html_content
        
    except Exception as e:
        print(f"❌ Lỗi đọc file: {e}")
        return f"Error loading page: {str(e)}", 500

# ✅ CHỈ GIỮ 1 ROUTE serve_static_files
@app.route("/<path:path>")
def serve_static_files(path):
    """Serve các file static khác (CSS, JS, images, etc.)"""
    return send_from_directory("../frontend", path)

# ============================
# 🚀 CHẠY SERVER
# ============================
if __name__ == "__main__":
    print(f"📂 Đang chạy Flask tại: {os.path.abspath(BASE_DIR)}")
    print(f"📄 File CSV: {os.path.exists(CSV_FILE)}")
    print(f"📄 File reviews.json: {os.path.exists(REVIEWS_FILE)}")
    print(f"📄 Languages File: {'✅ Found' if os.path.exists(LANGUAGES_FILE) else '⚠️ Not Found (using defaults)'}")
    print("=" * 60)
    print("🎉 COMPONENTS LOADED:")
    print("   ✅ Chatbot Component")
    print("   ✅ Food Planner Component")
    print("   ✅ Music Player Component")
    print("   ✅ Language Toggle Component (V2 - Real-time Sync) 🆕")
    print("=" * 60)
    print("🌐 API ENDPOINTS:")
    print("   • GET  /                    → Main page (main_web.html)")
    print("   • GET  /account             → Account page")
    print("   • GET  /accounts/<file>     → User management pages")
    print("   • GET  /api/places          → Get restaurant list")
    print("   • GET  /api/reviews/<id>    → Get reviews")
    print("   • GET  /api/food-plan       → Generate food plan")
    print("   • GET  /languages.json      → Get translations")
    print("=" * 60)
    print("✨ AUTO-INJECT FEATURES:")
    print("   • Language Toggle → All HTML pages")
    print("   • Real-time sync → Between all tabs")
    print("   • Auto cleanup → Remove old scripts")
    print("=" * 60)
    print("🔥 Server running at: http://localhost:5000")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=False)