import pandas as pd
import requests
import json
import os
import time

# ⚙️ Cấu hình
SERP_API_KEY = "a3ce5e1007e887b80f0c3114d9bd93854917de1e7caae81e7887148f233072a4"  # giữ API key của bạn ở đây

CSV_FILE = "Data_with_flavor.csv"

# Thư mục hiện tại (vd: D:\Food_map\backend)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Thư mục gốc project (vd: D:\Food_map)
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# ✅ File user_reviews.json nằm trong thư mục user_management (D:\Food_map\user_management\user_reviews.json)
REVIEWS_FILE = os.path.join(PROJECT_ROOT, "user_management", "user_reviews.json")


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


def crawl_all_reviews(start_row=None, end_row=None):
    """
    Lấy review cho các quán trong Data.csv
    Có thể giới hạn từ dòng start_row đến end_row (tính từ 1, không tính header).
    Nếu không truyền gì thì sẽ chạy cho toàn bộ file.
    """
    if not os.path.exists(CSV_FILE):
        print(f"❌ Không tìm thấy file {CSV_FILE}")
        return

    df = pd.read_csv(CSV_FILE)

    # 🧮 Chọn khoảng dòng nếu người dùng truyền vào
    # start_row / end_row đang tính từ 1 (dòng đầu tiên sau header là 1)
    if start_row is not None or end_row is not None:
        # Nếu không nhập start thì mặc định từ 1
        if start_row is None:
            start_row = 1
        # Nếu không nhập end thì mặc định đến hết file
        if end_row is None:
            end_row = len(df)

        # Chuyển sang index 0-based cho pandas
        start_idx = max(start_row - 1, 0)
        end_idx = min(end_row, len(df))  # end_idx trong iloc là exclusive

        df = df.iloc[start_idx:end_idx].reset_index(drop=True)
        print(f"🔍 Chỉ crawl từ dòng {start_row} đến dòng {end_row} (tổng {len(df)} dòng).")

    all_reviews = {}

    # Tạo thư mục chứa file json nếu chưa có
    os.makedirs(os.path.dirname(REVIEWS_FILE), exist_ok=True)

    if os.path.exists(REVIEWS_FILE):
        with open(REVIEWS_FILE, "r", encoding="utf-8") as f:
            try:
                all_reviews = json.load(f)
            except json.JSONDecodeError:
                all_reviews = {}

    print(f"📊 Tổng quán sẽ crawl: {len(df)}")
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

        print(f"✅ {idx + 1}/{len(df)} - {ten_quan}: {len(reviews)} review")

        # Lưu dần để tránh mất dữ liệu
        with open(REVIEWS_FILE, "w", encoding="utf-8") as f:
            json.dump(all_reviews, f, ensure_ascii=False, indent=2)

        time.sleep(5)  # tránh vượt giới hạn API

    print(f"🎉 Hoàn tất! Dữ liệu lưu vào {REVIEWS_FILE}")


if __name__ == "__main__":
    # 👇 Hỏi người dùng muốn chạy từ dòng nào đến dòng nào
    print("Nhập khoảng dòng muốn crawl trong Data.csv (tính từ 1, bỏ trống nếu muốn từ đầu / đến cuối).")
    start_input = input("Dòng bắt đầu: ").strip()
    end_input = input("Dòng kết thúc: ").strip()

    start_row = int(start_input) if start_input else None
    end_row = int(end_input) if end_input else None

    crawl_all_reviews(start_row=start_row, end_row=end_row)
