FROM python:3.11-slim

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Set working directory
WORKDIR /app

# Install dependencies first for better caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . ./

# Run the web service on container startup using Uvicorn.
# Cloud Run injects the $PORT environment variable (default is 8080)
CMD ["sh", "-c", "uvicorn app_build.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
