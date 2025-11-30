FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

# ✅ THÊM timeout
RUN pip install --no-cache-dir \
    --default-timeout=1000 \
    --retries 5 \
    -r requirements.txt

COPY . .

EXPOSE 8000

# ✅ Tách migrate ra script riêng (chỉ chạy 1 lần khi setup)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]