from flask import Flask, jsonify, request, send_from_directory
from chatbot_component_v2 import get_chatbot_html
import pandas as pd
import os
import json

app = Flask(__name__)
CSV_FILE = "Data.csv"
GEMINI_API_KEY = "AIzaSyApgc9Zzduf1d7LdXUvsZriymK4RvBHOjc"


@app.route("/api/places", methods=["GET"])
def get_places_data():
    """Trả danh sách quán ăn từ Data.csv"""
    if not os.path.exists(CSV_FILE):
        return jsonify([])

    df = pd.read_csv(CSV_FILE)
    df = df.where(pd.notnull(df), None)

    query = request.args.get("query", "").lower()
    if query:
        df = df[df["ten_quan"].str.lower().str.contains(query, na=False) |
                df["dia_chi"].str.lower().str.contains(query, na=False)]

    json_str = df.to_json(orient="records", force_ascii=False)
    data = json.loads(json_str)
    return jsonify(data)


@app.route("/")
def serve_index():
    """Serve trang chính với chatbot tích hợp"""
    # Đọc file HTML gốc
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Lấy chatbot HTML
    chatbot_html = get_chatbot_html(GEMINI_API_KEY)
    
    # Inject chatbot vào trước thẻ </body>
    html_content = html_content.replace("</body>", f"{chatbot_html}</body>")
    
    return html_content


@app.route("/<path:path>")
def serve_frontend(path):
    return send_from_directory("frontend", path)


if __name__ == "__main__":
    app.run(debug=True, port=5000)