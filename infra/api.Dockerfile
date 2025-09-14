FROM python:3.11-slim

# 1) 設定工作目錄
WORKDIR /app

# 2) 環境變數
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 3) 系統依賴
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# 4) 安裝 Python 套件
COPY apps/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# 5) 複製 API 原始碼
COPY apps/api /app

# 6) 設定環境變數，讓 Python 能找到 /app/src
ENV PYTHONPATH=/app

# 7) Port 設定
ENV PORT=8000
EXPOSE 8000

# 8) 啟動 Gunicorn，正確指向 src/main.py 裡的 app
CMD ["sh", "-c", "gunicorn -w 2 -k gthread -b 0.0.0.0:${PORT} src.main:app"]
