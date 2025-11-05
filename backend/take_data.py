from serpapi import GoogleSearch
import pandas as pd
import os
import time

# ⚙️ Cấu hình
SERP_API_KEY = "965493118ea3afd38375442b8a2345f83ad60b1a6deea265d96ed02a81d47c94"  # Nhớ điền key thật của bạn
CSV_FILE = "Data.csv"


def get_places(query: str, lat: float, lon: float):
    """Gọi SerpAPI để lấy danh sách quán gần vị trí chỉ định."""
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

        # ❌ Không cần lấy hình ảnh nữa
        image_url = ""

        # 🍜 Thực đơn
        menu_items = ""
        if "menu_items" in p and isinstance(p["menu_items"], list):
            menu_items = ", ".join([i.get("title", "") for i in p["menu_items"]])

        # 💰 Giá
        price = p.get("price", p.get("price_level", ""))

        # 🕒 Giờ mở cửa
        gio_mo_cua = p.get("hours", "")
        if not gio_mo_cua or str(gio_mo_cua).strip() == "":
            gio_mo_cua = "Đang mở cửa ⋅ Đóng cửa lúc 22:00"

        records.append({
            "data_id": p.get("data_id", ""),
            "ten_quan": p.get("title", ""),
            "dia_chi": p.get("address", ""),
            "so_dien_thoai": p.get("phone", ""),
            "rating": p.get("rating", ""),
            "gio_mo_cua": gio_mo_cua,
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
    """Crawl dữ liệu + parse + lưu CSV"""
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
        "Bình Thạnh": (10.8050, 106.6960),
        "Phú Nhuận": (10.7990, 106.6800),
        "Tân Bình": (10.8010, 106.6520),
        "Gò Vấp": (10.8340, 106.6800),
        "Quận 10": (10.7735, 106.6670),
        "Thủ Đức": (10.8490, 106.7600)
    }

    query = input("🔍 Nhập từ khóa muốn tìm (vd: phở, trà sữa, cơm tấm): ").strip()
    print(f"🚀 Bắt đầu crawl '{query}' ...\n")

    for name, (lat, lon) in DISTRICTS.items():
        print(f"📍 {name} ({lat}, {lon})")
        data = crawl_and_save_places(query, lat, lon)
        print(f"✅ {name}: {len(data)} kết quả.\n")
        time.sleep(5)

    print("🎉 Hoàn tất! Dữ liệu lưu trong Data.csv")
