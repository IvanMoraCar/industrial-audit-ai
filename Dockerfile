# 1. Base image with Python 3.12
FROM python:3.12-slim

# 2. Install Linux system-level dependencies with explicit error handling
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    poppler-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 3. Establish operational directory
WORKDIR /app

# 4. Copy and install library requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of the application files
COPY . .

# 6. Command to start the application using the dynamic port assigned by Render
CMD ["uvicorn", "api_auditor:app", "--host", "0.0.0.0", "--port", "8000"]