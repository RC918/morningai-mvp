FROM python:3.11-slim

# 系統相依
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# 設定工作目錄為 /app
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 複製 requirements 並安裝
COPY apps/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# 複製 apps/api 的內容到 /app
COPY apps/api /app

# 偵錯指令：列出 /app 目錄內容
RUN ls -R /app

# 偵錯指令：列印 Python 模組搜尋路徑
RUN python -c "import sys; print(sys.path)"

# 服務埠與啟動
ENV PORT=8000
EXPOSE 8000

# 用 gunicorn 啟動 Flask app，並在命令中設定 PYTHONPATH
CMD ["sh", "-c", "PYTHONPATH=/app gunicorn -w 2 -k gthread -b 0.0.0.0:${PORT} src.main:app"]

