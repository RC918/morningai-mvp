FROM python:3.9-slim-buster

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set PYTHONPATH to include the current directory (which is /app) and the src subdirectory
ENV PYTHONPATH=/app:/app/src

# Use gunicorn to serve the Flask application
# The format is 'module_name:app_instance_name'
# Since main.py is in src, and the app instance is named 'app' in main.py
# it should be src.main:app
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "src.main:app"]
