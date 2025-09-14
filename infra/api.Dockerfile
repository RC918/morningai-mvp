FROM python:3.11-slim

# 系統相依
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# 放在 /app 當作 API 的根
WORKDIR /app

# 2) 環境變數
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

<<<<<<< HEAD
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
=======
# 先裝 Python 相依
COPY apps/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# 複製 API 原始碼到 /app
COPY apps/api /app/apps/api

# 切換到 API 應用程式的根目錄
WORKDIR /app/apps/api/src

# 偵錯指令：列出當前目錄內容
RUN ls -R .

# 偵錯指令：列印 Python 模組搜尋路徑
RUN python -c "import sys; print(sys.path)"

# 服務埠與啟動
ENV PORT=8000
EXPOSE 8000

# 用 gunicorn 啟動 Flask app：main:app
CMD ["gunicorn", "-w", "2", "-k", "gthread", "-b", "0.0.0.0:${PORT}", "main:app"]

>>>>>>> 4e1f3db (fix(api): set WORKDIR to /app/apps/api/src and CMD to main:app)
