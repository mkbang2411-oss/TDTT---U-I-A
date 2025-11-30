FROM python:3.11-slim

WORKDIR /app

# Copy requirements trước
COPY backend/requirements.txt .

# ✅ THÊM timeout và retry
RUN pip install --no-cache-dir \
    --default-timeout=1000 \
    --retries 5 \
    -r requirements.txt

# Copy ONLY backend code
COPY backend/ .

EXPOSE 5000

CMD ["python", "main_web.py"]