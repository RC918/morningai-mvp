FROM python:3.11-slim

# 放在 /app 當作 API 的根
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 系統相依
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# 先裝 Python 相依
COPY apps/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# 複製 API 原始碼到 /app，這裡應該會有 /app/src/main.py
COPY apps/api /app

# 關鍵：讓 Python 能 import 到 /app 下的 src 模組
ENV PYTHONPATH=/app

# 服務埠與啟動
ENV PORT=8000
EXPOSE 8000

# 用 gunicorn 啟動 Flask app：src.main:app
CMD ["sh","-c","gunicorn -w 2 -k gthread -b 0.0.0.0:${PORT} src.main:app"]

