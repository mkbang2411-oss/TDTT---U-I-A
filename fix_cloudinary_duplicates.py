import csv
import re
from pathlib import Path

CLOUD_NAME = "dbmq2hme4"
BASE = f"https://res.cloudinary.com/{CLOUD_NAME}/image/upload/"

# Regex bắt lỗi link bị lặp domain
pattern = re.compile(
    rf"(https://res\.cloudinary\.com/{CLOUD_NAME}/image/upload/)+",
    re.IGNORECASE
)

def fix_cloudinary_url(url):
    """Sửa URL bị lặp domain Cloudinary."""
    if not url:
        return url

    # Nếu có lặp, chỉ giữ 1 lần domain
    fixed = pattern.sub(BASE, url)

    return fixed


def fix_csv(csv_path):
    csv_path = Path(csv_path)

    if not csv_path.exists():
        print("❌ Không tìm thấy file CSV!")
        return

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames

    modified = False

    for row in rows:
        for col in row:
            value = row[col]

            if not value:
                continue

            original = value
            fixed = fix_cloudinary_url(value)

            # Nếu cột chứa nhiều ảnh phân tách bằng ;
            if ";" in fixed:
                items = [fix_cloudinary_url(x.strip()) for x in fixed.split(";")]
                fixed = ";".join(items)

            if fixed != original:
                row[col] = fixed
                modified = True

    # Ghi lại file CSV khi có thay đổi
    if modified:
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        print("✅ Đã sửa xong toàn bộ link bị lặp domain Cloudinary!")
    else:
        print("ℹ️ Không có link nào bị lặp domain.")

# Chạy sửa file
fix_csv("backend/Data_with_flavor.csv")
