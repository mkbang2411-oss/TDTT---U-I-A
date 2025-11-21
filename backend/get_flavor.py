import csv
import re
import os
from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ======================================================
# 🔹 1. Cấu hình file
# ======================================================
BASE_DIR = os.path.dirname(__file__)          # thư mục chứa get_flavor.py (backend)
PROJECT_ROOT = os.path.dirname(BASE_DIR)      # thư mục gốc project (Food_map)
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

# 🟢 Bây giờ ta chỉ làm việc với Data_with_flavor.csv
CSV_FILE = os.path.join(BASE_DIR, "Data_with_flavor.csv")

# ======================================================
# 🔹 1.1. CHỌN KHOẢNG DÒNG MUỐN XỬ LÝ (TỪ CODE)
#      - Tính từ 1, không tính dòng header
#      - Để None nếu muốn từ đầu / đến cuối
# ======================================================
START_ROW = 1825      # ví dụ: 2
END_ROW   = 1826      # ví dụ: 20

# ======================================================
# 🔹 2. Bảng từ khóa khẩu vị
# ======================================================
rules = {
    "cay": [
        "sa tế", "lẩu thái", "kim chi", "curry", "cà ri",
        "ớt hiểm", "hạt tiêu", "mì cay","mỳ cay",
        "ớt", "huế", "spicy", "chili"
    ],
    "mặn": [
        "bánh canh", "bánh mì", "cơm tấm", "bò kho",
        "trứng muối", "mặn", "phở", "sườn", "bún", "lẩu",
        "fish sauce", "soy sauce","cháy tỏi","chay toi","rang muối","rang muoi"
    ],
    "ngọt": [
        "bánh ngọt", "trà sữa", "sữa chua", "sữa tươi",
        "bánh flan", "ngọt", "bánh", "cake", "chè", "kem",
        "matcha", "kẹo", "bakery", "caramel", "sweet",
        "chocolate", "crème brûlée", "creme brulee"
    ],
    "chua": [
        "canh chua", "chua", "me", "chanh", "tắc", "dấm","bưởi",
        "giấm", "thái", "nước cam", "tamarind", "lemon", "kim chi",
        "lime", "passion fruit"
    ],
    "đắng": [
        "ca cao", "socola", "coffe", "coffee", "đắng",
        "trà", "matcha", "cacao"
    ],
    "tanh": [
        "sushi", "sashimi",
    ],
    "thanh": [
        "thanh mát", "thanh mat", "nước dừa", "nuoc dua",
        "coconut water", "detox","rau",
        "salad", "rau trộn", "rau tron",
        "gỏi rau", "goi rau",
        "fresh herbs", "herbal",
        "nước ép", "nuoc ep", "juice",
        "smoothie",
        "trà trái cây", "tra trai cay",
        "infused water"
    ],
}

# ======================================================
# 🔹 3. Hàm OCR đọc text từ ảnh trong cột 'thuc_don'
# ======================================================
def ocr_menu_images(menu_field: str) -> str:
    if not menu_field:
        return ""

    texts = []
    image_rel_paths = [p.strip() for p in menu_field.split(";") if p.strip()]

    for rel_path in image_rel_paths:
        image_path = os.path.join(FRONTEND_DIR, rel_path.replace("/", os.sep))

        if not os.path.exists(image_path):
            print(f"⚠️ Không tìm thấy ảnh menu: {image_path}")
            continue

        try:
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img, lang="vie+eng")
            texts.append(text)
        except Exception as e:
            print(f"❌ Lỗi OCR với ảnh {image_path}: {e}")

    return "\n".join(texts)

