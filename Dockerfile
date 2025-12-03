# Stage 1: Builder (Installs dependencies)
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime (Runs the app)
FROM python:3.11-slim

# Set timezone to UTC (Required for correct TOTP codes)
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

# Install Cron (The scheduler)
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

# Copy dependencies from Stage 1
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy your code
COPY . .

# Setup Cron Job
COPY cron/2fa-cron /etc/cron.d/2fa-cron
RUN chmod 0644 /etc/cron.d/2fa-cron
RUN crontab /etc/cron.d/2fa-cron

# Create folders for saving data
RUN mkdir -p /data /cron && chmod 755 /data /cron

# Expose Port 8080
EXPOSE 8080

# START COMMAND: Starts Cron AND your Python App
CMD cron && uvicorn main:app --host 0.0.0.0 --port 8080