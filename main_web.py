from flask import Flask, jsonify, request, send_from_directory, Response
from chatbot_component_v2 import render_food_chatbot
import pandas as pd
import os
import json
import streamlit.components.v1 as components

app = Flask(__name__)
CSV_FILE = "Data.csv"


@app.route("/api/places", methods=["GET"])
def get_places_data():
    """Trả danh sách quán ăn từ Data.csv"""
    if not os.path.exists(CSV_FILE):
        return jsonify([])

    df = pd.read_csv(CSV_FILE)

    # 🔧 Chuyển NaN -> None
    df = df.where(pd.notnull(df), None)

    # ⚙️ Lọc theo từ khóa nếu có
    query = request.args.get("query", "").lower()
    if query:
        df = df[df["ten_quan"].str.lower().str.contains(query, na=False) |
                df["dia_chi"].str.lower().str.contains(query, na=False)]

    # 🚀 Xuất ra JSON đúng chuẩn (không có NaN)
    json_str = df.to_json(orient="records", force_ascii=False)
    data = json.loads(json_str)
    return jsonify(data)


# --- Giao diện web ---
@app.route("/<path:path>")
def serve_frontend(path):
    return send_from_directory("frontend", path)

@app.route("/")
def serve_index():
    return send_from_directory("frontend", "index.html")

if __name__ == "__main__":
    app.run(debug=True)
    
#---CHATBOT-----Start--------------------------------------------------------
GEMINI_API_KEY = "AIzaSyApgc9Zzduf1d7LdXUvsZriymK4RvBHOjc"
render_food_chatbot(gemini_api_key=GEMINI_API_KEY)
