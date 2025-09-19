FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 為了利用 Docker 的快取機制，先複製並安裝相依套件
COPY apps/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# 複製應用程式的程式碼
COPY apps/api/ /app/

# 賦予 pre-deploy 腳本執行權限 (如果存在)
RUN chmod +x /app/pre_deploy_script.sh || true

# 設定 PYTHONPATH，讓 Python 能夠找到 src 模組
ENV PYTHONPATH=/app

# 設定啟動指令，使用 sh -c 來確保 $PORT 環境變數能被正確解析
CMD sh -c 'gunicorn -w 2 -k gthread -b 0.0.0.0:$PORT src.main:app'

