import re
import csv
from pathlib import Path

# CLOUD NAME CỦA BẠN
CLOUD_NAME = "dbmq2hme4"
BASE_URL = f"https://res.cloudinary.com/{CLOUD_NAME}/image/upload"

def fix_local_path(path):
    """
    Nếu path đã là URL Cloudinary → giữ nguyên.
    Nếu là images/xxx.png → convert sang Cloudinary.
    Nếu là rỗng → giữ nguyên.
    """
    if not path or path.startswith("http://") or path.startswith("https://"):
        return path  # không replace link Cloudinary hoặc link HTTP

    # Nếu path bắt đầu bằng images/
    if path.startswith("images/"):
        return f"{BASE_URL}/{path}"

    return path  # fallback an toàn


def replace_in_csv(csv_path):
    """Thay thế đường dẫn ảnh trong file CSV (chỉ trong Data_with_flavor.csv)."""
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            fieldnames = reader.fieldnames
    
        modified = False

        for row in rows:
            # ----- Cột 'thuc_don' -----
            if "thuc_don" in row and row["thuc_don"]:
                images = row["thuc_don"].split(";")
                fixed = [fix_local_path(x.strip()) for x in images]
                new_value = ";".join(fixed)

                if new_value != row["thuc_don"]:
                    row["thuc_don"] = new_value
                    modified = True

            # ----- Cột 'hinh_anh' -----
            if "hinh_anh" in row and row["hinh_anh"]:
                images = row["hinh_anh"].split(";")
                fixed = [fix_local_path(x.strip()) for x in images]
                new_value = ";".join(fixed)

                if new_value != row["hinh_anh"]:
                    row["hinh_anh"] = new_value
                    modified = True

        # Ghi file nếu có thay đổi
        if modified:
            with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            
            print(f"✅ Đã cập nhật link ảnh trong {csv_path.name}")
            return True
        else:
            print(f"ℹ️ Không có thay đổi trong {csv_path.name}")
            return False

    except Exception as e:
        print(f"❌ Lỗi khi xử lý CSV: {e}")
        return False


# ===== CHẠY SCRIPT =====
csv_path = Path("backend/Data_with_flavor.csv")

print("\n🚀 Bắt đầu xử lý CSV...")
if csv_path.exists():
    replace_in_csv(csv_path)
else:
    print(f"❌ Không tìm thấy file: {csv_path}")

print("\n✨ HOÀN TẤT!")
