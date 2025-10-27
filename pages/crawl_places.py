from serpapi import GoogleSearch
import pandas as pd
import os
import time

# 🔑 Thay bằng key SerpAPI thật của bạn
SERP_API_KEY = ""
CSV_FILE = "Data.csv"


def get_places(query, lat, lon):
    """Gọi SerpAPI để lấy danh sách quán gần vị trí chỉ định"""
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


def save_places_to_csv(places, CSV_FILE="Data.csv"):
    """Lưu danh sách quán vào CSV, tránh trùng lặp và lỗi file trống"""
    if not places:
        print("⚠️ Không có dữ liệu mới để lưu.")
        return pd.DataFrame()

    new_data = []
    for p in places:
        if "gps_coordinates" not in p:
            continue
        new_data.append({
            "ten_quan": p.get("title", ""),
            "dia_chi": p.get("address", ""),
            "so_dien_thoai": p.get("phone", ""),
            "rating": p.get("rating", ""),
            "gio_mo_cua": p.get("hours", ""),
            "lat": p["gps_coordinates"]["latitude"],
            "lon": p["gps_coordinates"]["longitude"]
        })

    df_new = pd.DataFrame(new_data)

    # 🧩 Tạo thư mục nếu cần
    folder = os.path.dirname(CSV_FILE)
    if folder:
        os.makedirs(folder, exist_ok=True)

    # 🧩 Nếu file chưa tồn tại hoặc trống -> tạo mới
    if not os.path.exists(CSV_FILE) or os.stat(CSV_FILE).st_size == 0:
        df_new.to_csv(CSV_FILE, index=False)
        print(f"💾 Đã tạo mới file {CSV_FILE} với {len(df_new)} quán.")
        return df_new

    # 🧩 Gộp dữ liệu cũ và mới
    try:
        df_old = pd.read_csv(CSV_FILE)
    except Exception:
        df_old = pd.DataFrame()

    df_all = pd.concat([df_old, df_new], ignore_index=True)
    df_all.drop_duplicates(subset=["ten_quan", "dia_chi"], inplace=True)
    df_all.to_csv(CSV_FILE, index=False)

    print(f"✅ Đã thêm {len(df_new)} quán (sau khi lọc trùng: {len(df_all)}) vào {CSV_FILE}")
    return df_new


# 👇 Crawl nhiều khu vực (quận) theo toạ độ
if __name__ == "__main__":
    # Danh sách toạ độ trung tâm các quận TP.HCM
    DISTRICTS = {
        #"Quận 1": (10.7769, 106.7009),
        #"Quận 3": (10.7840, 106.6945),
        "Quận 5": (10.7520, 106.6620),
        #"Bình Thạnh": (10.8050, 106.6960),
        #"Phú Nhuận": (10.7990, 106.6800),
        #"Tân Bình": (10.8010, 106.6520),
        #"Gò Vấp": (10.8340, 106.6800),
        #"Quận 10": (10.7735, 106.6670),
        #"Thủ Đức": (10.8490, 106.7600)
    }

    query = input("🔍 Nhập từ khóa muốn tìm (vd: phở, trà sữa, cơm tấm): ").strip()
    print(f"🚀 Bắt đầu crawl dữ liệu '{query}' cho {len(DISTRICTS)} khu vực...\n")

    for district, (lat, lon) in DISTRICTS.items():
        print(f"📍 Đang crawl {query} tại {district} ({lat}, {lon}) ...")
        data = get_places(query, lat, lon)
        save_places_to_csv(data, CSV_FILE)
        print(f"✅ Hoàn tất {district}, tìm được {len(data)} địa điểm.\n")
        time.sleep(5)  # nghỉ 5 giây tránh bị giới hạn API

    print(f"🎉 Hoàn tất crawl tất cả khu vực! Dữ liệu nằm trong {CSV_FILE}")
