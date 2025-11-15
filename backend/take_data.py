from serpapi import GoogleSearch
import pandas as pd
import os
import time

# ⚙️ Cấu hình
SERP_API_KEY = "919519991034d358c7da2ae6f11bc21ded6a8e50a6193c568000e4ef8c9d8e2a"  # Nhớ điền key thật của bạn
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
    """Chuyển đổi dữ liệu từ SerpAPI thành DataFrame chuẩn các cột"""
    if not places:
        return pd.DataFrame()

    records = []
    for p in places:
        if "gps_coordinates" not in p:
            continue

        # Danh sách món
        menu_items = ""
        if "menu_items" in p and isinstance(p["menu_items"], list):
            menu_items = ", ".join([i.get("title", "") for i in p["menu_items"]])

        # Giá trung bình
        price = p.get("price", p.get("price_level", ""))

        # Giờ mở cửa
        gio_mo_cua = p.get("open_state") or p.get("hours") or "Không rõ giờ mở cửa"

        # Thêm các cột mới: khẩu vị, mô tả (nếu SerpAPI không có, để trống)
        khau_vi = p.get("keywords", "")  # ví dụ SerpAPI trả về tags/keywords
        mo_ta = p.get("description", "")

        records.append({
            "ten_quan": p.get("title", ""),
            "dia_chi": p.get("address", ""),
            "so_dien_thoai": p.get("phone", ""),
            "rating": p.get("rating", ""),
            "gio_mo_cua": gio_mo_cua,
            "lat": p["gps_coordinates"]["latitude"],
            "lon": p["gps_coordinates"]["longitude"],
            "gia_trung_binh": price,
            "thuc_don": menu_items,
            "hinh_anh": "",  # bạn có thể điền link hình nếu muốn
            "data_id": p.get("data_id", ""),
            "khau_vi": "",
            "mo_ta": ""
        })

    # Chọn thứ tự cột chuẩn
    df = pd.DataFrame(records)
    df = df[[
        "ten_quan", "dia_chi", "so_dien_thoai", "rating", "gio_mo_cua",
        "lat", "lon", "gia_trung_binh", "thuc_don", "hinh_anh", "data_id",
        "khau_vi", "mo_ta"
    ]]
    return df



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
         "Quận 1": (10.77566, 106.70042),
    "Quận 3": (10.78353, 106.68710),
    "Quận 4": (10.76073, 106.70755),
    "Quận 5": (10.75669, 106.66370),
    "Quận 6": (10.74805, 106.63550),
    "Quận 7": (10.73861, 106.72639),
    "Quận 8": (10.72464, 106.62863),
    "Quận 10": (10.77347, 106.66700),
    "Quận 11": (10.76287, 106.65015),
    "Quận 12": (10.86752, 106.64113),
    "Bình Thạnh": (10.81058, 106.70915),
    "Gò Vấp": (10.83806, 106.66750),
    "Phú Nhuận": (10.79919, 106.68026),
    "Tân Bình": (10.80203, 106.64931),
    "Tân Phú": (10.78640, 106.62883),

    # Thành phố Thủ Đức (tương ứng Quận 2 + 9 + Thủ Đức cũ)
    "Thành phố Thủ Đức": (10.84941, 106.75371)
    }

    query = input("🔍 Nhập từ khóa muốn tìm (vd: phở, trà sữa, cơm tấm): ").strip()
    print(f"🚀 Bắt đầu crawl '{query}' ...\n")

    for name, (lat, lon) in DISTRICTS.items():
        print(f"📍 {name} ({lat}, {lon})")
        data = crawl_and_save_places(query, lat, lon)
        print(f"✅ {name}: {len(data)} kết quả.\n")
        time.sleep(5)

    print("🎉 Hoàn tất! Dữ liệu lưu trong Data.csv")