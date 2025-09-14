FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# deps
COPY apps/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# src
COPY apps/api /app

# runtime
ENV PORT=8000
EXPOSE 8000
# 關鍵：src.main:app（因為程式碼被 COPY 到 /app）
CMD ["sh","-c","gunicorn -w 2 -k gthread -b 0.0.0.0:${PORT} src.main:app"]

