import pandas as pd
import requests
import json
import os
import time

# ⚙️ Cấu hình
SERP_API_KEY = "caf590cf1799aa732de0975966415b48a4d0911ec5c336407111c0e73fc4ed9d"

CSV_FILE = "Data_with_flavor.csv"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
REVIEWS_FILE = os.path.join(PROJECT_ROOT, "user_management", "user_reviews.json")

# 🎯 Tự chỉnh start / end ngay tại đây
START_ROW = 2457
END_ROW = 2463

# 🔒 Sử dụng đúng 16 review (chuẩn Option B)
MAX_REVIEWS = 16


def get_google_reviews(data_id, max_reviews=MAX_REVIEWS):
    if not SERP_API_KEY:
        print("⚠️ Chưa có SERP_API_KEY.")
        return []

    all_reviews = []
    page_token = None

    while len(all_reviews) < max_reviews:
        params = {
            "engine": "google_maps_reviews",
            "data_id": data_id,
            "api_key": SERP_API_KEY,
        }
        if page_token:
            params["next_page_token"] = page_token

        try:
            res = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
            if res.status_code != 200:
                print(f"⚠️ Lỗi HTTP {res.status_code} cho data_id={data_id}")
                break

            data = res.json()
            reviews = data.get("reviews", [])
            if not reviews:
                break

            for r in reviews:
                all_reviews.append({
                    "user": r.get("user", {}).get("name", "Ẩn danh"),
                    "avatar": r.get("user", {}).get("thumbnail", ""),
                    "rating": r.get("rating", ""),
                    "comment": r.get("snippet", ""),
                    "date": r.get("date", "")
                })
                if len(all_reviews) >= max_reviews:
                    break

            page_token = data.get("serpapi_pagination", {}).get("next_page_token")
            if not page_token:
                break

            time.sleep(2)

        except Exception as e:
            print(f"❌ Lỗi khi gọi API cho {data_id}: {e}")
            break

    return all_reviews[:max_reviews]


def crawl_all_reviews(start_row=None, end_row=None):
    if not os.path.exists(CSV_FILE):
        print(f"❌ Không tìm thấy file {CSV_FILE}")
        return

    df = pd.read_csv(CSV_FILE)

    # Nếu có start/end thì cắt đúng hàng
    if start_row is not None or end_row is not None:
        if start_row is None:
            start_row = 1
        if end_row is None:
            end_row = len(df)

        start_idx = start_row - 1
        end_idx = end_row

        df = df.iloc[start_idx:end_idx].reset_index(drop=True)
        print(f"🔍 Crawl từ dòng {start_row} đến {end_row} — tổng {len(df)} dòng.")

    # Load file JSON cũ
    all_reviews = {}
    os.makedirs(os.path.dirname(REVIEWS_FILE), exist_ok=True)

    if os.path.exists(REVIEWS_FILE):
        with open(REVIEWS_FILE, "r", encoding="utf-8") as f:
            try:
                all_reviews = json.load(f)
            except json.JSONDecodeError:
                all_reviews = {}

    print(f"📊 Tổng quán cần crawl: {len(df)}")
    print("🚀 Bắt đầu...")

    for idx, row in df.iterrows():
        data_id = str(row.get("data_id", "")).strip()
        ten_quan = row.get("ten_quan", "Không tên")

        if not data_id:
            continue

        existing = all_reviews.get(data_id, [])

        # ⛔ Skip đúng chuẩn 16 review
        if len(existing) >= MAX_REVIEWS:
            print(f"✅ Bỏ qua {ten_quan} (đã có {len(existing)} review)")
            continue

        print(f"🔁 Đang lấy review cho {ten_quan}...")

        reviews = get_google_reviews(data_id, max_reviews=MAX_REVIEWS)
        all_reviews[data_id] = reviews

        print(f"✅ {idx + 1}/{len(df)} - {ten_quan}: {len(reviews)} review")

        # Lưu liên tục để tránh mất dữ liệu
        with open(REVIEWS_FILE, "w", encoding="utf-8") as f:
            json.dump(all_reviews, f, ensure_ascii=False, indent=2)

        time.sleep(4)

    print(f"🎉 Hoàn tất! Dữ liệu lưu tại {REVIEWS_FILE}")


if __name__ == "__main__":
    crawl_all_reviews(start_row=START_ROW, end_row=END_ROW)