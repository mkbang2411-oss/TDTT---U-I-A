import csv
import re
import os

# ======================================================
# 🔹 1. Cấu hình file
# ======================================================
BASE_DIR = os.path.dirname(__file__)  # thư mục chứa get_flavor.py
INPUT_CSV = os.path.join(BASE_DIR, "Data.csv")
OUTPUT_CSV = os.path.join(BASE_DIR, "Data_with_flavor.csv")

# ======================================================
# 🔹 2. Bảng từ khóa khẩu vị
# ======================================================
rules = {
    "cay": ["cay", "sa tế", "ớt", "huế", "lẩu thái", "kim chi", "hàn quốc"],
    "mặn": ["mặn", "phở", "cơm tấm", "sườn", "bánh canh", "bún", "bò kho", "trứng muối","bánh mì","lẩu"],
    "ngọt": ["ngọt","bánh", "cake", "chè", "trà sữa", "kem", "bánh ngọt", "sữa chua", "sữa tươi", "matcha","kẹo","bakery","bánh flan"],
    "chua": ["chua", "me", "chanh", "tắc", "dấm", "giấm", "canh chua", "thái"],
    "đắng": ["coffe", "đắng", "trà", "matcha", "ca cao", "socola", "cacao"],
    "tanh": ["hải sản", "cá", "tôm", "mực", "ốc", "hến", "nghêu", "sò", "gỏi cá", "lẩu hải sản"],
}

# ======================================================
# 🔹 3. Hàm nhận diện khẩu vị theo tên quán
# ======================================================
def detect_flavor_from_name(name: str) -> str:
    name_lower = name.lower()
    matched_flavors = []

    for flavor, keywords in rules.items():
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", name_lower):
                matched_flavors.append(flavor)
                break  # nếu khớp 1 keyword thì đủ cho vị đó

    if not matched_flavors:
        return "không xác định"

    # loại trùng, giữ thứ tự
    matched_flavors = list(dict.fromkeys(matched_flavors))
    return ", ".join(matched_flavors)

# ======================================================
# 🔹 4. Đọc và xử lý file CSV
# ======================================================
results = []

# Sử dụng utf-8-sig để xử lý BOM nếu có
with open(INPUT_CSV, encoding="utf-8-sig", newline='') as f:
    reader = csv.DictReader(f, delimiter=',')
    
    # Debug: In ra tên cột để kiểm tra
    print("📋 Các cột trong CSV:", reader.fieldnames)
    print()
    
    # Lọc bỏ các cột None/rỗng trong fieldnames
    valid_fieldnames = [field for field in reader.fieldnames if field and field.strip()]
    print(f"📋 Các cột hợp lệ: {valid_fieldnames}")
    print()
    
    for row in reader:
        # Loại bỏ các key None/rỗng khỏi row
        cleaned_row = {k: v for k, v in row.items() if k and k.strip()}
        
        # Kiểm tra xem cột 'ten_quan' có tồn tại không
        if "ten_quan" not in cleaned_row:
            print(f"⚠️ Lỗi: Không tìm thấy cột 'ten_quan'. Các cột có sẵn: {list(cleaned_row.keys())}")
            break
            
        shop_name = cleaned_row["ten_quan"]
        flavor = detect_flavor_from_name(shop_name)
        print(f"🏪 {shop_name} → 🍽️ {flavor}")
        
        # Thêm cột khẩu vị
        cleaned_row["khau_vi"] = flavor
        results.append(cleaned_row)

# ======================================================
# 🔹 5. Ghi file kết quả
# ======================================================
if results:
    # Lấy fieldnames từ dòng đầu tiên (đã được làm sạch)
    fieldnames = list(results[0].keys())
    
    print(f"\n📝 Các cột sẽ được ghi: {fieldnames}")
    
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✅ Đã lưu kết quả vào: {OUTPUT_CSV}")
    print(f"✅ Tổng số quán đã xử lý: {len(results)}")
else:
    print("\n❌ Không có dữ liệu để ghi. Vui lòng kiểm tra lại file CSV.")
