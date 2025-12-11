import requests
import json

# Thay YOUR_API_KEY bằng key thật
API_KEY = "AIzaSyC9_hNLV5J6Dy2gX5QgLLdA8RGAnE-rWqg"

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={API_KEY}"

payload = {
    "contents": [{
        "parts": [{"text": "Say hello"}]
    }]
}

response = requests.post(url, json=payload)

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 403:
    print("\n❌ Key chưa valid! Kiểm tra:")
    print("1. API có được enable trong Cloud Console?")
    print("2. Billing có được enable?")
    print("3. Key có bị restrict sai?")