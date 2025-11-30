# auto_replace_images.py (PHIÊN BẢN ĐẦY ĐỦ)
import re
from pathlib import Path
import csv

# ⭐ CLOUD NAME CỦA BẠN
CLOUD_NAME = "dbmq2hme4"
BASE_URL = f"https://res.cloudinary.com/{CLOUD_NAME}/image/upload"

def replace_in_file(file_path):
    """Tự động thay thế tất cả đường dẫn ảnh trong HTML/CSS/JS"""
    try:
        content = file_path.read_text(encoding='utf-8')
    except:
        print(f"⚠️  Skip: {file_path.name} (encoding error)")
        return False
    
    original = content
    
    # Pattern 1: src="images/xxx.png"
    content = re.sub(
        r'src=["\']images/([^"\']+)["\']',
        f'src="{BASE_URL}/images/\\1"',
        content
    )
    
    # Pattern 2: src="Picture/xxx.png"
    content = re.sub(
        r'src=["\']Picture/([^"\']+)["\']',
        f'src="{BASE_URL}/Picture/\\1"',
        content
    )
    
    # Pattern 3: src="icons/xxx.png"
    content = re.sub(
        r'src=["\']icons/([^"\']+)["\']',
        f'src="{BASE_URL}/icons/\\1"',
        content
    )
    
    # Pattern 4: src="disc_covers/xxx.png"
    content = re.sub(
        r'src=["\']disc_covers/([^"\']+)["\']',
        f'src="{BASE_URL}/disc_covers/\\1"',
        content
    )
    
    # Pattern 5: CSS background: url('images/xxx.png')
    content = re.sub(
        r'url\(["\']?images/([^)"\';]+)["\']?\)',
        f'url({BASE_URL}/images/\\1)',
        content
    )
    
    # Pattern 6: CSS background: url('Picture/xxx.png')
    content = re.sub(
        r'url\(["\']?Picture/([^)"\';]+)["\']?\)',
        f'url({BASE_URL}/Picture/\\1)',
        content
    )
    
    # Pattern 7: CSS background: url('icons/xxx.png')
    content = re.sub(
        r'url\(["\']?icons/([^)"\';]+)["\']?\)',
        f'url({BASE_URL}/icons/\\1)',
        content
    )
    
    # Pattern 8: JS strings: "images/xxx.png"
    content = re.sub(
        r'(["\'])images/([^"\']+\.(png|jpg|jpeg|gif|webp|svg|ico))\1',
        f'\\1{BASE_URL}/images/\\2\\1',
        content,
        flags=re.IGNORECASE
    )
    
    # Pattern 9: JS strings: 'Picture/xxx.png'
    content = re.sub(
        r'(["\'])Picture/([^"\']+\.(png|jpg|jpeg|gif|webp|svg|ico))\1',
        f'\\1{BASE_URL}/Picture/\\2\\1',
        content,
        flags=re.IGNORECASE
    )
    
    # Pattern 10: JS strings: 'icons/xxx.png'
    content = re.sub(
        r'(["\'])icons/([^"\']+\.(png|jpg|jpeg|gif|webp|svg|ico))\1',
        f'\\1{BASE_URL}/icons/\\2\\1',
        content,
        flags=re.IGNORECASE
    )
    
    if content != original:
        file_path.write_text(content, encoding='utf-8')
        return True
    return False

def replace_in_csv(csv_path):
    """Thay thế đường dẫn ảnh trong file CSV"""
    try:
        # Đọc CSV
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            fieldnames = reader.fieldnames
        
        modified = False
        
        # Thay thế trong từng row
        for row in rows:
            # Thay thế trong cột 'thuc_don'
            if 'thuc_don' in row and row['thuc_don']:
                original = row['thuc_don']
                # Thay thế images/xxx.png
                row['thuc_don'] = re.sub(
                    r'images/([^;,\s]+)',
                    f'{BASE_URL}/images/\\1',
                    row['thuc_don']
                )
                if row['thuc_don'] != original:
                    modified = True
            
            # Thay thế trong cột 'hinh_anh'
            if 'hinh_anh' in row and row['hinh_anh']:
                original = row['hinh_anh']
                # Thay thế images/xxx.png
                row['hinh_anh'] = re.sub(
                    r'images/([^;,\s]+)',
                    f'{BASE_URL}/images/\\1',
                    row['hinh_anh']
                )
                if row['hinh_anh'] != original:
                    modified = True
        
        if modified:
            # Ghi lại CSV
            with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Lỗi khi xử lý CSV: {e}")
        return False

# ===== PHẦN 1: XỬ LÝ HTML, CSS, JS =====
frontend_path = Path("frontend")
file_patterns = ["*.html", "*.css", "*.js"]

print(f"🚀 Bắt đầu thay thế đường dẫn ảnh...")
print(f"📁 Thư mục: {frontend_path.absolute()}")
print(f"🌐 Base URL: {BASE_URL}\n")

updated_files = []
skipped_files = []

for pattern in file_patterns:
    for file_path in frontend_path.glob(pattern):
        if replace_in_file(file_path):
            updated_files.append(file_path.name)
            print(f"✅ Updated: {file_path.name}")
        else:
            skipped_files.append(file_path.name)
            print(f"ℹ️  No change: {file_path.name}")

# ===== PHẦN 2: XỬ LÝ FILE CSV =====
print(f"\n📄 Đang xử lý file CSV...")

csv_path = Path("backend/Data_with_flavor.csv")

if csv_path.exists():
    if replace_in_csv(csv_path):
        print(f"✅ Updated: {csv_path.name}")
        updated_files.append(csv_path.name)
    else:
        print(f"ℹ️  No change: {csv_path.name}")
        skipped_files.append(csv_path.name)
else:
    print(f"⚠️  Không tìm thấy: {csv_path}")

# ===== KẾT QUẢ =====
print(f"\n{'='*60}")
print(f"✨ HOÀN THÀNH!")
print(f"{'='*60}")
print(f"📊 Thống kê:")
print(f"   - Đã cập nhật: {len(updated_files)} files")
print(f"   - Không thay đổi: {len(skipped_files)} files")

if updated_files:
    print(f"\n📝 Các file đã được cập nhật:")
    for f in updated_files:
        print(f"   ✅ {f}")

print(f"\n💡 Bước tiếp theo:")
print(f"   1. cd frontend")
print(f"   2. python -m http.server 8080")
print(f"   3. Mở http://localhost:8080/main_web.html")