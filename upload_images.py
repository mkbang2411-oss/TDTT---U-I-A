# upload_images_optimized.py
import cloudinary
import cloudinary.uploader
import cloudinary.api
from pathlib import Path

# ⭐ ĐIỀN THÔNG TIN API
cloudinary.config(
    cloud_name="dbmq2hme4",
    api_key="987591597383922",
    api_secret="B7_sz_w_PFIq4Kv6Zb_hP0J1v4k"
)

# ⭐ DANH SÁCH CÁC FOLDER CẦN UPLOAD
folders_to_upload = [
    "images",
    "icons", 
    "Picture",
    "disc_covers"
]

frontend_path = Path(r"D:\Food_map\frontend")

def get_all_cloudinary_images():
    """
    Lấy danh sách TẤT CẢ ảnh trên Cloudinary một lần
    Tiết kiệm API calls!
    """
    print("🔍 Đang lấy danh sách ảnh từ Cloudinary...")
    all_public_ids = set()
    next_cursor = None
    
    try:
        while True:
            # Lấy tối đa 500 ảnh mỗi lần (max của Cloudinary)
            result = cloudinary.api.resources(
                type="upload",
                resource_type="image",
                max_results=500,
                next_cursor=next_cursor
            )
            
            # Thêm public_id vào set
            for resource in result.get('resources', []):
                all_public_ids.add(resource['public_id'])
            
            print(f"   📥 Đã tải: {len(all_public_ids)} ảnh...")
            
            # Kiểm tra có trang tiếp theo không
            next_cursor = result.get('next_cursor')
            if not next_cursor:
                break
                
    except Exception as e:
        print(f"⚠️  Lỗi khi lấy danh sách: {e}")
    
    print(f"✅ Tổng cộng: {len(all_public_ids)} ảnh trên cloud\n")
    return all_public_ids

print("🚀 Bắt đầu upload ảnh lên Cloudinary...")
print(f"📁 Thư mục gốc: {frontend_path}")
print(f"🌐 Cloud: dbmq2hme4")
print(f"📂 Các folder sẽ upload: {', '.join(folders_to_upload)}\n")

# ✅ LẤY DANH SÁCH ẢNH MỘT LẦN DUY NHẤT
existing_images = get_all_cloudinary_images()

uploaded = 0
skipped = 0
failed = 0
total_size_mb = 0

for folder_name in folders_to_upload:
    folder_path = frontend_path / folder_name
    
    if not folder_path.exists():
        print(f"⚠️  Bỏ qua: {folder_name} (không tồn tại)")
        continue
    
    print(f"\n📂 Đang xử lý folder: {folder_name}...")
    
    for image_path in folder_path.rglob("*"):
        # Chỉ upload file ảnh
        if image_path.is_file() and image_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.ico', '.bmp']:
            try:
                # Lấy đường dẫn tương đối từ frontend/
                relative_path = image_path.relative_to(frontend_path)
                
                # Tạo public_id giữ nguyên cấu trúc
                public_id = str(relative_path.with_suffix('')).replace("\\", "/")
                
                # ✅ KIỂM TRA TRONG SET (CỰC NHANH, KHÔNG TỐN API CALL)
                if public_id in existing_images:
                    skipped += 1
                    if skipped % 100 == 0:
                        print(f"   ⏭️  Đã bỏ qua: {skipped} ảnh (đã có trên cloud)")
                    continue
                
                # Upload ảnh mới
                result = cloudinary.uploader.upload(
                    str(image_path),
                    public_id=public_id,
                    overwrite=False,
                    invalidate=True,
                    resource_type="image"
                )
                
                uploaded += 1
                file_size_mb = image_path.stat().st_size / (1024 * 1024)
                total_size_mb += file_size_mb
                
                # Hiện progress mỗi 20 ảnh
                if uploaded % 20 == 0:
                    print(f"   📤 Đã upload: {uploaded} ảnh mới ({total_size_mb:.1f} MB)")
                
            except Exception as e:
                failed += 1
                print(f"   ❌ Lỗi: {relative_path} - {str(e)}")

print(f"\n{'='*70}")
print(f"✨ HOÀN THÀNH!")
print(f"{'='*70}")
print(f"📊 Thống kê:")
print(f"   ✅ Upload mới: {uploaded} ảnh")
print(f"   ⏭️  Bỏ qua (đã có): {skipped} ảnh")
print(f"   ❌ Thất bại: {failed} ảnh")
print(f"   💾 Dung lượng upload: {total_size_mb:.2f} MB")
print(f"   🎯 Tổng xử lý: {uploaded + skipped + failed} ảnh")
print(f"\n📋 Các folder đã xử lý:")
for folder in folders_to_upload:
    print(f"   - {folder}/")
print(f"\n💡 Tiết kiệm: Chỉ dùng ~3-5 API calls thay vì hàng trăm!")