FROM python:3.11-slim

# 系統相依
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# 放在 /app 當作 API 的根
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 先裝 Python 相依
COPY apps/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# 複製 API 原始碼到 /app，這裡應該會有 /app/src/main.py
COPY apps/api /app

# 偵錯指令：列出 /app 目錄內容
RUN ls -R /app

# 偵錯指令：列印 Python 模組搜尋路徑
RUN python -c "import sys; print(sys.path)"

# 關鍵：讓 Python 能 import 到 /app 下的 src 模組
ENV PYTHONPATH=/app

# 服務埠與啟動
ENV PORT=8000
EXPOSE 8000

# 用 gunicorn 啟動 Flask app：src.main:app
CMD ["sh","-c","gunicorn -w 2 -k gthread -b 0.0.0.0:${PORT} src.main:app"]

