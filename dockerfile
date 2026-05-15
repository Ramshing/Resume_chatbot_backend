FROM python:3.12-slim

# Prevent python from buffering logs
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port (optional but recommended)
EXPOSE 8000

# Start FastAPI app with Railway dynamic PORT support
CMD gunicorn -w 1 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:${PORT:-8000}