# ======================================================
# 🔹 4. Hàm nhận diện khẩu vị theo text (tên quán / menu)
# ======================================================
def detect_flavor_from_text(text: str) -> str:
    text_lower = text.lower()
    matched_flavors = []
    matched_positions = {}

    for flavor, keywords in rules.items():
        for kw in keywords:
            pattern = rf"\b{re.escape(kw)}\b"
            matches = list(re.finditer(pattern, text_lower))

            for match in matches:
                start, end = match.span()

                overlapped = False
                for saved_flavor, (saved_start, saved_end) in matched_positions.items():
                    if start >= saved_start and end <= saved_end:
                        overlapped = True
                        break
                    elif start <= saved_start and end >= saved_end:
                        if saved_flavor in matched_flavors:
                            matched_flavors.remove(saved_flavor)
                        del matched_positions[saved_flavor]
                        break

                if not overlapped:
                    if flavor not in matched_flavors:
                        matched_flavors.append(flavor)
                    matched_positions[flavor] = (start, end)
                    break

    if not matched_flavors:
        return "không xác định"

    matched_flavors = list(dict.fromkeys(matched_flavors))
    return ", ".join(matched_flavors)

# ======================================================
# 🔹 5. Đọc Data_with_flavor.csv và chỉ UPDATE cột khau_vi
# ======================================================
if not os.path.exists(CSV_FILE):
    raise FileNotFoundError(f"Không tìm thấy file {CSV_FILE}. Hãy tạo nó trước bằng script cũ.")

with open(CSV_FILE, encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f, delimiter=",")
    fieldnames = [fn for fn in (reader.fieldnames or []) if fn and fn.strip()]
    rows = []
    for row in reader:
        cleaned = {k: row.get(k, "") for k in fieldnames}
        rows.append(cleaned)

# đảm bảo luôn có cột khau_vi
if "khau_vi" not in fieldnames:
    fieldnames.append("khau_vi")
    for row in rows:
        row.setdefault("khau_vi", "")

print("📋 Các cột trong dữ liệu:", fieldnames)
print(f"📊 Tổng số dòng dữ liệu: {len(rows)}\n")

processed_count = 0

# BẮT ĐẦU ĐẾM TỪ DÒNG 2 (vì dòng 1 là header)
for file_row_index, row in enumerate(rows, start=2):
    # Bỏ qua nếu trước dòng bắt đầu (theo số dòng file)
    if START_ROW is not None and file_row_index < START_ROW:
        continue

    # Dừng nếu đã vượt quá dòng kết thúc
    if END_ROW is not None and file_row_index > END_ROW:
        break

    if "ten_quan" not in row:
        print(f"⚠️ Lỗi: Không tìm thấy cột 'ten_quan' ở dòng {file_row_index}. Các cột: {list(row.keys())}")
        continue

    shop_name = row["ten_quan"]
    menu_field = row.get("thuc_don", "")

    # 1️⃣ Khẩu vị từ tên quán
    flavor_from_name = detect_flavor_from_text(shop_name)

    # 2️⃣ Khẩu vị từ menu (OCR)
    flavor_from_menu = "không xác định"
    if menu_field:
        menu_text = ocr_menu_images(menu_field)
        if menu_text and len(menu_text.strip()) > 30:
            flavor_from_menu = detect_flavor_from_text(menu_text)

    # 3️⃣ Gộp lại
    flavors = []
    if flavor_from_name != "không xác định":
        flavors.extend([x.strip() for x in flavor_from_name.split(",") if x.strip()])
    if flavor_from_menu != "không xác định":
        flavors.extend([x.strip() for x in flavor_from_menu.split(",") if x.strip()])

    if not flavors:
        final_flavor = "không xác định"
    else:
        final_flavor = ", ".join(dict.fromkeys(flavors))

    row["khau_vi"] = final_flavor
    processed_count += 1

    # In theo số dòng thật trong file
    print(f"#{file_row_index} 🏪 {shop_name} → 🍽️ {final_flavor}")


# ======================================================
# 🔹 6. Ghi lại chính file Data_with_flavor.csv
# ======================================================
print(f"\n💾 Đang ghi cập nhật vào: {CSV_FILE}")
with open(CSV_FILE, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
    writer.writeheader()
    writer.writerows(rows)

print(f"✅ Đã cập nhật xong. Số dòng được xử lý khẩu vị: {processed_count}")
