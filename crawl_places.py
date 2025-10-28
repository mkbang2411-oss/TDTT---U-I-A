from serpapi import GoogleSearch
import pandas as pd
import os
import time

# ⚙️ Cấu hình
#94605f0ff0080702a523fc8065a1e348af088289a63febf6aa93b5cc9f375d75
SERP_API_KEY = "94605f0ff0080702a523fc8065a1e348af088289a63febf6aa93b5cc9f375d75"
CSV_FILE = "Data.csv"


def get_places(query: str, lat: float, lon: float):
    """
    Gọi SerpAPI để lấy danh sách quán gần vị trí chỉ định.
    Trả về danh sách dict (mỗi quán ăn).
    """
    if not SERP_API_KEY:
        print("⚠️ Chưa có SERP_API_KEY. Hãy đặt biến môi trường hoặc sửa trong code.")
        return []

    params = {
        "engine": "google_maps",
        "q": query,
        "ll": f"@{lat},{lon},15z",
        "type": "search",
        "hl": "vi",
        "api_key": SERP_API_KEY
    }

    search = GoogleSearch(params)
    results = search.get_dict()
    return results.get("local_results", [])


def parse_place_data(places: list):
    """Chuyển đổi dữ liệu từ SerpAPI thành DataFrame"""
    if not places:
        return pd.DataFrame()

    records = []
    for p in places:
        if "gps_coordinates" not in p:
            continue

        # 🖼️ Hình ảnh
        image_url = p.get("thumbnail", "")
        if not image_url and "images" in p and p["images"]:
            image_url = p["images"][0].get("image", "")

        # 🍜 Thực đơn
        menu_items = ""
        if "menu_items" in p and isinstance(p["menu_items"], list):
            menu_items = ", ".join([i.get("title", "") for i in p["menu_items"]])

        # 💰 Giá
        price = p.get("price", p.get("price_level", ""))

        records.append({
            "ten_quan": p.get("title", ""),
            "dia_chi": p.get("address", ""),
            "so_dien_thoai": p.get("phone", ""),
            "rating": p.get("rating", ""),
            "gio_mo_cua": p.get("hours", ""),
            "gia_trung_binh": price,
            "thuc_don": menu_items,
            "hinh_anh": image_url,
            "lat": p["gps_coordinates"]["latitude"],
            "lon": p["gps_coordinates"]["longitude"]
        })

    return pd.DataFrame(records)


def save_places_to_csv(df_new: pd.DataFrame, CSV_FILE: str = CSV_FILE):
    """Lưu DataFrame vào CSV, tránh trùng lặp"""
    if df_new.empty:
        print("⚠️ Không có dữ liệu mới.")
        return

    folder = os.path.dirname(CSV_FILE)
    if folder:
        os.makedirs(folder, exist_ok=True)

    if not os.path.exists(CSV_FILE) or os.stat(CSV_FILE).st_size == 0:
        df_new.to_csv(CSV_FILE, index=False)
        print(f"💾 Tạo mới {CSV_FILE} ({len(df_new)} dòng).")
        return

    try:
        df_old = pd.read_csv(CSV_FILE)
    except Exception:
        df_old = pd.DataFrame()

    df_all = pd.concat([df_old, df_new], ignore_index=True)
    df_all.drop_duplicates(subset=["ten_quan", "dia_chi"], inplace=True)
    df_all.to_csv(CSV_FILE, index=False)
    print(f"✅ Cập nhật {CSV_FILE}: tổng {len(df_all)} quán.")


def crawl_and_save_places(query: str, lat: float, lon: float):
    """
    Hàm tổng hợp để backend gọi:
    - Crawl dữ liệu theo query + toạ độ
    - Parse thành DataFrame
    - Lưu CSV
    - Trả về danh sách dict (cho API)
    """
    print(f"🚀 Crawling '{query}' tại ({lat}, {lon}) ...")
    places = get_places(query, lat, lon)
    df_new = parse_place_data(places)
    if not df_new.empty:
        save_places_to_csv(df_new, CSV_FILE)
    else:
        print("❌ Không có dữ liệu thu được.")
    return df_new.to_dict(orient="records")


# ✅ Cho phép chạy thủ công để test CLI
if __name__ == "__main__":
    DISTRICTS = {
        "Quận 1": (10.7769, 106.7009),
        "Quận 3": (10.7840, 106.6945),
        "Quận 5": (10.7520, 106.6620),
    }

    query = input("🔍 Nhập từ khóa muốn tìm (vd: phở, trà sữa, cơm tấm): ").strip()
    print(f"🚀 Bắt đầu crawl '{query}' ...\n")

    for name, (lat, lon) in DISTRICTS.items():
        print(f"📍 {name} ({lat}, {lon})")
        data = crawl_and_save_places(query, lat, lon)
        print(f"✅ {name}: {len(data)} kết quả.\n")
        time.sleep(5)

    print("🎉 Hoàn tất! Dữ liệu lưu trong Data.csv")
