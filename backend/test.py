import cv2
import numpy as np
from PIL import Image
import pytesseract
import os

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ======================================================
# 🔹 CẤU HÌNH
# ======================================================
IMAGE_PATH = r"D:\Food_map\frontend\images\3.2.png"
SAVE_PROCESSED = True  # Lưu ảnh đã xử lý để xem kết quả

# ======================================================
# 🔹 CÁC HÀM XỬ LÝ ẢNH
# ======================================================

def preprocess_image_v1(image_path):
    """
    Phương pháp 1: Cơ bản - Grayscale + Threshold
    Tốt cho: Ảnh có nền sáng, chữ đen
    """
    img = cv2.imread(image_path)
    
    # Chuyển sang grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Tăng độ tương phản
    gray = cv2.equalizeHist(gray)
    
    # Threshold (nhị phân hóa)
    _, threshold = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    if SAVE_PROCESSED:
        cv2.imwrite("processed_v1.png", threshold)
    
    return threshold


def preprocess_image_v2(image_path):
    """
    Phương pháp 2: Nâng cao - Khử nhiễu + Adaptive Threshold
    Tốt cho: Ảnh có độ sáng không đều
    """
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Khử nhiễu
    denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
    
    # Adaptive threshold (thích nghi với từng vùng)
    threshold = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    
    if SAVE_PROCESSED:
        cv2.imwrite("processed_v2.png", threshold)
    
    return threshold


def preprocess_image_v3(image_path):
    """
    Phương pháp 3: Mạnh mẽ - Tăng kích thước + Sharpen + Morphology
    Tốt cho: Ảnh chữ nhỏ, mờ
    """
    img = cv2.imread(image_path)
    
    # Tăng kích thước ảnh lên 2x (giúp OCR đọc tốt hơn)
    img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Làm sắc nét (sharpen)
    kernel_sharpen = np.array([[-1,-1,-1],
                               [-1, 9,-1],
                               [-1,-1,-1]])
    sharpened = cv2.filter2D(gray, -1, kernel_sharpen)
    
    # Threshold
    _, threshold = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Morphology - Loại bỏ nhiễu nhỏ
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    morphed = cv2.morphologyEx(threshold, cv2.MORPH_CLOSE, kernel)
    
    if SAVE_PROCESSED:
        cv2.imwrite("processed_v3.png", morphed)
    
    return morphed


def preprocess_image_v4(image_path):
    """
    Phương pháp 4: Tối ưu cho menu - Dilation + Blur
    Tốt cho: Ảnh menu thực tế (có nhiều chi tiết)
    """
    img = cv2.imread(image_path)
    
    # Tăng size
    img = cv2.resize(img, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Làm mờ nhẹ để giảm nhiễu
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    
    # Tăng độ tương phản
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(blurred)
    
    # Threshold
    _, threshold = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Dilation - Làm chữ rõ hơn
    kernel = np.ones((2, 2), np.uint8)
    dilated = cv2.dilate(threshold, kernel, iterations=1)
    
    if SAVE_PROCESSED:
        cv2.imwrite("processed_v4.png", dilated)
    
    return dilated


# ======================================================
# 🔹 HÀM OCR VỚI TESSERACT
# ======================================================

def ocr_with_config(image, config_name, tesseract_config):
    """Chạy OCR với config tùy chỉnh"""
    # Chuyển numpy array về PIL Image
    pil_image = Image.fromarray(image)
    
    # OCR
    text = pytesseract.image_to_string(pil_image, lang="vie+eng", config=tesseract_config)
    
    return text


# ======================================================
# 🔹 TEST TẤT CẢ CÁC PHƯƠNG PHÁP
# ======================================================

def test_all_methods(image_path):
    """Test tất cả các phương pháp và so sánh kết quả"""
    
    print("🚀 BẮT ĐẦU TEST CẢI THIỆN TESSERACT OCR\n")
    print(f"📸 Ảnh gốc: {image_path}\n")
    print("=" * 80)
    
    # Tesseract configs
    configs = {
        "Mặc định": "",
        "PSM 6 (Khối text đơn)": "--psm 6",
        "PSM 3 (Tự động)": "--psm 3",
        "PSM 11 (Text rải rác)": "--psm 11",
    }
    
    preprocessing_methods = {
        "Gốc (không xử lý)": lambda x: cv2.cvtColor(cv2.imread(x), cv2.COLOR_BGR2GRAY),
        "V1: Grayscale + Threshold": preprocess_image_v1,
        "V2: Khử nhiễu + Adaptive": preprocess_image_v2,
        "V3: Resize + Sharpen": preprocess_image_v3,
        "V4: Tối ưu menu": preprocess_image_v4,
    }
    
    results = []
    
    for prep_name, prep_func in preprocessing_methods.items():
        print(f"\n📋 PHƯƠNG PHÁP: {prep_name}")
        print("-" * 80)
        
        # Xử lý ảnh
        processed_img = prep_func(image_path)
        
        # Thử các config khác nhau
        best_text = ""
        best_config = ""
        max_length = 0
        
        for config_name, tesseract_config in configs.items():
            text = ocr_with_config(processed_img, config_name, tesseract_config)
            text_length = len(text.strip())
            
            if text_length > max_length:
                max_length = text_length
                best_text = text
                best_config = config_name
        
        print(f"✅ Config tốt nhất: {best_config} ({max_length} ký tự)")
        print(f"📝 Preview (100 ký tự đầu):\n{best_text[:100]}...")
        
        results.append({
            "method": prep_name,
            "config": best_config,
            "text": best_text,
            "length": max_length
        })
    
    # Tìm phương pháp tốt nhất
    print("\n" + "=" * 80)
    print("🏆 KẾT QUẢ TỔNG HỢP")
    print("=" * 80)
    
    best_result = max(results, key=lambda x: x["length"])
    
    for r in results:
        marker = "🥇" if r == best_result else "  "
        print(f"{marker} {r['method']:<30} | {r['config']:<25} | {r['length']} ký tự")
    
    print("\n" + "=" * 80)
    print(f"🎯 PHƯƠNG PHÁP TỐT NHẤT: {best_result['method']}")
    print(f"📊 Config: {best_result['config']}")
    print(f"📝 Kết quả đầy đủ:")
    print("=" * 80)
    print(best_result['text'])
    print("=" * 80)
    
    return best_result


# ======================================================
# 🔹 CHẠY TEST
# ======================================================

if __name__ == "__main__":
    if not os.path.exists(IMAGE_PATH):
        print(f"❌ Không tìm thấy ảnh: {IMAGE_PATH}")
        exit(1)
    
    # Cài đặt opencv-python nếu chưa có
    try:
        import cv2
    except ImportError:
        print("⚠️ Chưa cài opencv-python!")
        print("👉 Chạy lệnh: pip install opencv-python")
        exit(1)
    
    best = test_all_methods(IMAGE_PATH)
    
    print("\n✨ HOÀN THÀNH!")
    print("\n💡 HƯỚNG DẪN SỬ DỤNG KẾT QUẢ:")
    print(f"   - Copy phương pháp '{best['method']}' vào get_flavor.py")
    print(f"   - Sử dụng config: {best['config']}")
    
    if SAVE_PROCESSED:
        print("\n📁 Các ảnh đã xử lý được lưu tại:")
        print("   - processed_v1.png, processed_v2.png, processed_v3.png, processed_v4.png")
        print("   👉 Mở các file này để xem ảnh sau xử lý")