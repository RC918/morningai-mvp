FROM python:3.9-slim-buster

# Set the working directory to /app
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire apps/api directory content to /app
COPY . .

# Set PYTHONPATH to include /app/src, so Python can find modules like 'models'
ENV PYTHONPATH=/app/src

# Add debugging commands to list contents and show Python path
RUN echo "--- Listing /app contents ---"
RUN ls -R /app
RUN echo "--- Python Path ---"
RUN python -c "import sys; print(sys.path)"

# Use gunicorn to serve the Flask application
# The format is 'module_name:app_instance_name'
# Since PYTHONPATH includes /app/src, we can reference main:app directly
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "main:app"]

