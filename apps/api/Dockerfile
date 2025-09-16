FROM python:3.9-slim-buster

# Set the working directory to /app
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Debugging steps: List files and print Python path
RUN echo "--- Listing files in /app ---"
RUN ls -R /app
RUN echo "--- Python Path ---"
RUN python -c "import sys; print(sys.path)"

# Change the working directory to the src folder
WORKDIR /app/src

# Debugging steps: List files and print Python path in /app/src
RUN echo "--- Listing files in /app/src ---"
RUN ls -R /app/src
RUN echo "--- Python Path in /app/src ---"
RUN python -c "import sys; print(sys.path)"

# Use gunicorn to serve the Flask application
# The format is 'module_name:app_instance_name'
# Since we are in the 'src' directory, it's just 'main:app'
CMD ['gunicorn', '-w', '4', '-b', '0.0.0.0:5000', 'main:app']
