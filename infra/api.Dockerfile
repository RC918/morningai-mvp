FROM python:3.11-slim

# 1) 以 /app 為根
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# 2) 先裝相依
COPY apps/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# 3) 複製原始碼（包含 src/main.py）
COPY apps/api /app

# 4) 切到 src，之後的相對匯入就找得到 main.py
WORKDIR /app/src

ENV PORT=8000
EXPOSE 8000

# 5) 直接以 main:app 啟動
CMD ["sh","-c","gunicorn -w 2 -k gthread -b 0.0.0.0:${PORT} main:app"]
