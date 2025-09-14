FROM python:3.11-slim

# 1) 設定工作目錄
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 2) 安裝系統相依
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# 3) 安裝 Python 相依
COPY apps/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# 4) 複製 API 原始碼 (包含 src/main.py)
COPY apps/api /app

# 5) 設定工作目錄到 src，這樣 gunicorn 就能找到 main.py
WORKDIR /app/src

# 6) 暴露 Port
ENV PORT=8000
EXPOSE 8000

# 7) 啟動 gunicorn，指向 main.py 裡的 app 物件
CMD ["sh", "-c", "gunicorn -w 2 -k gthread -b 0.0.0.0:${PORT} main:app"]
