import pandas as pd
import requests
import json
import os
import time

# ⚙️ Cấu hình
SERP_API_KEY = "919519991034d358c7da2ae6f11bc21ded6a8e50a6193c568000e4ef8c9d8e2a"  # nhập key của bạn
CSV_FILE = "Data.csv"
REVIEWS_FILE = "reviews.json"


def get_google_reviews(data_id, max_reviews=16):
    """
    Gọi SerpAPI để lấy tối đa `max_reviews` review (tối đa 20)
    Không yêu cầu phải có đủ các mức sao.
    """
    if not SERP_API_KEY:
        print("⚠️ Chưa có SERP_API_KEY. Hãy đặt biến môi trường hoặc sửa trong code.")
        return []

    all_reviews = []
    page_token = None
    page = 1

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
                print(f"⚠️ Lỗi HTTP {res.status_code} (page {page}) cho data_id={data_id}")
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

            page += 1
            time.sleep(3)

        except Exception as e:
            print(f"❌ Lỗi khi gọi API cho {data_id}: {e}")
            break

    return all_reviews[:max_reviews]


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

        # ✅ Nếu đã có >= 16 review thì bỏ qua
        existing = all_reviews.get(data_id, [])
        if len(existing) >= 16:
            print(f"✅ Bỏ qua {ten_quan} (đã có {len(existing)} review)")
            continue

        print(f"🔁 Đang lấy review cho {ten_quan}...")
        reviews = get_google_reviews(data_id, max_reviews=20)
        all_reviews[data_id] = reviews

        print(f"✅ {idx+1}/{len(df)} - {ten_quan}: {len(reviews)} review")

        # Lưu dần để tránh mất dữ liệu
        with open(REVIEWS_FILE, "w", encoding="utf-8") as f:
            json.dump(all_reviews, f, ensure_ascii=False, indent=2)

        time.sleep(5)  # tránh vượt giới hạn API

    print(f"🎉 Hoàn tất! Dữ liệu lưu vào {REVIEWS_FILE}")


if __name__ == "__main__":
    crawl_all_reviews()
