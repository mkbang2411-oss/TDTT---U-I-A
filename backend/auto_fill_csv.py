import csv

# ===== TÙY CHỈNH Ở ĐÂY =====
START_ROW = 1601  # Dòng bắt đầu (không tính header)
END_ROW = 1700    # Dòng kết thúc (không tính header)
CSV_FILE = "Data_with_flavor.csv"   # Tên file CSV cần chỉnh sửa
# ============================

def fill_images_and_menu(csv_file, start_row, end_row):
    """
    Điền thông tin hình ảnh và thực đơn vào CSV (chỉnh sửa trực tiếp)
    
    Args:
        csv_file: Đường dẫn file CSV cần chỉnh sửa
        start_row: Số dòng bắt đầu (không tính header, bắt đầu từ 1)
        end_row: Số dòng kết thúc
    """
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            fieldnames = reader.fieldnames
        
        # Kiểm tra các cột cần thiết có tồn tại không
        if 'hinh_anh' not in fieldnames or 'thuc_don' not in fieldnames:
            print("Lỗi: File CSV phải có cột 'hinh_anh' và 'thuc_don'")
            return
        
        # Điền dữ liệu cho các dòng được chỉ định
        for i in range(len(rows)):
            row_number = i + 2  # Số dòng thực tế trong file CSV (+2 vì có header ở dòng 1)
            
            if start_row <= row_number <= end_row:
                # Điền cột hinh_anh
                rows[i]['hinh_anh'] = f"images/{row_number}.png"
                
                # Điền cột thuc_don
                rows[i]['thuc_don'] = f"images/{row_number}.1.png;images/{row_number}.2.png"
                
                print(f"✓ Đã điền dòng {row_number}")
        
        # Ghi đè vào file gốc
        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            writer.writerows(rows)
        
        print(f"\n✅ Hoàn thành! Đã cập nhật {end_row - start_row + 1} dòng vào file '{csv_file}'")
        
    except FileNotFoundError:
        print(f"❌ Lỗi: Không tìm thấy file '{csv_file}'")
    except Exception as e:
        print(f"❌ Lỗi: {str(e)}")

# Chạy script
if __name__ == "__main__":
    print("=" * 50)
    print("SCRIPT ĐIỀN HÌNH ẢNH VÀ THỰC ĐƠN")
    print("=" * 50)
    print(f"Dòng bắt đầu: {START_ROW}")
    print(f"Dòng kết thúc: {END_ROW}")
    print(f"File CSV: {CSV_FILE}")
    print("=" * 50)
    print()
    
    fill_images_and_menu(CSV_FILE, START_ROW, END_ROW)