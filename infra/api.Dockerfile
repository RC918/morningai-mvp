FROM python:3.11-slim

# 設定工作目錄在 /app
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 安裝系統相依
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# 安裝 Python 相依
COPY apps/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# 複製 API 原始碼
COPY apps/api /app

# 切換到 src 目錄，這裡有 main.py
WORKDIR /app/src

ENV PORT=8000
EXPOSE 8000

# 用 gunicorn 啟動 main.py 內的 app
CMD ["sh","-c","gunicorn -w 2 -k gthread -b 0.0.0.0:${PORT} main:app"]
