FROM python:3.10-slim

# Prevent python from writing pyc files to disk and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

# Install system dependencies required for OpenCV, PyTorch, and YOLOv8
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY backend/ /app/backend/

# Create persistent storage directories (if not already created)
RUN mkdir -p /app/uploads /app/results /app/logs /app/weights

# Expose API port
EXPOSE 8000

# Default entrypoint (FastAPI app)
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
