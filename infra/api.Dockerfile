FROM python:3.11-slim

# 系統相依
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# 放在 /app 當作 API 的根
WORKDIR /app/apps/api

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 先裝 Python 相依
COPY apps/api/requirements.txt /app/apps/api/requirements.txt
RUN pip install --no-cache-dir -r /app/apps/api/requirements.txt

# 複製 API 原始碼到 /app/apps/api
COPY apps/api /app/apps/api

# 偵錯指令：列出 /app/apps/api 目錄內容
RUN ls -R /app/apps/api

# 偵錯指令：列印 Python 模組搜尋路徑
RUN python -c "import sys; print(sys.path)"

# 服務埠與啟動
ENV PORT=8000
EXPOSE 8000

# 用 gunicorn 啟動 Flask app：main:app
CMD ["gunicorn", "-w", "2", "-k", "gthread", "-b", "0.0.0.0:${PORT}", "main:app"]

