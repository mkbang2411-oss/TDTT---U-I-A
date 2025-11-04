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
    "mặn": ["mặn", "phở", "cơm tấm", "sườn", "bánh canh", "bún", "bò kho", "trứng muối","bánh mì"],
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
with open(INPUT_CSV, encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        shop_name = row["ten_quan"]
        flavor = detect_flavor_from_name(shop_name)
        print(f"🏪 {shop_name} → 🍽️ {flavor}")
        row["khau_vi"] = flavor
        results.append(row)

# ======================================================
# 🔹 5. Ghi file kết quả (sửa tại đây)
# ======================================================
fieldnames = list(results[0].keys())
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
    writer.writeheader()
    writer.writerows(results)

print(f"\n✅ Đã lưu kết quả vào: {OUTPUT_CSV}")

