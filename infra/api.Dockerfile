FROM python:3.11-slim

# 1) 設定工作目錄
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 2) 系統相依
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# 3) 複製 requirements 並安裝
COPY apps/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# 4) 複製完整 API 程式碼
COPY apps/api /app

# 5) 切到 API 根目錄，這樣 /app/src 才能被找到
WORKDIR /app

# 6) 服務環境
ENV PORT=8000
EXPOSE 8000

# 7) 用 gunicorn 啟動 Flask app
CMD ["sh", "-c", "gunicorn -w 2 -k gthread -b 0.0.0.0:${PORT} src.main:app"]

