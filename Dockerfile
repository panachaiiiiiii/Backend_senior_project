# ใช้ Python image ที่คุณใช้อยู่
FROM python:3.11-slim 

# ติดตั้งระบบพื้นฐานที่จำเป็นสำหรับการ Build library (แก้ปัญหา C++ build tools ใน Linux)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# อัปเกรด pip และติดตั้งแพ็กเกจ
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]