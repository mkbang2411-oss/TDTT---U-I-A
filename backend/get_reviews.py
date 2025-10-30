import pandas as pd
import requests
import json
import os
import time

# ⚙️ Cấu hình
SERP_API_KEY = "c56afb87e174c9e1d73c0687e87900bfe2801e203aaba618732e2fe2e6e14f16"  # nhập key của bạn
CSV_FILE = "Data.csv"
REVIEWS_FILE = "reviews.json"


def get_google_reviews(data_id):
    """
    Gọi SerpAPI để lấy review thật từ Google Maps theo data_id
    """
    if not SERP_API_KEY:
        print("⚠️ Chưa có SERP_API_KEY. Hãy đặt biến môi trường hoặc sửa trong code.")
        return []

    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_maps_reviews",
        "data_id": data_id,
        "api_key": SERP_API_KEY
    }

    try:
        res = requests.get(url, params=params, timeout=30)
        if res.status_code != 200:
            print(f"⚠️ Lỗi HTTP {res.status_code} cho data_id={data_id}")
            return []
        data = res.json()
    except Exception as e:
        print(f"❌ Lỗi khi gọi API cho {data_id}: {e}")
        return []

    reviews = data.get("reviews", [])
    result = []
    for r in reviews:
        result.append({
            "user": r.get("user", {}).get("name", "Ẩn danh"),
            "avatar": r.get("user", {}).get("thumbnail", ""),
            "rating": r.get("rating", ""),
            "comment": r.get("snippet", ""),
            "date": r.get("date", "")
        })
    return result


def crawl_all_reviews():
    """
    Lấy review cho toàn bộ quán trong Data.csv
    và lưu vào reviews.json
    """
    if not os.path.exists(CSV_FILE):
        print(f"❌ Không tìm thấy file {CSV_FILE}")
        return

    df = pd.read_csv(CSV_FILE)
    all_reviews = {}

    if os.path.exists(REVIEWS_FILE):
        with open(REVIEWS_FILE, "r", encoding="utf-8") as f:
            try:
                all_reviews = json.load(f)
            except json.JSONDecodeError:
                all_reviews = {}

    print(f"📊 Tổng quán trong {CSV_FILE}: {len(df)}")
    print("🚀 Bắt đầu lấy review...")

    for idx, row in df.iterrows():
        data_id = str(row.get("data_id", "")).strip()
        ten_quan = row.get("ten_quan", "Không tên")

        if not data_id:
            continue

        # Nếu đã có review thì bỏ qua (để tiết kiệm API)
        if data_id in all_reviews:
            print(f"⏩ Bỏ qua {ten_quan} (đã có trong reviews.json)")
            continue

        reviews = get_google_reviews(data_id)
        all_reviews[data_id] = reviews

        print(f"✅ {idx+1}/{len(df)} - {ten_quan}: {len(reviews)} review")

        # Lưu dần để tránh mất dữ liệu
        with open(REVIEWS_FILE, "w", encoding="utf-8") as f:
            json.dump(all_reviews, f, ensure_ascii=False, indent=2)

        time.sleep(5)  # để tránh vượt giới hạn SerpAPI

    print(f"🎉 Hoàn tất! Dữ liệu lưu vào {REVIEWS_FILE}")


if __name__ == "__main__":
    crawl_all_reviews()
