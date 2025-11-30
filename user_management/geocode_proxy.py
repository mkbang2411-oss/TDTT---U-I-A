# geocode_proxy.py (hoặc thêm vào views.py có sẵn)
import requests
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET"])
def geocode_proxy(request):
    address = request.GET.get('address', '')
    
    if not address:
        return JsonResponse({'error': 'Thiếu địa chỉ'}, status=400)
    
    url = f'https://nominatim.openstreetmap.org/search?format=json&q={address}&limit=1'
    
    try:
        response = requests.get(
            url, 
            headers={'User-Agent': 'UIA-Food-Finder/1.0'},
            timeout=5
        )
        data = response.json()
        
        if data and len(data) > 0:
            return JsonResponse({
                'lat': data[0]['lat'],
                'lon': data[0]['lon'],
                'display_name': data[0].get('display_name', '')
            })
        else:
            return JsonResponse({'error': 'Không tìm thấy địa điểm'}, status=404)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)