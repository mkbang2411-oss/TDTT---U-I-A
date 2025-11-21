from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

img = Image.open(r"D:\Food_map\frontend\images\3.2.png")  # ví dụ: r"D:\Food_map\frontend\images\2.2.png"
text = pytesseract.image_to_string(img, lang="vie+eng")
print(text)
