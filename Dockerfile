# Use official lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy dependencies first (for caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose port (default Flask port)
EXPOSE 5001

# Run Gunicorn directly on startup
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "app:app"]
