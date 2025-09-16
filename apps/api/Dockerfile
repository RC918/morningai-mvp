FROM python:3.9-slim-buster

# Set the working directory to /app
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code from apps/api to /app
COPY . .

# Debugging steps: List files and print Python path
RUN echo "--- Listing files in /app ---"
RUN ls -R /app
RUN echo "--- Python Path ---"
RUN python -c "import sys; print(sys.path)"

# Use gunicorn to serve the Flask application
# The format is 'module_name:app_instance_name'
# Since the app is in src/main.py, and WORKDIR is /app, we reference it as src.main:app
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "src.main:app"]

