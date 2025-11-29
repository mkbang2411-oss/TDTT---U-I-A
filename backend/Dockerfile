FROM python:3.11-slim

WORKDIR /app

# ✅ Copy requirements từ backend/
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ✅ Copy code backend
COPY backend/ .

# ✅ Copy frontend vào container
COPY frontend/ /frontend

EXPOSE 5000

CMD ["python", "main_web.py"]