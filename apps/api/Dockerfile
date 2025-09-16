FROM python:3.9-slim-buster

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set PYTHONPATH to include the current directory (which is /app) and the src subdirectory
ENV PYTHONPATH=/app:/app/src

# Use gunicorn to serve the Flask application
# Explicitly set --pythonpath to ensure src is in the Python path
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--pythonpath", "src", "src.main:app"]
