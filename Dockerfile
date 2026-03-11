FROM python:3.11-slim

WORKDIR /app

# Install deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Create data & logs dirs
RUN mkdir -p data logs

# Default: run backend
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
