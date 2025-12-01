FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY backend/requirements.txt .

# Copy backend
COPY backend/ .

# Copy frontend files (HTML, CSS, JS)
COPY frontend/*.html /frontend/
COPY frontend/*.css /frontend/
COPY frontend/*.js /frontend/


# Copy font
COPY frontend/font /frontend/font

# KHÔNG COPY:
# - images/ (1.5GB) - đã lên Cloudinary
# - icons/ (0.7MB) - đã lên Cloudinary
# - Picture/ (36MB) - đã lên Cloudinary
# - disc_covers/ (0.1MB) - đã lên Cloudinary
# - music/ (172MB) - bỏ qua

# ✅ THÊM timeout và retry
RUN pip install --no-cache-dir \
    --default-timeout=1000 \
    --retries 5 \
    -r requirements.txt

# Copy ONLY backend code
COPY backend/ .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "main_web:app"]