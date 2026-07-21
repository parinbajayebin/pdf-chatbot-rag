FROM python:3.10-slim

WORKDIR /app

# Copy requirements and install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code
COPY app /app/app

# Create folder structure for dynamic local uploads and chroma vector storage, granting open permissions for non-root runtime environments
RUN mkdir -p /app/data/chroma_db /app/data/uploads && chmod -R 777 /app/data

# Expose default port
EXPOSE 8000

# Start application using uvicorn, dynamically binding to $PORT environment variable
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
