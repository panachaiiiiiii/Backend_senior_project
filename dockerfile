FROM python:3.13-slim

WORKDIR /app

# อัปเดต pip และติดตั้ง dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# ไม่ต้อง Fix PORT ใน ENV ก็ได้ เพราะ Railway จะฉีดค่ามาให้เอง
# แต่ถ้าจะใส่ไว้เป็น Default สำหรับรัน Local ก็ทำได้ครับ
ENV PORT=8000

# ใช้คำสั่งที่ยืดหยุ่นต่อการจัดการ Port ของ Cloud Provider
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}