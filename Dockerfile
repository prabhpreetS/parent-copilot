# Use Python 3.9 as the base image
FROM python:3.10-slim

# Set working directory in the container
WORKDIR /app

# Set environment variables
# - Prevents Python from writing pyc files
# - Ensures Python outputs are sent straight to terminal without buffering

ARG ENVFILE
USER root
COPY ./ ./
COPY $ENVFILE ./.env

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the project code into the container
COPY . .

# Expose the port the app runs on
# EXPOSE 8000

# Command to run the application
 CMD ["uvicorn", "src.v1.main:app", "--host", "0.0.0.0", "--port", "8000"]

