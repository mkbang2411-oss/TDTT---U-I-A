from nudenet import NudeDetector
import os

# Khởi tạo detector (chỉ 1 lần khi import)
print("🔄 Loading NudeNet model...")
detector = NudeDetector()
print("✅ NudeNet model loaded!\n")

def check_nsfw_image_local(image_file_or_path):
    """
    Kiểm tra ảnh NSFW bằng NudeNet (local, offline)
    
    Args:
        image_file_or_path: File path (str) hoặc Django UploadedFile
    
    Returns:
        dict: {
            'is_safe': bool,
            'reason': str,
            'details': dict
        }
    """
    
    temp_path = None
    cleanup = False
    
    try:
        # Xử lý input
        if isinstance(image_file_or_path, str):
            temp_path = image_file_or_path
            cleanup = False
        else:
            # Lưu tạm Django UploadedFile
            import tempfile
            temp_path = tempfile.mktemp(suffix='.jpg')
            
            with open(temp_path, 'wb') as f:
                for chunk in image_file_or_path.chunks():
                    f.write(chunk)
            
            cleanup = True
        
        # 🔍 PHÁT HIỆN
        detections = detector.detect(temp_path)
        
        # 🚨 DANH SÁCH CLASS NGUY HIỂM (✅ TÊN ĐÚNG)
        unsafe_classes = {
            'ANUS_EXPOSED': 'nội dung nhạy cảm',
            'BUTTOCKS_EXPOSED': 'nội dung nhạy cảm',
            'FEMALE_BREAST_EXPOSED': 'nội dung 18+',          # ✅ TÊN ĐÚNG
            'FEMALE_GENITALIA_EXPOSED': 'nội dung 18+',       # ✅ TÊN ĐÚNG
            'MALE_GENITALIA_EXPOSED': 'nội dung 18+',         # ✅ TÊN ĐÚNG
            'MALE_BREAST_EXPOSED': 'nội dung nhạy cảm',
        }
        
        print(f"\n🔍 [NUDENET DETECTION]")
        
        max_unsafe_score = 0
        max_unsafe_class = None
        
        for detection in detections:
            class_name = detection['class']
            confidence = detection['score']
            
            print(f"   {class_name}: {confidence*100:.1f}%")
            
            # Tìm class nguy hiểm nhất
            if class_name in unsafe_classes:
                if confidence > max_unsafe_score:
                    max_unsafe_score = confidence
                    max_unsafe_class = class_name
        
        # 🚨 CHẶN NẾU > 60% CONFIDENCE
        if max_unsafe_class and max_unsafe_score > 0.6:
            print(f"   ❌ BLOCKED: {max_unsafe_class} ({max_unsafe_score*100:.1f}%)\n")
            
            if cleanup and os.path.exists(temp_path):
                os.remove(temp_path)
            
            return {
                'is_safe': False,
                'reason': f'Phát hiện {unsafe_classes[max_unsafe_class]} ({max_unsafe_score*100:.1f}%)',
                'details': {
                    'class': max_unsafe_class,
                    'confidence': round(max_unsafe_score * 100, 1),
                    'all_detections': detections
                }
            }
        
        # ✅ ẢNH AN TOÀN
        print(f"   ✅ Image is safe\n")
        
        if cleanup and os.path.exists(temp_path):
            os.remove(temp_path)
        
        return {
            'is_safe': True,
            'reason': 'OK',
            'details': detections
        }
        
    except Exception as e:
        print(f"❌ NudeNet Error: {e}")
        import traceback
        traceback.print_exc()
        
        # Cleanup nếu lỗi
        if cleanup and temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        
        # Fail-safe: cho qua nếu lỗi
        return {
            'is_safe': True,
            'reason': f'Error: {str(e)}',
            'details': {}
        }