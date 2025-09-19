FROM python:3.11-slim

WORKDIR /app

COPY apps/api/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY apps/api/ /app/

RUN chmod +x /app/pre_deploy_script.sh || true

ENV PYTHONPATH=/app

CMD sh -c 'gunicorn -w 2 -k gthread -b 0.0.0.0:$PORT src.main:app'

