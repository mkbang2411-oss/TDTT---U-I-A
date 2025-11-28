import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'user_management.settings')
django.setup()

from accounts.models import FoodStory


def create_food_stories():
    """Tạo dữ liệu mẫu cho 3 món ăn"""
    
    stories = [
        {
            'map_name': 'banh_mi',
            'title': 'Bánh Mì - Biểu Tượng Ẩm Thực Việt Nam',
            'description': 'Sự kết hợp hoàn hảo giữa ẩm thực Pháp và Việt Nam',
            'history': '''
                Bánh mì Việt Nam ra đời vào thời kỳ Pháp thuộc (1858-1954), 
                khi người Pháp mang bánh baguette đến Việt Nam. Tuy nhiên, 
                người Việt đã sáng tạo biến tấu bằng cách thêm nhân phong phú: 
                pate, thịt nguội, chả lụa, rau thơm, dưa chuột, ớt... 
                
                Đến thập niên 1950-1960, bánh mì trở thành món ăn phổ biến ở 
                miền Nam, đặc biệt tại Sài Gòn. Ngày nay, bánh mì Việt Nam 
                đã trở thành biểu tượng ẩm thực được yêu thích trên toàn thế giới.
            ''',
            'fun_facts': [
                '🏆 Năm 2011, từ "bánh mì" được đưa vào từ điển Oxford',
                '🌍 Bánh mì Việt Nam nằm trong top 10 món sandwich ngon nhất thế giới',
                '💰 Giá một ổ bánh mì ở Sài Gòn trung bình 15.000 - 25.000đ',
                '🥖 Bánh mì Việt Nam mềm hơn baguette Pháp vì ít gluten hơn',
                '🔥 Có hơn 50 biến thể bánh mì khác nhau tại Việt Nam'
            ],
            'variants': [
                'Bánh mì pate',
                'Bánh mì thịt nướng',
                'Bánh mì xíu mại',
                'Bánh mì ốp la',
                'Bánh mì chả cá',
                'Bánh mì gà xé',
                'Bánh mì heo quay'
            ],
            'origin_region': 'Thành phố Hồ Chí Minh (Sài Gòn)',
            'image_url': 'Picture/banh_mi.png',
            'video_url': '', 
            'unesco_recognized': False,
            'recognition_text': ''
        },
        {
            'map_name': 'com_tam',
            'title': 'Cơm Tấm - Hồn Sài Gòn Trong Từng Hạt Gạo',
            'description': 'Món ăn bình dân đặc trưng của người Sài Gòn',
            'history': '''
                Cơm tấm xuất hiện từ đầu thế kỷ 20 tại khu vực Chợ Lớn - Sài Gòn. 
                Ban đầu, "tấm" là những hạt gạo bị vỡ trong quá trình xay xát, 
                được bán với giá rẻ cho người lao động nghèo.
                
                Từ món ăn của người lao động, cơm tấm dần trở thành đặc sản 
                đường phố với cách chế biến tinh tế: cơm được nấu mềm dẻo, 
                ăn kèm sườn nướng, bì, chả trứng, nước mắm pha chua ngọt...
                
                Ngày nay, cơm tấm không chỉ là món ăn bình dân mà còn xuất hiện 
                trong các nhà hàng cao cấp với nhiều biến tấu sáng tạo.
            ''',
            'fun_facts': [
                '🍚 "Tấm" nghĩa là hạt gạo bị vỡ, thường chiếm 5-7% sau xay xát',
                '⏰ Cơm tấm có thể ăn cả 3 bữa: sáng, trưa, tối',
                '💡 Món ăn yêu thích của nhiều người nước ngoài khi đến Việt Nam',
                '🔥 Sườn nướng phải ướp tỏi, mật ong, nước mắm ít nhất 2 tiếng',
                '📍 Khu Chợ Lớn (Quận 5) là nơi cơm tấm nổi tiếng nhất Sài Gòn'
            ],
            'variants': [
                'Cơm tấm sườn',
                'Cơm tấm sườn bì chả',
                'Cơm tấm gà nướng',
                'Cơm tấm tứ sắc',
                'Cơm tấm bò nướng',
                'Cơm tấm chả cá',
                'Cơm tấm phong cách mới (thêm trứng ốp la, pate)'
            ],
            'origin_region': 'Thành phố Hồ Chí Minh (Sài Gòn)',
            'image_url': 'Picture/com_tam.png',
            'video_url': '', 
            'unesco_recognized': False,
            'recognition_text': ''
        },
        {
            'map_name': 'bun_bo_hue',
            'title': 'Bún Bò Huế - Tinh Hoa Ẩm Thực Cố Đô',
            'description': 'Món ăn đặc sản xứ Huế với hương vị đậm đà khó quên',
            'history': '''
                Bún bò Huế xuất hiện từ đầu thế kỷ 20 tại cố đô Huế. 
                Món ăn này mang đậm nét ẩm thực cung đình với sự cầu kỳ 
                trong cách chế biến và trình bày.
                
                Điểm đặc biệt của bún bò Huế là nước dùng được ninh từ xương 
                ống bò, thịt bò, giò heo trong nhiều giờ, thêm sả, mắm ruốc 
                và ớt tạo nên hương vị cay nồng đặc trưng.
                
                Từ xứ Huế, món ăn này lan rộng ra cả nước và trở thành một 
                trong những món bún nổi tiếng nhất Việt Nam, được UNESCO 
                ghi nhận là Di sản ẩm thực phi vật thể của nhân loại.
            ''',
            'fun_facts': [
                '🏛️ UNESCO công nhận Bún Bò Huế là Di sản ẩm thực (2023)',
                '🌶️ Nước dùng phải ninh từ 6-8 tiếng để đạt độ đậm đà',
                '🔴 Màu đỏ đặc trưng đến từ dầu màu điều (annatto oil)',
                '🍋 Ăn kèm rau sống: giá, rau thơm, hoa chuối, mía lù',
                '👑 Món ăn ưa thích của các vua chùa Huế thời xưa'
            ],
            'variants': [
                'Bún bò Huế truyền thống',
                'Bún bò giò heo',
                'Bún bò chả cua',
                'Bún bò cầu mống',
                'Bún bò khô (không nước)',
                'Bún bò Nam Bộ (vị ngọt nhẹ hơn)',
                'Bún bò cung đình (nhiều topping cao cấp)'
            ],
            'origin_region': 'Thành phố Huế',
            'image_url': 'Picture/bun_bo_hue.png',
            'video_url': '', 
            'unesco_recognized': True,
            'recognition_text': 'Năm 2023, Bún Bò Huế được UNESCO công nhận là Di sản ẩm thực phi vật thể của nhân loại'
        }
    ]
    
    for story_data in stories:
        story, created = FoodStory.objects.update_or_create(
            map_name=story_data['map_name'],
            defaults=story_data
        )
        
        if created:
            print(f"✅ Tạo mới: {story.title}")
        else:
            print(f"🔄 Cập nhật: {story.title}")
    
    print("\n🎉 Hoàn thành! Đã tạo/cập nhật 3 food stories.")

if __name__ == '__main__':
    create_food_stories()